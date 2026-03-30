"""
Gate Review Evaluator — Auto-evaluates gate readiness before stage transitions.

Each HITL gate has defined criteria. The evaluator checks whether a deal
meets the criteria and returns a traffic-light assessment:
  - RED: Critical criteria not met, transition should be blocked
  - AMBER: Non-critical criteria missing, transition allowed with warnings
  - GREEN: All criteria met
"""

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class GateCriterion:
    name: str
    description: str
    is_critical: bool = True
    status: str = "red"  # red | amber | green
    detail: str = ""


@dataclass
class GateEvaluation:
    stage: str
    overall_status: str = "red"  # red | amber | green
    criteria: list = field(default_factory=list)
    can_proceed: bool = False
    summary: str = ""


def evaluate_gate(deal, target_stage: str) -> GateEvaluation:
    """
    Evaluate whether a deal meets the gate criteria for the target stage.

    Returns a GateEvaluation with per-criterion status.
    """
    evaluator = GATE_EVALUATORS.get(target_stage)
    if not evaluator:
        return GateEvaluation(
            stage=target_stage,
            overall_status="green",
            can_proceed=True,
            summary="No gate criteria defined for this stage.",
        )
    return evaluator(deal)


def _evaluate_bid_no_bid(deal) -> GateEvaluation:
    """Evaluate bid/no-bid gate criteria."""
    criteria = []

    # 1. Opportunity should have a score (recommended, not blocking)
    has_score = hasattr(deal.opportunity, "score")
    criteria.append(GateCriterion(
        name="Opportunity Scored",
        description="Opportunity should be scored by AI or manually",
        is_critical=False,
        status="green" if has_score else "amber",
        detail=f"Score: {deal.opportunity.score.total_score}" if has_score else "Not scored yet — recommended before bid decision",
    ))

    # 2. Strategy assessment should exist
    has_strategy = deal.ai_recommendation != ""
    criteria.append(GateCriterion(
        name="Strategy Assessment",
        description="AI strategy recommendation available",
        is_critical=False,
        status="green" if has_strategy else "amber",
        detail=deal.ai_recommendation[:100] if has_strategy else "No AI recommendation yet",
    ))

    # 3. Deal should have an owner assigned
    has_owner = deal.owner is not None
    criteria.append(GateCriterion(
        name="Owner Assigned",
        description="Deal should have a designated owner",
        is_critical=False,
        status="green" if has_owner else "amber",
        detail=str(deal.owner) if has_owner else "No owner assigned — recommended before bid decision",
    ))

    # 4. Minimum information available
    has_value = deal.estimated_value is not None
    criteria.append(GateCriterion(
        name="Value Estimated",
        description="Estimated contract value available",
        is_critical=False,
        status="green" if has_value else "amber",
        detail=f"${deal.estimated_value:,.0f}" if has_value else "Not estimated",
    ))

    return _build_evaluation("bid_no_bid", criteria)


def _evaluate_final_review(deal) -> GateEvaluation:
    """Evaluate final review gate criteria."""
    criteria = []

    # 1. Proposal must exist and have sections
    from apps.proposals.models import Proposal
    proposal = Proposal.objects.filter(deal=deal).first()
    has_proposal = proposal is not None
    section_count = proposal.sections.count() if has_proposal else 0

    criteria.append(GateCriterion(
        name="Proposal Exists",
        description="Proposal workspace should be created with sections",
        is_critical=False,
        status="green" if section_count > 0 else "amber",
        detail=f"{section_count} sections" if has_proposal else "No proposal — recommended before final review",
    ))

    # 2. Compliance matrix should be populated
    from apps.rfp.models import ComplianceMatrixItem
    compliance_count = ComplianceMatrixItem.objects.filter(
        rfp_document__deal=deal
    ).count()
    compliance_addressed = ComplianceMatrixItem.objects.filter(
        rfp_document__deal=deal, status="addressed"
    ).count()

    if compliance_count > 0:
        pct = (compliance_addressed / compliance_count) * 100
        criteria.append(GateCriterion(
            name="Compliance Coverage",
            description="Compliance matrix items addressed",
            is_critical=False,
            status="green" if pct >= 90 else ("amber" if pct >= 70 else "red"),
            detail=f"{compliance_addressed}/{compliance_count} addressed ({pct:.0f}%)",
        ))
    else:
        criteria.append(GateCriterion(
            name="Compliance Coverage",
            description="Compliance matrix items addressed",
            is_critical=False,
            status="amber",
            detail="No compliance matrix items found",
        ))

    # 3. Pricing should be approved
    pricing_approved = deal.approvals.filter(
        approval_type="pricing", status="approved"
    ).exists()
    criteria.append(GateCriterion(
        name="Pricing Approved",
        description="Pricing scenario should be approved",
        is_critical=False,
        status="green" if pricing_approved else "amber",
        detail="Approved" if pricing_approved else "Not approved — recommended before final review",
    ))

    # 4. Red team review completed
    red_team_done = deal.tasks.filter(
        stage="red_team", status="completed"
    ).exists()
    criteria.append(GateCriterion(
        name="Red Team Review",
        description="Red team review tasks completed",
        is_critical=False,
        status="green" if red_team_done else "amber",
        detail="Completed" if red_team_done else "Not completed",
    ))

    return _build_evaluation("final_review", criteria)


