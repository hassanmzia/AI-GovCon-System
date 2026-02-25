"""
Stage Orchestrator — Maps deal stages to agent chains and auto-creates
domain artifacts (proposals, contracts, workspaces) on stage transitions.

This is the server-side (Django) component that handles the "side effects"
of stage transitions that must happen in the backend:
  - Auto-create Proposal when entering proposal_dev
  - Auto-create Contract when entering contract_setup
  - Auto-create CapturePlan when entering capture_plan
  - Trigger learning agent when deal closes
"""

import logging

from django.utils import timezone

logger = logging.getLogger(__name__)


def handle_stage_transition(deal, from_stage: str, to_stage: str, user=None):
    """
    Called after a successful stage transition to handle domain-level side effects.

    This runs synchronously within the transition. Heavy work is deferred
    to Celery tasks via `deals.tasks.execute_stage_side_effects`.
    """
    handler = STAGE_HANDLERS.get(to_stage)
    if handler:
        try:
            handler(deal, from_stage, user)
        except Exception:
            logger.warning(
                "Stage handler for '%s' failed for deal %s",
                to_stage, deal.id,
                exc_info=True,
            )


def _on_enter_proposal_dev(deal, from_stage, user):
    """Auto-create a Proposal workspace when deal enters proposal_dev."""
    from apps.proposals.models import Proposal

    proposal, created = Proposal.objects.get_or_create(
        deal=deal,
        defaults={
            "title": f"Proposal — {deal.title}",
            "status": "draft",
        },
    )
    if created:
        logger.info("Auto-created Proposal %s for deal %s", proposal.id, deal.id)
        from apps.deals.models import Activity
        Activity.objects.create(
            deal=deal,
            actor=None,
            action="proposal_workspace_created",
            description=f"Proposal workspace auto-created for '{deal.title}'",
            metadata={"proposal_id": str(proposal.id)},
            is_ai_action=True,
        )


def _on_enter_capture_plan(deal, from_stage, user):
    """Auto-create a CapturePlan when deal enters capture_plan stage."""
    from apps.deals.models import Activity, CapturePlan

    plan, created = CapturePlan.objects.get_or_create(
        deal=deal,
        defaults={
            "status": "draft",
        },
    )
    if created:
        logger.info("Auto-created CapturePlan %s for deal %s", plan.id, deal.id)
        Activity.objects.create(
            deal=deal,
            actor=None,
            action="capture_plan_created",
            description="Capture plan auto-created",
            metadata={"capture_plan_id": str(plan.id)},
            is_ai_action=True,
        )


def _on_enter_contract_setup(deal, from_stage, user):
    """Auto-create a Contract shell when deal is awarded."""
    from apps.contracts.models import Contract

    contract, created = Contract.objects.get_or_create(
        deal=deal,
        defaults={
            "title": f"Contract — {deal.title}",
            "status": "drafting",
            "estimated_value": deal.estimated_value,
            "start_date": timezone.now().date(),
        },
    )
    if created:
        logger.info("Auto-created Contract %s for deal %s", contract.id, deal.id)
        from apps.deals.models import Activity
        Activity.objects.create(
            deal=deal,
            actor=None,
            action="contract_created",
            description="Contract shell auto-created on award",
            metadata={"contract_id": str(contract.id)},
            is_ai_action=True,
        )


def _on_enter_closed_won(deal, from_stage, user):
    """Record win outcome and trigger analytics."""
    deal.outcome = "won"
    deal.award_date = timezone.now()
    deal.save(update_fields=["outcome", "award_date", "updated_at"])


def _on_enter_closed_lost(deal, from_stage, user):
    """Record loss outcome and trigger analytics."""
    deal.outcome = "lost"
    deal.save(update_fields=["outcome", "updated_at"])


def _on_enter_no_bid(deal, from_stage, user):
    """Record no-bid outcome."""
    deal.outcome = "no_bid"
    deal.bid_decision_date = timezone.now()
    deal.save(update_fields=["outcome", "bid_decision_date", "updated_at"])


# Map of stage -> handler function
STAGE_HANDLERS = {
    "capture_plan": _on_enter_capture_plan,
    "proposal_dev": _on_enter_proposal_dev,
    "contract_setup": _on_enter_contract_setup,
    "closed_won": _on_enter_closed_won,
    "closed_lost": _on_enter_closed_lost,
    "no_bid": _on_enter_no_bid,
}
