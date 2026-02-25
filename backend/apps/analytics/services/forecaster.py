"""
Revenue & Pipeline Forecaster Service.

Computes quarterly revenue forecasts by weighting pipeline deal values
against win probabilities, segmented by deal stage, agency, and NAICS.
Exposes a clean API consumed by the analytics views and the executive dashboard.
"""

import logging
from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Avg, Count, F, Q, Sum
from django.db.models.functions import TruncQuarter

logger = logging.getLogger(__name__)

# Stages treated as "active pipeline" for forecast purposes
PIPELINE_STAGES = [
    "qualify", "bid_no_bid", "capture_plan", "proposal_dev",
    "red_team", "final_review", "submit", "post_submit", "award_pending",
]

# Default win probability by stage (used when deal.win_probability is null)
STAGE_DEFAULT_WIN_PROB: dict[str, float] = {
    "qualify": 0.15,
    "bid_no_bid": 0.25,
    "capture_plan": 0.30,
    "proposal_dev": 0.40,
    "red_team": 0.50,
    "final_review": 0.60,
    "submit": 0.65,
    "post_submit": 0.65,
    "award_pending": 0.75,
}

# Conservative / optimistic multipliers for scenario bands
CONSERVATIVE_MULT = 0.70
OPTIMISTIC_MULT = 1.35


def _quarter_label(d: date) -> str:
    """Return a label like '2026-Q1' for the given date."""
    q = (d.month - 1) // 3 + 1
    return f"{d.year}-Q{q}"


def _quarter_start(d: date) -> date:
    """Return the first day of the quarter containing *d*."""
    q = (d.month - 1) // 3
    return date(d.year, q * 3 + 1, 1)


def _add_quarters(d: date, n: int) -> date:
    """Advance *d* by *n* quarters (approx)."""
    year = d.year + (d.month - 1 + n * 3) // 12
    month = (d.month - 1 + n * 3) % 12 + 1
    return date(year, month, 1)


def compute_quarterly_forecast(quarters_ahead: int = 4) -> list[dict]:
    """
    Compute a quarterly revenue forecast for the next *quarters_ahead* quarters.

    Each quarter dict contains:
        quarter         – label e.g. "2026-Q1"
        quarter_start   – ISO date string of quarter start
        pipeline_value  – total estimated value of deals due in window
        weighted_value  – pipeline_value × average win probability
        low             – conservative estimate (70% of weighted)
        high            – optimistic estimate (135% of weighted)
        deal_count      – number of deals contributing
        by_stage        – breakdown by stage
        by_agency       – top 5 agencies by weighted value
    """
    from apps.deals.models import Deal  # local import to avoid circular

    today = date.today()
    q_start = _quarter_start(today)

    results = []

    for i in range(quarters_ahead):
        window_start = _add_quarters(q_start, i)
        window_end = _add_quarters(q_start, i + 1) - timedelta(days=1)
        label = _quarter_label(window_start)

        # Deals with response/award deadline in this quarter window
        # Fall back to all active-stage deals if no deadline set
        qs = Deal.objects.filter(
            stage__in=PIPELINE_STAGES,
        ).filter(
            Q(rfp_release_date__range=(window_start, window_end))
            | Q(estimated_value__isnull=False),
        )

        # Include all active deals without a deadline filter (proportional distribution)
        # When no deadline, distribute evenly across quarters
        all_active = Deal.objects.filter(stage__in=PIPELINE_STAGES)

        pipeline_value = Decimal("0")
        weighted_value = Decimal("0")
        deal_count = 0
        by_stage: dict[str, dict] = {}
        by_agency: dict[str, Decimal] = {}

        for deal in all_active:
            est_val = deal.estimated_value or Decimal("0")
            win_prob = (
                Decimal(str(deal.win_probability / 100))
                if deal.win_probability
                else Decimal(str(STAGE_DEFAULT_WIN_PROB.get(deal.stage, 0.3)))
            )

            # Distribute value across the 4 quarters if no specific deadline
            quarterly_portion = est_val / quarters_ahead

            pipeline_value += quarterly_portion
            weighted_value += quarterly_portion * win_prob
            deal_count += 1

            # By stage breakdown
            if deal.stage not in by_stage:
                by_stage[deal.stage] = {"pipeline": Decimal("0"), "weighted": Decimal("0"), "count": 0}
            by_stage[deal.stage]["pipeline"] += quarterly_portion
            by_stage[deal.stage]["weighted"] += quarterly_portion * win_prob
            by_stage[deal.stage]["count"] += 1

            # By agency
            agency = getattr(deal, "agency", None) or ""
            if agency:
                by_agency[agency] = by_agency.get(agency, Decimal("0")) + quarterly_portion * win_prob

        # Top 5 agencies
        top_agencies = sorted(by_agency.items(), key=lambda x: x[1], reverse=True)[:5]

        results.append({
            "quarter": label,
            "quarter_start": window_start.isoformat(),
            "pipeline_value": str(pipeline_value.quantize(Decimal("1"))),
            "weighted_value": str(weighted_value.quantize(Decimal("1"))),
            "low": str((weighted_value * Decimal(str(CONSERVATIVE_MULT))).quantize(Decimal("1"))),
            "high": str((weighted_value * Decimal(str(OPTIMISTIC_MULT))).quantize(Decimal("1"))),
            "deal_count": deal_count // quarters_ahead,  # unique deals approximate
            "by_stage": {
                stage: {
                    "pipeline": str(v["pipeline"].quantize(Decimal("1"))),
                    "weighted": str(v["weighted"].quantize(Decimal("1"))),
                    "count": v["count"],
                }
                for stage, v in by_stage.items()
            },
            "top_agencies": [
                {"agency": name, "weighted_value": str(val.quantize(Decimal("1")))}
                for name, val in top_agencies
            ],
        })

    return results


