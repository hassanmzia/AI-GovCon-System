"""
Risk Scoring Engine — deterministic composite risk calculator for AI autonomy governance.

Computes 6 risk dimensions (0.0–1.0 each) and a weighted composite.
Used by the HITL gate to decide whether AI can act autonomously.

Weights: legal=0.25, compliance=0.25, deadline=0.15, financial=0.15, security=0.10, reputation=0.10
"""

from __future__ import annotations

from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Weight constants
# ---------------------------------------------------------------------------

WEIGHTS = {
    "legal": 0.25,
    "compliance": 0.25,
    "deadline": 0.15,
    "financial": 0.15,
    "security": 0.10,
    "reputation": 0.10,
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    """Clamp *value* to the range [low, high]."""
    return max(low, min(high, value))


# ---------------------------------------------------------------------------
# Individual risk dimension calculators
# ---------------------------------------------------------------------------

def compute_deadline_risk(days_remaining: float, days_needed_estimate: float) -> float:
    """
    Calculate deadline risk (0.0–1.0).

    If days_remaining is at or below zero (past deadline), returns 0.95.
    Otherwise: clamp(1 - days_remaining / days_needed_estimate, 0, 1).
    """
    if days_remaining <= 0:
        return 0.95
    if days_needed_estimate <= 0:
        # No estimate means we cannot assess — treat as moderate risk
        return 0.5
    return _clamp(1.0 - days_remaining / days_needed_estimate)


def compute_compliance_risk(coverage_pct: float, missing_forms: int = 0) -> float:
    """
    Calculate compliance risk (0.0–1.0).

    Base risk = clamp(1 - coverage_pct, 0, 1).
    Additional penalty: 0.05 per missing form, clamped to 0–1.
    """
    base = _clamp(1.0 - coverage_pct)
    return _clamp(base + 0.05 * missing_forms)


def compute_legal_risk(
    prohibited_clauses_found: int = 0,
    review_clauses_found: int = 0,
) -> float:
    """
    Calculate legal risk (0.0–1.0).

    Returns 1.0 if any prohibited clauses are found.
    Otherwise returns min(0.6 * review_clauses_found, 1.0).
    """
    if prohibited_clauses_found > 0:
        return 1.0
    return min(0.6 * review_clauses_found, 1.0)


def compute_financial_risk(
    margin_pct: float,
    margin_floor: float,
    price_uncertainty: float = 0.2,
    assumption_weakness: float = 0.0,
) -> float:
    """
    Calculate financial risk (0.0–1.0).

    margin_floor_proximity = clamp((margin_floor - margin_pct) / margin_floor, 0, 1)
        when margin_pct < margin_floor, else 0.
    Result = 0.5 * price_uncertainty + 0.3 * margin_floor_proximity + 0.2 * assumption_weakness
    """
    if margin_pct < margin_floor and margin_floor != 0:
        margin_floor_proximity = _clamp((margin_floor - margin_pct) / margin_floor)
    else:
        margin_floor_proximity = 0.0

    raw = (
        0.5 * _clamp(price_uncertainty)
        + 0.3 * margin_floor_proximity
        + 0.2 * _clamp(assumption_weakness)
    )
    return _clamp(raw)


def compute_security_risk(
    has_cui: bool = False,
    has_itar: bool = False,
    classified_handling: bool = False,
) -> float:
    """
    Calculate security risk (0.0–1.0) based on data sensitivity flags.

    Each flag contributes incrementally:
        - has_cui: +0.3
        - has_itar: +0.4
        - classified_handling: +0.5
    Clamped to 0–1.
    """
    score = 0.0
    if has_cui:
        score += 0.3
    if has_itar:
        score += 0.4
    if classified_handling:
        score += 0.5
    return _clamp(score)


def compute_reputation_risk(
    past_performance_gaps: int = 0,
    compliance_history_score: float = 1.0,
) -> float:
    """
    Calculate reputation risk (0.0–1.0).

    Each past performance gap contributes 0.15.
    compliance_history_score is inverted (1.0 = perfect history → 0 risk).
    Result = clamp(0.15 * past_performance_gaps + (1 - compliance_history_score), 0, 1).
    """
    gap_contribution = 0.15 * past_performance_gaps
    history_contribution = 1.0 - _clamp(compliance_history_score)
    return _clamp(gap_contribution + history_contribution)


def compute_composite_risk(
    legal: float,
    compliance: float,
    deadline: float,
    financial: float,
    security: float,
    reputation: float,
) -> float:
    """
    Compute weighted composite risk score (0.0–1.0).

    Weights: legal=0.25, compliance=0.25, deadline=0.15, financial=0.15,
             security=0.10, reputation=0.10
    """
    composite = (
        WEIGHTS["legal"] * legal
        + WEIGHTS["compliance"] * compliance
        + WEIGHTS["deadline"] * deadline
        + WEIGHTS["financial"] * financial
        + WEIGHTS["security"] * security
        + WEIGHTS["reputation"] * reputation
    )
    return _clamp(composite)


# ---------------------------------------------------------------------------
# RiskAssessment dataclass
# ---------------------------------------------------------------------------

@dataclass
class RiskAssessment:
    """Full risk assessment result with individual dimensions and composite score."""

    legal: float
    compliance: float
    deadline: float
    financial: float
    security: float
    reputation: float
    composite: float
    # Optional metadata carried through for traceability
    metadata: dict = field(default_factory=dict)

    def exceeds_threshold(self, threshold: float) -> bool:
        """Return True if the composite risk score exceeds *threshold*."""
        return self.composite > threshold

    def requires_hitl(self, policy: dict) -> bool:
        """
        Return True if the risk assessment mandates human-in-the-loop review
        according to *policy*.

        The policy dict is expected to have a structure like:
            {
                "hitl_risk_threshold": 0.6,
                "always_hitl_if_legal_max": true,
                ...
            }
        """
        hitl_threshold = policy.get("hitl_risk_threshold", 0.6)
        if self.composite >= hitl_threshold:
            return True
        # Hard rule: any maxed-out legal risk always triggers HITL
        if policy.get("always_hitl_if_legal_max", True) and self.legal >= 1.0:
            return True
        return False

    def to_dict(self) -> dict:
        """Serialize the assessment to a plain dict suitable for JSON serialization."""
        return {
            "legal": self.legal,
            "compliance": self.compliance,
            "deadline": self.deadline,
            "financial": self.financial,
            "security": self.security,
            "reputation": self.reputation,
            "composite": self.composite,
            "metadata": self.metadata,
        }


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def assess_risk(deal_context: dict, policy: dict) -> RiskAssessment:
    """
    Compute a full RiskAssessment for a given deal context under a policy.

    deal_context keys (all optional, sensible defaults apply):
        days_remaining          (float) — calendar days until submission deadline
        days_needed_estimate    (float) — estimated days needed to complete proposal
        compliance_coverage_pct (float) — 0.0–1.0 fraction of requirements covered
        missing_forms           (int)   — count of missing required forms
        prohibited_clauses      (int)   — count of prohibited contract clauses found
        review_clauses          (int)   — count of clauses flagged for legal review
        margin_pct              (float) — current bid margin as fraction (e.g. 0.12)
        margin_floor            (float) — minimum acceptable margin (e.g. 0.08)
        price_uncertainty       (float) — 0.0–1.0 confidence in cost estimates
        assumption_weakness     (float) — 0.0–1.0 degree of weak cost assumptions
        has_cui                 (bool)  — deal involves Controlled Unclassified Info
        has_itar                (bool)  — deal involves ITAR-controlled material
        classified_handling     (bool)  — deal requires classified document handling
        past_performance_gaps   (int)   — count of past performance gaps on record
        compliance_history_score (float) — 0.0–1.0 historical compliance score

    policy keys used here:
        hitl_risk_threshold     (float, default 0.6)
        always_hitl_if_legal_max (bool, default True)
    """
    # --- Deadline risk ---
    days_remaining = float(deal_context.get("days_remaining", 30))
    days_needed_estimate = float(deal_context.get("days_needed_estimate", 20))
    deadline = compute_deadline_risk(days_remaining, days_needed_estimate)

    # --- Compliance risk ---
    compliance_coverage_pct = float(deal_context.get("compliance_coverage_pct", 1.0))
    missing_forms = int(deal_context.get("missing_forms", 0))
    compliance = compute_compliance_risk(compliance_coverage_pct, missing_forms)

    # --- Legal risk ---
    prohibited_clauses = int(deal_context.get("prohibited_clauses", 0))
    review_clauses = int(deal_context.get("review_clauses", 0))
    legal = compute_legal_risk(prohibited_clauses, review_clauses)

    # --- Financial risk ---
    margin_pct = float(deal_context.get("margin_pct", 0.15))
    margin_floor = float(deal_context.get("margin_floor", 0.08))
    price_uncertainty = float(deal_context.get("price_uncertainty", 0.2))
    assumption_weakness = float(deal_context.get("assumption_weakness", 0.0))
    financial = compute_financial_risk(
        margin_pct, margin_floor, price_uncertainty, assumption_weakness
    )

    # --- Security risk ---
    has_cui = bool(deal_context.get("has_cui", False))
    has_itar = bool(deal_context.get("has_itar", False))
    classified_handling = bool(deal_context.get("classified_handling", False))
    security = compute_security_risk(has_cui, has_itar, classified_handling)

    # --- Reputation risk ---
    past_performance_gaps = int(deal_context.get("past_performance_gaps", 0))
    compliance_history_score = float(deal_context.get("compliance_history_score", 1.0))
    reputation = compute_reputation_risk(past_performance_gaps, compliance_history_score)

    # --- Composite ---
    composite = compute_composite_risk(legal, compliance, deadline, financial, security, reputation)

    return RiskAssessment(
        legal=legal,
        compliance=compliance,
        deadline=deadline,
        financial=financial,
        security=security,
        reputation=reputation,
        composite=composite,
        metadata={
            "deal_context_snapshot": {
                "days_remaining": days_remaining,
                "days_needed_estimate": days_needed_estimate,
                "compliance_coverage_pct": compliance_coverage_pct,
                "missing_forms": missing_forms,
                "prohibited_clauses": prohibited_clauses,
                "review_clauses": review_clauses,
                "margin_pct": margin_pct,
                "margin_floor": margin_floor,
                "price_uncertainty": price_uncertainty,
                "assumption_weakness": assumption_weakness,
                "has_cui": has_cui,
                "has_itar": has_itar,
                "classified_handling": classified_handling,
                "past_performance_gaps": past_performance_gaps,
                "compliance_history_score": compliance_history_score,
            }
        },
    )
