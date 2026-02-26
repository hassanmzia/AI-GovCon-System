"""
HITL Gate Manager — enforces Human-In-The-Loop requirements based on active policy.

Determines whether an AI action can proceed autonomously or needs human approval.
Posts HITL requests to the Django backend when approval is needed.
"""
import logging
import os
from typing import Optional

import httpx

from src.governance.risk_engine import RiskScore

logger = logging.getLogger("ai_orchestrator.governance.hitl_manager")

DJANGO_API_URL = os.getenv("DJANGO_API_URL", "http://django-api:8001")
DJANGO_SERVICE_TOKEN = os.getenv("DJANGO_SERVICE_TOKEN", "")

# Actions that always require human approval regardless of autonomy level or risk score.
MANDATORY_HITL: frozenset[str] = frozenset({
    "bid_no_bid",
    "final_price",
    "final_submission",
    "contract_terms",
    "contract_sign",
})


def _auth_headers() -> dict[str, str]:
    t = DJANGO_SERVICE_TOKEN
    return {"Authorization": f"Bearer {t}"} if t else {}


async def check_gate(
    action: str,
    deal_id: str,
    policy: dict,
    risk_score: Optional[RiskScore] = None,
) -> dict:
    """
    Determine whether the AI can proceed with an action autonomously or needs HITL.

    Evaluation order:
      1. Kill switch active → always block.
      2. Mandatory HITL actions → always require approval.
      3. Risk thresholds exceeded (if risk_score provided) → require approval.
      4. Action not in allowed_actions for current autonomy level → require approval.
      5. Action in requires_hitl list for current autonomy level → require approval.
      6. Otherwise → allowed autonomously.

    Args:
        action:     The action identifier being requested (e.g. "final_submission").
        deal_id:    The deal this action relates to.
        policy:     The active AI Autonomy Policy dict.
        risk_score: Optional pre-computed RiskScore for threshold checks.

    Returns:
        dict with keys: allowed (bool), requires_hitl (bool), reason (str),
                        autonomy_level (int).
    """
    autonomy_level: int = int(policy.get("current_autonomy_level", 1))
    kill_switch: bool = bool(policy.get("kill_switch_active", False))

    # ── 1. Kill switch ─────────────────────────────────────────────────────────
    if kill_switch:
        logger.warning(
            "HITL Gate: KILL SWITCH active — blocking action '%s' for deal %s",
            action, deal_id,
        )
        return {
            "allowed": False,
            "requires_hitl": False,
            "reason": "Kill switch is active. All autonomous actions are blocked.",
            "autonomy_level": autonomy_level,
        }

    # ── 2. Mandatory HITL actions ──────────────────────────────────────────────
    if action in MANDATORY_HITL:
        logger.info(
            "HITL Gate: mandatory HITL for action '%s' on deal %s", action, deal_id
        )
        return {
            "allowed": False,
            "requires_hitl": True,
            "reason": f"Action '{action}' is in the mandatory HITL set and always requires human approval.",
            "autonomy_level": autonomy_level,
        }

    # ── 3. Risk threshold checks ───────────────────────────────────────────────
    if risk_score is not None:
        risk_thresholds: dict = policy.get("risk_thresholds", {})
        max_legal = float(risk_thresholds.get("max_legal_risk", 0.30))
        max_compliance = float(risk_thresholds.get("max_compliance_risk", 0.25))
        max_deadline = float(risk_thresholds.get("max_deadline_risk", 0.35))

        if risk_score.legal > max_legal:
            return {
                "allowed": False,
                "requires_hitl": True,
                "reason": (
                    f"Legal risk {risk_score.legal:.3f} exceeds policy threshold {max_legal:.3f}."
                ),
                "autonomy_level": autonomy_level,
            }
        if risk_score.compliance > max_compliance:
            return {
                "allowed": False,
                "requires_hitl": True,
                "reason": (
                    f"Compliance risk {risk_score.compliance:.3f} exceeds policy threshold "
                    f"{max_compliance:.3f}."
                ),
                "autonomy_level": autonomy_level,
            }
        if risk_score.deadline > max_deadline:
            return {
                "allowed": False,
                "requires_hitl": True,
                "reason": (
                    f"Deadline risk {risk_score.deadline:.3f} exceeds policy threshold "
                    f"{max_deadline:.3f}."
                ),
                "autonomy_level": autonomy_level,
            }

    # ── 4 & 5. Autonomy-level allowed_actions and requires_hitl lists ──────────
    level_key = f"L{autonomy_level}"
    autonomy_levels: dict = policy.get("autonomy_levels", {})
    level_config: dict = autonomy_levels.get(level_key, {})

    allowed_actions: list[str] = level_config.get("allowed_actions", [])
    requires_hitl_actions: list[str] = level_config.get("requires_hitl", [])

    if action in requires_hitl_actions:
        logger.info(
            "HITL Gate: action '%s' is in requires_hitl for level %s on deal %s",
            action, level_key, deal_id,
        )
        return {
            "allowed": False,
            "requires_hitl": True,
            "reason": (
                f"Action '{action}' requires HITL approval at autonomy level {autonomy_level} ({level_key})."
            ),
            "autonomy_level": autonomy_level,
        }

    if action not in allowed_actions:
        logger.info(
            "HITL Gate: action '%s' not in allowed_actions for level %s on deal %s",
            action, level_key, deal_id,
        )
        return {
            "allowed": False,
            "requires_hitl": True,
            "reason": (
                f"Action '{action}' is not in the allowed_actions list for autonomy "
                f"level {autonomy_level} ({level_key})."
            ),
            "autonomy_level": autonomy_level,
        }

    # ── Approved for autonomous execution ──────────────────────────────────────
    logger.info(
        "HITL Gate: action '%s' APPROVED autonomously at level %s for deal %s",
        action, level_key, deal_id,
    )
    return {
        "allowed": True,
        "requires_hitl": False,
        "reason": f"Action '{action}' is permitted at autonomy level {autonomy_level} ({level_key}).",
        "autonomy_level": autonomy_level,
    }


