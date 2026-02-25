import logging
from datetime import date
from decimal import Decimal

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def compute_strategic_scores(self):
    """Score all unscored active opportunities against the current strategy.

    Finds every active Opportunity that does not yet have a StrategicScore
    (or whose score references an outdated strategy) and computes one using
    the StrategyScorer service.
    """
    from apps.opportunities.models import Opportunity
    from apps.strategy.models import CompanyStrategy, StrategicScore
    from apps.strategy.services.strategy_scorer import StrategyScorer

    strategy = CompanyStrategy.objects.filter(is_active=True).first()
    if not strategy:
        logger.warning("compute_strategic_scores: No active strategy found. Skipping.")
        return {"scored": 0, "skipped": 0, "error": "No active strategy"}

    scorer = StrategyScorer(strategy)

    # Find opportunities that either have no score or whose score is from a
    # different (older) strategy version.
    opportunities = Opportunity.objects.filter(
        status="active",
    ).exclude(
        strategic_score__strategy=strategy,
    ).select_related("source")

    scored = 0
    skipped = 0

    for opp in opportunities:
        try:
            result = scorer.score(opp)
            StrategicScore.objects.update_or_create(
                opportunity=opp,
                defaults={
                    "strategy": strategy,
                    "strategic_score": result["strategic_score"],
                    "agency_alignment": result["agency_alignment"],
                    "domain_alignment": result["domain_alignment"],
                    "growth_market_bonus": result["growth_market_bonus"],
                    "portfolio_balance": result["portfolio_balance"],
                    "revenue_contribution": result["revenue_contribution"],
                    "capacity_fit": result["capacity_fit"],
                    "relationship_value": result["relationship_value"],
                    "competitive_positioning": result["competitive_positioning"],
                    "bid_recommendation": result["bid_recommendation"],
                    "strategic_rationale": result["strategic_rationale"],
                },
            )
            scored += 1
        except Exception as exc:
            logger.exception(
                "compute_strategic_scores: Failed to score opportunity %s: %s",
                opp.id,
                exc,
            )
            skipped += 1

    logger.info(
        "compute_strategic_scores: Scored %d opportunities, skipped %d.",
        scored,
        skipped,
    )
    return {"scored": scored, "skipped": skipped}


@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def generate_portfolio_snapshot(self):
    """Generate a weekly portfolio snapshot with pipeline health metrics.

    Aggregates active opportunities into a PortfolioSnapshot record,
    breaking them down by agency, domain, stage, and size bucket.
    """
    from django.db.models import Count, Sum

    from apps.opportunities.models import Opportunity
    from apps.strategy.models import CompanyStrategy, PortfolioSnapshot, StrategicScore

    today = date.today()
    strategy = CompanyStrategy.objects.filter(is_active=True).first()

    active_opps = Opportunity.objects.filter(status="active")

    total_count = active_opps.count()
    total_value = active_opps.aggregate(
        total=Sum("estimated_value")
    )["total"] or Decimal("0.00")

    # --- Deals by agency ---
    agency_qs = (
        active_opps.values("agency")
        .annotate(count=Count("id"))
        .order_by("-count")
    )
    deals_by_agency = {
        row["agency"] or "Unknown": row["count"] for row in agency_qs
    }

    # --- Deals by domain (top keywords) ---
    # Simplified: count by NAICS code as a proxy for domain
    naics_qs = (
        active_opps.values("naics_code")
        .annotate(count=Count("id"))
        .order_by("-count")
    )
    deals_by_domain = {
        row["naics_code"] or "Unknown": row["count"] for row in naics_qs
    }

    # --- Deals by stage (notice_type as proxy) ---
    stage_qs = (
        active_opps.values("notice_type")
        .annotate(count=Count("id"))
        .order_by("-count")
    )
    deals_by_stage = {
        row["notice_type"] or "Unknown": row["count"] for row in stage_qs
    }

    # --- Deals by size bucket ---
    size_buckets = {"<100K": 0, "100K-1M": 0, "1M-10M": 0, "10M-50M": 0, "50M+": 0, "Unknown": 0}
    for opp in active_opps.only("estimated_value"):
        val = opp.estimated_value
        if val is None:
            size_buckets["Unknown"] += 1
        elif val < 100_000:
            size_buckets["<100K"] += 1
        elif val < 1_000_000:
            size_buckets["100K-1M"] += 1
        elif val < 10_000_000:
            size_buckets["1M-10M"] += 1
        elif val < 50_000_000:
            size_buckets["10M-50M"] += 1
        else:
            size_buckets["50M+"] += 1

    # --- Weighted pipeline (sum of estimated_value * pwin proxy) ---
    # Use strategic score / 100 as pwin proxy when available
    weighted_total = Decimal("0.00")
    scored_opps = StrategicScore.objects.filter(
        opportunity__status="active",
    ).select_related("opportunity")
    for ss in scored_opps:
        val = ss.opportunity.estimated_value or Decimal("0.00")
        pwin = Decimal(str(ss.strategic_score / 100.0))
        weighted_total += val * pwin

    # --- Capacity utilization ---
    max_proposals = strategy.max_concurrent_proposals if strategy else 5
    capacity_util = total_count / max(max_proposals, 1)

    # --- Concentration risk ---
    concentration_risk = {}
    if deals_by_agency and total_count > 0:
        max_agency_count = max(deals_by_agency.values())
        concentration_risk["top_agency_pct"] = round(
            max_agency_count / total_count * 100, 1
        )
    if deals_by_domain and total_count > 0:
        max_domain_count = max(deals_by_domain.values())
        concentration_risk["top_domain_pct"] = round(
            max_domain_count / total_count * 100, 1
        )

    # --- Strategic alignment (average score) ---
    avg_alignment = 0.0
    if scored_opps.exists():
        score_sum = sum(s.strategic_score for s in scored_opps)
        avg_alignment = round(score_sum / scored_opps.count(), 1)

    # --- AI recommendations (simple rule-based for now) ---
    recommendations = []
    if capacity_util > 0.8:
        recommendations.append(
            "Pipeline is near capacity. Consider deferring lower-scored opportunities."
        )
    if concentration_risk.get("top_agency_pct", 0) > 50:
        recommendations.append(
            "High agency concentration risk. Diversify pipeline across agencies."
        )
    if avg_alignment < 40:
        recommendations.append(
            "Average strategic alignment is low. Review targeting criteria."
        )

    snapshot = PortfolioSnapshot.objects.create(
        snapshot_date=today,
        active_deals=total_count,
        total_pipeline_value=total_value,
        weighted_pipeline=weighted_total,
        deals_by_agency=deals_by_agency,
        deals_by_domain=deals_by_domain,
        deals_by_stage=deals_by_stage,
        deals_by_size=size_buckets,
        capacity_utilization=round(capacity_util, 2),
        concentration_risk=concentration_risk,
        strategic_alignment_score=avg_alignment,
        ai_recommendations=recommendations,
        strategy=strategy,
    )

    logger.info(
        "generate_portfolio_snapshot: Created snapshot %s with %d active deals, "
        "$%s total pipeline.",
        snapshot.id,
        total_count,
        total_value,
    )
    return {
        "snapshot_id": str(snapshot.id),
        "active_deals": total_count,
        "total_pipeline_value": str(total_value),
        "weighted_pipeline": str(weighted_total),
    }
