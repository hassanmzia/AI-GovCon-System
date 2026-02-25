"""Security gap analyzer: identifies compliance gaps and generates remediation plans."""
import logging
from typing import Any

logger = logging.getLogger("ai_deal_manager.security.gap_analyzer")


def analyze_compliance_gaps(
    current_controls: list[str],
    required_controls: list[str],
    framework: str = "NIST_800_53",
) -> dict[str, Any]:
    """Identify gaps between current and required security controls.

    Args:
        current_controls: List of currently implemented control IDs.
        required_controls: List of required control IDs for compliance.
        framework: Framework context for enrichment.

    Returns:
        Dict with: missing_controls, implemented, partially_implemented,
                   gap_count, compliance_score, remediation_priority.
    """
    from backend.apps.security_compliance.services.control_mapper import get_control_details

    current_set = {c.upper() for c in current_controls}
    required_set = {c.upper() for c in required_controls}

    missing = required_set - current_set
    implemented = required_set & current_set
    extra = current_set - required_set  # implemented but not required

    # Enrich missing controls with details
    missing_details = []
    for ctrl_id in sorted(missing):
        ctrl = get_control_details(ctrl_id)
        priority = _assign_priority(ctrl_id, ctrl)
        missing_details.append({
            "control_id": ctrl_id,
            "title": ctrl.get("title", ""),
            "family": ctrl.get("family", ""),
            "priority": priority,
            "estimated_effort": _estimate_effort(ctrl_id),
            "risk_level": _assess_risk_level(ctrl_id),
        })

    # Sort by priority
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    missing_details.sort(key=lambda x: priority_order.get(x["priority"], 99))

    compliance_score = (len(implemented) / len(required_set) * 100) if required_set else 100.0

    return {
        "framework": framework,
        "required_count": len(required_set),
        "implemented_count": len(implemented),
        "missing_count": len(missing),
        "extra_count": len(extra),
        "compliance_score": round(compliance_score, 1),
        "compliance_level": _classify_compliance_score(compliance_score),
        "missing_controls": missing_details,
        "implemented_controls": sorted(implemented),
        "gap_count": len(missing),
        "remediation_priority": missing_details[:10],  # top 10 to fix first
        "effort_estimate": _total_effort_estimate(missing_details),
    }


def generate_remediation_plan(
    gaps: list[dict[str, Any]],
    timeline_weeks: int = 52,
) -> dict[str, Any]:
    """Generate a phased remediation plan from gap analysis results.

    Returns:
        Dict with: phases (list of phase dicts), total_controls, timeline_weeks.
    """
    critical = [g for g in gaps if g.get("priority") == "critical"]
    high = [g for g in gaps if g.get("priority") == "high"]
    medium = [g for g in gaps if g.get("priority") == "medium"]
    low = [g for g in gaps if g.get("priority") == "low"]

    phases = []

    if critical:
        phases.append({
            "phase": 1,
            "name": "Critical Remediation",
            "duration_weeks": min(8, timeline_weeks // 4),
            "controls": critical,
            "objective": "Address all critical security gaps immediately",
            "success_criteria": f"All {len(critical)} critical controls implemented and tested",
        })

    if high:
        phases.append({
            "phase": 2,
            "name": "High-Priority Remediation",
            "duration_weeks": min(12, timeline_weeks // 3),
            "controls": high,
            "objective": "Implement high-priority controls",
            "success_criteria": f"All {len(high)} high-priority controls operational",
        })

    if medium:
        phases.append({
            "phase": 3,
            "name": "Standard Compliance",
            "duration_weeks": min(16, timeline_weeks // 2),
            "controls": medium,
            "objective": "Complete medium-priority control implementation",
            "success_criteria": f"All {len(medium)} medium controls deployed",
        })

    if low:
        phases.append({
            "phase": 4,
            "name": "Optimization",
            "duration_weeks": timeline_weeks // 4,
            "controls": low,
            "objective": "Implement remaining controls and optimize",
            "success_criteria": f"Full compliance achieved",
        })

    return {
        "phases": phases,
        "total_controls": len(gaps),
        "timeline_weeks": timeline_weeks,
        "estimated_completion_weeks": sum(p["duration_weeks"] for p in phases),
        "summary": f"{len(phases)}-phase remediation plan covering {len(gaps)} controls",
    }


def assess_fedramp_readiness(
    current_controls: list[str],
    fedramp_level: str = "moderate",
) -> dict[str, Any]:
    """Assess FedRAMP readiness at a given impact level."""
    from backend.apps.security_compliance.services.cross_walker import get_fedramp_baseline

    required = get_fedramp_baseline(fedramp_level)
    gaps = analyze_compliance_gaps(current_controls, required, f"FedRAMP_{fedramp_level.capitalize()}")

    readiness_level = "not_ready"
    score = gaps["compliance_score"]
    if score >= 95:
        readiness_level = "ready"
    elif score >= 80:
        readiness_level = "substantially_ready"
    elif score >= 60:
        readiness_level = "partially_ready"

    return {
        **gaps,
        "fedramp_level": fedramp_level,
        "readiness_level": readiness_level,
        "authorization_recommendation": _fedramp_auth_recommendation(readiness_level, score),
    }


# ── Helpers ────────────────────────────────────────────────────────────────────

_CRITICAL_CONTROLS = {"IA-2", "AC-2", "AC-3", "AU-2", "SC-7", "SC-8", "SC-28", "SI-2", "SI-3", "IR-4"}
_HIGH_CONTROLS = {"AC-17", "AU-12", "CM-2", "CM-6", "CM-7", "IA-5", "IR-6", "RA-3"}


def _assign_priority(ctrl_id: str, ctrl: dict) -> str:
    if ctrl_id in _CRITICAL_CONTROLS:
        return "critical"
    if ctrl_id in _HIGH_CONTROLS:
        return "high"
    family = ctrl_id.split("-")[0]
    if family in ("AC", "IA", "SI", "SC"):
        return "high"
    if family in ("AU", "CM", "IR"):
        return "medium"
    return "low"


def _estimate_effort(ctrl_id: str) -> str:
    high_effort = {"PL-2", "CA-3", "SA-9"}
    if ctrl_id in high_effort:
        return "high (4+ weeks)"
    if ctrl_id in _CRITICAL_CONTROLS:
        return "medium (1-3 weeks)"
    return "low (< 1 week)"


def _assess_risk_level(ctrl_id: str) -> str:
    if ctrl_id in _CRITICAL_CONTROLS:
        return "high"
    if ctrl_id in _HIGH_CONTROLS:
        return "medium"
    return "low"


def _classify_compliance_score(score: float) -> str:
    if score >= 95:
        return "compliant"
    if score >= 80:
        return "substantially_compliant"
    if score >= 60:
        return "partially_compliant"
    return "non_compliant"


def _total_effort_estimate(missing: list[dict]) -> str:
    high_count = sum(1 for m in missing if "high" in m.get("estimated_effort", ""))
    medium_count = sum(1 for m in missing if "medium" in m.get("estimated_effort", ""))
    weeks = high_count * 4 + medium_count * 2 + (len(missing) - high_count - medium_count)
    if weeks > 52:
        return f"~{weeks // 4} months"
    return f"~{weeks} weeks"


def _fedramp_auth_recommendation(readiness: str, score: float) -> str:
    if readiness == "ready":
        return "Proceed with 3PAO assessment"
    if readiness == "substantially_ready":
        return "Address remaining gaps before initiating 3PAO assessment"
    if readiness == "partially_ready":
        return "Significant remediation required before FedRAMP authorization"
    return "Not ready for FedRAMP – comprehensive security program build-out required"
