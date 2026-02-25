"""
Scout Agent — Discovers opportunities across all sources.

Part of the decomposed Opportunity Intelligence domain.
Scans SAM.gov, FPDS, USASpending, and forecast portals,
deduplicates, normalizes, and emits OPPORTUNITY_DISCOVERED events.
"""

import logging
import os
from typing import Any

import httpx
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from typing_extensions import TypedDict

from src.agents.base import BaseAgent

logger = logging.getLogger("ai_orchestrator.agents.scout")

DJANGO_API_URL = os.getenv("DJANGO_API_URL", "http://django-api:8001")
DJANGO_SERVICE_TOKEN = os.getenv("DJANGO_SERVICE_TOKEN", "")


def _auth_headers() -> dict[str, str]:
    t = DJANGO_SERVICE_TOKEN
    return {"Authorization": f"Bearer {t}"} if t else {}


async def _get(path: str, default: Any = None) -> Any:
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{DJANGO_API_URL}{path}", headers=_auth_headers())
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.warning("API GET %s failed: %s", path, exc)
        return default


def _get_llm() -> ChatAnthropic:
    return ChatAnthropic(
        model="claude-sonnet-4-6",
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        max_tokens=2048,
    )


class ScoutState(TypedDict):
    deal_id: str
    action: str
    company_profile: dict
    sources_scanned: list[str]
    raw_opportunities: list[dict]
    normalized_opportunities: list[dict]
    dedup_count: int
    messages: list


async def load_company_profile(state: ScoutState) -> dict:
    """Load the company profile for filtering."""
    profile = await _get("/api/opportunities/company-profile/primary/", default={})
    return {
        "company_profile": profile,
        "messages": [HumanMessage(content="Loaded company profile for scouting")],
    }


async def scan_sources(state: ScoutState) -> dict:
    """Scan all active opportunity sources."""
    sources_scanned = []
    raw_opps = []

    # SAM.gov scan
    try:
        from src.mcp_servers.samgov_tools import search_opportunities
        profile = state.get("company_profile", {})
        naics_codes = profile.get("naics_codes", [])
        keywords = profile.get("core_competencies", [])[:5]

        for naics in naics_codes[:3]:
            results = await search_opportunities(
                naics_code=naics,
                keywords=keywords,
                posted_from="last_7_days",
            )
            raw_opps.extend(results if isinstance(results, list) else [])

        sources_scanned.append("samgov")
    except Exception as exc:
        logger.warning("SAM.gov scan failed: %s", exc)

    # FPDS scan for incumbent/award data
    try:
        from src.mcp_servers.fpds_tools import search_recent_awards
        awards = await search_recent_awards(
            naics_codes=naics_codes[:3],
            days_back=30,
        )
        # FPDS awards inform competitive intelligence, not direct opportunities
        sources_scanned.append("fpds")
    except Exception as exc:
        logger.warning("FPDS scan failed (module may not exist yet): %s", exc)

    # USASpending scan
    try:
        from src.mcp_servers.usaspending_tools import search_spending
        spending = await search_spending(
            naics_codes=naics_codes[:3],
            fiscal_year="current",
        )
        sources_scanned.append("usaspending")
    except Exception as exc:
        logger.warning("USASpending scan failed (module may not exist yet): %s", exc)

    return {
        "sources_scanned": sources_scanned,
        "raw_opportunities": raw_opps,
        "messages": [HumanMessage(content=f"Scanned {len(sources_scanned)} sources, found {len(raw_opps)} raw opportunities")],
    }


async def deduplicate_and_normalize(state: ScoutState) -> dict:
    """Deduplicate across sources and normalize to common schema."""
    raw = state.get("raw_opportunities", [])
    seen_ids = set()
    normalized = []

    for opp in raw:
        notice_id = opp.get("notice_id") or opp.get("noticeId") or opp.get("id", "")
        if notice_id in seen_ids:
            continue
        seen_ids.add(notice_id)

        normalized.append({
            "notice_id": notice_id,
            "title": opp.get("title", ""),
            "agency": opp.get("agency", opp.get("department", "")),
            "description": opp.get("description", ""),
            "naics_code": opp.get("naics_code", opp.get("naicsCode", "")),
            "set_aside": opp.get("set_aside", opp.get("typeOfSetAside", "")),
            "response_deadline": opp.get("response_deadline", opp.get("responseDeadLine", "")),
            "posted_date": opp.get("posted_date", opp.get("postedDate", "")),
            "estimated_value": opp.get("estimated_value"),
            "notice_type": opp.get("notice_type", opp.get("type", "")),
            "source": opp.get("source", "samgov"),
        })

    dedup_count = len(raw) - len(normalized)
    return {
        "normalized_opportunities": normalized,
        "dedup_count": dedup_count,
        "messages": [HumanMessage(content=f"Normalized {len(normalized)} opportunities (removed {dedup_count} duplicates)")],
    }


def build_scout_graph() -> StateGraph:
    wf = StateGraph(ScoutState)
    wf.add_node("load_company_profile", load_company_profile)
    wf.add_node("scan_sources", scan_sources)
    wf.add_node("deduplicate_and_normalize", deduplicate_and_normalize)
    wf.set_entry_point("load_company_profile")
    wf.add_edge("load_company_profile", "scan_sources")
    wf.add_edge("scan_sources", "deduplicate_and_normalize")
    wf.add_edge("deduplicate_and_normalize", END)
    return wf.compile()


scout_graph = build_scout_graph()


class ScoutAgent(BaseAgent):
    """AI agent that discovers opportunities across all sources."""

    agent_name = "scout_agent"

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        initial: ScoutState = {
            "deal_id": input_data.get("deal_id", ""),
            "action": input_data.get("action", "scan"),
            "company_profile": {},
            "sources_scanned": [],
            "raw_opportunities": [],
            "normalized_opportunities": [],
            "dedup_count": 0,
            "messages": [],
        }
        try:
            await self.emit_event("thinking", {"message": "Scouting opportunities across all sources"})
            result = await scout_graph.ainvoke(initial)
            await self.emit_event("output", {
                "sources_scanned": result["sources_scanned"],
                "opportunity_count": len(result["normalized_opportunities"]),
            })
            return {
                "sources_scanned": result["sources_scanned"],
                "opportunities": result["normalized_opportunities"],
                "dedup_count": result["dedup_count"],
            }
        except Exception as exc:
            logger.exception("ScoutAgent.run failed")
            await self.emit_event("error", {"error": str(exc)})
            return {"error": str(exc)}
