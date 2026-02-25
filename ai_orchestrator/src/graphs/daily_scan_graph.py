"""Daily opportunity scan graph – orchestrates the morning digest pipeline.

Runs on a schedule (e.g. 6 AM daily) to:
1. Scan SAM.gov for new opportunities matching company profile
2. Score and rank all opportunities (fit score + strategic score)
3. Apply Thompson Sampling to select Top 10 from Top 30
4. Notify users of Top 10 daily digest
"""
import logging
import os
from typing import Annotated, Any
import operator

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from typing_extensions import TypedDict

import httpx

logger = logging.getLogger("ai_orchestrator.graphs.daily_scan")

DJANGO_API_URL = os.getenv("DJANGO_API_URL", "http://django-api:8001")
DJANGO_SERVICE_TOKEN = os.getenv("DJANGO_SERVICE_TOKEN", "")


def _auth_headers() -> dict:
    return {"Authorization": f"Bearer {DJANGO_SERVICE_TOKEN}"} if DJANGO_SERVICE_TOKEN else {}


# ── State ─────────────────────────────────────────────────────────────────────

class DailyScanState(TypedDict):
    company_profile: dict
    company_strategy: dict
    raw_opportunities: list
    scored_opportunities: list
    top_30: list
    top_10: list
    digest_sent: bool
    scan_stats: dict
    messages: Annotated[list, operator.add]


# ── Node functions ─────────────────────────────────────────────────────────────

async def load_company_profile(state: DailyScanState) -> dict:
    """Load company profile and strategy for scoring context."""
    logger.info("Loading company profile for daily scan")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            profile_resp = await client.get(
                f"{DJANGO_API_URL}/api/opportunities/company-profile/",
                headers=_auth_headers(),
            )
            strategy_resp = await client.get(
                f"{DJANGO_API_URL}/api/strategy/",
                headers=_auth_headers(),
            )
            profile = profile_resp.json() if profile_resp.status_code == 200 else {}
            strategy = strategy_resp.json() if strategy_resp.status_code == 200 else {}
    except Exception as exc:
        logger.error("Profile load failed: %s", exc)
        profile = {}
        strategy = {}

    return {
        "company_profile": profile,
        "company_strategy": strategy,
        "messages": [HumanMessage(content="Starting daily opportunity scan")],
    }


async def scan_sam_gov(state: DailyScanState) -> dict:
    """Scan SAM.gov for new opportunities."""
    logger.info("Scanning SAM.gov for new opportunities")
    profile = state["company_profile"]

    naics = profile.get("naics_codes", [])
    keywords = profile.get("keywords", [])

    try:
        from src.mcp_servers.samgov_tools import search_opportunities

        raw = await search_opportunities(
            naics=naics[:5] if naics else None,
            keywords=keywords[:5] if keywords else None,
            limit=100,
        )
        opportunities = raw.get("opportunitiesData", [])
        logger.info("Found %d raw opportunities from SAM.gov", len(opportunities))
    except Exception as exc:
        logger.error("SAM.gov scan failed: %s", exc)
        opportunities = []

    return {
        "raw_opportunities": opportunities,
        "scan_stats": {
            "samgov_count": len(opportunities),
        },
    }


async def score_opportunities(state: DailyScanState) -> dict:
    """Score and rank all opportunities using fit scoring engine."""
    logger.info("Scoring %d opportunities", len(state["raw_opportunities"]))

    scored = []
    for opp in state["raw_opportunities"][:200]:  # Cap for performance
        score = await _score_single_opportunity(opp, state["company_profile"], state["company_strategy"])
        scored.append({**opp, **score})

    # Sort by composite score
    scored.sort(key=lambda o: o.get("composite_score", 0), reverse=True)

    return {"scored_opportunities": scored}


async def select_top_30(state: DailyScanState) -> dict:
    """Select the top 30 candidates for bandit selection."""
    top_30 = state["scored_opportunities"][:30]
    logger.info("Selected top 30 from %d scored opportunities", len(state["scored_opportunities"]))
    return {"top_30": top_30}


async def apply_bandit_selection(state: DailyScanState) -> dict:
    """Apply Thompson Sampling to select daily Top 10 from Top 30."""
    from src.learning.bandit import DailyOpportunitySelector, opportunity_to_features

    selector = DailyOpportunitySelector()

    # Add features to each opportunity
    candidates_with_features = []
    for opp in state["top_30"]:
        features = opportunity_to_features(opp)
        candidates_with_features.append({**opp, "features": features})

    top_10 = selector.select_top_10(candidates_with_features, use_linucb=True)
    logger.info("Bandit selected %d opportunities for daily digest", len(top_10))

    return {"top_10": top_10}


