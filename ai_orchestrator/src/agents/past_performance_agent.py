"""Past Performance AI Agent using LangGraph.

Matches relevant past performance records to an opportunity/deal and
scores each match for relevance and proposal-readiness.

Events: PAST_PERFORMANCE_MATCHED, PAST_PERFORMANCE_SCORED.
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

logger = logging.getLogger("ai_orchestrator.agents.past_performance")

DJANGO_API_URL = os.getenv("DJANGO_API_URL", "http://django-api:8001")
DJANGO_SERVICE_TOKEN = os.getenv("DJANGO_SERVICE_TOKEN", "")


# ── State ─────────────────────────────────────────────────────────────────────

class PastPerformanceState(TypedDict):
    deal_id: str
    opportunity_id: str
    deal: dict
    opportunity: dict
    all_past_performance: list[dict]
    matched_records: list[dict]          # Top matches with relevance scores
    scoring_rationale: str
    narrative_suggestions: list[dict]    # {pp_id, suggested_narrative_excerpt}
    gap_analysis: str                    # Missing PP categories
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


async def _llm(system: str, human: str) -> str:
    try:
        llm = ChatAnthropic(
            model="claude-sonnet-4-6",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            max_tokens=3000,
        )
        resp = await llm.ainvoke([SystemMessage(content=system), HumanMessage(content=human)])
        return resp.content
    except Exception as exc:
        logger.error("LLM failed: %s", exc)
        return ""


# ── Graph nodes ───────────────────────────────────────────────────────────────

async def load_pp_context(state: PastPerformanceState) -> dict:
    logger.info("PPAgent: loading context for deal %s", state["deal_id"])
    deal = await _get(f"/api/deals/{state['deal_id']}/", default={})
    opp_id = state.get("opportunity_id") or deal.get("opportunity") or ""
    opportunity = await _get(f"/api/opportunities/{opp_id}/", default={}) if opp_id else {}
    pp_data = await _get("/api/past-performance/?is_active=true&limit=50", default={})
    pp_list = pp_data.get("results", []) if isinstance(pp_data, dict) else []
    return {
        "deal": deal,
        "opportunity": opportunity,
        "all_past_performance": pp_list,
        "messages": [HumanMessage(content=f"Matching PP for: {deal.get('title', state['deal_id'])}")],
    }


async def match_past_performance(state: PastPerformanceState) -> dict:
    """Claude scores each PP record for relevance to the opportunity."""
    logger.info("PPAgent: matching PP records for deal %s", state["deal_id"])

    if not state["all_past_performance"]:
        return {
            "matched_records": [],
            "scoring_rationale": "No past performance records found.",
            "messages": [HumanMessage(content="No PP records available.")],
        }

    pp_summaries = "\n".join(
        f"[{pp.get('id', i)}] {pp.get('project_name', '')} | {pp.get('client_agency', '')} | "
        f"NAICS: {pp.get('naics_codes', [])} | Domains: {pp.get('domains', [])} | "
        f"Value: ${pp.get('contract_value', 'N/A')} | Rating: {pp.get('performance_rating', '')}"
        for i, pp in enumerate(state["all_past_performance"][:30])
    )

    content = await _llm(
        system=(
            "You are a past performance and capture specialist. Score and rank past "
            "performance records for relevance to a specific opportunity. Consider NAICS "
            "alignment, technical domain overlap, agency similarity, and contract size similarity."
        ),
        human=(
            f"Opportunity:\n{state['opportunity']}\n\n"
            f"Past Performance Records ({len(state['all_past_performance'])} total):\n{pp_summaries}\n\n"
            "For each record provide a relevance score (0.0–1.0). Format each line:\n"
            "[ID] SCORE: X.XX | REASON: brief rationale (one line)\n\n"
            "Then list the top 5 most relevant records with detailed rationale."
        ),
    )

    import re
    matches = []
    score_pattern = re.compile(r'\[([^\]]+)\]\s+SCORE:\s*([\d.]+)\s*\|?\s*REASON:\s*(.+)')
    for m in score_pattern.finditer(content):
        pp_id_str, score_str, reason = m.group(1), m.group(2), m.group(3).strip()
        try:
            score = float(score_str)
        except ValueError:
            score = 0.5
        # Find the original PP record
        pp_record = next(
            (pp for pp in state["all_past_performance"]
             if str(pp.get("id", "")) == pp_id_str.strip()),
            {"id": pp_id_str},
        )
        matches.append({**pp_record, "relevance_score": score, "match_reason": reason})

    # Sort by score descending, keep top 10
    matches.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
    top_matches = matches[:10]

    if not top_matches and state["all_past_performance"]:
        # Fallback: return top 5 with default scores
        top_matches = [
            {**pp, "relevance_score": 0.6, "match_reason": "Included as fallback — manual review required"}
            for pp in state["all_past_performance"][:5]
        ]

    return {
        "matched_records": top_matches,
        "scoring_rationale": content,
        "messages": [HumanMessage(content=f"Matched {len(top_matches)} past performance records.")],
    }


async def generate_narrative_suggestions(state: PastPerformanceState) -> dict:
    """Generate proposal narrative excerpts for top PP matches."""
    logger.info("PPAgent: generating narrative suggestions for deal %s", state["deal_id"])

    top = state["matched_records"][:5]
    if not top:
        return {
            "narrative_suggestions": [],
            "gap_analysis": "No past performance records to generate narratives from.",
            "messages": [HumanMessage(content="No matched records — no narratives generated.")],
        }

    content = await _llm(
        system=(
            "You are a proposal writer specializing in past performance sections. "
            "Write compelling, concise narrative excerpts for each past performance "
            "record that will resonate with the evaluating agency."
        ),
        human=(
            f"Target Opportunity: {state['opportunity'].get('title', '')}\n"
            f"Agency: {state['opportunity'].get('agency', '')}\n\n"
            "For each past performance record below, write a 2-paragraph narrative "
            "excerpt (150-200 words) suitable for a proposal Volume III / Past "
            "Performance volume. Emphasize relevance to the current opportunity.\n\n"
            + "\n\n".join(
                f"Record {i+1}: {pp.get('project_name', '')} | {pp.get('client_agency', '')} | "
                f"${pp.get('contract_value', 'N/A')} | {pp.get('performance_rating', '')}\n"
                f"Description: {pp.get('description', '')[:300]}"
                for i, pp in enumerate(top)
            )
        ),
    )

    suggestions = []
    # Split response into per-record blocks
    blocks = content.split("Record ")
    for i, pp in enumerate(top):
        excerpt = blocks[i + 1] if i + 1 < len(blocks) else content[:400]
        suggestions.append({
            "pp_id": str(pp.get("id", "")),
            "project_name": pp.get("project_name", ""),
            "suggested_narrative_excerpt": excerpt[:600],
        })

    # Gap analysis
    gap_content = await _llm(
        system="You are a capture manager identifying past performance gaps.",
        human=(
            f"Opportunity requirements: {state['opportunity'].get('description', '')[:500]}\n\n"
            f"Available past performance domains: "
            f"{[pp.get('domains', []) for pp in state['matched_records'][:10]]}\n\n"
            "Identify:\n"
            "1. Technical areas required by the RFP but NOT covered by existing PP\n"
            "2. Agencies/contract types where we lack relevant references\n"
            "3. Recommendations for addressing gaps (teaming, new references, etc.)"
        ),
    )

    return {
        "narrative_suggestions": suggestions,
        "gap_analysis": gap_content,
        "messages": [HumanMessage(content=f"Generated {len(suggestions)} narrative suggestion(s).")],
    }


# ── Graph ─────────────────────────────────────────────────────────────────────

def build_past_performance_graph() -> StateGraph:
    wf = StateGraph(PastPerformanceState)
    wf.add_node("load_pp_context", load_pp_context)
    wf.add_node("match_past_performance", match_past_performance)
    wf.add_node("generate_narrative_suggestions", generate_narrative_suggestions)
    wf.set_entry_point("load_pp_context")
    wf.add_edge("load_pp_context", "match_past_performance")
    wf.add_edge("match_past_performance", "generate_narrative_suggestions")
    wf.add_edge("generate_narrative_suggestions", END)
    return wf.compile()


past_performance_graph = build_past_performance_graph()


# ── Agent ─────────────────────────────────────────────────────────────────────

class PastPerformanceAgent(BaseAgent):
    """AI agent that matches and scores past performance records for proposals."""

    agent_name = "past_performance_agent"

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        deal_id = input_data.get("deal_id", "")
        if not deal_id:
            return {"error": "deal_id is required"}

        initial: PastPerformanceState = {
            "deal_id": deal_id,
            "opportunity_id": input_data.get("opportunity_id", ""),
            "deal": {},
            "opportunity": {},
            "all_past_performance": [],
            "matched_records": [],
            "scoring_rationale": "",
            "narrative_suggestions": [],
            "gap_analysis": "",
            "messages": [],
        }
        try:
            await self.emit_event(
                "thinking",
                {"message": f"Matching past performance for deal {deal_id}"},
                execution_id=deal_id,
            )
            fs = await past_performance_graph.ainvoke(initial)
            await self.emit_event(
                "output",
                {"matched_count": len(fs["matched_records"])},
                execution_id=deal_id,
            )
            return {
                "deal_id": fs["deal_id"],
                "matched_records": fs["matched_records"],
                "scoring_rationale": fs["scoring_rationale"],
                "narrative_suggestions": fs["narrative_suggestions"],
                "gap_analysis": fs["gap_analysis"],
            }
        except Exception as exc:
            logger.exception("PastPerformanceAgent.run failed for deal %s", deal_id)
            await self.emit_event("error", {"error": str(exc)}, execution_id=deal_id)
            return {"error": str(exc), "deal_id": deal_id}