def _evaluate_submit(deal) -> GateEvaluation:
    """Evaluate submission gate criteria."""
    criteria = []

    # 1. Final review should be approved
    final_approved = deal.approvals.filter(
        approval_type="proposal_final", status="approved"
    ).exists()
    criteria.append(GateCriterion(
        name="Final Proposal Approved",
        description="Final proposal approval gate should be passed",
        is_critical=False,
        status="green" if final_approved else "amber",
        detail="Approved" if final_approved else "Not approved — recommended before submission",
    ))

    # 2. Submission deadline not passed
    from django.utils import timezone
    deadline_ok = (
        deal.due_date is None or deal.due_date > timezone.now()
    )
    criteria.append(GateCriterion(
        name="Deadline Not Passed",
        description="Submission deadline has not expired",
        is_critical=True,
        status="green" if deadline_ok else "red",
        detail=str(deal.due_date) if deal.due_date else "No deadline set",
    ))

    # 3. All critical tasks completed
    pending_critical = deal.tasks.filter(
        stage__in=["proposal_dev", "red_team", "final_review"],
        status__in=["pending", "in_progress"],
        priority__lte=2,  # Critical/High
    ).count()
    criteria.append(GateCriterion(
        name="Critical Tasks Complete",
        description="All critical/high-priority tasks completed",
        is_critical=False,
        status="green" if pending_critical == 0 else "amber",
        detail=f"{pending_critical} critical tasks remaining" if pending_critical else "All done",
    ))

    return _build_evaluation("submit", criteria)


def _evaluate_contract_setup(deal) -> GateEvaluation:
    """Evaluate contract setup gate criteria."""
    criteria = []

    # 1. Deal should have submission approved
    submission_approved = deal.approvals.filter(
        approval_type="submission", status="approved"
    ).exists()
    criteria.append(GateCriterion(
        name="Submission Authorized",
        description="Submission should have been authorized",
        is_critical=False,
        status="green" if submission_approved else "amber",
        detail="Authorized" if submission_approved else "Not authorized — recommended before contract setup",
    ))

    # 2. Award date should be set
    has_award_date = deal.award_date is not None
    criteria.append(GateCriterion(
        name="Award Confirmed",
        description="Award date should be recorded",
        is_critical=False,
        status="green" if has_award_date else "amber",
        detail=str(deal.award_date) if has_award_date else "Not set",
    ))

    return _build_evaluation("contract_setup", criteria)


def _build_evaluation(stage: str, criteria: list) -> GateEvaluation:
    """Compute overall status from individual criteria."""
    has_red_critical = any(c.status == "red" and c.is_critical for c in criteria)
    has_red_noncritical = any(c.status == "red" and not c.is_critical for c in criteria)
    has_amber = any(c.status == "amber" for c in criteria)

    if has_red_critical:
        overall = "red"
        can_proceed = False
        summary = "Critical criteria not met. Cannot proceed."
    elif has_red_noncritical or has_amber:
        overall = "amber"
        can_proceed = True
        summary = "Some criteria have warnings. Proceed with caution."
    else:
        overall = "green"
        can_proceed = True
        summary = "All criteria met. Ready to proceed."

    return GateEvaluation(
        stage=stage,
        overall_status=overall,
        can_proceed=can_proceed,
        criteria=criteria,
        summary=summary,
    )


# Map of stage -> evaluator function
GATE_EVALUATORS = {
    "bid_no_bid": _evaluate_bid_no_bid,
    "final_review": _evaluate_final_review,
    "submit": _evaluate_submit,
    "contract_setup": _evaluate_contract_setup,
}
