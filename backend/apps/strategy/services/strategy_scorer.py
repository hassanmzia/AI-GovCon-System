import logging

logger = logging.getLogger(__name__)

STRATEGY_WEIGHTS = {
    "agency_alignment": 0.20,
    "domain_alignment": 0.15,
    "growth_market_bonus": 0.10,
    "portfolio_balance": 0.10,
    "revenue_contribution": 0.10,
    "capacity_fit": 0.15,
    "relationship_value": 0.10,
    "competitive_positioning": 0.10,
}


class StrategyScorer:
    """Score opportunities against company strategy."""

    def __init__(self, strategy):
        self.strategy = strategy

    def score(self, opportunity, portfolio_context=None) -> dict:
        factors = {
            "agency_alignment": self._score_agency(opportunity),
            "domain_alignment": self._score_domain(opportunity),
            "growth_market_bonus": self._score_growth_market(opportunity),
            "portfolio_balance": self._score_portfolio_balance(opportunity, portfolio_context),
            "revenue_contribution": self._score_revenue(opportunity),
            "capacity_fit": self._score_capacity(opportunity),
            "relationship_value": self._score_relationship(opportunity),
            "competitive_positioning": self._score_competitive(opportunity),
        }

        total = sum(factors[k] * STRATEGY_WEIGHTS[k] for k in factors) * 100
        total = max(0.0, min(100.0, total))

        recommendation = "bid" if total >= 60 else ("conditional_bid" if total >= 35 else "no_bid")

        return {
            "strategic_score": round(total, 1),
            **{k: round(v * 100, 1) for k, v in factors.items()},
            "bid_recommendation": recommendation,
            "strategic_rationale": self._generate_rationale(factors, total),
        }

    def _score_agency(self, opp) -> float:
        if not opp.agency:
            return 0.3
        agency_lower = opp.agency.lower()
        for target in self.strategy.target_agencies:
            if target.lower() in agency_lower:
                return 1.0
        return 0.2

    def _score_domain(self, opp) -> float:
        keywords = [k.lower() for k in (opp.keywords if hasattr(opp, 'keywords') and opp.keywords else [])]
        if not keywords:
            return 0.3
        domains = [d.lower() for d in self.strategy.target_domains]
        matches = sum(1 for d in domains if any(d in kw for kw in keywords))
        return min(1.0, matches / max(len(domains), 1))

    def _score_growth_market(self, opp) -> float:
        if not self.strategy.growth_markets:
            return 0.5
        desc = (opp.description or "").lower()
        for market in self.strategy.growth_markets:
            if market.lower() in desc:
                return 1.0
        return 0.0

    def _score_portfolio_balance(self, opp, context=None) -> float:
        # Phase 2: Compare current portfolio concentration
        return 0.5

    def _score_revenue(self, opp) -> float:
        if not opp.estimated_value or not self.strategy.target_revenue:
            return 0.5
        ratio = float(opp.estimated_value) / float(self.strategy.target_revenue)
        if ratio > 0.3:
            return 0.3  # Too large, concentration risk
        if ratio > 0.05:
            return 1.0  # Good contribution
        return 0.5

    def _score_capacity(self, opp) -> float:
        return 0.6  # Phase 2: Check against available_key_personnel + clearance_capacity

    def _score_relationship(self, opp) -> float:
        return 0.5  # Phase 2: Check past interactions with agency

    def _score_competitive(self, opp) -> float:
        if not opp.set_aside:
            return 0.5
        for cat in self.strategy.differentiators:
            if cat.lower() in (opp.description or "").lower():
                return 0.8
        return 0.4

    def _generate_rationale(self, factors, total) -> str:
        strengths = [k.replace("_", " ").title() for k, v in factors.items() if v >= 0.7]
        weaknesses = [k.replace("_", " ").title() for k, v in factors.items() if v < 0.3]
        parts = []
        if strengths:
            parts.append(f"Strengths: {', '.join(strengths)}.")
        if weaknesses:
            parts.append(f"Concerns: {', '.join(weaknesses)}.")
        parts.append(f"Overall strategic alignment: {total:.0f}/100.")
        return " ".join(parts)
