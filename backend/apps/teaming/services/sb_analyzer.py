"""Small business compliance analyzer for teaming plans."""
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Standard SB program goals (FAR Part 19)
STANDARD_SB_GOALS = {
    "overall": 0.23,
    "SDB": 0.05,
    "WOSB": 0.05,
    "HUBZone": 0.03,
    "SDVOSB": 0.03,
}


async def analyze_sb_compliance(
    team_members: list[dict[str, Any]],
    opportunity: dict[str, Any],
    rfp_sb_goals: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Analyze small business compliance for a proposed team.

    Args:
        team_members: List of team member dicts (prime included).
        opportunity: Opportunity dict.
        rfp_sb_goals: SB goals from the RFP (uses standard if not provided).

    Returns:
        Dict with compliance_status, participation_by_category, gaps, recommendations,
               mentor_protege_opportunities, isp_data.
    """
    goals = rfp_sb_goals or STANDARD_SB_GOALS

    # Separate prime from subs
    prime = next((m for m in team_members if m.get("is_prime")), None)
    subs = [m for m in team_members if not m.get("is_prime")]

    # Compute participation percentages
    participation: dict[str, float] = {cat: 0.0 for cat in goals}
    total_sub_share = 0.0

    for sub in subs:
        work_share = float(sub.get("work_share_pct", 0) or 0) / 100.0
        total_sub_share += work_share
        sb_certs = sub.get("sb_certifications") or []

        for cert in sb_certs:
            if cert in participation:
                participation[cert] += work_share

        if sb_certs:
            participation["overall"] = participation.get("overall", 0.0) + work_share

    # Identify gaps
    gaps: dict[str, dict] = {}
    for category, target in goals.items():
        actual = participation.get(category, 0.0)
        if actual < target:
            gaps[category] = {
                "target": round(target, 4),
                "actual": round(actual, 4),
                "shortfall": round(target - actual, 4),
                "shortfall_pct": round((target - actual) * 100, 2),
            }

    # Generate recommendations
    recommendations = _generate_sb_recommendations(gaps, subs)

    # ISP data
    isp_data = _generate_isp_data(subs, participation, goals)

    # Mentor-protégé opportunities
    mp_opportunities = _identify_mp_opportunities(prime, subs, gaps)

    compliance_status = "compliant" if not gaps else "non_compliant"

    return {
        "compliance_status": compliance_status,
        "participation_by_category": {k: round(v * 100, 2) for k, v in participation.items()},
        "goals": {k: round(v * 100, 2) for k, v in goals.items()},
        "gaps": gaps,
        "gap_count": len(gaps),
        "recommendations": recommendations,
        "isp_data": isp_data,
        "mentor_protege_opportunities": mp_opportunities,
        "total_sub_participation": round(total_sub_share * 100, 2),
        "sb_prime": any(m.get("is_prime") and m.get("sb_certifications") for m in team_members),
    }


async def generate_isp_narrative(
    team_members: list[dict[str, Any]],
    opportunity: dict[str, Any],
    goals: dict[str, float] | None = None,
) -> str:
    """Generate the Individual Subcontracting Plan (ISP) narrative.

    Returns:
        Formatted ISP narrative text.
    """
    analysis = await analyze_sb_compliance(team_members, opportunity, goals)
    participation = analysis["participation_by_category"]
    subs = [m for m in team_members if not m.get("is_prime") and m.get("sb_certifications")]

    lines = [
        "INDIVIDUAL SUBCONTRACTING PLAN",
        f"Contract/Opportunity: {opportunity.get('title', '[Opportunity]')}",
        f"Agency: {opportunity.get('agency_name', '[Agency]')}",
        "",
        "SMALL BUSINESS PARTICIPATION GOALS:",
    ]
    for cat, target in (goals or STANDARD_SB_GOALS).items():
        actual = participation.get(cat, 0)
        lines.append(f"  {cat}: Target {target*100:.1f}%, Planned {actual:.1f}%")

    lines.append("\nSMALL BUSINESS SUBCONTRACTORS:")
    for sub in subs:
        lines.append(
            f"  {sub.get('company_name', 'TBD')}: "
            f"{sub.get('work_share_pct', 0):.1f}% – "
            f"{', '.join(sub.get('sb_certifications', []))}"
        )

    return "\n".join(lines)


async def check_limitation_on_subcontracting(
    prime: dict[str, Any],
    contract_type: str,
    set_aside_type: str | None,
) -> dict[str, Any]:
    """Check FAR 52.219-14 limitations on subcontracting.

    For SB set-asides, the prime must perform a minimum percentage.

    Args:
        prime: Prime contractor dict.
        contract_type: "services", "supplies", "construction", "specialty_construction".
        set_aside_type: Type of set-aside (e.g. "SBA", "8(a)", "WOSB").

    Returns:
        Dict with limit (%), prime_must_perform_pct, compliant, far_reference.
    """
    if not set_aside_type:
        return {"applies": False, "reason": "Not a set-aside contract"}

    # FAR 52.219-14 percentages
    limits = {
        "services": {"prime_minimum": 0.50, "description": "Prime must perform ≥50% of the cost of services"},
        "supplies": {"prime_minimum": 0.50, "description": "Prime must perform ≥50% (or add ≥50% value)"},
        "construction": {"prime_minimum": 0.15, "description": "Prime must self-perform ≥15% of work"},
        "specialty_construction": {"prime_minimum": 0.25, "description": "Prime must self-perform ≥25% of work"},
    }

    limit_info = limits.get(contract_type, limits["services"])
    prime_work_pct = float(prime.get("work_share_pct", 51) or 51) / 100.0

    return {
        "applies": True,
        "set_aside_type": set_aside_type,
        "prime_minimum_pct": round(limit_info["prime_minimum"] * 100, 0),
        "prime_planned_pct": round(prime_work_pct * 100, 1),
        "compliant": prime_work_pct >= limit_info["prime_minimum"],
        "description": limit_info["description"],
        "far_reference": "FAR 52.219-14",
    }


# ── Internal helpers ──────────────────────────────────────────────────────────

def _generate_sb_recommendations(gaps: dict, subs: list) -> list[str]:
    recs = []
    for category, gap_info in gaps.items():
        shortfall_pct = gap_info["shortfall_pct"]
        recs.append(
            f"Add a {category} partner contributing at least {shortfall_pct:.1f}% of work share "
            f"to meet the {gap_info['target'] * 100:.0f}% {category} goal"
        )
    if not recs:
        recs.append("Small business participation goals are being met")
    return recs


def _generate_isp_data(
    subs: list,
    participation: dict,
    goals: dict,
) -> dict:
    """Generate Individual Subcontracting Plan data structure."""
    return {
        "total_sb_participation": round(participation.get("overall", 0) * 100, 2),
        "categories": {
            cat: {
                "goal_pct": round(target * 100, 2),
                "planned_pct": round(participation.get(cat, 0) * 100, 2),
            }
            for cat, target in goals.items()
        },
        "sb_subcontractors": [
            {
                "name": s.get("company_name", "TBD"),
                "certifications": s.get("sb_certifications", []),
                "planned_spend_pct": s.get("work_share_pct", 0),
                "naics": s.get("primary_naics", ""),
            }
            for s in subs
            if s.get("sb_certifications")
        ],
    }


def _identify_mp_opportunities(
    prime: dict | None,
    subs: list,
    gaps: dict,
) -> list[dict]:
    """Identify potential mentor-protégé opportunities."""
    opportunities = []
    if not prime:
        return opportunities

    # If prime is large business and there are SB gaps, suggest mentor-protégé
    if not (prime or {}).get("is_small_business") and gaps:
        for cat in list(gaps.keys())[:2]:
            opportunities.append(
                {
                    "type": "mentor_protege",
                    "benefit": f"Establish mentor-protégé with {cat} firm to fill gap and improve ISP",
                    "program": "SBA All Small Mentor-Protégé Program",
                    "far_reference": "FAR 19.705-1",
                }
            )
    return opportunities
