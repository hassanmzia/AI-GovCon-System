"""
Fit Agent — Scores opportunities against company profile + capacity.

Part of the decomposed Opportunity Intelligence domain.
Enhances the existing scoring with capacity-aware ranking.
"""

import logging
import os
from typing import Any

import httpx
from src.llm_provider import get_chat_model
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from typing_extensions import TypedDict

from src.agents.base import BaseAgent

logger = logging.getLogger("ai_orchestrator.agents.fit")

DJANGO_API_URL = os.getenv("DJANGO_API_URL", "http://django-api:8001")
DJANGO_SERVICE_TOKEN = os.getenv("DJANGO_SERVICE_TOKEN", "")


def _auth_headers() -> dict[str, str]:
    t = DJANGO_SERVICE_TOKEN
    return {"Authorization": f"Bearer {t}"} if t else {}


async def _get(path: str, default: Any = None) -> Any:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{DJANGO_API_URL}{path}", headers=_auth_headers())
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.warning("API GET %s failed: %s", path, exc)
        return default


def _get_llm():
    return get_chat_model(max_tokens=2048)


class FitState(TypedDict):
    opportunity_id: str
    deal_id: str
    opportunity: dict
    company_profile: dict
    pipeline_load: dict
    factor_scores: dict
    capacity_score: float
    total_score: float
    recommendation: str
    rationale: str
    messages: list


async def load_context(state: FitState) -> dict:
    """Load opportunity, company profile, and current pipeline load."""
    opp_id = state.get("opportunity_id", "")
    deal_id = state.get("deal_id", "")

    opp = {}
    if opp_id:
        opp = await _get(f"/api/opportunities/{opp_id}/", default={})
    elif deal_id:
        deal = await _get(f"/api/deals/{deal_id}/", default={})
        opp = deal.get("opportunity_detail", {}) or {}

    profile = await _get("/api/opportunities/company-profile/primary/", default={})
    pipeline = await _get("/api/analytics/pipeline-load/", default={})

    return {
        "opportunity": opp,
        "company_profile": profile,
        "pipeline_load": pipeline,
        "messages": [HumanMessage(content=f"Loaded context for fit scoring: {opp.get('title', 'N/A')}")],
    }


async def score_factors(state: FitState) -> dict:
    """Score each fit factor individually."""
    opp = state.get("opportunity", {})
    profile = state.get("company_profile", {})

    # NAICS match
    opp_naics = opp.get("naics_code", "")
    company_naics = profile.get("naics_codes", [])
    naics_score = 1.0 if opp_naics in company_naics else 0.0

    # PSC match
    opp_psc = opp.get("psc_code", "")
    company_psc = profile.get("psc_codes", [])
    psc_score = 1.0 if opp_psc in company_psc else 0.0

    # Keyword overlap
    opp_kw = set(k.lower() for k in opp.get("keywords", []))
    comp_kw = set(k.lower() for k in profile.get("core_competencies", []))
    keyword_score = len(opp_kw & comp_kw) / max(len(opp_kw), 1) if opp_kw else 0.5

    # Set-aside match
    opp_sa = opp.get("set_aside", "")
    company_sa = profile.get("set_aside_categories", [])
    if not opp_sa:
        set_aside_score = 0.7
    else:
        set_aside_score = 1.0 if opp_sa in company_sa else 0.0

    # Deadline feasibility
    days = opp.get("days_until_deadline")
    if days is None:
        deadline_score = 0.5
    elif days < 7:
        deadline_score = 0.1
    elif days < 14:
        deadline_score = 0.4
    elif days < 30:
        deadline_score = 0.8
    else:
        deadline_score = 1.0

    # Value fit
    est_val = opp.get("estimated_value")
    target_min = profile.get("target_value_min")
    target_max = profile.get("target_value_max")
    if est_val is None:
        value_score = 0.5
    elif target_min and float(est_val) < float(target_min):
        value_score = 0.2
    elif target_max and float(est_val) > float(target_max):
        value_score = 0.3
    else:
        value_score = 1.0

    # Capacity score from pipeline load
    pipeline = state.get("pipeline_load", {})
    active_deals = pipeline.get("active_deal_count", 0)
    proposal_deals = pipeline.get("proposal_stage_count", 0)
    max_active = 20
    max_proposals = 5
    deal_util = min(1.0, active_deals / max(max_active, 1))
    prop_util = min(1.0, proposal_deals / max(max_proposals, 1))
    capacity = 1.0 - (deal_util * 0.4 + prop_util * 0.6)
    capacity = max(0.0, min(1.0, capacity))

    factors = {
        "naics_match": round(naics_score, 2),
        "psc_match": round(psc_score, 2),
        "keyword_overlap": round(keyword_score, 2),
        "set_aside_match": round(set_aside_score, 2),
        "deadline_feasibility": round(deadline_score, 2),
        "value_fit": round(value_score, 2),
        "capacity": round(capacity, 2),
    }

    # Weighted total
    weights = {
        "naics_match": 0.15,
        "psc_match": 0.10,
        "keyword_overlap": 0.15,
        "set_aside_match": 0.10,
        "deadline_feasibility": 0.07,
        "value_fit": 0.08,
        "capacity": 0.10,  # New capacity factor
    }
    total = sum(factors[k] * weights.get(k, 0.1) for k in factors)
    total = round(max(0.0, min(1.0, total / sum(weights.values()))), 3)

    # Recommendation
    if total >= 0.75:
        rec = "strong_bid"
    elif total >= 0.55:
        rec = "bid"
    elif total >= 0.35:
        rec = "consider"
    else:
        rec = "no_bid"

    return {
        "factor_scores": factors,
        "capacity_score": capacity,
        "total_score": total,
        "recommendation": rec,
        "messages": [HumanMessage(content=f"Fit score: {total:.3f} → {rec}")],
    }


