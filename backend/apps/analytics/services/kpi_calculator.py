"""
KPI Calculator — Service functions for computing cross-domain analytics KPIs.

All functions query Django models directly using the ORM and return
plain dictionaries suitable for JSON serialisation in API responses.
"""

import logging
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Avg, Count, F, Q, Sum
from django.db.models.functions import TruncMonth, TruncQuarter

logger = logging.getLogger(__name__)

# Stages considered "active" in the pipeline
ACTIVE_STAGES = [
    "intake", "qualify", "bid_no_bid", "capture_plan",
    "proposal_dev", "red_team", "final_review", "submit",
    "post_submit", "award_pending", "contract_setup", "delivery",
]


def compute_pipeline_funnel() -> dict:
    """
    Return funnel metrics for the deal pipeline.

    Returns:
        {
            "stages": {<stage>: <count>, ...},
            "conversion_rates": {<from_stage -> to_stage>: <rate>, ...},
            "total_active": int,
        }
    """
    from apps.deals.models import Deal

    stage_counts: dict[str, int] = {}
    for stage_code, _ in Deal.STAGES:
        stage_counts[stage_code] = Deal.objects.filter(stage=stage_code).count()

    # Compute stage-to-stage conversion rates
    conversion_rates: dict[str, float] = {}
    ordered_stages = [s[0] for s in Deal.STAGES]
    for i in range(len(ordered_stages) - 1):
        current = ordered_stages[i]
        next_stage = ordered_stages[i + 1]
        current_count = stage_counts.get(current, 0)
        next_count = stage_counts.get(next_stage, 0)
        if current_count > 0:
            rate = round((next_count / current_count) * 100, 1)
        else:
            rate = 0.0
        conversion_rates[f"{current}_to_{next_stage}"] = rate

    total_active = sum(
        stage_counts.get(s, 0) for s in ACTIVE_STAGES
    )

    return {
        "stages": stage_counts,
        "conversion_rates": conversion_rates,
        "total_active": total_active,
    }


