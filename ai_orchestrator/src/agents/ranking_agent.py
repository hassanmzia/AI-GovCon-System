"""
Ranking Agent — Ranks and prioritizes a set of scored opportunities.

Extracted from OpportunityAgent. Takes a list of opportunities with
pre-computed fit scores and applies multi-factor ranking logic:
  - Strategic alignment weight
  - Capacity availability weight
  - Timing / deadline urgency
  - Win probability estimate
  - Set-aside preference match

Emits OPPORTUNITIES_RANKED event with a ranked list.
"""

import logging
import os
from datetime import date, datetime
from typing import Any

import httpx
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from typing_extensions import TypedDict

from src.agents.base import BaseAgent

logger = logging.getLogger("ai_orchestrator.agents.ranking")

DJANGO_API_URL = os.getenv("DJANGO_API_URL", "http://django-api:8001")
DJANGO_SERVICE_TOKEN = os.getenv("DJANGO_SERVICE_TOKEN", "")

# Ranking weights — must sum to 1.0
WEIGHT_FIT_SCORE = 0.35
WEIGHT_WIN_PROBABILITY = 0.25
WEIGHT_STRATEGIC_ALIGNMENT = 0.20
WEIGHT_URGENCY = 0.12
WEIGHT_CAPACITY = 0.08


def _auth_headers() -> dict[str, str]:
    t = DJANGO_SERVICE_TOKEN
    return {"Authorization": f"Bearer {t}"} if t else {}


async def _get(path: str, default: Any = None) -> Any:
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
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


class RankingState(TypedDict):
    opportunities: list[dict]   # Each has: id, title, ai_score, response_deadline, estimated_value, set_aside
    company_profile: dict
    capacity_status: dict
    ranked_opportunities: list[dict]
    ranking_rationale: str
    messages: list


def _days_until_deadline(deadline_str: str | None) -> float:
    """Return days until deadline. Returns 999 if None or unparseable."""
    if not deadline_str:
        return 999.0
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(deadline_str, fmt)
            return (dt.date() - date.today()).days
        except ValueError:
            pass
    return 999.0


def _urgency_score(days: float) -> float:
    """Normalize deadline urgency to 0–1. Tighter deadline = higher score."""
    if days <= 0:
        return 0.0   # Past deadline — deprioritize
    if days <= 14:
        return 1.0
    if days <= 30:
        return 0.85
    if days <= 60:
        return 0.65
    if days <= 90:
        return 0.45
    if days <= 180:
        return 0.25
    return 0.10


def _capacity_score(capacity_status: dict, opportunity: dict) -> float:
    """
    Score 0–1 based on whether the company has capacity for this opportunity.
    Uses pipeline_utilization from capacity_status if available.
    """
    utilization = capacity_status.get("pipeline_utilization", 0.5)
    # Invert: low utilization (more capacity) → higher score
    capacity_available = max(0.0, 1.0 - utilization)
    # Small deals get a slight boost when capacity is tight
    est_value = opportunity.get("estimated_value") or 0
    if utilization > 0.85 and float(est_value) > 5_000_000:
        capacity_available *= 0.6
    return min(1.0, capacity_available)


def _compute_composite_score(opp: dict, capacity_status: dict) -> float:
    """Compute weighted composite ranking score for a single opportunity."""
    fit = float(opp.get("ai_score", 0.5))
    win_prob = float(opp.get("win_probability", 0.3))
    strategic = float(opp.get("strategic_alignment", opp.get("ai_score", 0.5)))
    days = _days_until_deadline(opp.get("response_deadline"))
    urgency = _urgency_score(days)
    capacity = _capacity_score(capacity_status, opp)

    composite = (
        WEIGHT_FIT_SCORE * fit
        + WEIGHT_WIN_PROBABILITY * win_prob
        + WEIGHT_STRATEGIC_ALIGNMENT * strategic
        + WEIGHT_URGENCY * urgency
        + WEIGHT_CAPACITY * capacity
    )
    return round(composite, 4)


async def load_context(state: RankingState) -> dict:
    """Load company profile and current capacity status."""
    profile = await _get("/api/opportunities/company-profile/primary/", default={})
    capacity = await _get("/api/deals/pipeline/capacity/", default={})

    return {
        "company_profile": profile,
        "capacity_status": capacity,
        "messages": [HumanMessage(content="Loaded ranking context")],
    }


