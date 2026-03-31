"""Adaptive Learning Agent — Outcome Feedback Loop.

Extends the Learning Agent concept with a feedback loop that:
1. Records outcome metrics to a persistent store (Redis + Django)
2. Computes Thompson Sampling-inspired confidence weights per strategy area
3. Publishes updated strategy weights that downstream agents can query
4. Tracks which win themes, pricing approaches, and teaming strategies
   correlated with wins vs losses over time

This is the "system gets smarter" agent — it closes the loop between
deal outcomes and future agent behavior.
"""

import json
import logging
import math
import os
import random
from typing import Annotated, Any
import operator

import httpx
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from typing_extensions import TypedDict

from src.agents.base import BaseAgent
from src.llm_provider import get_chat_model

logger = logging.getLogger("ai_orchestrator.agents.adaptive_learning")

DJANGO_API_URL = os.getenv("DJANGO_API_URL", "http://django-api:8001")
DJANGO_SERVICE_TOKEN = os.getenv("DJANGO_SERVICE_TOKEN", "")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Redis key for persistent strategy weights
STRATEGY_WEIGHTS_KEY = "adaptive:strategy_weights"
OUTCOME_HISTORY_KEY = "adaptive:outcome_history"


# ── State ────────────────────────────────────────────────────────────────────

class AdaptiveLearningState(TypedDict):
    deal_id: str
    outcome: str  # win, loss, no_bid
    deal: dict
    opportunity: dict
    # Historical data
    historical_outcomes: list[dict]
    # Strategy tracking
    strategy_signals: dict  # extracted signals from this deal
    # Thompson Sampling weights
    current_weights: dict
    updated_weights: dict
    # Feedback recommendations
    feedback_report: str
    agent_tuning_recommendations: list[dict]
    messages: Annotated[list, operator.add]


# ── Helpers ──────────────────────────────────────────────────────────────────

def _auth_headers() -> dict[str, str]:
    t = DJANGO_SERVICE_TOKEN
    return {"Authorization": f"Bearer {t}"} if t else {}


async def _get(path: str, default: Any = None) -> Any:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{DJANGO_API_URL}{path}", headers=_auth_headers()
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.warning("API GET %s failed: %s", path, exc)
        return default


async def _redis_get(key: str) -> dict | None:
    """Read a JSON dict from Redis."""
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(REDIS_URL, decode_responses=True)
        raw = await r.get(key)
        await r.close()
        return json.loads(raw) if raw else None
    except Exception as exc:
        logger.warning("Redis GET %s failed: %s", key, exc)
        return None


async def _redis_set(key: str, value: dict, ttl: int = 0) -> None:
    """Write a JSON dict to Redis."""
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(REDIS_URL, decode_responses=True)
        if ttl:
            await r.setex(key, ttl, json.dumps(value, default=str))
        else:
            await r.set(key, json.dumps(value, default=str))
        await r.close()
    except Exception as exc:
        logger.warning("Redis SET %s failed: %s", key, exc)


async def _redis_rpush(key: str, value: dict) -> None:
    """Append a record to a Redis list."""
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(REDIS_URL, decode_responses=True)
        await r.rpush(key, json.dumps(value, default=str))
        # Keep last 500 entries
        await r.ltrim(key, -500, -1)
        await r.close()
    except Exception as exc:
        logger.warning("Redis RPUSH %s failed: %s", key, exc)


async def _redis_lrange(key: str, start: int = 0, stop: int = -1) -> list[dict]:
    """Read list entries from Redis."""
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(REDIS_URL, decode_responses=True)
        raw_list = await r.lrange(key, start, stop)
        await r.close()
        return [json.loads(item) for item in raw_list]
    except Exception as exc:
        logger.warning("Redis LRANGE %s failed: %s", key, exc)
        return []


def _thompson_sample(alpha: float, beta: float) -> float:
    """
    Thompson Sampling: draw from Beta(alpha, beta).
    alpha = success count + 1, beta = failure count + 1.
    Returns a value between 0 and 1.
    """
    return random.betavariate(max(alpha, 0.1), max(beta, 0.1))