def compute_revenue_forecast() -> list[dict]:
    """
    Return quarterly weighted pipeline value.

    Each deal contributes: deal.estimated_value * deal.win_probability.

    Returns:
        [
            {
                "quarter": "2026-Q1",
                "pipeline_value": "...",
                "weighted_value": "...",
                "deal_count": int,
            },
            ...
        ]
    """
    from apps.deals.models import Deal

    deals = (
        Deal.objects
        .filter(stage__in=ACTIVE_STAGES)
        .exclude(estimated_value__isnull=True)
        .annotate(quarter=TruncQuarter("due_date"))
        .values("quarter")
        .annotate(
            pipeline_value=Sum("estimated_value"),
            deal_count=Count("id"),
        )
        .order_by("quarter")
    )

    results = []
    for row in deals:
        quarter_dt = row["quarter"]
        if quarter_dt is None:
            quarter_label = "Unscheduled"
        else:
            q_num = (quarter_dt.month - 1) // 3 + 1
            quarter_label = f"{quarter_dt.year}-Q{q_num}"

        pipeline_val = row["pipeline_value"] or Decimal("0")

        # Compute weighted value for deals in this quarter
        quarter_deals = (
            Deal.objects
            .filter(stage__in=ACTIVE_STAGES, due_date__quarter=quarter_dt.month // 3 + 1 if quarter_dt else 0)
            .exclude(estimated_value__isnull=True)
        ) if quarter_dt else Deal.objects.none()

        # Simpler approach: aggregate weighted values for the quarter directly
        weighted_total = Decimal("0")
        if quarter_dt:
            q_start = quarter_dt
            month_offset = 3
            q_end_month = q_start.month + month_offset
            q_end_year = q_start.year
            if q_end_month > 12:
                q_end_month -= 12
                q_end_year += 1
            q_end = q_start.replace(year=q_end_year, month=q_end_month, day=1)

            quarter_deal_qs = Deal.objects.filter(
                stage__in=ACTIVE_STAGES,
                due_date__gte=q_start,
                due_date__lt=q_end,
            ).exclude(estimated_value__isnull=True)

            for deal in quarter_deal_qs:
                weighted_total += deal.estimated_value * Decimal(str(deal.win_probability))

        results.append({
            "quarter": quarter_label,
            "pipeline_value": str(pipeline_val),
            "weighted_value": str(weighted_total),
            "deal_count": row["deal_count"],
        })

    return results


def compute_win_rate_trend(months: int = 12) -> list[dict]:
    """
    Return monthly win rates with a 3-month moving average.

    Returns:
        [
            {
                "month": "2025-06",
                "won": int,
                "lost": int,
                "total": int,
                "win_rate": float | None,
                "moving_avg": float | None,
            },
            ...
        ]
    """
    from apps.deals.models import Deal

    cutoff = date.today() - timedelta(days=months * 31)

    monthly_data = (
        Deal.objects
        .filter(
            stage__in=["closed_won", "closed_lost"],
            updated_at__date__gte=cutoff,
        )
        .annotate(month=TruncMonth("updated_at"))
        .values("month")
        .annotate(
            won=Count("id", filter=Q(stage="closed_won")),
            lost=Count("id", filter=Q(stage="closed_lost")),
            total=Count("id"),
        )
        .order_by("month")
    )

    results = []
    win_rates: list[float] = []

    for row in monthly_data:
        month_dt = row["month"]
        month_label = month_dt.strftime("%Y-%m") if month_dt else "Unknown"
        won = row["won"]
        lost = row["lost"]
        total = row["total"]
        win_rate = round((won / total) * 100, 1) if total > 0 else None

        win_rates.append(win_rate if win_rate is not None else 0.0)

        # 3-month moving average
        window = win_rates[-3:]
        moving_avg = round(sum(window) / len(window), 1) if window else None

        results.append({
            "month": month_label,
            "won": won,
            "lost": lost,
            "total": total,
            "win_rate": win_rate,
            "moving_avg": moving_avg,
        })

    return results


def compute_executive_summary() -> dict:
    """
    Return a cross-domain executive summary of key KPIs.

    Returns:
        {
            "active_deals": int,
            "pipeline_value": str,
            "proposals_in_progress": int,
            "active_contracts": int,
            "pending_approvals": int,
            "upcoming_deadlines": [...],
            "win_rate": float | None,
            "closed_won": int,
            "closed_lost": int,
        }
    """
    from apps.deals.models import Deal, Approval
    from apps.proposals.models import Proposal
    from apps.contracts.models import Contract

    # Active deals
    active_deals = Deal.objects.filter(stage__in=ACTIVE_STAGES)
    active_count = active_deals.count()

    pipeline_value = active_deals.aggregate(
        total=Sum("estimated_value")
    )["total"] or Decimal("0")

    # Win rate
    closed_won = Deal.objects.filter(stage="closed_won").count()
    closed_lost = Deal.objects.filter(stage="closed_lost").count()
    closed_total = closed_won + closed_lost
    win_rate = round((closed_won / closed_total) * 100, 1) if closed_total else None

    # Proposals in progress (not yet submitted)
    proposals_in_progress = Proposal.objects.exclude(
        status="submitted"
    ).count()

    # Active contracts
    active_contracts = Contract.objects.filter(
        status__in=["active", "executed"]
    ).count()

    # Pending approvals
    pending_approvals = Approval.objects.filter(status="pending").count()

    # Upcoming deadlines (deals with due_date in the next 30 days)
    today = date.today()
    thirty_days = today + timedelta(days=30)
    upcoming = (
        Deal.objects
        .filter(
            stage__in=ACTIVE_STAGES,
            due_date__date__gte=today,
            due_date__date__lte=thirty_days,
        )
        .order_by("due_date")
        .values("id", "title", "stage", "due_date")[:10]
    )

    return {
        "active_deals": active_count,
        "pipeline_value": str(pipeline_value),
        "proposals_in_progress": proposals_in_progress,
        "active_contracts": active_contracts,
        "pending_approvals": pending_approvals,
        "upcoming_deadlines": list(upcoming),
        "win_rate": win_rate,
        "closed_won": closed_won,
        "closed_lost": closed_lost,
    }
