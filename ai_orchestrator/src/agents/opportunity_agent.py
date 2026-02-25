"""Opportunity Intelligence AI Agent using LangGraph.

Discovers, scores, enriches, and recommends opportunities from the database.
Emits events: OPPORTUNITY_SCORED, OPPORTUNITY_ENRICHED, OPPORTUNITY_RECOMMENDED,
OPPORTUNITY_DIGEST_READY.
"""
import logging
import os
from typing import Annotated, Any
import operator

import httpx
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from typing_extensions import TypedDict

from src.agents.base import BaseAgent

logger = logging.getLogger("ai_orchestrator.agents.opportunity")

DJANGO_API_URL = os.getenv("DJANGO_API_URL", "http://django-api:8001")
DJANGO_SERVICE_TOKEN = os.getenv("DJANGO_SERVICE_TOKEN", "")


# ── State ─────────────────────────────────────────────────────────────────────

class OpportunityState(TypedDict):
    opportunity_id: str
    opportunity: dict
    company_strategy: dict
    similar_past_performance: list[dict]
    ai_score: float                  # 0.0–1.0 fit score
    score_rationale: str
    enrichment: dict                 # Additional intelligence added
    recommendation: str              # "PURSUE" | "WATCH" | "PASS"
    recommendation_rationale: str
    pursuit_actions: list[str]       # Next steps if pursuing
    messages: Annotated[list, operator.add]


# ── Helpers ───────────────────────────────────────────────────────────────────

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


def _get_llm() -> ChatAnthropic:
    return ChatAnthropic(
        model="claude-sonnet-4-6",
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        max_tokens=2048,
    )


async def _llm(system: str, human: str) -> str:
    try:
        resp = await _get_llm().ainvoke([
            SystemMessage(content=system), HumanMessage(content=human)
        ])
        return resp.content
    except Exception as exc:
        logger.error("LLM failed: %s", exc)
        return ""


# ── Graph nodes ───────────────────────────────────────────────────────────────

async def load_opportunity(state: OpportunityState) -> dict:
    logger.info("OppAgent: loading opportunity %s", state["opportunity_id"])
    opp = await _get(f"/api/opportunities/{state['opportunity_id']}/", default={})
    strategy = await _get("/api/strategy/current/", default={})
    pp_data = await _get(
        f"/api/past-performance/?limit=10", default={}
    )
    pp = pp_data.get("results", []) if isinstance(pp_data, dict) else []
    return {
        "opportunity": opp,
        "company_strategy": strategy,
        "similar_past_performance": pp,
        "messages": [HumanMessage(content=f"Analyzing opportunity: {opp.get('title', state['opportunity_id'])}")],
    }


async def score_opportunity(state: OpportunityState) -> dict:
    logger.info("OppAgent: scoring opportunity %s", state["opportunity_id"])
    content = await _llm(
        system=(
            "You are a business development director at a U.S. government contracting firm. "
            "Score opportunities on strategic fit (0.0–1.0) based on company strategy, "
            "past performance, and win probability factors. Be concise and numerical."
        ),
        human=(
            f"Opportunity:\n{state['opportunity']}\n\n"
            f"Company Strategy:\n{state['company_strategy']}\n\n"
            f"Relevant Past Performance (sample):\n{state['similar_past_performance'][:5]}\n\n"
            "Score this opportunity (0.0–1.0) on:\n"
            "1. Strategic alignment (0.0–1.0)\n"
            "2. Technical fit (0.0–1.0)\n"
            "3. Win probability factors (0.0–1.0)\n"
            "4. Overall fit score (0.0–1.0)\n\n"
            "Start with 'OVERALL_SCORE: X.XX' then provide rationale."
        ),
    )
    score = 0.5
    for line in content.split("\n"):
        if line.strip().startswith("OVERALL_SCORE:"):
            try:
                score = float(line.split(":", 1)[1].strip())
                score = max(0.0, min(1.0, score))
            except ValueError:
                pass
            break
    return {
        "ai_score": score,
        "score_rationale": content,
        "messages": [HumanMessage(content=f"Opportunity scored: {score:.2f}")],
    }


async def enrich_opportunity(state: OpportunityState) -> dict:
    logger.info("OppAgent: enriching opportunity %s", state["opportunity_id"])
    content = await _llm(
        system=(
            "You are a capture manager enriching an opportunity record with intelligence. "
            "Provide specific, actionable intel about the incumbent, key contacts, "
            "procurement history, and competitive landscape."
        ),
        human=(
            f"Opportunity:\n{state['opportunity']}\n\n"
            "Enrich with:\n"
            "1. Incumbent contractor (if identifiable from agency/contract history)\n"
            "2. Key decision makers (titles and procurement office)\n"
            "3. Contract vehicle likely to be used (GSA, SEWP, open market, etc.)\n"
            "4. Likely competitors (3-5 based on agency and NAICS)\n"
            "5. Bid/no-bid factors to investigate\n"
            "6. Set-aside considerations\n"
        ),
    )
    return {
        "enrichment": {"intelligence": content, "source": "ai_analysis"},
        "messages": [HumanMessage(content="Opportunity enriched.")],
    }


