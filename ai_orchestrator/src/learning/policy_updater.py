"""Policy updater for the learning loop.

Updates scoring weights, confidence thresholds, and agent policies based on
accumulated feedback and outcomes.

Uses offline RL: learns from historical data rather than live exploration.
"""
import json
import logging
import os
from typing import Any

import httpx

logger = logging.getLogger("ai_orchestrator.learning.policy_updater")

_DJANGO_URL = os.getenv("DJANGO_API_URL", "http://django-api:8001")
_SERVICE_TOKEN = os.getenv("DJANGO_SERVICE_TOKEN", "")


def _headers() -> dict:
    return {"Authorization": f"Bearer {_SERVICE_TOKEN}"} if _SERVICE_TOKEN else {}


# ── Default policy weights ────────────────────────────────────────────────────

DEFAULT_FIT_SCORE_WEIGHTS = {
    "naics_match": 0.20,
    "psc_match": 0.10,
    "keyword_overlap": 0.15,
    "capability_similarity": 0.20,
    "past_performance_relevance": 0.15,
    "value_fit": 0.05,
    "deadline_feasibility": 0.05,
    "set_aside_match": 0.10,
    "competition_intensity": -0.05,  # penalize
    "risk_factors": -0.05,  # penalize
}

DEFAULT_STRATEGY_WEIGHTS = {
    "agency_alignment": 0.20,
    "domain_alignment": 0.15,
    "growth_market": 0.10,
    "portfolio_balance": 0.10,
    "revenue_contribution": 0.15,
    "capacity_fit": 0.15,
    "strategic_relationship": 0.10,
    "competitive_risk": -0.05,
}

DEFAULT_CONFIDENCE_THRESHOLDS = {
    "auto_score": 0.90,       # Auto-apply scoring without human review
    "auto_advance": 0.85,     # Auto-advance deal stage
    "bid_recommendation": 0.80,
    "pricing_selection": 0.75,
    "proposal_generation": 0.70,
}


# ── Weight update logic ───────────────────────────────────────────────────────

def update_weights_from_outcomes(
    current_weights: dict[str, float],
    outcomes: list[dict[str, Any]],
    learning_rate: float = 0.05,
) -> dict[str, float]:
    """Update feature weights using simplified gradient-based learning.

    For each feature, if it was high when we won → increase weight.
    If it was high when we lost → decrease weight.

    Args:
        current_weights: Current weight dict.
        outcomes: List of outcome dicts with features and reward.
        learning_rate: Step size for weight updates (0-1).

    Returns:
        Updated weight dict.
    """
    if not outcomes:
        return current_weights

    weight_gradients: dict[str, float] = {k: 0.0 for k in current_weights}
    n = len(outcomes)

    for outcome in outcomes:
        reward = outcome.get("reward", 0)
        features = outcome.get("context_features", {})

        for feature, weight in current_weights.items():
            feature_value = features.get(feature, 0)
            # Gradient: reward × feature_value (policy gradient approximation)
            weight_gradients[feature] += reward * float(feature_value) / n

    # Apply gradient updates with clipping
    updated = {}
    for feature, weight in current_weights.items():
        gradient = weight_gradients.get(feature, 0)
        new_weight = weight + learning_rate * gradient
        # Clip to reasonable range
        if weight > 0:
            updated[feature] = max(0.01, min(0.50, new_weight))
        else:
            updated[feature] = max(-0.20, min(-0.01, new_weight))

    # Renormalize positive weights to sum to ~1
    pos_sum = sum(v for v in updated.values() if v > 0)
    if pos_sum > 0:
        for k in updated:
            if updated[k] > 0:
                updated[k] = updated[k] / pos_sum

    return updated


