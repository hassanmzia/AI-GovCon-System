"""MCP tool server: Rate cards, LOE estimation, cost modeling, pricing scenarios."""
import logging
import os
from typing import Any

import httpx

logger = logging.getLogger("ai_orchestrator.mcp.pricing")

_DJANGO_URL = os.getenv("DJANGO_API_URL", "http://django-api:8001")
_SERVICE_TOKEN = os.getenv("DJANGO_SERVICE_TOKEN", "")


def _headers() -> dict:
    return {"Authorization": f"Bearer {_SERVICE_TOKEN}"} if _SERVICE_TOKEN else {}


async def get_rate_cards(
    labor_category: str | None = None,
    clearance_level: str | None = None,
) -> list[dict[str, Any]]:
    """Fetch labor rate cards from the Django backend.

    Args:
        labor_category: Optional partial match filter.
        clearance_level: Optional clearance level ("None", "Secret", "TS", "TS/SCI").

    Returns:
        List of rate card entries with fully_loaded_rate, fringe, overhead, G&A.
    """
    try:
        params: dict[str, Any] = {}
        if labor_category:
            params["category"] = labor_category
        if clearance_level:
            params["clearance"] = clearance_level

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{_DJANGO_URL}/api/pricing/rate-cards/",
                params=params,
                headers=_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.warning("Rate card fetch failed: %s", exc)
        from src.mcp_servers.market_rate_tools import _default_rate_card

        return _default_rate_card(labor_category)


