"""
Pipeline Analytics — Computes pipeline load, capacity, and velocity metrics.

Used by the capacity-aware scoring engine to demote opportunities that would
overload the current workforce or conflict with active proposals.
"""

import logging
from decimal import Decimal

from django.db.models import Avg, Count, Q, Sum
from django.utils import timezone

logger = logging.getLogger(__name__)

# Stages that consume active workforce / BD capacity
ACTIVE_STAGES = [
    "qualify", "bid_no_bid", "capture_plan",
    "proposal_dev", "red_team", "final_review",
    "submit", "post_submit", "award_pending",
]

# Stages that are resource-intensive for proposal teams
PROPOSAL_HEAVY_STAGES = ["proposal_dev", "red_team", "final_review"]


def get_pipeline_load() -> dict:
    """
    Calculate the current pipeline load metrics.

    Returns dict with:
      - active_deal_count: deals in active stages
      - proposal_stage_count: deals in proposal-heavy stages
      - total_pipeline_value: sum of estimated_value for active deals
      - weighted_pipeline_value: value × win_probability
      - stage_distribution: {stage: count}
      - avg_win_probability: average P(win) across active deals
    """
    from apps.deals.models import Deal

    active_deals = Deal.objects.filter(stage__in=ACTIVE_STAGES)

    stage_dist = dict(
        active_deals.values_list("stage")
        .annotate(count=Count("id"))
        .values_list("stage", "count")
    )

    agg = active_deals.aggregate(
        total_value=Sum("estimated_value"),
        avg_win_prob=Avg("win_probability"),
        deal_count=Count("id"),
    )

    proposal_count = active_deals.filter(stage__in=PROPOSAL_HEAVY_STAGES).count()

    # Weighted pipeline value
    weighted = Decimal("0")
    for d in active_deals.values("estimated_value", "win_probability"):
        val = d["estimated_value"] or Decimal("0")
        prob = Decimal(str(d["win_probability"] or 0))
        weighted += val * prob

    return {
        "active_deal_count": agg["deal_count"] or 0,
        "proposal_stage_count": proposal_count,
        "total_pipeline_value": float(agg["total_value"] or 0),
        "weighted_pipeline_value": float(weighted),
        "stage_distribution": stage_dist,
        "avg_win_probability": agg["avg_win_prob"] or 0.0,
    }


def get_capacity_score(max_active_deals: int = 20, max_proposals: int = 5) -> float:
    """
    Return a capacity score between 0.0 (fully loaded) and 1.0 (fully available).

    Used as a factor in opportunity scoring to penalize new opportunities
    when the team is at capacity.
    """
    load = get_pipeline_load()

    deal_utilization = min(1.0, load["active_deal_count"] / max(max_active_deals, 1))
    proposal_utilization = min(1.0, load["proposal_stage_count"] / max(max_proposals, 1))

    # Weight proposal capacity more heavily — proposals consume more resources
    capacity = 1.0 - (deal_utilization * 0.4 + proposal_utilization * 0.6)
    return max(0.0, min(1.0, capacity))


def get_pipeline_velocity() -> dict:
    """
    Calculate average time spent in each stage (days).

    Returns {stage: avg_days} for stages that have sufficient data.
    """
    from apps.deals.models import DealStageHistory

    velocity = {}
    stages_with_data = (
        DealStageHistory.objects.filter(
            duration_in_previous_stage__isnull=False,
        )
        .values("from_stage")
        .annotate(
            avg_duration=Avg("duration_in_previous_stage"),
            count=Count("id"),
        )
        .filter(count__gte=2)
    )

    for entry in stages_with_data:
        avg_td = entry["avg_duration"]
        if avg_td:
            velocity[entry["from_stage"]] = round(avg_td.total_seconds() / 86400, 1)

    return velocity


def get_upcoming_deadlines(days_ahead: int = 30) -> list:
    """Return deals with due dates within the specified window."""
    from apps.deals.models import Deal

    now = timezone.now()
    cutoff = now + timezone.timedelta(days=days_ahead)

    return list(
        Deal.objects.filter(
            stage__in=ACTIVE_STAGES,
            due_date__gte=now,
            due_date__lte=cutoff,
        )
        .order_by("due_date")
        .values("id", "title", "stage", "due_date", "estimated_value")
    )
