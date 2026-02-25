"""
Demand Forecaster Service

Queries active deals in proposal+ stages, extracts labor category needs
from pricing scenarios, weights by win probability, and returns a
{labor_category: demand_count} forecast along with gap analysis.
"""

import logging
from collections import defaultdict

from django.db.models import Q, Sum

logger = logging.getLogger(__name__)

# Deal stages that indicate active pursuit requiring future staffing
ACTIVE_PIPELINE_STAGES = [
    "capture_plan",
    "proposal_dev",
    "red_team",
    "final_review",
    "submit",
    "post_submit",
    "award_pending",
]


class DemandForecaster:
    """
    Computes a workforce demand forecast from the deal pipeline.

    The forecast is derived by:
    1. Querying deals in proposal+ stages.
    2. Extracting labor category needs from associated pricing scenarios
       (via cost model labor_detail and LOE staffing plans).
    3. Weighting FTE demand by each deal's win probability.
    4. Comparing the weighted demand against current workforce capacity
       to identify gaps.
    """

    def compute_forecast(self) -> dict:
        """
        Return the complete demand forecast.

        Returns:
            dict with keys:
                - forecast: {labor_category: weighted_fte_demand}
                - pipeline_deals: count of deals considered
                - current_capacity: {labor_category: available_fte_count}
                - gaps: {labor_category: shortfall_fte}
                - details: per-deal breakdown
        """
        pipeline_deals = self._get_pipeline_deals()
        raw_demand, deal_details = self._extract_demand(pipeline_deals)
        current_capacity = self._get_current_capacity()
        gaps = self._compute_gaps(raw_demand, current_capacity)

        return {
            "forecast": dict(raw_demand),
            "pipeline_deals": len(pipeline_deals),
            "current_capacity": dict(current_capacity),
            "gaps": dict(gaps),
            "details": deal_details,
        }

    # ── Internal helpers ─────────────────────────────────

    @staticmethod
    def _get_pipeline_deals():
        """Fetch deals in active pipeline stages."""
        from apps.deals.models import Deal

        return list(
            Deal.objects.filter(
                stage__in=ACTIVE_PIPELINE_STAGES,
            )
            .exclude(outcome__in=["lost", "no_bid", "cancelled"])
            .select_related("opportunity")
        )

    @staticmethod
    def _extract_demand(deals) -> tuple[dict, list]:
        """
        Extract labor category demand from pricing scenarios and LOE estimates.

        For each deal, looks at:
        - PricingScenario -> CostModel -> labor_detail
        - LOEEstimate -> staffing_plan
        Weights each labor category's FTE count by the deal's win_probability.
        """
        from apps.pricing.models import PricingScenario

        weighted_demand: dict[str, float] = defaultdict(float)
        deal_details: list[dict] = []

        for deal in deals:
            win_prob = deal.win_probability or 0.0
            deal_labor: dict[str, float] = defaultdict(float)

            # 1. Check recommended pricing scenario -> cost model labor_detail
            scenarios = PricingScenario.objects.filter(
                deal=deal, is_recommended=True
            ).select_related("cost_model")

            if not scenarios.exists():
                # Fall back to any scenario
                scenarios = PricingScenario.objects.filter(
                    deal=deal
                ).select_related("cost_model")[:1]

            for scenario in scenarios:
                cost_model = scenario.cost_model
                if cost_model and cost_model.labor_detail:
                    for entry in cost_model.labor_detail:
                        category = entry.get("category", "Unknown")
                        hours = entry.get("hours", 0)
                        # Convert hours to FTEs (assuming 1,880 billable hours/year)
                        ftes = hours / 1880.0 if hours else 0.0
                        deal_labor[category] += ftes

            # 2. Check LOE estimates -> staffing_plan
            if not deal_labor:
                loe_estimates = deal.loe_estimates.order_by("-version")[:1]
                for loe in loe_estimates:
                    if loe.staffing_plan:
                        # staffing_plan format: {month: {labor_cat: hours}}
                        cat_totals: dict[str, float] = defaultdict(float)
                        for _month, cats in loe.staffing_plan.items():
                            if isinstance(cats, dict):
                                for cat, hours in cats.items():
                                    cat_totals[cat] += float(hours)
                        months = max(len(loe.staffing_plan), 1)
                        for cat, total_hours in cat_totals.items():
                            # Average monthly hours -> annualized FTEs
                            avg_monthly = total_hours / months
                            annual_hours = avg_monthly * 12
                            ftes = annual_hours / 1880.0
                            deal_labor[cat] += ftes

            # Weight by win probability
            for cat, ftes in deal_labor.items():
                weighted_demand[cat] += ftes * win_prob

            deal_details.append(
                {
                    "deal_id": str(deal.id),
                    "deal_title": deal.title,
                    "stage": deal.stage,
                    "win_probability": win_prob,
                    "labor_demand": dict(deal_labor),
                    "weighted_demand": {
                        cat: round(ftes * win_prob, 2) for cat, ftes in deal_labor.items()
                    },
                }
            )

        # Round final values
        for cat in weighted_demand:
            weighted_demand[cat] = round(weighted_demand[cat], 2)

        return dict(weighted_demand), deal_details

    @staticmethod
    def _get_current_capacity() -> dict[str, int]:
        """Count active employees by labor category."""
        from apps.workforce.models import Employee

        capacity: dict[str, int] = defaultdict(int)
        employees = Employee.objects.filter(is_active=True).exclude(
            labor_category=""
        )
        for emp in employees:
            capacity[emp.labor_category] += 1

        return dict(capacity)

    @staticmethod
    def _compute_gaps(
        demand: dict[str, float], capacity: dict[str, int]
    ) -> dict[str, float]:
        """
        Compute the gap (shortfall) between forecasted demand and current capacity.

        Positive values indicate a hiring need; negative values indicate surplus.
        """
        all_categories = set(demand.keys()) | set(capacity.keys())
        gaps: dict[str, float] = {}

        for cat in sorted(all_categories):
            needed = demand.get(cat, 0.0)
            available = capacity.get(cat, 0)
            gap = round(needed - available, 2)
            if gap != 0:
                gaps[cat] = gap

        return gaps
