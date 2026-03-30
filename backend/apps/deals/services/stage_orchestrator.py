"""
Stage Orchestrator — Maps deal stages to auto-created artifacts and agent tasks.

This is the server-side (Django) component that handles the "side effects"
of stage transitions.  It:
  - Auto-creates domain shells (Proposal, CapturePlan, Contract)
  - Fires Celery tasks that run AI agents (Solution Architect, Pricing, etc.)
  - Records learning feedback on terminal stages

Each handler runs synchronously for quick DB operations, but delegates
heavy AI work to Celery so the HTTP response returns immediately.
"""

import logging

from django.utils import timezone

logger = logging.getLogger(__name__)


def handle_stage_transition(deal, from_stage: str, to_stage: str, user=None):
    """
    Called after a successful stage transition to handle domain-level side effects.

    This runs synchronously within the transition. Heavy work is deferred
    to Celery tasks via `deals.tasks.*`.
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


# ── Stage Handlers ───────────────────────────────────────────────────────────


def _on_enter_qualify(deal, from_stage, user):
    """Auto-score the opportunity when deal enters qualify."""
    try:
        from apps.deals.tasks import auto_score_opportunity
        auto_score_opportunity.delay(str(deal.id))
        logger.info("Queued auto_score_opportunity for deal %s", deal.id)
    except Exception:
        logger.warning("Could not queue auto_score_opportunity for deal %s", deal.id, exc_info=True)


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

    # Fire the Capture Agent to populate the plan
    try:
        from apps.deals.tasks import auto_run_capture_agent
        auto_run_capture_agent.delay(str(deal.id))
        logger.info("Queued auto_run_capture_agent for deal %s", deal.id)
    except Exception:
        logger.warning("Could not queue auto_run_capture_agent for deal %s", deal.id, exc_info=True)


def _on_enter_proposal_dev(deal, from_stage, user):
    """Auto-create a Proposal workspace and trigger Solution Architect + Pricing pipeline."""
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

    # Fire the Solution Architect → Pricing → Proposal population chain
    try:
        from apps.deals.tasks import auto_run_solution_architect
        auto_run_solution_architect.delay(str(deal.id))
        logger.info("Queued auto_run_solution_architect for deal %s", deal.id)
    except Exception:
        logger.warning(
            "Could not queue auto_run_solution_architect for deal %s",
            deal.id, exc_info=True,
        )

    # Fire the RFP Analyst to parse requirements and build compliance matrix
    try:
        from apps.deals.tasks import auto_run_rfp_analyst
        auto_run_rfp_analyst.delay(str(deal.id))
        logger.info("Queued auto_run_rfp_analyst for deal %s", deal.id)
    except Exception:
        logger.warning(
            "Could not queue auto_run_rfp_analyst for deal %s",
            deal.id, exc_info=True,
        )

    # Fire the Management Approach Agent to draft Vol II
    try:
        from apps.deals.tasks import auto_run_management_approach
        auto_run_management_approach.delay(str(deal.id))
        logger.info("Queued auto_run_management_approach for deal %s", deal.id)
    except Exception:
        logger.warning("Could not queue auto_run_management_approach for deal %s", deal.id, exc_info=True)


def _on_enter_red_team(deal, from_stage, user):
    """Fire Red Team review and Compliance check agents."""
    try:
        from apps.deals.tasks import auto_run_red_team
        auto_run_red_team.delay(str(deal.id))
        logger.info("Queued auto_run_red_team for deal %s", deal.id)
    except Exception:
        logger.warning("Could not queue auto_run_red_team for deal %s", deal.id, exc_info=True)

    try:
        from apps.deals.tasks import auto_run_compliance
        auto_run_compliance.delay(str(deal.id))
        logger.info("Queued auto_run_compliance for deal %s", deal.id)
    except Exception:
        logger.warning("Could not queue auto_run_compliance for deal %s", deal.id, exc_info=True)


def _on_enter_final_review(deal, from_stage, user):
    """Fire CUI Handler and Section 508 checks during final review."""
    try:
        from apps.deals.tasks import auto_run_cui_handler
        auto_run_cui_handler.delay(str(deal.id))
        logger.info("Queued auto_run_cui_handler for deal %s", deal.id)
    except Exception:
        logger.warning("Could not queue auto_run_cui_handler for deal %s", deal.id, exc_info=True)


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
    """Record win outcome, trigger analytics and learning feedback."""
    deal.outcome = "won"
    deal.award_date = timezone.now()
    deal.save(update_fields=["outcome", "award_date", "updated_at"])
    _trigger_learning_feedback(deal)


def _on_enter_closed_lost(deal, from_stage, user):
    """Record loss outcome, trigger analytics and learning feedback."""
    deal.outcome = "lost"
    deal.save(update_fields=["outcome", "updated_at"])
    _trigger_learning_feedback(deal)


def _on_enter_no_bid(deal, from_stage, user):
    """Record no-bid outcome and trigger learning feedback."""
    deal.outcome = "no_bid"
    deal.bid_decision_date = timezone.now()
    deal.save(update_fields=["outcome", "bid_decision_date", "updated_at"])
    _trigger_learning_feedback(deal)


def _trigger_learning_feedback(deal):
    """Trigger win/loss analysis, velocity recording, scoring weight updates, and AI learning agent."""
    try:
        from apps.analytics.tasks import analyze_win_loss, record_deal_velocity
        analyze_win_loss.delay(str(deal.id))
        record_deal_velocity.delay(str(deal.id), deal.stage, "exit")
        logger.info("Triggered learning feedback for deal %s (%s)", deal.id, deal.outcome)
    except Exception:
        logger.warning(
            "Failed to trigger learning feedback for deal %s",
            deal.id,
            exc_info=True,
        )

    # Fire the AI Learning Agent for deeper win/loss pattern analysis
    try:
        from apps.deals.tasks import auto_run_learning_agent
        auto_run_learning_agent.delay(str(deal.id))
        logger.info("Queued auto_run_learning_agent for deal %s", deal.id)
    except Exception:
        logger.warning("Could not queue auto_run_learning_agent for deal %s", deal.id, exc_info=True)


# ── Handler Map ──────────────────────────────────────────────────────────────

STAGE_HANDLERS = {
    "qualify": _on_enter_qualify,
    "capture_plan": _on_enter_capture_plan,
    "proposal_dev": _on_enter_proposal_dev,
    "red_team": _on_enter_red_team,
    "final_review": _on_enter_final_review,
    "contract_setup": _on_enter_contract_setup,
    "closed_won": _on_enter_closed_won,
    "closed_lost": _on_enter_closed_lost,
    "no_bid": _on_enter_no_bid,
}
