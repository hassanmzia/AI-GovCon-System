"""Learning Agent using LangGraph.

Records deal outcomes (win/loss), extracts lessons learned, identifies
strategy patterns from historical performance, and recommends strategy
updates to improve future win rates.

Events: OUTCOME_RECORDED, STRATEGY_UPDATE_RECOMMENDED.
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

logger = logging.getLogger("ai_orchestrator.agents.learning")

DJANGO_API_URL = os.getenv("DJANGO_API_URL", "http://django-api:8001")
DJANGO_SERVICE_TOKEN = os.getenv("DJANGO_SERVICE_TOKEN", "")


# ── State ─────────────────────────────────────────────────────────────────────

class LearningState(TypedDict):
    deal_id: str
    outcome: str                        # "win", "loss", "no_bid", "cancelled"
    outcome_reason: str                 # CO debrief notes, reason for loss/win
    deal: dict
    opportunity: dict
    historical_deals: list[dict]        # Past deals with outcomes for pattern analysis
    win_patterns: list[str]             # Common traits of winning deals
    loss_patterns: list[str]            # Common traits of losing deals
    lessons_learned: list[dict]         # [{category, lesson, recommendation}]
    strategy_updates: list[dict]        # [{area, current_approach, recommended_update, rationale}]
    outcome_metrics: dict               # {win_rate, avg_score, pricing_accuracy, etc.}
    learning_summary: str               # Summary report for the team
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


async def _post(path: str, payload: dict) -> Any:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{DJANGO_API_URL}{path}",
                json=payload,
                headers=_auth_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.warning("API POST %s failed: %s", path, exc)
        return {}


async def _llm(system: str, human: str, max_tokens: int = 2500) -> str:
    try:
        llm = ChatAnthropic(
            model="claude-sonnet-4-6",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            max_tokens=max_tokens,
        )
        resp = await llm.ainvoke([SystemMessage(content=system), HumanMessage(content=human)])
        return resp.content
    except Exception as exc:
        logger.error("LLM failed: %s", exc)
        return ""


# ── Graph nodes ───────────────────────────────────────────────────────────────

async def record_outcome(state: LearningState) -> dict:
    """Load deal context and record the outcome in the system."""
    logger.info("LearningAgent: recording outcome for deal %s", state["deal_id"])

    deal = await _get(f"/api/deals/{state['deal_id']}/", default={})
    opp_id = deal.get("opportunity", "")
    opportunity = await _get(f"/api/opportunities/{opp_id}/", default={}) if opp_id else {}

    # Record outcome via API
    if state.get("outcome"):
        await _post(f"/api/deals/{state['deal_id']}/record_outcome/", {
            "outcome": state["outcome"],
            "outcome_reason": state.get("outcome_reason", ""),
        })

    return {
        "deal": deal,
        "opportunity": opportunity,
        "messages": [HumanMessage(content=f"Outcome recorded: {state.get('outcome', 'unknown')} for {deal.get('title', state['deal_id'])}")],
    }


async def load_historical_performance(state: LearningState) -> dict:
    """Load historical deal outcomes for pattern analysis."""
    logger.info("LearningAgent: loading historical data for deal %s", state["deal_id"])

    # Get recent completed deals
    deals_data = await _get("/api/deals/?stage=closed_won,closed_lost&limit=50", default={})
    historical = deals_data.get("results", []) if isinstance(deals_data, dict) else []

    # Compute basic metrics
    total = len(historical)
    wins = sum(1 for d in historical if d.get("outcome") == "win" or d.get("stage") == "closed_won")
    losses = total - wins
    win_rate = wins / total if total > 0 else 0.0

    metrics = {
        "total_deals": total,
        "wins": wins,
        "losses": losses,
        "win_rate": round(win_rate, 3),
        "sample_size": total,
    }

    return {
        "historical_deals": historical,
        "outcome_metrics": metrics,
        "messages": [HumanMessage(content=f"Loaded {total} historical deals. Win rate: {win_rate:.1%}")],
    }


async def analyze_patterns(state: LearningState) -> dict:
    """Identify win and loss patterns from historical data using Claude."""
    logger.info("LearningAgent: analyzing patterns for deal %s", state["deal_id"])

    historical = state.get("historical_deals") or []
    current_outcome = state.get("outcome", "unknown")
    current_deal = state.get("deal") or {}
    outcome_reason = state.get("outcome_reason", "No debrief provided.")

    if not historical and not current_outcome:
        return {
            "win_patterns": [],
            "loss_patterns": [],
            "messages": [HumanMessage(content="Insufficient data for pattern analysis.")],
        }

    # Summarize historical deals
    historical_summary = "\n".join(
        f"- {d.get('title', 'Unknown')} | {d.get('stage', '')} | "
        f"Value: ${d.get('contract_value', 'N/A')} | Agency: {d.get('agency', '')}"
        for d in historical[:20]
    )

    content = await _llm(
        system=(
            "You are a capture management analyst. Identify patterns in win/loss history "
            "to improve future bid decisions and proposal strategies."
        ),
        human=(
            f"Current Deal: {current_deal.get('title', state['deal_id'])}\n"
            f"Current Outcome: {current_outcome.upper()}\n"
            f"Debrief / Outcome Reason: {outcome_reason[:500]}\n\n"
            f"Historical Deals (last {len(historical)}):\n{historical_summary}\n\n"
            "Identify:\n"
            "WIN_PATTERNS: List 5 common characteristics of winning deals (one per line, start with 'WIN:')\n"
            "LOSS_PATTERNS: List 5 common characteristics of losing deals (one per line, start with 'LOSS:')\n"
            "KEY_INSIGHT: Most important insight from this outcome analysis"
        ),
        max_tokens=1500,
    )

    win_patterns = []
    loss_patterns = []
    for line in content.split("\n"):
        stripped = line.strip()
        if stripped.startswith("WIN:"):
            win_patterns.append(stripped[4:].strip())
        elif stripped.startswith("LOSS:"):
            loss_patterns.append(stripped[5:].strip())

    return {
        "win_patterns": win_patterns[:5],
        "loss_patterns": loss_patterns[:5],
        "messages": [HumanMessage(content=f"Patterns: {len(win_patterns)} win, {len(loss_patterns)} loss.")],
    }


async def extract_lessons_learned(state: LearningState) -> dict:
    """Extract actionable lessons from this deal outcome."""
    logger.info("LearningAgent: extracting lessons for deal %s", state["deal_id"])

    outcome = state.get("outcome", "unknown")
    outcome_reason = state.get("outcome_reason", "")
    win_patterns = state.get("win_patterns") or []
    loss_patterns = state.get("loss_patterns") or []
    deal = state.get("deal") or {}

    content = await _llm(
        system=(
            "You are a capture excellence manager extracting actionable lessons learned "
            "from a government contract bid outcome. Focus on specific, implementable "
            "improvements for future bids."
        ),
        human=(
            f"Deal: {deal.get('title', state['deal_id'])}\n"
            f"Outcome: {outcome.upper()}\n"
            f"Reason: {outcome_reason[:500]}\n\n"
            f"Win Patterns Identified: {win_patterns[:3]}\n"
            f"Loss Patterns Identified: {loss_patterns[:3]}\n\n"
            "Extract 5–7 specific lessons learned. For each:\n"
            "CATEGORY: [Capture/Pricing/Technical/Teaming/Proposal/Strategy]\n"
            "LESSON: [What happened and what we learned]\n"
            "RECOMMENDATION: [Specific action to take on future bids]\n"
            "IMPACT: HIGH/MEDIUM/LOW\n"
            "---"
        ),
        max_tokens=2000,
    )

    lessons = []
    blocks = content.split("---")
    for block in blocks:
        if "LESSON:" in block:
            lines = {}
            for line in block.strip().split("\n"):
                if ":" in line:
                    key, _, val = line.partition(":")
                    lines[key.strip().upper()] = val.strip()
            if lines.get("LESSON"):
                lessons.append({
                    "category": lines.get("CATEGORY", "General"),
                    "lesson": lines.get("LESSON", ""),
                    "recommendation": lines.get("RECOMMENDATION", ""),
                    "impact": lines.get("IMPACT", "MEDIUM"),
                })

    return {
        "lessons_learned": lessons,
        "messages": [HumanMessage(content=f"Extracted {len(lessons)} lesson(s) learned.")],
    }


async def recommend_strategy_updates(state: LearningState) -> dict:
    """Generate strategic recommendations to improve future win rates."""
    logger.info("LearningAgent: recommending strategy updates for deal %s", state["deal_id"])

    lessons = state.get("lessons_learned") or []
    win_patterns = state.get("win_patterns") or []
    loss_patterns = state.get("loss_patterns") or []
    metrics = state.get("outcome_metrics") or {}

    content = await _llm(
        system=(
            "You are a business development strategist. Based on deal outcome analysis, "
            "recommend specific updates to the company's capture and proposal strategy "
            "to improve win rates and ROI."
        ),
        human=(
            f"Win Rate: {metrics.get('win_rate', 0):.1%} ({metrics.get('wins', 0)}W / {metrics.get('losses', 0)}L)\n\n"
            f"Win Patterns:\n" + "\n".join(f"- {p}" for p in win_patterns[:5])
            + f"\n\nLoss Patterns:\n" + "\n".join(f"- {p}" for p in loss_patterns[:5])
            + f"\n\nKey Lessons:\n" + "\n".join(f"- [{l['category']}] {l['recommendation']}" for l in lessons[:5])
            + "\n\n"
            "Recommend 4–6 specific strategy updates. For each:\n"
            "AREA: [Bid/No-Bid/Pricing/Teaming/Capture/Proposal]\n"
            "CURRENT: [current approach, one line]\n"
            "RECOMMENDED: [specific change to make]\n"
            "RATIONALE: [evidence-based justification]\n"
            "TIMELINE: [immediate/next bid/next quarter]\n"
            "---"
        ),
        max_tokens=2000,
    )

    updates = []
    blocks = content.split("---")
    for block in blocks:
        if "AREA:" in block and "RECOMMENDED:" in block:
            lines = {}
            for line in block.strip().split("\n"):
                if ":" in line:
                    key, _, val = line.partition(":")
                    lines[key.strip().upper()] = val.strip()
            if lines.get("RECOMMENDED"):
                updates.append({
                    "area": lines.get("AREA", "General"),
                    "current_approach": lines.get("CURRENT", ""),
                    "recommended_update": lines.get("RECOMMENDED", ""),
                    "rationale": lines.get("RATIONALE", ""),
                    "timeline": lines.get("TIMELINE", "next bid"),
                })

    summary = (
        f"Learning Summary — Deal: {state['deal'].get('title', state['deal_id'])}\n"
        f"Outcome: {state.get('outcome', 'unknown').upper()}\n\n"
        f"Metrics: {metrics.get('wins', 0)}W / {metrics.get('losses', 0)}L "
        f"({metrics.get('win_rate', 0):.1%} win rate)\n\n"
        f"Lessons Learned: {len(lessons)}\n"
        f"Strategy Updates Recommended: {len(updates)}\n\n"
        f"Top Recommendation: {updates[0]['recommended_update'] if updates else 'See lessons learned'}"
    )

    return {
        "strategy_updates": updates,
        "learning_summary": summary,
        "messages": [HumanMessage(content=f"Strategy updates: {len(updates)} recommendation(s).")],
    }


# ── Graph ─────────────────────────────────────────────────────────────────────

def build_learning_graph() -> StateGraph:
    wf = StateGraph(LearningState)
    wf.add_node("record_outcome", record_outcome)
    wf.add_node("load_historical_performance", load_historical_performance)
    wf.add_node("analyze_patterns", analyze_patterns)
    wf.add_node("extract_lessons_learned", extract_lessons_learned)
    wf.add_node("recommend_strategy_updates", recommend_strategy_updates)
    wf.set_entry_point("record_outcome")
    wf.add_edge("record_outcome", "load_historical_performance")
    wf.add_edge("load_historical_performance", "analyze_patterns")
    wf.add_edge("analyze_patterns", "extract_lessons_learned")
    wf.add_edge("extract_lessons_learned", "recommend_strategy_updates")
    wf.add_edge("recommend_strategy_updates", END)
    return wf.compile()


learning_graph = build_learning_graph()


# ── Agent ─────────────────────────────────────────────────────────────────────

class LearningAgent(BaseAgent):
    """AI agent that records outcomes and drives continuous improvement from lessons learned."""

    agent_name = "learning_agent"

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        deal_id = input_data.get("deal_id", "")
        if not deal_id:
            return {"error": "deal_id is required"}

        outcome = input_data.get("outcome", "")
        if outcome not in ("win", "loss", "no_bid", "cancelled", ""):
            return {"error": f"Invalid outcome: {outcome}. Must be win/loss/no_bid/cancelled"}

        initial: LearningState = {
            "deal_id": deal_id,
            "outcome": outcome,
            "outcome_reason": input_data.get("outcome_reason", ""),
            "deal": {},
            "opportunity": {},
            "historical_deals": [],
            "win_patterns": [],
            "loss_patterns": [],
            "lessons_learned": [],
            "strategy_updates": [],
            "outcome_metrics": {},
            "learning_summary": "",
            "messages": [],
        }
        try:
            await self.emit_event(
                "thinking",
                {"message": f"Recording and analyzing outcome for deal {deal_id}: {outcome}"},
                execution_id=deal_id,
            )
            fs = await learning_graph.ainvoke(initial)
            await self.emit_event(
                "output",
                {
                    "outcome": outcome,
                    "lessons_count": len(fs["lessons_learned"]),
                    "strategy_updates_count": len(fs["strategy_updates"]),
                },
                execution_id=deal_id,
            )
            return {
                "deal_id": fs["deal_id"],
                "outcome": outcome,
                "outcome_metrics": fs["outcome_metrics"],
                "win_patterns": fs["win_patterns"],
                "loss_patterns": fs["loss_patterns"],
                "lessons_learned": fs["lessons_learned"],
                "strategy_updates": fs["strategy_updates"],
                "learning_summary": fs["learning_summary"],
            }
        except Exception as exc:
            logger.exception("LearningAgent.run failed for deal %s", deal_id)
            await self.emit_event("error", {"error": str(exc)}, execution_id=deal_id)
            return {"error": str(exc), "deal_id": deal_id}