def _default_weights() -> dict:
    """Default strategy weights (uninformative priors)."""
    return {
        "pricing": {
            "aggressive": {"alpha": 1, "beta": 1},
            "competitive": {"alpha": 1, "beta": 1},
            "value_based": {"alpha": 1, "beta": 1},
            "maximum_profit": {"alpha": 1, "beta": 1},
        },
        "win_themes": {
            "past_performance": {"alpha": 1, "beta": 1},
            "technical_innovation": {"alpha": 1, "beta": 1},
            "cost_efficiency": {"alpha": 1, "beta": 1},
            "mission_understanding": {"alpha": 1, "beta": 1},
            "incumbent_experience": {"alpha": 1, "beta": 1},
            "small_business": {"alpha": 1, "beta": 1},
        },
        "teaming": {
            "prime_only": {"alpha": 1, "beta": 1},
            "joint_venture": {"alpha": 1, "beta": 1},
            "sub_to_large": {"alpha": 1, "beta": 1},
            "mentor_protege": {"alpha": 1, "beta": 1},
        },
        "contract_type": {
            "ffp": {"alpha": 1, "beta": 1},
            "t_and_m": {"alpha": 1, "beta": 1},
            "cpff": {"alpha": 1, "beta": 1},
            "idiq": {"alpha": 1, "beta": 1},
        },
        # Metadata
        "total_outcomes": 0,
        "total_wins": 0,
        "total_losses": 0,
        "last_updated": "",
    }


# ── Graph Nodes ──────────────────────────────────────────────────────────────

async def load_deal_and_history(state: AdaptiveLearningState) -> dict:
    """Load deal context and current strategy weights from Redis."""
    logger.info("AdaptiveLearning: loading context for deal %s", state["deal_id"])

    deal = await _get(f"/api/deals/deals/{state['deal_id']}/", default={})
    opp_id = deal.get("opportunity") or ""
    opportunity = await _get(f"/api/opportunities/opportunities/{opp_id}/", default={}) if opp_id else {}

    # Load existing weights from Redis
    weights = await _redis_get(STRATEGY_WEIGHTS_KEY) or _default_weights()

    # Load recent outcome history
    history = await _redis_lrange(OUTCOME_HISTORY_KEY, -100, -1)

    return {
        "deal": deal,
        "opportunity": opportunity,
        "current_weights": weights,
        "historical_outcomes": history,
        "messages": [HumanMessage(content=(
            f"Loaded deal: {deal.get('title', state['deal_id'])}. "
            f"History: {len(history)} outcomes, weights from {weights.get('total_outcomes', 0)} deals."
        ))],
    }


async def extract_strategy_signals(state: AdaptiveLearningState) -> dict:
    """Extract strategy signals from the deal — what approaches were used."""
    logger.info("AdaptiveLearning: extracting signals for deal %s", state["deal_id"])

    deal = state.get("deal") or {}
    opp = state.get("opportunity") or {}
    outcome = state.get("outcome", "")

    llm = get_chat_model(max_tokens=1500)

    system = SystemMessage(content=(
        "You are analyzing a completed government contract bid to extract "
        "which strategy signals were used. Extract specific signals for: "
        "pricing approach, win themes used, teaming structure, and contract type. "
        "Use ONLY the categories listed. Format:\n"
        "PRICING: aggressive|competitive|value_based|maximum_profit\n"
        "WIN_THEMES: comma-separated from: past_performance, technical_innovation, "
        "cost_efficiency, mission_understanding, incumbent_experience, small_business\n"
        "TEAMING: prime_only|joint_venture|sub_to_large|mentor_protege\n"
        "CONTRACT_TYPE: ffp|t_and_m|cpff|idiq"
    ))

    human = HumanMessage(content=(
        f"Deal: {deal.get('title', 'Unknown')}\n"
        f"Agency: {opp.get('agency', deal.get('agency', 'Unknown'))}\n"
        f"Value: ${deal.get('contract_value', 'N/A')}\n"
        f"Contract Type: {deal.get('contract_type', opp.get('contract_type', 'Unknown'))}\n"
        f"Win Themes: {deal.get('win_themes', [])}\n"
        f"Outcome: {outcome.upper()}\n"
        f"Stage: {deal.get('stage', '')}\n\n"
        "Extract the strategy signals used in this deal."
    ))

    signals = {
        "pricing": "competitive",
        "win_themes": [],
        "teaming": "prime_only",
        "contract_type": "ffp",
    }

    try:
        response = await llm.ainvoke([system, human])
        content = response.content

        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("PRICING:"):
                val = line.split(":", 1)[1].strip().lower()
                if val in ("aggressive", "competitive", "value_based", "maximum_profit"):
                    signals["pricing"] = val
            elif line.startswith("WIN_THEMES:"):
                themes = [t.strip().lower() for t in line.split(":", 1)[1].split(",")]
                signals["win_themes"] = [t for t in themes if t]
            elif line.startswith("TEAMING:"):
                val = line.split(":", 1)[1].strip().lower()
                if val in ("prime_only", "joint_venture", "sub_to_large", "mentor_protege"):
                    signals["teaming"] = val
            elif line.startswith("CONTRACT_TYPE:"):
                val = line.split(":", 1)[1].strip().lower()
                if val in ("ffp", "t_and_m", "cpff", "idiq"):
                    signals["contract_type"] = val
    except Exception as exc:
        logger.error("LLM failed in extract_strategy_signals: %s", exc)

    return {
        "strategy_signals": signals,
        "messages": [HumanMessage(content=f"Signals: pricing={signals['pricing']}, teaming={signals['teaming']}")],
    }


