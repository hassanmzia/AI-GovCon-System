"""
AI-side Risk Engine — mirrors the Django risk engine but runs inside the orchestrator.
Used to compute risk scores before deciding whether to proceed autonomously.
"""
import logging
import math
from dataclasses import dataclass, field

logger = logging.getLogger("ai_orchestrator.governance.risk_engine")


# ── Individual risk dimension functions ───────────────────────────────────────


def compute_deadline_risk(
    days_remaining: float,
    days_needed_estimate: float = 14.0,
) -> float:
    """
    Compute deadline risk based on remaining calendar days vs. estimated effort.

    Returns a float in [0, 1]:
      - 0.0  → ample time (2x+ margin)
      - 1.0  → deadline already passed or critically overdue
    """
    if days_remaining <= 0:
        return 1.0
    if days_needed_estimate <= 0:
        return 0.0

    # Ratio of days_needed to days_remaining — clipped to [0, 1]
    ratio = days_needed_estimate / days_remaining
    # Sigmoid-style: smooth transition between comfortable and critical
    risk = 1.0 / (1.0 + math.exp(-5.0 * (ratio - 1.0)))
    return round(min(max(risk, 0.0), 1.0), 4)


def compute_compliance_risk(
    coverage_pct: float,
    missing_forms: int = 0,
) -> float:
    """
    Compute compliance risk from requirement coverage percentage and missing forms.

    Args:
        coverage_pct: Fraction of RFP requirements addressed (0.0–1.0).
        missing_forms: Number of mandatory forms/certifications not yet completed.

    Returns float in [0, 1].
    """
    if coverage_pct < 0.0:
        coverage_pct = 0.0
    if coverage_pct > 1.0:
        coverage_pct = 1.0

    # Base risk from coverage gap
    coverage_risk = 1.0 - coverage_pct

    # Each missing form adds 0.10, capped at 0.40 additional risk
    form_penalty = min(missing_forms * 0.10, 0.40)

    risk = min(coverage_risk + form_penalty, 1.0)
    return round(risk, 4)


def compute_legal_risk(
    prohibited_clauses: int = 0,
    review_clauses: int = 0,
) -> float:
    """
    Compute legal risk based on flagged contract clauses.

    Args:
        prohibited_clauses: Clauses that are explicitly prohibited or unacceptable.
        review_clauses:     Clauses requiring legal review but not outright prohibited.

    Returns float in [0, 1].
    """
    # Each prohibited clause contributes 0.30, capped at 0.90
    prohibited_risk = min(prohibited_clauses * 0.30, 0.90)
    # Each review clause contributes 0.08, capped at 0.40
    review_risk = min(review_clauses * 0.08, 0.40)

    risk = min(prohibited_risk + review_risk, 1.0)
    return round(risk, 4)


def compute_financial_risk(
    margin_pct: float,
    margin_floor: float = 18.0,
    price_uncertainty: float = 0.2,
    assumption_weakness: float = 0.1,
) -> float:
    """
    Compute financial/pricing risk.

    Args:
        margin_pct:          Estimated gross margin percentage (e.g. 22.5 for 22.5%).
        margin_floor:        Minimum acceptable margin percentage (policy guardrail).
        price_uncertainty:   Fraction representing uncertainty in cost estimates (0–1).
        assumption_weakness: Fraction representing weakness in cost assumptions (0–1).

    Returns float in [0, 1].
    """
    # Margin deficit risk: how far below floor we are (if at all)
    if margin_pct >= margin_floor:
        margin_risk = 0.0
    else:
        deficit = margin_floor - margin_pct
        # Each percentage point below floor adds 0.05, capped at 0.60
        margin_risk = min(deficit * 0.05, 0.60)

    # Uncertainty and assumption weakness compound the risk
    uncertainty_risk = min(price_uncertainty * 0.25, 0.25)
    assumption_risk = min(assumption_weakness * 0.15, 0.15)

    risk = min(margin_risk + uncertainty_risk + assumption_risk, 1.0)
    return round(risk, 4)


def compute_security_risk(
    has_cui: bool = False,
    has_itar: bool = False,
) -> float:
    """
    Compute security risk from classification and export-control requirements.

    Args:
        has_cui:  Contract involves Controlled Unclassified Information.
        has_itar: Contract involves ITAR-controlled data or technology.

    Returns float in [0, 1].
    """
    risk = 0.0
    if has_cui:
        risk += 0.35
    if has_itar:
        risk += 0.50
    return round(min(risk, 1.0), 4)


def compute_reputation_risk(
    pp_gaps: int = 0,
    compliance_history: float = 1.0,
) -> float:
    """
    Compute reputational risk from past performance gaps and compliance history.

    Args:
        pp_gaps:            Number of past performance relevance gaps identified.
        compliance_history: Historical compliance score (1.0 = perfect, 0.0 = poor).

    Returns float in [0, 1].
    """
    if compliance_history < 0.0:
        compliance_history = 0.0
    if compliance_history > 1.0:
        compliance_history = 1.0

    # Past performance gaps: each gap adds 0.12, capped at 0.48
    pp_risk = min(pp_gaps * 0.12, 0.48)

    # Poor compliance history increases risk
    history_risk = 1.0 - compliance_history

    risk = min((pp_risk + history_risk) / 2.0, 1.0)
    return round(risk, 4)


