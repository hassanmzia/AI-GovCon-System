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
    from apps.pricing.models import CostModel, PricingScenario
    from apps.pricing.services.scenario_engine import PricingScenarioEngine

    try:
        cost_model = CostModel.objects.select_related("deal").get(pk=cost_model_id)
    except CostModel.DoesNotExist:
        logger.error("calculate_pricing_scenarios: CostModel %s not found", cost_model_id)
        return

    logger.info(
        "Calculating pricing scenarios for deal %s, cost model %s",
        deal_id,
        cost_model_id,
    )

    try:
        engine = PricingScenarioEngine(cost_model=cost_model)
        scenarios = engine.generate_all_scenarios()

        created_count = 0
        for scenario_data in scenarios:
            PricingScenario.objects.update_or_create(
                deal=cost_model.deal,
                cost_model=cost_model,
                strategy_type=scenario_data["strategy_type"],
                defaults={
                    "name": scenario_data["name"],
                    "total_price": scenario_data["total_price"],
                    "profit": scenario_data["profit"],
                    "margin_pct": scenario_data["margin_pct"],
                    "probability_of_win": scenario_data["probability_of_win"],
                    "expected_value": scenario_data["expected_value"],
                    "competitive_position": scenario_data.get("competitive_position", ""),
                    "sensitivity_data": scenario_data.get("sensitivity_data", {}),
                    "is_recommended": scenario_data.get("is_recommended", False),
                    "rationale": scenario_data.get("rationale", ""),
                },
            )
            created_count += 1

        logger.info(
            "Created/updated %d pricing scenarios for deal %s", created_count, deal_id
        )
        return {"scenarios": created_count}

    except Exception as exc:
        logger.error("calculate_pricing_scenarios failed for deal %s: %s", deal_id, exc)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=120)
def fetch_pricing_intelligence(self, labor_category: str = None, agency: str = None):
    """
    Pull market rate intelligence from GSA and FPDS and store as
    PricingIntelligence records.
    """
    from apps.pricing.models import PricingIntelligence
    from apps.pricing.services.price_to_win import PriceToWinAnalyzer

    logger.info(
        "Fetching pricing intelligence: category=%s, agency=%s",
        labor_category,
        agency,
    )

    try:
        analyzer = PriceToWinAnalyzer()
        records = analyzer.fetch_market_rates(
            labor_category=labor_category, agency=agency
        )

        saved = 0
        for rec in records:
            PricingIntelligence.objects.update_or_create(
                source=rec["source"],
                labor_category=rec.get("labor_category", ""),
                agency=rec.get("agency", ""),
                defaults={
                    "rate_low": rec.get("rate_low"),
                    "rate_median": rec.get("rate_median"),
                    "rate_high": rec.get("rate_high"),
                    "data_date": rec.get("data_date"),
                    "raw_data": rec.get("raw_data", {}),
                },
            )
            saved += 1

        logger.info("Saved %d pricing intelligence records", saved)
        return {"saved": saved}

    except Exception as exc:
        logger.error("fetch_pricing_intelligence failed: %s", exc)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def run_price_to_win_analysis(self, deal_id: str):
    """
    Run price-to-win analysis for a deal: pulls competitor pricing signals,
    government budget estimates, and sets is_recommended on the best scenario.
    """
    from apps.deals.models import Deal
    from apps.pricing.models import PricingScenario
    from apps.pricing.services.price_to_win import PriceToWinAnalyzer

    try:
        deal = Deal.objects.get(pk=deal_id)
    except Deal.DoesNotExist:
        logger.error("run_price_to_win_analysis: deal %s not found", deal_id)
        return

    scenarios = PricingScenario.objects.filter(deal=deal)
    if not scenarios.exists():
        logger.warning("No pricing scenarios found for deal %s — run scenario engine first", deal_id)
        return {"status": "no_scenarios"}

    try:
        analyzer = PriceToWinAnalyzer()
        ptw_result = analyzer.analyze(deal=deal, scenarios=list(scenarios))

        # Mark the recommended scenario
        PricingScenario.objects.filter(deal=deal).update(is_recommended=False)
        recommended_type = ptw_result.get("recommended_strategy_type")
        if recommended_type:
            PricingScenario.objects.filter(deal=deal, strategy_type=recommended_type).update(
                is_recommended=True,
                rationale=ptw_result.get("rationale", ""),
            )

        logger.info(
            "Price-to-win analysis complete for deal %s: recommended=%s",
            deal_id,
            recommended_type,
        )
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