async def update_weights(state: AdaptiveLearningState) -> dict:
    """Update Thompson Sampling weights based on deal outcome."""
    logger.info("AdaptiveLearning: updating weights for deal %s", state["deal_id"])

    outcome = state.get("outcome", "")
    signals = state.get("strategy_signals") or {}
    weights = dict(state.get("current_weights") or _default_weights())

    is_win = outcome == "win"

    # Update pricing strategy weight
    pricing_strategy = signals.get("pricing", "competitive")
    if pricing_strategy in weights.get("pricing", {}):
        if is_win:
            weights["pricing"][pricing_strategy]["alpha"] += 1
        else:
            weights["pricing"][pricing_strategy]["beta"] += 1

    # Update win theme weights
    for theme in signals.get("win_themes", []):
        if theme in weights.get("win_themes", {}):
            if is_win:
                weights["win_themes"][theme]["alpha"] += 1
            else:
                weights["win_themes"][theme]["beta"] += 1

    # Update teaming strategy weight
    teaming = signals.get("teaming", "prime_only")
    if teaming in weights.get("teaming", {}):
        if is_win:
            weights["teaming"][teaming]["alpha"] += 1
        else:
            weights["teaming"][teaming]["beta"] += 1

    # Update contract type weight
    ct = signals.get("contract_type", "ffp")
    if ct in weights.get("contract_type", {}):
        if is_win:
            weights["contract_type"][ct]["alpha"] += 1
        else:
            weights["contract_type"][ct]["beta"] += 1

    # Update counters
    from datetime import datetime
    weights["total_outcomes"] = weights.get("total_outcomes", 0) + 1
    weights["total_wins"] = weights.get("total_wins", 0) + (1 if is_win else 0)
    weights["total_losses"] = weights.get("total_losses", 0) + (0 if is_win else 1)
    weights["last_updated"] = datetime.utcnow().isoformat()

    # Persist to Redis
    await _redis_set(STRATEGY_WEIGHTS_KEY, weights)

    # Also record this outcome in history list
    await _redis_rpush(OUTCOME_HISTORY_KEY, {
        "deal_id": state["deal_id"],
        "outcome": outcome,
        "signals": signals,
        "timestamp": weights["last_updated"],
    })

    return {
        "updated_weights": weights,
        "messages": [HumanMessage(content=(
            f"Weights updated. Total outcomes: {weights['total_outcomes']} "
            f"({weights['total_wins']}W / {weights['total_losses']}L)"
        ))],
    }