async def score_and_rank(state: RankingState) -> dict:
    """Apply multi-factor ranking to all opportunities."""
    opps = state.get("opportunities", [])
    capacity = state.get("capacity_status", {})

    if not opps:
        return {
            "ranked_opportunities": [],
            "messages": [HumanMessage(content="No opportunities to rank")],
        }

    scored = []
    for opp in opps:
        composite = _compute_composite_score(opp, capacity)
        days = _days_until_deadline(opp.get("response_deadline"))
        scored.append({
            **opp,
            "composite_score": composite,
            "urgency_days": int(days) if days < 999 else None,
            "urgency_score": _urgency_score(days),
            "capacity_score": _capacity_score(capacity, opp),
        })

    # Sort descending by composite score
    ranked = sorted(scored, key=lambda x: x["composite_score"], reverse=True)

    # Assign rank positions
    for i, opp in enumerate(ranked):
        opp["rank"] = i + 1

    return {
        "ranked_opportunities": ranked,
        "messages": [HumanMessage(content=f"Ranked {len(ranked)} opportunities")],
    }


async def generate_ranking_rationale(state: RankingState) -> dict:
    """Use LLM to generate a brief rationale for top-3 opportunities."""
    ranked = state.get("ranked_opportunities", [])
    if not ranked:
        return {
            "ranking_rationale": "No opportunities to rank.",
            "messages": [HumanMessage(content="No ranking rationale needed")],
        }

    top3 = ranked[:3]
    try:
        llm = _get_llm()
        resp = await llm.ainvoke([
            SystemMessage(content=(
                "You are a business development director. Given the top-ranked opportunities "
                "with their composite scores, provide a concise 2-3 sentence rationale "
                "for why these should be the highest priority pursuits. Be specific."
            )),
            HumanMessage(content=(
                f"Top 3 ranked opportunities:\n"
                + "\n".join(
                    f"{i+1}. {o.get('title', 'N/A')} — "
                    f"Score: {o.get('composite_score', 0):.3f}, "
                    f"Fit: {o.get('ai_score', 0):.2f}, "
                    f"Deadline: {o.get('urgency_days', 'N/A')}d, "
                    f"Value: {o.get('estimated_value', 'N/A')}"
                    for i, o in enumerate(top3)
                )
                + f"\n\nTotal ranked: {len(ranked)} opportunities."
            )),
        ])
        rationale = resp.content
    except Exception as exc:
        logger.error("Ranking rationale LLM failed: %s", exc)
        rationale = (
            f"Top opportunity: {top3[0].get('title', 'N/A')} "
            f"(score {top3[0].get('composite_score', 0):.3f}). "
            "Rankings based on fit score, win probability, urgency, and capacity."
        )

    return {
        "ranking_rationale": rationale,
        "messages": [HumanMessage(content="Ranking rationale generated")],
    }


def build_ranking_graph() -> StateGraph:
    wf = StateGraph(RankingState)
    wf.add_node("load_context", load_context)
    wf.add_node("score_and_rank", score_and_rank)
    wf.add_node("generate_ranking_rationale", generate_ranking_rationale)
    wf.set_entry_point("load_context")
    wf.add_edge("load_context", "score_and_rank")
    wf.add_edge("score_and_rank", "generate_ranking_rationale")
    wf.add_edge("generate_ranking_rationale", END)
    return wf.compile()


ranking_graph = build_ranking_graph()


class RankingAgent(BaseAgent):
    """
    AI agent that ranks and prioritizes scored opportunities using
    multi-factor weighted scoring (fit, win probability, urgency, capacity).
    """

    agent_name = "ranking_agent"

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        opportunities = input_data.get("opportunities", [])
        if not opportunities:
            # Fetch unranked opportunities from Django if none provided
            opp_data = await _get("/api/opportunities/?ordering=-ai_score&limit=50", default={})
            opportunities = opp_data.get("results", []) if isinstance(opp_data, dict) else []

        initial: RankingState = {
            "opportunities": opportunities,
            "company_profile": {},
            "capacity_status": {},
            "ranked_opportunities": [],
            "ranking_rationale": "",
            "messages": [],
        }

        try:
            await self.emit_event("thinking", {"message": f"Ranking {len(opportunities)} opportunities"})
            result = await ranking_graph.ainvoke(initial)
            ranked = result.get("ranked_opportunities", [])
            await self.emit_event("output", {
                "ranked_count": len(ranked),
                "top_opportunity": ranked[0].get("title", "") if ranked else None,
            })
            return {
                "ranked_opportunities": ranked,
                "ranking_rationale": result.get("ranking_rationale", ""),
                "total_ranked": len(ranked),
            }
        except Exception as exc:
            logger.exception("RankingAgent.run failed")
            await self.emit_event("error", {"error": str(exc)})
            return {"error": str(exc)}