async def estimate_loe(
    deal_id: str,
    solution_summary: str | None = None,
    wbs_components: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Estimate Level of Effort (LOE) for a deal.

    Args:
        deal_id: Deal UUID.
        solution_summary: Text description of the technical solution.
        wbs_components: Optional pre-defined WBS components with estimated hours.

    Returns:
        Dict with total_hours, by_labor_category, by_wbs_task, staffing_plan, confidence.
    """
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{_DJANGO_URL}/api/pricing/{deal_id}/estimate-loe/",
                json={
                    "solution_summary": solution_summary or "",
                    "wbs_components": wbs_components or [],
                },
                headers=_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("LOE estimation failed for %s: %s", deal_id, exc)
        return {
            "deal_id": deal_id,
            "total_hours": 0,
            "by_labor_category": {},
            "confidence": "low",
            "error": str(exc),
        }


async def build_cost_model(
    deal_id: str,
    loe_estimate: dict[str, Any] | None = None,
    rate_card_ids: list[str] | None = None,
    odc_budget: float = 0,
    travel_budget: float = 0,
    subcontractor_costs: float = 0,
) -> dict[str, Any]:
    """Build a detailed cost model for a deal.

    Args:
        deal_id: Deal UUID.
        loe_estimate: LOE estimate dict (fetched from deal if None).
        rate_card_ids: Specific rate card IDs to use.
        odc_budget: Other Direct Costs budget.
        travel_budget: Travel budget.
        subcontractor_costs: Total subcontractor costs.

    Returns:
        Dict with direct_labor, fringe, overhead, ODCs, travel, materials, G&A,
               total_cost, profit, total_price.
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{_DJANGO_URL}/api/pricing/{deal_id}/build-cost-model/",
                json={
                    "loe_estimate": loe_estimate,
                    "rate_card_ids": rate_card_ids or [],
                    "odc_budget": odc_budget,
                    "travel_budget": travel_budget,
                    "subcontractor_costs": subcontractor_costs,
                },
                headers=_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("Cost model build failed for %s: %s", deal_id, exc)
        return {"deal_id": deal_id, "error": str(exc)}


async def generate_pricing_scenarios(
    deal_id: str,
    cost_model: dict[str, Any] | None = None,
    market_intelligence: dict[str, Any] | None = None,
    evaluation_method: str = "best_value",
) -> list[dict[str, Any]]:
    """Generate 7 pricing scenarios for a deal.

    The 7 scenarios are: max_profit, value_based, competitive, aggressive,
    incumbent_match, budget_fit, floor.

    Args:
        deal_id: Deal UUID.
        cost_model: Cost model dict (built if None).
        market_intelligence: Market pricing intelligence dict.
        evaluation_method: Evaluation method ("lpta", "best_value", "highest_rated").

    Returns:
        List of 7 scenario dicts, each with strategy_type, total_price, profit,
        margin_percent, win_probability, expected_value.
    """
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{_DJANGO_URL}/api/pricing/{deal_id}/scenarios/",
                json={
                    "cost_model": cost_model,
                    "market_intelligence": market_intelligence,
                    "evaluation_method": evaluation_method,
                },
                headers=_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("Pricing scenario generation failed for %s: %s", deal_id, exc)
        return []


async def select_pricing_scenario(
    deal_id: str,
    scenario_id: str,
    rationale: str = "",
) -> dict[str, Any]:
    """Select a pricing scenario (triggers HITL approval workflow).

    Args:
        deal_id: Deal UUID.
        scenario_id: Selected scenario UUID.
        rationale: Rationale for selection.

    Returns:
        Dict with approval_id and status (approved immediately if auto-approved, else pending).
    """
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{_DJANGO_URL}/api/pricing/{deal_id}/select-scenario/",
                json={"scenario_id": scenario_id, "rationale": rationale},
                headers=_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("Scenario selection failed: %s", exc)
        return {"error": str(exc)}


async def get_optimal_scenario(
    scenarios: list[dict[str, Any]],
    optimization_goal: str = "expected_value",
) -> dict[str, Any]:
    """Select the optimal pricing scenario based on the optimization goal.

    Args:
        scenarios: List of pricing scenario dicts from generate_pricing_scenarios.
        optimization_goal: What to optimize for:
            "expected_value" (P(win) × profit), "win_probability", "margin", "total_price".

    Returns:
        The optimal scenario dict with a recommendation_reason field added.
    """
    if not scenarios:
        return {}

    def score(s: dict) -> float:
        if optimization_goal == "expected_value":
            return s.get("expected_value", 0) or 0
        if optimization_goal == "win_probability":
            return s.get("win_probability", 0) or 0
        if optimization_goal == "margin":
            return s.get("margin_percent", 0) or 0
        if optimization_goal == "total_price":
            return -(s.get("total_price", 0) or 0)  # minimize price
        return s.get("expected_value", 0) or 0

    optimal = max(scenarios, key=score)
    optimal = dict(optimal)
    optimal["recommendation_reason"] = (
        f"Selected for highest {optimization_goal}: "
        f"EV=${optimal.get('expected_value', 0):,.0f}, "
        f"P(win)={optimal.get('win_probability', 0)*100:.0f}%, "
        f"Margin={optimal.get('margin_percent', 0):.1f}%"
    )
    return optimal


async def run_sensitivity_analysis(
    deal_id: str,
    base_scenario: dict[str, Any],
    price_range_pct: float = 0.20,
    monte_carlo_runs: int = 1000,
) -> dict[str, Any]:
    """Run sensitivity analysis on a pricing scenario.

    Args:
        deal_id: Deal UUID.
        base_scenario: Base scenario to analyze.
        price_range_pct: Price range to analyze (±% of base price).
        monte_carlo_runs: Number of Monte Carlo simulations.

    Returns:
        Dict with price_distribution, breakeven_price, optimal_price, risk_profile.
    """
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{_DJANGO_URL}/api/pricing/{deal_id}/sensitivity/",
                json={
                    "base_scenario": base_scenario,
                    "price_range_pct": price_range_pct,
                    "monte_carlo_runs": monte_carlo_runs,
                },
                headers=_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("Sensitivity analysis failed: %s", exc)
        return _simple_sensitivity(base_scenario, price_range_pct)


async def prepare_price_defense(
    deal_id: str,
    selected_scenario: dict[str, Any],
) -> dict[str, Any]:
    """Prepare price defense materials (rate substantiation, BOE backup, FAR compliance).

    Args:
        deal_id: Deal UUID.
        selected_scenario: The selected pricing scenario.

    Returns:
        Dict with rate_substantiation, boe_backup, market_comparisons, far_compliance.
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{_DJANGO_URL}/api/pricing/{deal_id}/price-defense/",
                json={"scenario": selected_scenario},
                headers=_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("Price defense preparation failed: %s", exc)
        return {
            "deal_id": deal_id,
            "rate_substantiation": [],
            "boe_backup": [],
            "market_comparisons": [],
            "error": str(exc),
        }


# ── Internal helpers ──────────────────────────────────────────────────────────

def _simple_sensitivity(scenario: dict, range_pct: float) -> dict:
    base_price = scenario.get("total_price", 0) or 0
    base_profit = scenario.get("profit", 0) or 0
    base_pwin = scenario.get("win_probability", 0.5) or 0.5

    low = base_price * (1 - range_pct)
    high = base_price * (1 + range_pct)

    # Simple linear sensitivity
    results = []
    steps = 10
    for i in range(steps + 1):
        price = low + (high - low) * i / steps
        ratio = price / base_price if base_price > 0 else 1
        pwin = max(0.0, min(1.0, base_pwin * (2 - ratio)))  # inverse linear approx
        profit = price - (base_price - base_profit)
        ev = pwin * profit
        results.append({"price": round(price, 0), "win_probability": round(pwin, 3), "expected_value": round(ev, 0)})

    optimal = max(results, key=lambda x: x["expected_value"])
    return {
        "price_distribution": results,
        "optimal_price": optimal["price"],
        "breakeven_price": base_price - base_profit,
        "risk_profile": "low" if range_pct < 0.1 else "medium",
    }