async def generate_tuning_recommendations(state: AdaptiveLearningState) -> dict:
    """Generate agent-specific tuning recommendations from accumulated weights."""
    logger.info("AdaptiveLearning: generating recommendations for deal %s", state["deal_id"])

    weights = state.get("updated_weights") or {}
    outcome = state.get("outcome", "")
    signals = state.get("strategy_signals") or {}

    recommendations = []

    # Compute Thompson Sampling rankings for each category
    for category in ("pricing", "win_themes", "teaming", "contract_type"):
        cat_weights = weights.get(category, {})
        if not isinstance(cat_weights, dict):
            continue

        # Sample and rank strategies
        rankings = []
        for strategy, params in cat_weights.items():
            if not isinstance(params, dict) or "alpha" not in params:
                continue
            alpha = params["alpha"]
            beta = params["beta"]
            sample = _thompson_sample(alpha, beta)
            total = alpha + beta - 2  # subtract priors
            win_rate = (alpha - 1) / max(total, 1) if total > 0 else 0.5
            rankings.append({
                "strategy": strategy,
                "sample": round(sample, 3),
                "win_rate": round(win_rate, 3),
                "observations": total,
            })

        rankings.sort(key=lambda x: x["sample"], reverse=True)

        if rankings:
            best = rankings[0]
            worst = rankings[-1]

            if best["observations"] >= 3:
                agent_map = {
                    "pricing": "pricing_agent",
                    "win_themes": "marketing_agent",
                    "teaming": "teaming_agent",
                    "contract_type": "strategy_agent",
                }

                recommendations.append({
                    "target_agent": agent_map.get(category, category),
                    "category": category,
                    "best_strategy": best["strategy"],
                    "best_win_rate": best["win_rate"],
                    "best_observations": best["observations"],
                    "worst_strategy": worst["strategy"],
                    "worst_win_rate": worst["win_rate"],
                    "recommendation": (
                        f"Prefer '{best['strategy']}' (win rate {best['win_rate']:.0%} "
                        f"over {best['observations']} deals) over '{worst['strategy']}' "
                        f"({worst['win_rate']:.0%}) for {category} decisions."
                    ),
                    "rankings": rankings,
                })

    # Build feedback report
    total = weights.get("total_outcomes", 0)
    wins = weights.get("total_wins", 0)
    overall_wr = wins / max(total, 1)

    report_lines = [
        f"ADAPTIVE LEARNING FEEDBACK — Deal: {state['deal'].get('title', state['deal_id'])}",
        f"Outcome: {outcome.upper()}",
        f"Overall Win Rate: {overall_wr:.0%} ({wins}W / {weights.get('total_losses', 0)}L over {total} deals)",
        "",
        "STRATEGY RANKINGS (Thompson Sampling):",
    ]

    for rec in recommendations:
        report_lines.append(f"\n  {rec['category'].upper()}:")
        for r in rec["rankings"]:
            marker = " ★" if r["strategy"] == rec["best_strategy"] else ""
            report_lines.append(
                f"    {r['strategy']}: {r['win_rate']:.0%} win rate "
                f"({r['observations']} obs, sample={r['sample']:.3f}){marker}"
            )

    report_lines.append("\nRECOMMENDATIONS:")
    for rec in recommendations:
        report_lines.append(f"  → {rec['target_agent']}: {rec['recommendation']}")

    return {
        "feedback_report": "\n".join(report_lines),
        "agent_tuning_recommendations": recommendations,
        "messages": [HumanMessage(content=f"Generated {len(recommendations)} tuning recommendations")],
    }


# ── Graph Builder ────────────────────────────────────────────────────────────

def build_adaptive_learning_graph() -> StateGraph:
    wf = StateGraph(AdaptiveLearningState)

    wf.add_node("load_deal_and_history", load_deal_and_history)
    wf.add_node("extract_strategy_signals", extract_strategy_signals)
    wf.add_node("update_weights", update_weights)
    wf.add_node("generate_tuning_recommendations", generate_tuning_recommendations)

    wf.set_entry_point("load_deal_and_history")
    wf.add_edge("load_deal_and_history", "extract_strategy_signals")
    wf.add_edge("extract_strategy_signals", "update_weights")
    wf.add_edge("update_weights", "generate_tuning_recommendations")
    wf.add_edge("generate_tuning_recommendations", END)

    return wf.compile()


