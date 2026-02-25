import logging
from decimal import Decimal

logger = logging.getLogger(__name__)

# Default weights (Phase 1 rule-based)
DEFAULT_WEIGHTS = {
    "naics_match": 0.15,
    "psc_match": 0.10,
    "keyword_overlap": 0.15,
    "capability_similarity": 0.20,
    "past_performance_relevance": 0.10,
    "value_fit": 0.08,
    "deadline_feasibility": 0.07,
    "set_aside_match": 0.10,
    "competition_intensity": -0.03,
    "risk_factors": -0.02,
}


class OpportunityScorer:
    """Rule-based opportunity fit scoring engine (Phase 1)."""

    def __init__(self, company_profile=None, weights=None):
        self.weights = weights or DEFAULT_WEIGHTS
        self.company_profile = company_profile

    def score(self, opportunity) -> dict:
        """Score a single opportunity against company profile."""
        if not self.company_profile:
            return self._empty_score()

        factors = {
            "naics_match": self._score_naics(opportunity),
            "psc_match": self._score_psc(opportunity),
            "keyword_overlap": self._score_keywords(opportunity),
            "capability_similarity": self._score_capability(opportunity),
            "past_performance_relevance": self._score_past_performance(opportunity),
            "value_fit": self._score_value(opportunity),
            "deadline_feasibility": self._score_deadline(opportunity),
            "set_aside_match": self._score_set_aside(opportunity),
            "competition_intensity": self._score_competition(opportunity),
            "risk_factors": self._score_risk(opportunity),
        }

        total = sum(factors[k] * self.weights[k] for k in factors) * 100
        total = max(0.0, min(100.0, total))

        recommendation = self._get_recommendation(total)

        return {
            "total_score": round(total, 1),
            "recommendation": recommendation,
            **{k: round(v * 100, 1) for k, v in factors.items()},
            "score_explanation": self._explain(factors),
        }

    def _score_naics(self, opp) -> float:
        if not opp.naics_code or not self.company_profile.naics_codes:
            return 0.5
        return 1.0 if opp.naics_code in self.company_profile.naics_codes else 0.0

    def _score_psc(self, opp) -> float:
        if not opp.psc_code or not self.company_profile.psc_codes:
            return 0.5
        return 1.0 if opp.psc_code in self.company_profile.psc_codes else 0.0

    def _score_keywords(self, opp) -> float:
        if not opp.keywords or not self.company_profile.core_competencies:
            return 0.5
        opp_kw = set(k.lower() for k in opp.keywords)
        comp_kw = set(k.lower() for k in self.company_profile.core_competencies)
        if not opp_kw:
            return 0.5
        overlap = len(opp_kw & comp_kw)
        return min(1.0, overlap / max(len(opp_kw), 1))

    def _score_capability(self, opp) -> float:
        # In Phase 2, this uses embedding cosine similarity
        # Phase 1: keyword-based approximation
        return 0.5

    def _score_past_performance(self, opp) -> float:
        # In Phase 2, this uses RAG matching
        return 0.5

    def _score_value(self, opp) -> float:
        if not opp.estimated_value:
            return 0.5
        cp = self.company_profile
        if cp.target_value_min and opp.estimated_value < cp.target_value_min:
            return 0.2
        if cp.target_value_max and opp.estimated_value > cp.target_value_max:
            return 0.3
        return 1.0

    def _score_deadline(self, opp) -> float:
        days = opp.days_until_deadline
        if days is None:
            return 0.5
        if days < 7:
            return 0.1
        if days < 14:
            return 0.4
        if days < 30:
            return 0.8
        return 1.0

    def _score_set_aside(self, opp) -> float:
        if not opp.set_aside:
            return 0.7  # Full and open is ok
        if not self.company_profile.set_aside_categories:
            return 0.0
        return 1.0 if opp.set_aside in self.company_profile.set_aside_categories else 0.0

    def _score_competition(self, opp) -> float:
        # Lower score = more competitive (worse for us)
        return 0.5  # Phase 2: estimate from FPDS historical bidder count

    def _score_risk(self, opp) -> float:
        return 0.3  # Phase 2: NLP-based risk extraction from description

    def _get_recommendation(self, score: float) -> str:
        if score >= 75:
            return "strong_bid"
        if score >= 55:
            return "bid"
        if score >= 35:
            return "consider"
        return "no_bid"

    def _explain(self, factors: dict) -> dict:
        explanations = {}
        for factor, value in factors.items():
            label = factor.replace("_", " ").title()
            if value >= 0.8:
                explanations[factor] = f"{label}: Strong match"
            elif value >= 0.5:
                explanations[factor] = f"{label}: Moderate match"
            else:
                explanations[factor] = f"{label}: Weak match"
        return explanations

    def _empty_score(self) -> dict:
        return {
            "total_score": 0.0,
            "recommendation": "no_bid",
            "naics_match": 0.0,
            "psc_match": 0.0,
            "keyword_overlap": 0.0,
            "capability_similarity": 0.0,
            "past_performance_relevance": 0.0,
            "value_fit": 0.0,
            "deadline_feasibility": 0.0,
            "set_aside_match": 0.0,
            "competition_intensity": 0.0,
            "risk_factors": 0.0,
            "score_explanation": {},
        }
