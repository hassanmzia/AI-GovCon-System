"""
Pricing scenario engine.

Generates pricing scenarios (Max Profit, Competitive, Aggressive, etc.)
from a CostModel, applying market intelligence and win-probability curves
to compute expected value for each scenario.
"""
import logging
import math
import random
from decimal import Decimal

logger = logging.getLogger(__name__)

_WIN_PROB_STEEPNESS = 5.0

# Margin rate and expected market position for each strategy
_STRATEGY_CONFIG: dict[str, dict] = {
    "floor":           {"margin": Decimal("0.02"), "label": "Floor Pricing"},
    "aggressive":      {"margin": Decimal("0.05"), "label": "Aggressive Pricing"},
    "competitive":     {"margin": Decimal("0.12"), "label": "Competitive Pricing"},
    "value_based":     {"margin": Decimal("0.18"), "label": "Value-Based Pricing"},
    "incumbent_match": {"margin": Decimal("0.15"), "label": "Incumbent Match"},
    "budget_fit":      {"margin": Decimal("0.10"), "label": "Budget Fit"},
    "max_profit":      {"margin": Decimal("0.28"), "label": "Maximum Profit"},
}


def _win_prob(price: Decimal, market_median: Decimal) -> float:
    """Logistic win-probability model."""
    if not market_median or market_median == 0:
        return 0.5
    ratio = float(price) / float(market_median)
    return 1.0 / (1.0 + math.exp(_WIN_PROB_STEEPNESS * (ratio - 1.0)))


def _market_median(cost_model) -> Decimal:
    """Derive market median from PricingIntelligence, falling back to the
    deal's estimated opportunity value or a 15 % cost uplift."""
    from apps.pricing.models import PricingIntelligence, RateCard

    labor_detail = cost_model.labor_detail or []
    labor_cats = list({item.get("category") for item in labor_detail if item.get("category")})

    intel_qs = PricingIntelligence.objects.filter(rate_median__isnull=False)
    if labor_cats:
        intel_qs = intel_qs.filter(labor_category__in=labor_cats)

    medians = [float(i.rate_median) for i in intel_qs]
    if medians:
        avg_rate = sum(medians) / len(medians)
        internal_rates = list(
            RateCard.objects.filter(
                labor_category__in=labor_cats, is_active=True
            ).values_list("internal_rate", flat=True)
        )
        if internal_rates:
            avg_internal = sum(float(r) for r in internal_rates) / len(internal_rates)
            ratio = avg_rate / avg_internal if avg_internal > 0 else 1.15
            return cost_model.total_cost * Decimal(str(ratio))

    opp = getattr(getattr(cost_model, "deal", None), "opportunity", None)
    if opp and opp.estimated_value:
        return opp.estimated_value

    return cost_model.total_cost * Decimal("1.15")


def generate_scenarios(cost_model_id, strategy_types=None):
    """
    Generate pricing scenarios for a given cost model.

    Args:
        cost_model_id: UUID of the CostModel to price.
        strategy_types: Optional list of strategy types to generate.
            Defaults to all types if not provided.

    Returns:
        list[PricingScenario]: Created/updated scenario instances.
    """
    from apps.pricing.models import CostModel, PricingScenario

    try:
        cm = CostModel.objects.select_related("deal__opportunity").get(pk=cost_model_id)
    except CostModel.DoesNotExist:
        raise ValueError(f"CostModel {cost_model_id} not found.")

    total_cost = cm.total_cost
    if total_cost == 0:
        raise ValueError("CostModel has zero total_cost; cannot generate scenarios.")

    types_to_generate = strategy_types or list(_STRATEGY_CONFIG.keys())
    median = _market_median(cm)
    created = []

    for st in types_to_generate:
        cfg = _STRATEGY_CONFIG.get(st)
        if not cfg:
            logger.warning("Unknown strategy type '%s'. Skipping.", st)
            continue

        margin = cfg["margin"]

        # Budget-fit: price just under the estimated opportunity value
        if st == "budget_fit":
            opp = getattr(cm.deal, "opportunity", None)
            if opp and opp.estimated_value and opp.estimated_value > total_cost:
                total_price = opp.estimated_value * Decimal("0.95")
                margin = (total_price - total_cost) / total_cost
            else:
                total_price = total_cost * (1 + margin)
        else:
            total_price = total_cost * (1 + margin)

        profit = total_price - total_cost
        p_win = _win_prob(total_price, median)
        expected_value = total_price * Decimal(str(p_win))

        ratio = float(total_price) / float(median) if median > 0 else 1.0
        if ratio < 0.95:
            competitive_position = "Below market"
        elif ratio <= 1.05:
            competitive_position = "At market"
        else:
            competitive_position = "Above market"

        rationale = (
            f"{cfg['label']} priced at ${total_price:,.2f} "
            f"({float(margin):.1%} margin). "
            f"Win probability: {p_win:.1%}. "
            f"Expected value: ${expected_value:,.2f}. "
            f"Market position: {competitive_position}."
        )

        scenario, _ = PricingScenario.objects.update_or_create(
            deal=cm.deal,
            cost_model=cm,
            strategy_type=st,
            defaults={
                "name": cfg["label"],
                "total_price": total_price.quantize(Decimal("0.01")),
                "profit": profit.quantize(Decimal("0.01")),
                "margin_pct": float(margin),
                "probability_of_win": round(p_win, 4),
                "expected_value": expected_value.quantize(Decimal("0.01")),
                "competitive_position": competitive_position,
                "rationale": rationale,
                "is_recommended": False,
            },
        )
        created.append(scenario)

    # Mark the scenario with the highest expected value as recommended
    if created:
        best = max(created, key=lambda s: s.expected_value)
        PricingScenario.objects.filter(deal=cm.deal, cost_model=cm).update(
            is_recommended=False
        )
        best.is_recommended = True
        best.save(update_fields=["is_recommended"])

    logger.info(
        "generate_scenarios: %d scenarios created for cost_model=%s",
        len(created),
        cost_model_id,
    )
    return created