async def generate_recommendation(state: OpportunityState) -> dict:
    logger.info("OppAgent: generating recommendation for %s", state["opportunity_id"])
    content = await _llm(
        system=(
            "You are a chief capture officer making pursuit decisions. "
            "Based on the analysis, make a clear PURSUE / WATCH / PASS decision "
            "with specific next steps."
        ),
        human=(
            f"Opportunity:\n{state['opportunity']}\n\n"
            f"Fit Score: {state['ai_score']:.2f}\n"
            f"Score Rationale:\n{state['score_rationale'][:800]}\n\n"
            f"Enrichment:\n{state['enrichment'].get('intelligence', '')[:600]}\n\n"
            "Provide:\n"
            "1. Recommendation: PURSUE / WATCH / PASS (first line, no other text)\n"
            "2. Rationale (3-4 sentences)\n"
            "3. If PURSUE: 5 specific next pursuit actions\n"
            "4. If WATCH: 3 trigger conditions to upgrade to PURSUE\n"
            "5. If PASS: reason why not competitive\n"
        ),
    )
    lines = content.strip().split("\n")
    rec = "WATCH"
    for opt in ("PURSUE", "PASS", "WATCH"):
        if opt in lines[0].upper() if lines else "":
            rec = opt
            break

    actions = [
        ln.strip("- •123456789.").strip()
        for ln in content.split("\n")
        if ln.strip() and any(ln.strip().startswith(p) for p in ("-", "•", "1.", "2.", "3.", "4.", "5."))
    ][:5]

    return {
        "recommendation": rec,
        "recommendation_rationale": content,
        "pursuit_actions": actions,
        "messages": [HumanMessage(content=f"Recommendation: {rec}")],
    }


# ── Graph ─────────────────────────────────────────────────────────────────────

def build_opportunity_graph() -> StateGraph:
    wf = StateGraph(OpportunityState)
    wf.add_node("load_opportunity", load_opportunity)
    wf.add_node("score_opportunity", score_opportunity)
    wf.add_node("enrich_opportunity", enrich_opportunity)
    wf.add_node("generate_recommendation", generate_recommendation)
    wf.set_entry_point("load_opportunity")
    wf.add_edge("load_opportunity", "score_opportunity")
    wf.add_edge("score_opportunity", "enrich_opportunity")
    wf.add_edge("enrich_opportunity", "generate_recommendation")
    wf.add_edge("generate_recommendation", END)
    return wf.compile()


opportunity_graph = build_opportunity_graph()


# ── Agent ─────────────────────────────────────────────────────────────────────

class OpportunityAgent(BaseAgent):
    """AI agent that scores, enriches, and recommends government opportunities."""

    agent_name = "opportunity_agent"

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        opportunity_id = input_data.get("opportunity_id", "")
        if not opportunity_id:
            return {"error": "opportunity_id is required"}

        initial: OpportunityState = {
            "opportunity_id": opportunity_id,
            "opportunity": {},
            "company_strategy": {},
            "similar_past_performance": [],
            "ai_score": 0.0,
            "score_rationale": "",
            "enrichment": {},
            "recommendation": "",
            "recommendation_rationale": "",
            "pursuit_actions": [],
            "messages": [],
        }
        try:
            await self.emit_event(
                "thinking",
                {"message": f"Analyzing opportunity {opportunity_id}"},
                execution_id=opportunity_id,
            )
            fs = await opportunity_graph.ainvoke(initial)
            await self.emit_event(
                "output",
                {"recommendation": fs["recommendation"], "score": fs["ai_score"]},
                execution_id=opportunity_id,
            )
            return {
                "opportunity_id": fs["opportunity_id"],
                "ai_score": fs["ai_score"],
                "score_rationale": fs["score_rationale"],
                "enrichment": fs["enrichment"],
                "recommendation": fs["recommendation"],
                "recommendation_rationale": fs["recommendation_rationale"],
                "pursuit_actions": fs["pursuit_actions"],
            }
        except Exception as exc:
            logger.exception("OpportunityAgent.run failed for %s", opportunity_id)
            await self.emit_event("error", {"error": str(exc)}, execution_id=opportunity_id)
            return {"error": str(exc), "opportunity_id": opportunity_id}