async def request_hitl_approval(
    action: str,
    deal_id: str,
    agent_name: str,
    payload: dict,
) -> dict:
    """
    Post a HITL approval request to the Django backend.

    POSTs to /api/deals/{deal_id}/approvals/ with the action, agent name,
    and any relevant payload. Returns the created approval request record
    or an error dict if the request fails.

    Args:
        action:     The action requiring approval.
        deal_id:    The deal this approval is for.
        agent_name: The agent requesting approval.
        payload:    Additional context for the approver.

    Returns:
        dict — the created approval record from Django, or {"error": str}.
    """
    body = {
        "approval_type": action,
        "agent_name": agent_name,
        "ai_recommendation": "approve",
        "ai_rationale": f"Agent '{agent_name}' requests human approval for action '{action}'.",
        "payload": payload,
    }
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{DJANGO_API_URL}/api/deals/{deal_id}/approvals/",
                json=body,
                headers=_auth_headers(),
            )
            resp.raise_for_status()
            result = resp.json()
            logger.info(
                "HITLManager: approval request created for action '%s' on deal %s (id=%s)",
                action, deal_id, result.get("id"),
            )
            return result
    except httpx.HTTPStatusError as exc:
        logger.error(
            "HITLManager: HTTP %s posting approval for action '%s' deal %s: %s",
            exc.response.status_code, action, deal_id, exc,
        )
        return {"error": str(exc), "action": action, "deal_id": deal_id}
    except Exception as exc:
        logger.error(
            "HITLManager: failed to post approval for action '%s' deal %s: %s",
            action, deal_id, exc,
        )
        return {"error": str(exc), "action": action, "deal_id": deal_id}


async def log_enforcement(
    action: str,
    deal_id: str,
    decision: str,
    reason: str,
    agent_name: str,
    policy: dict,
    risk_score: Optional[RiskScore] = None,
) -> None:
    """
    Post a PolicyEnforcementLog record to the Django backend for audit purposes.

    POSTs to /api/policies/enforcement-log/ with full context of the enforcement
    decision. Failures are logged as warnings and swallowed so they never block
    the primary workflow.

    Args:
        action:     The action that was evaluated.
        deal_id:    The deal being processed.
        decision:   "allowed", "hitl_required", or "blocked".
        reason:     Human-readable explanation of the decision.
        agent_name: The agent that triggered the gate check.
        policy:     The policy snapshot at time of enforcement.
        risk_score: Optional risk score computed for this check.
    """
    body: dict = {
        "action": action,
        "deal_id": deal_id,
        "decision": decision,
        "reason": reason,
        "agent_name": agent_name,
        "autonomy_level": policy.get("current_autonomy_level"),
        "policy_id": policy.get("id"),
        "kill_switch_active": policy.get("kill_switch_active", False),
    }
    if risk_score is not None:
        body["risk_scores"] = risk_score.to_dict()

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{DJANGO_API_URL}/api/policies/enforcement-log/",
                json=body,
                headers=_auth_headers(),
            )
            resp.raise_for_status()
            logger.info(
                "HITLManager: enforcement logged — action='%s' decision='%s' deal=%s",
                action, decision, deal_id,
            )
    except httpx.HTTPStatusError as exc:
        logger.warning(
            "HITLManager: HTTP %s logging enforcement for action '%s' deal %s: %s",
            exc.response.status_code, action, deal_id, exc,
        )
    except Exception as exc:
        logger.warning(
            "HITLManager: failed to log enforcement for action '%s' deal %s: %s",
            action, deal_id, exc,
        )