async def persist_scores(state: DailyScanState) -> dict:
    """Persist opportunity scores to Django backend."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{DJANGO_API_URL}/api/opportunities/bulk-score/",
                json={"opportunities": state["scored_opportunities"][:50]},
                headers=_auth_headers(),
            )
            if resp.status_code not in (200, 201):
                logger.warning("Bulk score persist returned %d", resp.status_code)
    except Exception as exc:
        logger.warning("Score persistence failed: %s", exc)

    return {}


async def send_daily_digest(state: DailyScanState) -> dict:
    """Send the daily Top 10 digest notification."""
    top_10 = state.get("top_10", [])
    if not top_10:
        logger.warning("No opportunities in Top 10 – skipping digest")
        return {"digest_sent": False}

    digest_payload = {
        "digest_type": "daily_top_10",
        "opportunities": [
            {
                "id": opp.get("noticeId", opp.get("id", "")),
                "title": opp.get("title", opp.get("opportunityTitle", "Unknown")),
                "agency": opp.get("fullParentPathName", opp.get("agency", "")),
                "due_date": opp.get("responseDeadLine", opp.get("due_date", "")),
                "fit_score": opp.get("fit_score", 0),
                "strategic_score": opp.get("strategic_score", 0),
                "composite_score": opp.get("composite_score", 0),
                "set_aside": opp.get("typeOfSetAsideDescription", ""),
                "naics": opp.get("naicsCode", ""),
                "estimated_value": opp.get("estimated_value", 0),
            }
            for opp in top_10
        ],
        "stats": state.get("scan_stats", {}),
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{DJANGO_API_URL}/api/notifications/daily-digest/",
                json=digest_payload,
                headers=_auth_headers(),
            )
            sent = resp.status_code in (200, 201)
    except Exception as exc:
        logger.error("Digest send failed: %s", exc)
        sent = False

    logger.info("Daily digest sent: %s (%d opportunities)", sent, len(top_10))
    return {"digest_sent": sent}


# ── Graph construction ─────────────────────────────────────────────────────────

def build_daily_scan_graph():
    """Build and compile the daily scan LangGraph workflow."""
    workflow = StateGraph(DailyScanState)

    workflow.add_node("load_company_profile", load_company_profile)
    workflow.add_node("scan_sam_gov", scan_sam_gov)
    workflow.add_node("score_opportunities", score_opportunities)
    workflow.add_node("select_top_30", select_top_30)
    workflow.add_node("apply_bandit_selection", apply_bandit_selection)
    workflow.add_node("persist_scores", persist_scores)
    workflow.add_node("send_daily_digest", send_daily_digest)

    workflow.set_entry_point("load_company_profile")
    workflow.add_edge("load_company_profile", "scan_sam_gov")
    workflow.add_edge("scan_sam_gov", "score_opportunities")
    workflow.add_edge("score_opportunities", "select_top_30")
    workflow.add_edge("select_top_30", "apply_bandit_selection")
    workflow.add_edge("apply_bandit_selection", "persist_scores")
    workflow.add_edge("persist_scores", "send_daily_digest")
    workflow.add_edge("send_daily_digest", END)

    return workflow.compile()


# ── Scoring helper ────────────────────────────────────────────────────────────

async def _score_single_opportunity(
    opp: dict,
    profile: dict,
    strategy: dict,
) -> dict:
    """Compute fit and strategic scores for a single opportunity."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(
                f"{DJANGO_API_URL}/api/opportunities/score/",
                json={"opportunity": opp, "profile": profile, "strategy": strategy},
                headers=_auth_headers(),
            )
            if resp.status_code == 200:
                return resp.json()
    except Exception:
        pass

    # Fallback: simple rule-based scoring
    profile_naics = set(profile.get("naics_codes", []))
    opp_naics = opp.get("naicsCode", "")

    naics_match = 0.8 if opp_naics in profile_naics else 0.2
    fit_score = naics_match * 0.5 + 0.3  # baseline

    return {
        "fit_score": round(fit_score, 2),
        "strategic_score": 0.5,
        "composite_score": round(fit_score * 0.7 + 0.5 * 0.3, 2),
    }


# Module-level compiled graph
daily_scan_graph = build_daily_scan_graph()