adaptive_learning_graph = build_adaptive_learning_graph()


# ── Agent Class ──────────────────────────────────────────────────────────────

class AdaptiveLearningAgent(BaseAgent):
    """
    Adaptive learning agent with Thompson Sampling feedback loop.

    Runs after every deal outcome (win/loss/no_bid) to:
    1. Extract what strategies were used
    2. Update Bayesian confidence weights per strategy
    3. Generate agent-specific tuning recommendations
    4. Persist weights to Redis for other agents to query
    """

    agent_name = "adaptive_learning_agent"

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        deal_id = input_data.get("deal_id", "")
        if not deal_id:
            return {"error": "deal_id is required"}

        outcome = input_data.get("outcome", "")
        if outcome not in ("win", "loss", "no_bid", "cancelled"):
            return {"error": f"Invalid outcome: {outcome}. Must be win/loss/no_bid/cancelled"}

        initial: AdaptiveLearningState = {
            "deal_id": deal_id,
            "outcome": outcome,
            "deal": {},
            "opportunity": {},
            "historical_outcomes": [],
            "strategy_signals": {},
            "current_weights": {},
            "updated_weights": {},
            "feedback_report": "",
            "agent_tuning_recommendations": [],
            "messages": [],
        }

        try:
            await self.emit_event(
                "thinking",
                {"message": f"Adaptive learning: analyzing {outcome} for deal {deal_id}"},
                execution_id=deal_id,
            )
            fs = await adaptive_learning_graph.ainvoke(initial)

            total = fs["updated_weights"].get("total_outcomes", 0)
            wins = fs["updated_weights"].get("total_wins", 0)

            await self.emit_event(
                "output",
                {
                    "outcome": outcome,
                    "total_outcomes": total,
                    "win_rate": round(wins / max(total, 1), 3),
                    "recommendations_count": len(fs["agent_tuning_recommendations"]),
                },
                execution_id=deal_id,
            )
            return {
                "deal_id": deal_id,
                "outcome": outcome,
                "strategy_signals": fs["strategy_signals"],
                "updated_weights": fs["updated_weights"],
                "feedback_report": fs["feedback_report"],
                "agent_tuning_recommendations": fs["agent_tuning_recommendations"],
            }
        except Exception as exc:
            logger.exception("AdaptiveLearningAgent failed for deal %s", deal_id)
            await self.emit_event("error", {"error": str(exc)}, execution_id=deal_id)
            return {"error": str(exc), "deal_id": deal_id}


# ── Public API: Query Strategy Weights ───────────────────────────────────────

async def get_strategy_recommendations(category: str = "") -> dict:
    """
    Public function for other agents to query current strategy weights.

    Usage (from pricing_agent, marketing_agent, etc.):
        from src.agents.adaptive_learning_agent import get_strategy_recommendations
        recs = await get_strategy_recommendations("pricing")
        best = recs.get("best_strategy")  # e.g. "competitive"
    """
    weights = await _redis_get(STRATEGY_WEIGHTS_KEY) or _default_weights()

    if category and category in weights:
        cat_weights = weights[category]
        if not isinstance(cat_weights, dict):
            return {"category": category, "weights": {}}

        rankings = []
        for strategy, params in cat_weights.items():
            if not isinstance(params, dict) or "alpha" not in params:
                continue
            total = params["alpha"] + params["beta"] - 2
            win_rate = (params["alpha"] - 1) / max(total, 1) if total > 0 else 0.5
            rankings.append({
                "strategy": strategy,
                "win_rate": round(win_rate, 3),
                "observations": total,
                "confidence": round(_thompson_sample(params["alpha"], params["beta"]), 3),
            })

        rankings.sort(key=lambda x: x["confidence"], reverse=True)

        return {
            "category": category,
            "best_strategy": rankings[0]["strategy"] if rankings else "",
            "rankings": rankings,
            "total_outcomes": weights.get("total_outcomes", 0),
        }

    return {
        "all_weights": weights,
        "total_outcomes": weights.get("total_outcomes", 0),
    }
