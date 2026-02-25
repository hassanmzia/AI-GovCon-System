"""
Policy Loader — fetches the active AI Autonomy Policy from the Django backend.

Caches policy for TTL_SECONDS to avoid hammering the API.
Falls back to a safe default policy (L1 autonomy, strict HITL) if unavailable.
"""
import logging
import os
import time
from typing import Any

import httpx

logger = logging.getLogger("ai_orchestrator.governance.policy_loader")

DJANGO_API_URL = os.getenv("DJANGO_API_URL", "http://django-api:8001")
DJANGO_SERVICE_TOKEN = os.getenv("DJANGO_SERVICE_TOKEN", "")

TTL_SECONDS = 300

# Module-level cache
_cache: dict[str, Any] = {
    "policy": None,
    "loaded_at": 0.0,
}

# Safe fallback policy — L1 autonomy, strict HITL, conservative thresholds.
# This policy is used when the Django backend is unreachable.
DEFAULT_POLICY: dict[str, Any] = {
    "id": "default-safe-policy",
    "name": "Safe Default Policy (fallback)",
    "current_autonomy_level": 1,
    "kill_switch_active": False,
    "autonomy_levels": {
        "L0": {
            "level": 0,
            "name": "Full Manual",
            "description": "AI assists only — all actions require human approval.",
            "allowed_actions": [],
            "requires_hitl": [
                "bid_no_bid",
                "final_price",
                "final_submission",
                "contract_terms",
                "contract_sign",
                "proposal_draft",
                "compliance_matrix",
                "past_performance_select",
                "pricing_scenario",
                "team_formation",
            ],
        },
        "L1": {
            "level": 1,
            "name": "Supervised Autonomy",
            "description": "AI can perform research, analysis, and draft content. Consequential actions require HITL.",
            "allowed_actions": [
                "opportunity_search",
                "rfp_analysis",
                "compliance_check",
                "proposal_draft",
                "past_performance_match",
                "competitor_analysis",
                "market_research",
                "risk_assessment",
            ],
            "requires_hitl": [
                "bid_no_bid",
                "final_price",
                "final_submission",
                "contract_terms",
                "contract_sign",
                "pricing_scenario",
            ],
        },
        "L2": {
            "level": 2,
            "name": "High Autonomy",
            "description": "AI can perform most actions autonomously. Only contract signing and final submission require HITL.",
            "allowed_actions": [
                "opportunity_search",
                "rfp_analysis",
                "compliance_check",
                "proposal_draft",
                "past_performance_match",
                "competitor_analysis",
                "market_research",
                "risk_assessment",
                "bid_no_bid",
                "pricing_scenario",
                "team_formation",
                "compliance_matrix",
            ],
            "requires_hitl": [
                "final_price",
                "final_submission",
                "contract_terms",
                "contract_sign",
            ],
        },
    },
    "risk_thresholds": {
        "max_legal_risk": 0.30,
        "max_compliance_risk": 0.25,
        "max_deadline_risk": 0.35,
        "min_confidence_to_act": 0.75,
        "min_requirement_coverage": 0.95,
    },
    "pricing_guardrails": {
        "min_margin_percent": 18,
        "requires_hitl_if_deal_over_usd": 250000,
    },
}


def _auth_headers() -> dict[str, str]:
    t = DJANGO_SERVICE_TOKEN
    return {"Authorization": f"Bearer {t}"} if t else {}


def _is_cache_valid() -> bool:
    """Return True if the cached policy is still within TTL."""
    if _cache["policy"] is None:
        return False
    age = time.monotonic() - _cache["loaded_at"]
    return age < TTL_SECONDS


async def load_policy() -> dict:
    """
    Fetch the active AI Autonomy Policy from the Django backend.

    GETs /api/policies/autonomy-policies/active/, caches result for TTL_SECONDS,
    and returns the policy dict. Falls back to DEFAULT_POLICY on any error.
    """
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{DJANGO_API_URL}/api/policies/autonomy-policies/active/",
                headers=_auth_headers(),
            )
            resp.raise_for_status()
            policy = resp.json()
            _cache["policy"] = policy
            _cache["loaded_at"] = time.monotonic()
            logger.info(
                "PolicyLoader: loaded active policy '%s' (level=%s, kill_switch=%s)",
                policy.get("name", "unknown"),
                policy.get("current_autonomy_level"),
                policy.get("kill_switch_active"),
            )
            return policy
    except httpx.HTTPStatusError as exc:
        logger.warning(
            "PolicyLoader: HTTP %s fetching active policy — using default: %s",
            exc.response.status_code,
            exc,
        )
    except Exception as exc:
        logger.warning(
            "PolicyLoader: failed to fetch active policy — using default: %s", exc
        )

    return DEFAULT_POLICY


async def get_policy() -> dict:
    """
    Return the active AI Autonomy Policy, using cache when available.

    If the in-memory cache is still within TTL, returns cached policy.
    Otherwise fetches a fresh copy from the Django backend.
    """
    if _is_cache_valid():
        return _cache["policy"]  # type: ignore[return-value]
    return await load_policy()


def invalidate_cache() -> None:
    """
    Invalidate the policy cache, forcing the next call to get_policy()
    to fetch a fresh copy from the Django backend.
    """
    _cache["policy"] = None
    _cache["loaded_at"] = 0.0
    logger.info("PolicyLoader: cache invalidated")
