import logging
from django.utils import timezone

logger = logging.getLogger(__name__)


# Valid transitions: from_stage -> [to_stages]
VALID_TRANSITIONS = {
    'intake': ['qualify', 'no_bid'],
    'qualify': ['bid_no_bid', 'no_bid'],
    'bid_no_bid': ['capture_plan', 'no_bid'],
    'capture_plan': ['proposal_dev'],
    'proposal_dev': ['red_team'],
    'red_team': ['proposal_dev', 'final_review'],  # Can loop back
    'final_review': ['submit', 'proposal_dev'],  # Can loop back
    'submit': ['post_submit'],
    'post_submit': ['award_pending', 'closed_lost'],
    'award_pending': ['contract_setup', 'closed_won', 'closed_lost'],
    'contract_setup': ['delivery'],
    'delivery': ['closed_won'],
}

HITL_GATES = {'bid_no_bid', 'final_review', 'submit', 'contract_setup'}


class WorkflowEngine:
    """State machine for deal pipeline stage transitions.

    The workflow engine is the Central Nervous System of the GovCon OS.
    On every stage transition it:
      1. Validates the transition is allowed
      2. Checks HITL gate approvals
      3. Optionally evaluates gate readiness criteria
      4. Records history and logs activity
      5. Triggers task auto-generation
      6. Executes domain-level side effects (auto-create proposals, contracts, etc.)
      7. Emits events to the AI orchestrator via Redis for agent chain execution
    """

    def can_transition(self, deal, target_stage: str) -> tuple[bool, str]:
        """Check if transition is valid.

        Returns a (bool, str) tuple where the bool indicates whether the
        transition is allowed and the str provides a human-readable reason
        when the transition is blocked.
        """
        current = deal.stage
        valid_targets = VALID_TRANSITIONS.get(current, [])

        if target_stage not in valid_targets:
            return False, (
                f"Cannot transition from '{current}' to '{target_stage}'. "
                f"Valid targets: {valid_targets}"
            )

        # HITL gate check: the target stage must have an approved approval
        # record, or at least a pending one (awaiting human decision).
        if target_stage in HITL_GATES:
            pending_approvals = deal.approvals.filter(
                approval_type=target_stage, status='pending'
            ).exists()
            approved = deal.approvals.filter(
                approval_type=target_stage, status='approved'
            ).exists()
            if not approved and not pending_approvals:
                return False, (
                    f"Stage '{target_stage}' requires HITL approval. "
                    f"Request approval first."
                )

        # Gate readiness check: evaluate criteria and block on critical failures.
        from apps.deals.services.gate_evaluator import evaluate_gate
        evaluation = evaluate_gate(deal, target_stage)
        if not evaluation.can_proceed:
            failed = [c.name for c in evaluation.criteria
                      if c.status == "red" and c.is_critical]
            return False, (
                f"Gate criteria not met for '{target_stage}': "
                f"{', '.join(failed)}. {evaluation.summary}"
            )

        return True, ""

    def evaluate_gate(self, deal, target_stage: str) -> dict:
        """Evaluate gate readiness criteria for a target stage.

        Returns a dict with overall_status (red/amber/green), can_proceed,
        criteria list, and summary.
        """
        from apps.deals.services.gate_evaluator import evaluate_gate
        evaluation = evaluate_gate(deal, target_stage)
        return {
            "stage": evaluation.stage,
            "overall_status": evaluation.overall_status,
            "can_proceed": evaluation.can_proceed,
            "summary": evaluation.summary,
            "criteria": [
                {
                    "name": c.name,
                    "description": c.description,
                    "is_critical": c.is_critical,
                    "status": c.status,
                    "detail": c.detail,
                }
                for c in evaluation.criteria
            ],
        }

    def transition(self, deal, target_stage: str, user=None, reason: str = "") -> bool:
        """Execute a stage transition.

        Creates a history record, updates the deal stage, logs activity,
        triggers auto-tasks, executes domain side effects, and emits
        events to the AI orchestrator.

        Raises ``ValueError`` when the transition is not allowed.
        """
        can, msg = self.can_transition(deal, target_stage)
        if not can:
            raise ValueError(msg)

        from apps.deals.models import DealStageHistory, Activity

        old_stage = deal.stage
        now = timezone.now()
        duration = now - deal.stage_entered_at if deal.stage_entered_at else None

        # Record the stage history entry
        DealStageHistory.objects.create(
            deal=deal,
            from_stage=old_stage,
            to_stage=target_stage,
            transitioned_by=user,
            reason=reason,
            duration_in_previous_stage=duration,
        )

        # Update the deal itself
        deal.stage = target_stage
        deal.stage_entered_at = now
        deal.save(update_fields=['stage', 'stage_entered_at', 'updated_at'])

        # Log the activity
        Activity.objects.create(
            deal=deal,
            actor=user,
            action='stage_changed',
            description=f"Stage changed from {old_stage} to {target_stage}",
            metadata={'from': old_stage, 'to': target_stage, 'reason': reason},
        )

        # Record stage velocity metrics (exit old stage, enter new stage)
        try:
            from apps.analytics.tasks import record_deal_velocity
            record_deal_velocity.delay(str(deal.id), old_stage, "exit")
            record_deal_velocity.delay(str(deal.id), target_stage, "enter")
        except Exception:
            logger.warning(
                "Could not enqueue velocity recording for deal %s",
                deal.id,
                exc_info=True,
            )

        # Trigger auto-generation of tasks for the new stage
        try:
            from apps.deals.tasks import auto_generate_stage_tasks
            auto_generate_stage_tasks.delay(str(deal.id), target_stage)
        except Exception:
            logger.warning(
                "Could not enqueue auto_generate_stage_tasks for deal %s",
                deal.id,
                exc_info=True,
            )

        # Execute domain-level side effects (auto-create proposals, contracts, etc.)
        try:
            from apps.deals.services.stage_orchestrator import handle_stage_transition
            handle_stage_transition(deal, old_stage, target_stage, user)
        except Exception:
            logger.warning(
                "Stage orchestrator failed for deal %s stage %s",
                deal.id, target_stage,
                exc_info=True,
            )

        # Emit events to AI orchestrator via Redis for agent chain execution
        try:
            from apps.deals.signals import on_deal_stage_changed
            on_deal_stage_changed(
                deal_id=str(deal.id),
                from_stage=old_stage,
                to_stage=target_stage,
                user_id=user.id if user else None,
            )
        except Exception:
            logger.warning(
                "Failed to emit stage_changed signal for deal %s",
                deal.id,
                exc_info=True,
            )

        # Emit outcome events for terminal stages
        if target_stage in ("closed_won", "closed_lost", "no_bid"):
            try:
                from apps.deals.signals import on_deal_outcome
                outcome_map = {
                    "closed_won": "won",
                    "closed_lost": "lost",
                    "no_bid": "no_bid",
                }
                on_deal_outcome(
                    deal_id=str(deal.id),
                    outcome=outcome_map[target_stage],
                    user_id=user.id if user else None,
                )
            except Exception:
                logger.warning(
                    "Failed to emit outcome signal for deal %s",
                    deal.id,
                    exc_info=True,
                )

        logger.info("Deal %s: %s -> %s by %s", deal.id, old_stage, target_stage, user)
        return True