def run_sensitivity_analysis(scenario_id, iterations=1000):
    """
    Run Monte Carlo sensitivity analysis on a pricing scenario.

    Varies key cost drivers (direct labour hours, fringe rate, overhead rate,
    G&A rate) by random normal perturbations to produce a price distribution.

    Args:
        scenario_id: UUID of the PricingScenario.
        iterations: Number of Monte Carlo iterations.

    Returns:
        dict: Sensitivity results with percentile distributions and the
              updated scenario.sensitivity_data field.
    """
    from apps.pricing.models import PricingScenario

    try:
        scenario = PricingScenario.objects.select_related("cost_model").get(
            pk=scenario_id
        )
    except PricingScenario.DoesNotExist:
        raise ValueError(f"PricingScenario {scenario_id} not found.")

    cm = scenario.cost_model
    base_labor = float(cm.direct_labor)
    base_fringe = cm.fringe_rate       # e.g. 0.30
    base_overhead = cm.overhead_rate   # e.g. 0.40
    base_ga = cm.ga_rate               # e.g. 0.10
    margin = float(scenario.margin_pct)

    prices = []
    for _ in range(iterations):
        # Perturb drivers with 8 % std-dev for labour, 5 % for rates
        labor_mult = random.gauss(1.0, 0.08)
        fringe_mult = random.gauss(1.0, 0.05)
        overhead_mult = random.gauss(1.0, 0.05)
        ga_mult = random.gauss(1.0, 0.04)

        varied_labor = base_labor * max(0.5, labor_mult)
        varied_fringe = base_fringe * max(0.05, fringe_mult)
        varied_overhead = base_overhead * max(0.05, overhead_mult)
        varied_ga = base_ga * max(0.01, ga_mult)

        # Simplified cost rebuild: labour * (1 + fringe + overhead) * (1 + ga)
        varied_cost = varied_labor * (1 + varied_fringe + varied_overhead) * (1 + varied_ga)
        prices.append(varied_cost * (1 + margin))

    prices.sort()
    n = len(prices)

    def pct(p: int) -> float:
        idx = min(int(p / 100 * n), n - 1)
        return round(prices[idx], 2)

    sensitivity = {
        "iterations": iterations,
        "base_price": float(scenario.total_price),
        "p10": pct(10),
        "p25": pct(25),
        "p50": pct(50),
        "p75": pct(75),
        "p90": pct(90),
        "min": round(prices[0], 2),
        "max": round(prices[-1], 2),
        "std_dev": round(
            (sum((p - prices[n // 2]) ** 2 for p in prices) / n) ** 0.5, 2
        ),
    }

    scenario.sensitivity_data = sensitivity
    scenario.save(update_fields=["sensitivity_data"])

    logger.info(
        "run_sensitivity_analysis: scenario=%s p50=%.2f range=[%.2f, %.2f]",
        scenario_id,
        sensitivity["p50"],
        sensitivity["p10"],
        sensitivity["p90"],
    )
    return sensitivity