def compute_annual_summary() -> dict:
    """
    Return a summary of the current fiscal year forecast.

    Returns:
        {
            "fiscal_year": int,
            "total_pipeline": str,
            "total_weighted": str,
            "expected_low": str,
            "expected_high": str,
            "active_deals": int,
            "avg_win_probability": float,
            "quarters": [...]
        }
    """
    from apps.deals.models import Deal

    quarters = compute_quarterly_forecast(quarters_ahead=4)

    totals = Deal.objects.filter(stage__in=PIPELINE_STAGES).aggregate(
        total_pipeline=Sum("estimated_value"),
        avg_win_prob=Avg("win_probability"),
        deal_count=Count("id"),
    )

    pipeline = totals["total_pipeline"] or Decimal("0")
    avg_prob = totals["avg_win_prob"] or 30.0

    weighted_total = sum(Decimal(q["weighted_value"]) for q in quarters)
    low_total = sum(Decimal(q["low"]) for q in quarters)
    high_total = sum(Decimal(q["high"]) for q in quarters)

    return {
        "fiscal_year": date.today().year,
        "total_pipeline": str(Decimal(str(pipeline)).quantize(Decimal("1"))),
        "total_weighted": str(weighted_total.quantize(Decimal("1"))),
        "expected_low": str(low_total.quantize(Decimal("1"))),
        "expected_high": str(high_total.quantize(Decimal("1"))),
        "active_deals": totals["deal_count"] or 0,
        "avg_win_probability": round(avg_prob, 1),
        "quarters": quarters,
    }


def compute_naics_breakdown() -> list[dict]:
    """
    Return weighted pipeline value grouped by NAICS code.

    Returns list of {naics_code, description, pipeline_value, weighted_value, deal_count}.
    """
    from apps.deals.models import Deal
    from apps.opportunities.models import Opportunity

    deals = Deal.objects.filter(stage__in=PIPELINE_STAGES).select_related("opportunity")
    naics_agg: dict[str, dict] = {}

    for deal in deals:
        opp = getattr(deal, "opportunity", None)
        naics = (opp.naics_code if opp else None) or "Unknown"
        est_val = deal.estimated_value or Decimal("0")
        win_prob = Decimal(str((deal.win_probability or 30) / 100))

        if naics not in naics_agg:
            naics_agg[naics] = {
                "pipeline": Decimal("0"),
                "weighted": Decimal("0"),
                "count": 0,
            }
        naics_agg[naics]["pipeline"] += est_val
        naics_agg[naics]["weighted"] += est_val * win_prob
        naics_agg[naics]["count"] += 1

    return sorted(
        [
            {
                "naics_code": naics,
                "pipeline_value": str(data["pipeline"].quantize(Decimal("1"))),
                "weighted_value": str(data["weighted"].quantize(Decimal("1"))),
                "deal_count": data["count"],
            }
            for naics, data in naics_agg.items()
        ],
        key=lambda x: Decimal(x["weighted_value"]),
        reverse=True,
    )