async def get_current_policy(policy_name: str = "fit_score_weights") -> dict[str, Any]:
    """Fetch the current policy from the Django backend.

    Args:
        policy_name: Policy identifier.

    Returns:
        Policy dict with weights/thresholds.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{_DJANGO_URL}/api/policies/{policy_name}/",
                headers=_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.warning("Policy fetch failed for %s: %s", policy_name, exc)
        # Return defaults
        defaults = {
            "fit_score_weights": DEFAULT_FIT_SCORE_WEIGHTS,
            "strategy_weights": DEFAULT_STRATEGY_WEIGHTS,
            "confidence_thresholds": DEFAULT_CONFIDENCE_THRESHOLDS,
        }
        return defaults.get(policy_name, {})


async def save_policy(
    policy_name: str,
    policy_data: dict[str, Any],
    update_reason: str = "",
) -> dict[str, Any]:
    """Save an updated policy to the Django backend.

    Args:
        policy_name: Policy identifier.
        policy_data: Updated policy data.
        update_reason: Explanation of why this update was made.

    Returns:
        Saved policy with version number.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.put(
                f"{_DJANGO_URL}/api/policies/{policy_name}/",
                json={"data": policy_data, "update_reason": update_reason},
                headers=_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("Policy save failed for %s: %s", policy_name, exc)
        return {"policy_name": policy_name, "data": policy_data, "error": str(exc)}


async def run_policy_update_cycle(
    min_outcomes: int = 10,
    learning_rate: float = 0.03,
) -> dict[str, Any]:
    """Run a full policy update cycle using recent outcomes.

    This is the main entry point for the learning loop. Called periodically
    (e.g. weekly or after each contract outcome).

    Args:
        min_outcomes: Minimum outcomes required to trigger an update.
        learning_rate: Learning rate for weight updates.

    Returns:
        Dict with updated_policies, outcomes_used, changes_summary.
    """
    from src.learning.reward_tracker import get_recent_outcomes

    outcomes = await get_recent_outcomes(limit=200)

    if len(outcomes) < min_outcomes:
        return {
            "updated": False,
            "reason": f"Insufficient outcomes ({len(outcomes)} < {min_outcomes})",
        }

    updated_policies: list[str] = []
    changes: dict[str, Any] = {}

    # Update fit score weights
    fit_weights = await get_current_policy("fit_score_weights")
    new_fit_weights = update_weights_from_outcomes(
        current_weights=fit_weights,
        outcomes=[o for o in outcomes if o.get("context_features")],
        learning_rate=learning_rate,
    )
    if new_fit_weights != fit_weights:
        await save_policy(
            "fit_score_weights",
            new_fit_weights,
            update_reason=f"Updated from {len(outcomes)} outcomes",
        )
        updated_policies.append("fit_score_weights")
        changes["fit_score_weights"] = _diff_weights(fit_weights, new_fit_weights)

    # Update strategy weights
    strategy_weights = await get_current_policy("strategy_weights")
    strategy_outcomes = [o for o in outcomes if o.get("agent_name") == "strategy_agent"]
    if len(strategy_outcomes) >= min_outcomes // 2:
        new_strategy_weights = update_weights_from_outcomes(
            current_weights=strategy_weights,
            outcomes=strategy_outcomes,
            learning_rate=learning_rate,
        )
        if new_strategy_weights != strategy_weights:
            await save_policy("strategy_weights", new_strategy_weights)
            updated_policies.append("strategy_weights")
            changes["strategy_weights"] = _diff_weights(strategy_weights, new_strategy_weights)

    # Update confidence thresholds based on accuracy
    await _update_confidence_thresholds(outcomes)
    updated_policies.append("confidence_thresholds")

    logger.info("Policy update cycle complete. Updated: %s", updated_policies)

    return {
        "updated": True,
        "updated_policies": updated_policies,
        "outcomes_used": len(outcomes),
        "changes_summary": changes,
    }


async def _update_confidence_thresholds(outcomes: list[dict]) -> None:
    """Adjust confidence thresholds based on agent prediction accuracy."""
    thresholds = await get_current_policy("confidence_thresholds")

    # Compute accuracy for each agent type
    agent_accuracies: dict[str, list[float]] = {}
    for o in outcomes:
        agent = o.get("agent_name", "")
        if not agent:
            continue
        reward = o.get("reward", 0)
        human_override = o.get("human_override", False)
        if not human_override:
            # Agent was correct (not overridden) and got positive reward
            accuracy = 1.0 if reward > 0 else 0.0
        else:
            accuracy = 0.0  # Human override = agent was wrong
        agent_accuracies.setdefault(agent, []).append(accuracy)

    for agent, accuracies in agent_accuracies.items():
        if len(accuracies) < 5:
            continue
        avg_accuracy = sum(accuracies) / len(accuracies)
        threshold_key = f"{agent.replace('_agent', '')}_approval"
        if threshold_key in thresholds:
            current = thresholds[threshold_key]
            # If agent is very accurate, lower threshold (allow more autonomy)
            # If agent is often wrong, raise threshold (require more human review)
            if avg_accuracy > 0.85:
                thresholds[threshold_key] = max(0.60, current - 0.02)
            elif avg_accuracy < 0.65:
                thresholds[threshold_key] = min(0.95, current + 0.05)

    await save_policy(
        "confidence_thresholds",
        thresholds,
        update_reason="Adjusted based on agent prediction accuracy",
    )


def _diff_weights(old: dict, new: dict) -> dict:
    """Return a dict of weight changes."""
    changes = {}
    for key in old:
        if key in new and abs(old[key] - new[key]) > 0.001:
            changes[key] = {"old": round(old[key], 4), "new": round(new[key], 4)}
    return changes
