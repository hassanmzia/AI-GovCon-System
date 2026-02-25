"""
Price-to-win analysis service.

Combines market intelligence, cost model data, and a logistic win-probability
model to estimate the optimal price point that maximises expected value.
"""
import logging
import math
from decimal import Decimal

logger = logging.getLogger(__name__)

_WIN_PROB_STEEPNESS = 5.0  # logistic curve steepness


def _logistic_win_prob(price: Decimal, market_median: Decimal) -> float:
    """Win probability = 1 / (1 + e^(k * (price/median - 1))).

    At the median: P(win) ≈ 0.50.
    20 % below median: P(win) ≈ 0.73.
    20 % above median: P(win) ≈ 0.27.
    """
    if not market_median or market_median == 0:
        return 0.5
    ratio = float(price) / float(market_median)
    return 1.0 / (1.0 + math.exp(_WIN_PROB_STEEPNESS * (ratio - 1.0)))


def estimate_price_to_win(deal_id):
    """
    Estimate the price-to-win for a deal.

    Args:
        deal_id: UUID of the Deal.

    Returns:
        dict: {
            "recommended_price": Decimal,
            "win_probability": float,
            "expected_value": Decimal,
            "competitor_range": {"low": Decimal, "median": Decimal, "high": Decimal},
            "confidence": float,
            "rationale": str,
        }
    """
    from apps.deals.models import Deal
    from apps.pricing.models import CostModel, PricingIntelligence

    try:
        deal = Deal.objects.select_related("opportunity").get(pk=deal_id)
    except Deal.DoesNotExist:
        raise ValueError(f"Deal {deal_id} not found.")

    cost_model = CostModel.objects.filter(deal=deal).order_by("-version").first()
    if not cost_model:
        raise ValueError(f"No CostModel found for deal {deal_id}. Create a cost model first.")

    total_cost = cost_model.total_cost

    # ── Determine market median ───────────────────────────────────────────────
    labor_detail = cost_model.labor_detail or []
    labor_cats = list({item.get("category") for item in labor_detail if item.get("category")})

    intel_qs = PricingIntelligence.objects.filter(rate_median__isnull=False)
    if labor_cats:
        intel_qs = intel_qs.filter(labor_category__in=labor_cats)

    medians = [float(i.rate_median) for i in intel_qs]

    if medians:
        # Average market rate as a ratio applied to cost
        avg_rate = sum(medians) / len(medians)
        # PricingIntelligence rates are $/hr; use ratio vs internal rate to scale
        from apps.pricing.models import RateCard
        internal_rates = list(
            RateCard.objects.filter(
                labor_category__in=labor_cats, is_active=True
            ).values_list("internal_rate", flat=True)
        )
        if internal_rates:
            avg_internal = sum(float(r) for r in internal_rates) / len(internal_rates)
            market_ratio = avg_rate / avg_internal if avg_internal > 0 else 1.15
            market_median = total_cost * Decimal(str(market_ratio))
        else:
            market_median = total_cost * Decimal("1.15")
        confidence_base = min(0.9, 0.5 + len(medians) * 0.04)
    elif deal.opportunity and deal.opportunity.estimated_value:
        market_median = deal.opportunity.estimated_value
        confidence_base = 0.55
    else:
        market_median = total_cost * Decimal("1.15")
        confidence_base = 0.40

    # ── Scan price points for maximum expected value ──────────────────────────
    best_ev = Decimal("-1")
    best_price = market_median
    best_prob = 0.5

    # Test 1.02x to 1.50x total cost in 1% steps
    for multiplier_cents in range(102, 151):
        multiplier = Decimal(str(multiplier_cents / 100))
        candidate = total_cost * multiplier
        p_win = _logistic_win_prob(candidate, market_median)
        ev = candidate * Decimal(str(p_win))
        if ev > best_ev:
            best_ev = ev
            best_price = candidate
            best_prob = p_win

    competitor_range = {
        "low":    market_median * Decimal("0.85"),
        "median": market_median,
        "high":   market_median * Decimal("1.25"),
    }

    rationale = (
        f"Recommended price ${best_price:,.2f} based on market median "
        f"${market_median:,.2f} derived from "
        f"{len(medians)} market intelligence data point(s). "
        f"At this price the estimated win probability is {best_prob:.1%} "
        f"(expected value ${best_ev:,.2f}). "
        f"Competitor prices estimated in the range "
        f"${competitor_range['low']:,.2f}–${competitor_range['high']:,.2f}."
    )

    logger.info(
        "estimate_price_to_win: deal=%s recommended=$%s p_win=%.2f ev=$%s",
        deal_id, best_price, best_prob, best_ev,
    )

    return {
        "recommended_price": best_price.quantize(Decimal("0.01")),
        "win_probability": round(best_prob, 3),
        "expected_value": best_ev.quantize(Decimal("0.01")),
        "competitor_range": {k: v.quantize(Decimal("0.01")) for k, v in competitor_range.items()},
        "confidence": round(confidence_base, 2),
        "rationale": rationale,
    }


def refresh_market_intelligence(labor_categories=None):
    """
    Refresh PricingIntelligence records from the active RateCard data.

    Args:
        labor_categories: Optional list of labor category names to refresh.
            Refreshes all active categories if not provided.

    Returns:
        int: Number of PricingIntelligence records created or updated.
    """
    from apps.pricing.models import PricingIntelligence, RateCard
    from django.utils import timezone

    qs = RateCard.objects.filter(is_active=True)
    if labor_categories:
        qs = qs.filter(labor_category__in=labor_categories)

    today = timezone.now().date()
    updated = 0

    for rc in qs:
        # Derive market low/median/high if not set
        internal = rc.internal_rate
        low = rc.market_low if rc.market_low else (internal * Decimal("0.85")).quantize(Decimal("0.01"))
        median = rc.market_median if rc.market_median else internal
        high = rc.market_high if rc.market_high else (internal * Decimal("1.25")).quantize(Decimal("0.01"))

        if rc.gsa_rate:
            median = rc.gsa_rate  # prefer GSA rate as market benchmark

        _, created = PricingIntelligence.objects.update_or_create(
            source="rate_card",
            labor_category=rc.labor_category,
            data_date=today,
            defaults={
                "rate_low": low,
                "rate_median": median,
                "rate_high": high,
                "raw_data": {
                    "gsa_rate": str(rc.gsa_rate) if rc.gsa_rate else None,
                    "internal_rate": str(rc.internal_rate),
                    "gsa_sin": rc.gsa_sin,
                    "education_requirement": rc.education_requirement,
                    "experience_years": rc.experience_years,
                    "clearance_required": rc.clearance_required,
                },
            },
        )
        updated += 1

    logger.info(
        "refresh_market_intelligence: %d records refreshed (categories=%s)",
        updated,
        labor_categories or "all",
    )
    return updated
