"""Reward tracker for the learning loop.

Tracks outcomes from bid decisions, proposal scores, win/loss results,
and pricing accuracy to feed into the reinforcement learning system.

Reward engineering:
  +10: contract win
  +5:  shortlisted / best value selection
  +1:  good review scores (≥ 8/10)
  -1:  compliance defects found
  -5:  missed submission deadlines
  -3:  significantly over/under priced (>15% off market)
"""
import logging
import os
from datetime import datetime, timezone
from typing import Any

import httpx

logger = logging.getLogger("ai_orchestrator.learning.reward_tracker")

_DJANGO_URL = os.getenv("DJANGO_API_URL", "http://django-api:8001")
_SERVICE_TOKEN = os.getenv("DJANGO_SERVICE_TOKEN", "")


def _headers() -> dict:
    return {"Authorization": f"Bearer {_SERVICE_TOKEN}"} if _SERVICE_TOKEN else {}


# ── Reward constants ──────────────────────────────────────────────────────────

REWARD_WIN = 10.0
REWARD_SHORTLISTED = 5.0
REWARD_GOOD_REVIEW = 1.0
PENALTY_COMPLIANCE_DEFECT = -1.0
PENALTY_MISSED_DEADLINE = -5.0
PENALTY_MISPRICED = -3.0
REWARD_BID_SUBMITTED = 0.5
REWARD_PASSED_GATE = 0.2


# ── Reward computation ────────────────────────────────────────────────────────

def compute_reward(outcome: dict[str, Any]) -> float:
    """Compute total reward from an outcome dict.

    Args:
        outcome: Dict with keys:
            - outcome_type: "win", "loss", "shortlisted", "no_bid", "submitted"
            - review_score: float 0-10 (optional)
            - compliance_defects: int (optional)
            - deadline_met: bool (optional)
            - pricing_accuracy_pct: float – how close our price was to award (optional)

    Returns:
        Total reward scalar.
    """
    reward = 0.0
    outcome_type = outcome.get("outcome_type", "")

    if outcome_type == "win":
        reward += REWARD_WIN
    elif outcome_type == "shortlisted":
        reward += REWARD_SHORTLISTED
    elif outcome_type == "submitted":
        reward += REWARD_BID_SUBMITTED
    elif outcome_type == "gate_passed":
        reward += REWARD_PASSED_GATE

    review_score = outcome.get("review_score")
    if review_score is not None and review_score >= 8.0:
        reward += REWARD_GOOD_REVIEW

    defects = outcome.get("compliance_defects", 0) or 0
    reward += PENALTY_COMPLIANCE_DEFECT * defects

    if outcome.get("deadline_met") is False:
        reward += PENALTY_MISSED_DEADLINE

    pricing_accuracy = outcome.get("pricing_accuracy_pct")
    if pricing_accuracy is not None and abs(pricing_accuracy) > 15:
        reward += PENALTY_MISPRICED

    return reward


async def record_outcome(
    deal_id: str,
    outcome_type: str,
    outcome_details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Record a deal outcome and compute its reward signal.

    Args:
        deal_id: Deal UUID.
        outcome_type: "win", "loss", "shortlisted", "submitted", "gate_passed".
        outcome_details: Additional outcome details for reward computation.

    Returns:
        Dict with deal_id, outcome_type, reward, and stored record ID.
    """
    details = outcome_details or {}
    details["outcome_type"] = outcome_type
    reward = compute_reward(details)

    record = {
        "deal_id": deal_id,
        "outcome_type": outcome_type,
        "reward": reward,
        "details": details,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{_DJANGO_URL}/api/learning/outcomes/",
                json=record,
                headers=_headers(),
            )
            resp.raise_for_status()
            return {**record, "id": resp.json().get("id")}
    except Exception as exc:
        logger.warning("Outcome recording to Django failed: %s", exc)
        return record


async def get_recent_outcomes(
    limit: int = 50,
    outcome_type: str | None = None,
) -> list[dict[str, Any]]:
    """Fetch recent outcomes from the Django backend.

    Args:
        limit: Max outcomes to return.
        outcome_type: Optional filter.

    Returns:
        List of outcome records with reward signals.
    """
    try:
        params: dict[str, Any] = {"limit": limit}
        if outcome_type:
            params["outcome_type"] = outcome_type

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{_DJANGO_URL}/api/learning/outcomes/",
                params=params,
                headers=_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("Outcomes fetch failed: %s", exc)
        return []


async def compute_win_rate(
    period_days: int = 365,
) -> dict[str, Any]:
    """Compute win rate and average reward over a period.

    Returns:
        Dict with total_bids, wins, losses, win_rate, avg_reward.
    """
    outcomes = await get_recent_outcomes(limit=500)
    if not outcomes:
        return {"total_bids": 0, "wins": 0, "losses": 0, "win_rate": 0.0, "avg_reward": 0.0}

    # Filter by period
    from datetime import timedelta

    cutoff = datetime.now(timezone.utc) - timedelta(days=period_days)
    recent = []
    for o in outcomes:
        recorded = o.get("recorded_at", "")
        if recorded:
            try:
                dt = datetime.fromisoformat(recorded.replace("Z", "+00:00"))
                if dt > cutoff:
                    recent.append(o)
            except Exception:
                recent.append(o)
        else:
            recent.append(o)

    submitted = [o for o in recent if o.get("outcome_type") in ("submitted", "win", "loss", "shortlisted")]
    wins = [o for o in recent if o.get("outcome_type") == "win"]
    losses = [o for o in recent if o.get("outcome_type") == "loss"]
    rewards = [o.get("reward", 0) for o in recent]

    return {
        "total_bids": len(submitted),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": len(wins) / max(1, len(submitted)),
        "avg_reward": sum(rewards) / max(1, len(rewards)),
        "period_days": period_days,
    }


async def record_agent_feedback(
    agent_name: str,
    action_type: str,
    context: dict[str, Any],
    outcome: str,
    human_override: bool = False,
) -> dict[str, Any]:
    """Record agent action feedback for offline RL training.

    Args:
        agent_name: Name of the agent (e.g. "pricing_agent").
        action_type: Type of action taken.
        context: Context features at decision time.
        outcome: Outcome of the action.
        human_override: Whether a human overrode the agent's recommendation.

    Returns:
        Recorded feedback entry.
    """
    entry = {
        "agent_name": agent_name,
        "action_type": action_type,
        "context": context,
        "outcome": outcome,
        "human_override": human_override,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{_DJANGO_URL}/api/learning/agent-feedback/",
                json=entry,
                headers=_headers(),
            )
            resp.raise_for_status()
            return {**entry, "id": resp.json().get("id")}
    except Exception as exc:
        logger.warning("Agent feedback recording failed: %s", exc)
        return entry