async def generate_rationale(state: FitState) -> dict:
    """Generate AI rationale for the fit assessment."""
    llm = _get_llm()
    try:
        resp = await llm.ainvoke([
            SystemMessage(content=(
                "You are a GovCon capture manager. Provide a concise 3-4 sentence "
                "rationale for the opportunity fit assessment. Be specific about "
                "strengths and weaknesses."
            )),
            HumanMessage(content=(
                f"Opportunity: {state.get('opportunity', {}).get('title', 'N/A')}\n"
                f"Factor Scores: {state.get('factor_scores', {})}\n"
                f"Total Score: {state.get('total_score', 0)}\n"
                f"Recommendation: {state.get('recommendation', 'N/A')}\n"
                f"Capacity Score: {state.get('capacity_score', 0)}\n\n"
                "Provide a concise rationale."
            )),
        ])
        rationale = resp.content
    except Exception as exc:
        logger.error("LLM rationale generation failed: %s", exc)
        rationale = f"Score: {state.get('total_score', 0)} — {state.get('recommendation', 'N/A')}"

    return {
        "rationale": rationale,
        "messages": [HumanMessage(content="Generated fit rationale")],
    }


def build_fit_graph() -> StateGraph:
    wf = StateGraph(FitState)
    wf.add_node("load_context", load_context)
    wf.add_node("score_factors", score_factors)
    wf.add_node("generate_rationale", generate_rationale)
    wf.set_entry_point("load_context")
    wf.add_edge("load_context", "score_factors")
    wf.add_edge("score_factors", "generate_rationale")
    wf.add_edge("generate_rationale", END)
    return wf.compile()


fit_graph = build_fit_graph()


class FitAgent(BaseAgent):
    """AI agent that scores opportunity fit with capacity awareness."""

    agent_name = "fit_agent"

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        initial: FitState = {
            "opportunity_id": input_data.get("opportunity_id", ""),
            "deal_id": input_data.get("deal_id", ""),
            "opportunity": {},
            "company_profile": {},
            "pipeline_load": {},
            "factor_scores": {},
            "capacity_score": 0.0,
            "total_score": 0.0,
            "recommendation": "",
            "rationale": "",
            "messages": [],
        }
        try:
            await self.emit_event("thinking", {"message": "Scoring opportunity fit"})
            result = await fit_graph.ainvoke(initial)
            await self.emit_event("output", {
                "score": result["total_score"],
                "recommendation": result["recommendation"],
            })
            return {
                "total_score": result["total_score"],
                "factor_scores": result["factor_scores"],
                "capacity_score": result["capacity_score"],
                "recommendation": result["recommendation"],
                "rationale": result["rationale"],
            }
        except Exception as exc:
            logger.exception("FitAgent.run failed")
            await self.emit_event("error", {"error": str(exc)})
            return {"error": str(exc)}
