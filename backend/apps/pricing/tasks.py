import logging
from decimal import Decimal

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def calculate_pricing_scenarios(self, deal_id: str, cost_model_id: str):
    """
    Run the pricing scenario engine for all 7 strategy types and persist
    PricingScenario records for the given cost model.
    """
    from apps.pricing.services.scenario_engine import generate_scenarios

    logger.info(
        "Calculating pricing scenarios for deal %s, cost model %s",
        deal_id,
        cost_model_id,
    )

    try:
        scenarios = generate_scenarios(cost_model_id)
        logger.info(
            "Created/updated %d pricing scenarios for deal %s",
            len(scenarios),
            deal_id,
        )
        return {"scenarios": len(scenarios)}

    except Exception as exc:
        logger.error("calculate_pricing_scenarios failed for deal %s: %s", deal_id, exc)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=120)
def fetch_pricing_intelligence(self, labor_categories=None):
    """
    Refresh market rate intelligence from RateCard data and store as
    PricingIntelligence records.
    """
    from apps.pricing.services.price_to_win import refresh_market_intelligence

    logger.info("Fetching pricing intelligence: categories=%s", labor_categories)

    try:
        updated = refresh_market_intelligence(labor_categories=labor_categories)
        logger.info("Saved %d pricing intelligence records", updated)
        return {"saved": updated}

    except Exception as exc:
        logger.error("fetch_pricing_intelligence failed: %s", exc)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def run_price_to_win_analysis(self, deal_id: str):
    """
    Run price-to-win analysis for a deal and mark the recommended scenario.
    """
    from apps.pricing.models import PricingScenario
    from apps.pricing.services.price_to_win import estimate_price_to_win

    scenarios = PricingScenario.objects.filter(deal_id=deal_id)
    if not scenarios.exists():
        logger.warning("No pricing scenarios found for deal %s — run scenario engine first", deal_id)
        return {"status": "no_scenarios"}

    try:
        ptw_result = estimate_price_to_win(deal_id)

        # Mark the scenario with highest expected value as recommended
        recommended_price = ptw_result.get("recommended_price", Decimal("0"))
        if recommended_price:
            PricingScenario.objects.filter(deal_id=deal_id).update(is_recommended=False)
            best = (
                PricingScenario.objects.filter(deal_id=deal_id)
                .order_by("-expected_value")
                .first()
            )
            if best:
                best.is_recommended = True
                best.rationale = ptw_result.get("rationale", "")
                best.save(update_fields=["is_recommended", "rationale"])

        logger.info("Price-to-win analysis complete for deal %s", deal_id)
        return ptw_result

    except Exception as exc:
        logger.error("run_price_to_win_analysis failed for deal %s: %s", deal_id, exc)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def request_pricing_approval(self, deal_id: str, scenario_id: str, requested_by_id: str):
    """
    Create a PricingApproval record (HITL gate) for a selected pricing scenario.
    """
    from django.contrib.auth import get_user_model
    from apps.pricing.models import PricingApproval, PricingScenario

    User = get_user_model()

    try:
        scenario = PricingScenario.objects.select_related("deal").get(pk=scenario_id)
        requester = User.objects.get(pk=requested_by_id)
    except (PricingScenario.DoesNotExist, User.DoesNotExist) as exc:
        logger.error("request_pricing_approval: %s", exc)
        return

    approval, created = PricingApproval.objects.get_or_create(
        deal=scenario.deal,
        scenario=scenario,
        status="pending",
        defaults={"requested_by": requester},
    )

    logger.info(
        "PricingApproval %s for scenario %s (deal %s): created=%s",
        approval.id,
        scenario_id,
        deal_id,
        created,
    )
    return {"approval_id": str(approval.id), "created": created}
