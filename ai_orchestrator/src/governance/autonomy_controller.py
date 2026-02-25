"""
Autonomy Controller — wraps policy_loader + hitl_manager + risk_engine into a single
interface that agents use before taking any consequential action.
"""
import logging

from src.governance import hitl_manager, policy_loader, risk_engine

logger = logging.getLogger("ai_orchestrator.governance.autonomy_controller")


class AutonomyController:
    """
    Single-entry-point governance interface for all AI agents.

    Agents should create an instance of this class and call either:
      - can_act()  — to check whether they may proceed autonomously.
      - enforce()  — to perform the full governance flow including HITL escalation
                     and audit logging.
    """

    async def can_act(
        self,
        action: str,
        deal_id: str,
        deal_context: dict | None = None,
    ) -> dict:
        """
        Check whether the AI may autonomously execute the given action.

        Loads the active policy, computes a risk score from deal_context, and
        delegates to hitl_manager.check_gate() for the final decision.

        Args:
            action:       Action identifier (e.g. "proposal_draft", "final_price").
            deal_id:      Deal being processed.
            deal_context: Optional deal-level context used for risk scoring.

        Returns:
            dict with keys:
                can_act (bool)        — True if autonomous execution is permitted.
                requires_hitl (bool)  — True if human approval is needed.
                reason (str)          — Explanation of the decision.
                risk_score (dict)     — Risk dimension scores and composite.
                policy_level (int)    — Current autonomy level from policy.
        """
        if deal_context is None:
            deal_context = {}

        try:
            policy = await policy_loader.get_policy()
        except Exception as exc:
            logger.warning(
                "AutonomyController.can_act: failed to load policy, using default: %s", exc
            )
            policy = policy_loader.DEFAULT_POLICY

        try:
            score = risk_engine.assess(deal_context, policy)
        except Exception as exc:
            logger.warning(
                "AutonomyController.can_act: risk assessment failed, using zero score: %s", exc
            )
            score = risk_engine.RiskScore()

        try:
            gate = await hitl_manager.check_gate(
                action=action,
                deal_id=deal_id,
                policy=policy,
                risk_score=score,
            )
        except Exception as exc:
            logger.error(
                "AutonomyController.can_act: check_gate failed — defaulting to block: %s", exc
            )
            gate = {
                "allowed": False,
                "requires_hitl": True,
                "reason": f"Gate check failed unexpectedly: {exc}",
                "autonomy_level": policy.get("current_autonomy_level", 1),
            }

        return {
            "can_act": gate["allowed"],
            "requires_hitl": gate["requires_hitl"],
            "reason": gate["reason"],
            "risk_score": score.to_dict(),
            "policy_level": gate["autonomy_level"],
        }

    async def enforce(
        self,
        action: str,
        deal_id: str,
        agent_name: str,
        deal_context: dict | None = None,
        payload: dict | None = None,
    ) -> dict:
        """
        Full governance enforcement: check gate, escalate to HITL if needed,
        and audit-log every decision.

        Decision outcomes:
          - Proceed autonomously   → {"proceed": True}
          - HITL required          → {"proceed": False, "hitl_requested": True,
                                       "approval_id": str | None}
          - Blocked (kill switch)  → {"proceed": False, "blocked": True, "reason": str}

        Args:
            action:       Action identifier.
            deal_id:      Deal being processed.
            agent_name:   Name of the calling agent (for audit log).
            deal_context: Deal-level context used for risk scoring.
            payload:      Additional data to include in the HITL approval request.

        Returns:
            dict describing the outcome (see above).
        """
        if deal_context is None:
            deal_context = {}
        if payload is None:
            payload = {}

        # ── Load policy and compute risk ───────────────────────────────────────
        try:
            policy = await policy_loader.get_policy()
        except Exception as exc:
            logger.warning(
                "AutonomyController.enforce: failed to load policy, using default: %s", exc
            )
            policy = policy_loader.DEFAULT_POLICY

        try:
            score = risk_engine.assess(deal_context, policy)
        except Exception as exc:
            logger.warning(
                "AutonomyController.enforce: risk assessment failed, using zero score: %s", exc
            )
            score = risk_engine.RiskScore()

        # ── Gate check ─────────────────────────────────────────────────────────
        try:
            gate = await hitl_manager.check_gate(
                action=action,
                deal_id=deal_id,
                policy=policy,
                risk_score=score,
            )
        except Exception as exc:
            logger.error(
                "AutonomyController.enforce: check_gate failed — defaulting to block: %s", exc
            )
            gate = {
                "allowed": False,
                "requires_hitl": True,
                "reason": f"Gate check failed unexpectedly: {exc}",
                "autonomy_level": policy.get("current_autonomy_level", 1),
            }

        # ── Case 1: Autonomous execution permitted ─────────────────────────────
        if gate["allowed"]:
            await hitl_manager.log_enforcement(
                action=action,
                deal_id=deal_id,
                decision="allowed",
                reason=gate["reason"],
                agent_name=agent_name,
                policy=policy,
                risk_score=score,
            )
            return {"proceed": True}

        # ── Case 2: Kill switch / hard block ───────────────────────────────────
        kill_switch_active = bool(policy.get("kill_switch_active", False))
        if kill_switch_active or not gate.get("requires_hitl", True):
            await hitl_manager.log_enforcement(
                action=action,
                deal_id=deal_id,
                decision="blocked",
                reason=gate["reason"],
                agent_name=agent_name,
                policy=policy,
                risk_score=score,
            )
            return {
                "proceed": False,
                "blocked": True,
                "reason": gate["reason"],
            }

        # ── Case 3: HITL required ──────────────────────────────────────────────
        approval_id: str | None = None
        hitl_payload = {
            **payload,
            "risk_score": score.to_dict(),
            "policy_level": gate["autonomy_level"],
            "reason": gate["reason"],
        }

        try:
            approval_result = await hitl_manager.request_hitl_approval(
                action=action,
                deal_id=deal_id,
                agent_name=agent_name,
                payload=hitl_payload,
            )
            if "error" not in approval_result:
                approval_id = approval_result.get("id")
        except Exception as exc:
            logger.error(
                "AutonomyController.enforce: HITL approval request failed for "
                "action '%s' deal %s: %s",
                action, deal_id, exc,
            )

        await hitl_manager.log_enforcement(
            action=action,
            deal_id=deal_id,
            decision="hitl_required",
            reason=gate["reason"],
            agent_name=agent_name,
            policy=policy,
            risk_score=score,
        )

        return {
            "proceed": False,
            "hitl_requested": True,
            "approval_id": approval_id,
            "reason": gate["reason"],
        }