def compute_composite(
    legal: float,
    compliance: float,
    deadline: float,
    financial: float,
    security: float,
    reputation: float,
) -> float:
    """
    Compute a single composite risk score from all six dimensions.

    Weights:
        legal       25%
        compliance  25%
        deadline    15%
        financial   15%
        security    10%
        reputation  10%

    Returns float in [0, 1].
    """
    composite = (
        legal      * 0.25
        + compliance * 0.25
        + deadline   * 0.15
        + financial  * 0.15
        + security   * 0.10
        + reputation * 0.10
    )
    return round(min(max(composite, 0.0), 1.0), 4)


# ── Data class ────────────────────────────────────────────────────────────────


@dataclass
class RiskScore:
    """Holds all six risk dimension scores and the computed composite."""

    legal: float = 0.0
    compliance: float = 0.0
    deadline: float = 0.0
    financial: float = 0.0
    security: float = 0.0
    reputation: float = 0.0
    composite: float = field(init=False, default=0.0)

    def __post_init__(self) -> None:
        self.composite = compute_composite(
            self.legal,
            self.compliance,
            self.deadline,
            self.financial,
            self.security,
            self.reputation,
        )

    def exceeds_threshold(self, t: float) -> bool:
        """Return True if the composite risk score is above the threshold t."""
        return self.composite > t

    def to_dict(self) -> dict:
        return {
            "legal": self.legal,
            "compliance": self.compliance,
            "deadline": self.deadline,
            "financial": self.financial,
            "security": self.security,
            "reputation": self.reputation,
            "composite": self.composite,
        }


# ── Main entry point ──────────────────────────────────────────────────────────


def assess(deal_context: dict, policy: dict) -> RiskScore:
    """
    Compute a full RiskScore from deal context and the active policy.

    Expected keys in deal_context (all optional, with safe defaults):
        days_remaining          (float) — calendar days until submission due date
        days_needed_estimate    (float) — estimated days needed to complete proposal
        compliance_coverage_pct (float) — fraction of requirements covered (0.0–1.0)
        missing_forms           (int)   — number of required forms not yet completed
        prohibited_clauses      (int)   — count of prohibited contract clauses flagged
        review_clauses          (int)   — count of clauses flagged for legal review
        margin_pct              (float) — estimated gross margin percentage
        price_uncertainty       (float) — cost estimate uncertainty (0.0–1.0)
        assumption_weakness     (float) — cost assumption weakness (0.0–1.0)
        has_cui                 (bool)  — involves Controlled Unclassified Information
        has_itar                (bool)  — involves ITAR-controlled technology
        pp_gaps                 (int)   — number of past performance relevance gaps
        compliance_history      (float) — historical compliance score (0.0–1.0)

    Args:
        deal_context: Dictionary of deal-level contextual data.
        policy:       Active AI Autonomy Policy (used for margin floor guardrail).

    Returns:
        RiskScore dataclass instance with all dimensions and composite populated.
    """
    pricing_guardrails = policy.get("pricing_guardrails", {})
    margin_floor = float(pricing_guardrails.get("min_margin_percent", 18.0))

    legal = compute_legal_risk(
        prohibited_clauses=int(deal_context.get("prohibited_clauses", 0)),
        review_clauses=int(deal_context.get("review_clauses", 0)),
    )
    compliance = compute_compliance_risk(
        coverage_pct=float(deal_context.get("compliance_coverage_pct", 1.0)),
        missing_forms=int(deal_context.get("missing_forms", 0)),
    )
    deadline = compute_deadline_risk(
        days_remaining=float(deal_context.get("days_remaining", 30.0)),
        days_needed_estimate=float(deal_context.get("days_needed_estimate", 14.0)),
    )
    financial = compute_financial_risk(
        margin_pct=float(deal_context.get("margin_pct", 20.0)),
        margin_floor=margin_floor,
        price_uncertainty=float(deal_context.get("price_uncertainty", 0.2)),
        assumption_weakness=float(deal_context.get("assumption_weakness", 0.1)),
    )
    security = compute_security_risk(
        has_cui=bool(deal_context.get("has_cui", False)),
        has_itar=bool(deal_context.get("has_itar", False)),
    )
    reputation = compute_reputation_risk(
        pp_gaps=int(deal_context.get("pp_gaps", 0)),
        compliance_history=float(deal_context.get("compliance_history", 1.0)),
    )

    score = RiskScore(
        legal=legal,
        compliance=compliance,
        deadline=deadline,
        financial=financial,
        security=security,
        reputation=reputation,
    )

    logger.info(
        "RiskEngine: composite=%.3f (legal=%.3f compliance=%.3f deadline=%.3f "
        "financial=%.3f security=%.3f reputation=%.3f)",
        score.composite,
        score.legal,
        score.compliance,
        score.deadline,
        score.financial,
        score.security,
        score.reputation,
    )

    return score
