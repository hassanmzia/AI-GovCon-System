"""Legal analysis quality evaluation service (DeepEval-inspired A-F grading)."""
import logging
from typing import Any

logger = logging.getLogger(__name__)


def evaluate_legal_analysis(
    analysis: dict[str, Any],
    analysis_type: str,
) -> dict[str, Any]:
    """Grade a legal analysis on A-F scale.

    Args:
        analysis: The legal analysis output to evaluate.
        analysis_type: Type of analysis ("rfp_review", "contract_review", "compliance_check",
                       "oci_assessment", "protest_viability").

    Returns:
        Dict with grade (A-F), score (0-100), criteria_scores, feedback.
    """
    criteria = _get_criteria(analysis_type)
    criteria_scores: dict[str, int] = {}
    total = 0
    max_total = 0

    for criterion, weight in criteria.items():
        score = _score_criterion(analysis, criterion, analysis_type)
        weighted_score = int(score * weight)
        criteria_scores[criterion] = weighted_score
        total += weighted_score
        max_total += weight

    final_score = int((total / max(1, max_total)) * 100)
    grade = _score_to_grade(final_score)

    return {
        "grade": grade,
        "score": final_score,
        "analysis_type": analysis_type,
        "criteria_scores": criteria_scores,
        "strengths": _identify_strengths(analysis, analysis_type),
        "weaknesses": _identify_weaknesses(analysis, analysis_type),
        "feedback": _generate_feedback(grade, analysis_type),
        "pass": final_score >= 60,
    }


# ── Criteria definitions ──────────────────────────────────────────────────────

def _get_criteria(analysis_type: str) -> dict[str, int]:
    base = {
        "completeness": 25,
        "accuracy": 30,
        "actionability": 20,
        "risk_identification": 15,
        "citation_quality": 10,
    }
    overrides = {
        "rfp_review": {
            "completeness": 20,
            "accuracy": 25,
            "actionability": 25,
            "risk_identification": 20,
            "citation_quality": 10,
        },
        "contract_review": {
            "completeness": 25,
            "accuracy": 30,
            "actionability": 20,
            "risk_identification": 20,
            "citation_quality": 5,
        },
        "oci_assessment": {
            "completeness": 20,
            "accuracy": 30,
            "risk_identification": 30,
            "actionability": 15,
            "citation_quality": 5,
        },
    }
    return overrides.get(analysis_type, base)


def _score_criterion(analysis: dict, criterion: str, analysis_type: str) -> float:
    """Score a single criterion (0-1)."""
    if criterion == "completeness":
        # Check required fields are present
        required = {
            "rfp_review": ["risk_summary", "clauses_found", "recommendations"],
            "contract_review": ["high_risk_clauses", "risk_summary", "recommendations"],
            "oci_assessment": ["oci_risk", "oci_types_identified", "mitigation_plan"],
            "protest_viability": ["viable", "grounds", "timeline"],
            "compliance_check": ["all_issues", "compliance_score", "recommendations"],
        }.get(analysis_type, ["recommendations"])

        present = sum(1 for f in required if analysis.get(f))
        return present / max(1, len(required))

    if criterion == "accuracy":
        # Check for FAR references and specific clause numbers
        has_far_ref = bool(
            analysis.get("far_references")
            or analysis.get("far_dfars_clauses_found")
            or any(
                "FAR" in str(v) or "DFARS" in str(v)
                for v in analysis.values()
                if isinstance(v, (str, list))
            )
        )
        return 0.9 if has_far_ref else 0.5

    if criterion == "actionability":
        recs = analysis.get("recommendations") or analysis.get("recommended_actions", [])
        if isinstance(recs, list) and len(recs) >= 3:
            return 1.0
        if isinstance(recs, list) and len(recs) >= 1:
            return 0.7
        if isinstance(recs, str) and len(recs) > 50:
            return 0.7
        return 0.3

    if criterion == "risk_identification":
        risk = analysis.get("oci_risk") or analysis.get("overall_risk") or analysis.get("risk_level")
        has_risk = risk is not None and risk != "unknown"
        issues = analysis.get("all_issues") or analysis.get("high_risk_clauses") or analysis.get("grounds")
        has_issues = bool(issues)
        score = 0.0
        if has_risk:
            score += 0.5
        if has_issues:
            score += 0.5
        return score

    if criterion == "citation_quality":
        text = str(analysis)
        # Check for specific legal citations
        has_far = "52." in text or "FAR" in text
        has_dfars = "252." in text or "DFARS" in text
        has_usc = "U.S.C." in text or "C.F.R." in text
        count = sum([has_far, has_dfars, has_usc])
        return min(1.0, count / 2)

    return 0.5  # default


def _score_to_grade(score: int) -> str:
    if score >= 93:
        return "A"
    if score >= 83:
        return "B"
    if score >= 73:
        return "C"
    if score >= 63:
        return "D"
    return "F"


def _identify_strengths(analysis: dict, analysis_type: str) -> list[str]:
    strengths = []
    if analysis.get("recommendations") and len(analysis.get("recommendations", [])) >= 3:
        strengths.append("Provides actionable recommendations")
    if analysis.get("far_references") or "FAR" in str(analysis):
        strengths.append("Cites relevant FAR/DFARS provisions")
    if analysis.get("risk_level") or analysis.get("overall_risk") or analysis.get("oci_risk"):
        strengths.append("Clearly identifies risk level")
    return strengths or ["Analysis structure is complete"]


def _identify_weaknesses(analysis: dict, analysis_type: str) -> list[str]:
    weaknesses = []
    if not analysis.get("recommendations"):
        weaknesses.append("Missing actionable recommendations")
    if not analysis.get("far_references") and "FAR" not in str(analysis):
        weaknesses.append("Lacks specific FAR/DFARS citations")
    return weaknesses or []


def _generate_feedback(grade: str, analysis_type: str) -> str:
    feedback_map = {
        "A": f"Excellent {analysis_type.replace('_', ' ')}. Comprehensive coverage with specific citations and actionable guidance.",
        "B": f"Good {analysis_type.replace('_', ' ')}. Covers key areas but could benefit from more specific legal citations.",
        "C": f"Adequate {analysis_type.replace('_', ' ')}. Consider adding more detail and specific FAR references.",
        "D": f"Below standard {analysis_type.replace('_', ' ')}. Missing critical elements – needs significant improvement.",
        "F": f"Insufficient {analysis_type.replace('_', ' ')}. Does not meet minimum standards for legal analysis.",
    }
    return feedback_map.get(grade, f"Analysis quality: {grade}")
