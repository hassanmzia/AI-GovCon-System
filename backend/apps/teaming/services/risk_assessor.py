"""Teaming risk assessment service."""
import logging
from typing import Any

logger = logging.getLogger(__name__)


async def assess_partner_risk(
    partner: dict[str, Any],
    opportunity: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Assess risk for a specific teaming partner.

    Risk factors assessed:
    - Performance risk (CPARS ratings, past performance issues)
    - Financial risk (size, stability indicators)
    - Clearance risk (clearance expiry, adjudication issues)
    - OCI risk (conflicts with this opportunity)
    - Dependency risk (too much reliance on one partner)
    - Key personnel risk (key people leaving)
    - Exclusivity risk (partner bidding with competitors)
    - SB certification expiry risk
    - CMMC compliance risk (if applicable)

    Returns:
        Dict with risk_score (0-10), risk_level, risk_factors, mitigations.
    """
    risk_factors: list[dict] = []
    total_risk = 0.0

    # Performance risk
    reliability = float(partner.get("reliability_score", 5) or 5)
    if reliability < 3:
        risk_factors.append(
            {
                "category": "performance",
                "severity": "high",
                "description": f"Low reliability score ({reliability}/10)",
                "mitigation": "Request recent CPARS ratings and past performance references",
                "weight": 2.0,
            }
        )
        total_risk += 2.5
    elif reliability < 6:
        risk_factors.append(
            {
                "category": "performance",
                "severity": "medium",
                "description": f"Below average reliability score ({reliability}/10)",
                "mitigation": "Conduct due diligence on recent performance",
                "weight": 1.0,
            }
        )
        total_risk += 1.0

    # CPARS risk
    if partner.get("has_cpars_issues"):
        risk_factors.append(
            {
                "category": "cpars",
                "severity": "high",
                "description": "Partner has documented CPARS performance issues",
                "mitigation": "Review specific CPARS issues and obtain written remediation plan",
                "weight": 2.5,
            }
        )
        total_risk += 2.5

    # SB certification expiry
    if partner.get("is_small_business") and partner.get("sb_cert_expiry_warning"):
        risk_factors.append(
            {
                "category": "sb_certification",
                "severity": "medium",
                "description": "SB certification(s) expiring within 6 months",
                "mitigation": "Confirm renewal is in progress before committing to SB goals",
                "weight": 1.5,
            }
        )
        total_risk += 1.5

    # Clearance risk
    if opportunity and opportunity.get("clearance_required"):
        partner_clearance = partner.get("max_clearance_level", "None")
        required_clearance = opportunity.get("clearance_required", "None")
        clearance_levels = {"None": 0, "Public Trust": 1, "Secret": 2, "TS": 3, "TS/SCI": 4}
        if clearance_levels.get(partner_clearance, 0) < clearance_levels.get(required_clearance, 0):
            risk_factors.append(
                {
                    "category": "clearance",
                    "severity": "critical",
                    "description": f"Partner lacks required {required_clearance} clearance",
                    "mitigation": "Find alternative partner with required clearance level",
                    "weight": 3.0,
                }
            )
            total_risk += 3.0

    # Key personnel risk
    if partner.get("high_personnel_turnover"):
        risk_factors.append(
            {
                "category": "key_personnel",
                "severity": "medium",
                "description": "Partner has high personnel turnover rate",
                "mitigation": "Require key personnel commitment letters; include retention incentives",
                "weight": 1.0,
            }
        )
        total_risk += 1.0

    # Financial risk
    if partner.get("financial_risk_flag"):
        risk_factors.append(
            {
                "category": "financial",
                "severity": "high",
                "description": "Financial stability concerns identified",
                "mitigation": "Request financial statements; consider payment holds or bonds",
                "weight": 2.0,
            }
        )
        total_risk += 2.0

    # Exclusive partner risk
    if partner.get("non_exclusive"):
        risk_factors.append(
            {
                "category": "exclusivity",
                "severity": "medium",
                "description": "Partner may be pursuing the same opportunity with competitors",
                "mitigation": "Negotiate exclusivity agreement before sharing sensitive information",
                "weight": 1.5,
            }
        )
        total_risk += 1.5

    # Normalize to 0-10 scale
    risk_score = min(10.0, total_risk)
    risk_level = _score_to_level(risk_score)

    return {
        "partner_name": partner.get("company_name", "Unknown"),
        "risk_score": round(risk_score, 1),
        "risk_level": risk_level,
        "risk_factors": risk_factors,
        "critical_factors": [f for f in risk_factors if f["severity"] == "critical"],
        "mitigations": [f["mitigation"] for f in risk_factors],
        "recommendation": _risk_recommendation(risk_level),
    }


async def assess_team_risk(
    team_members: list[dict[str, Any]],
    opportunity: dict[str, Any],
) -> dict[str, Any]:
    """Assess overall risk for the proposed team.

    Returns:
        Dict with team_risk_score, high_risk_partners, recommendations.
    """
    import asyncio

    subs = [m for m in team_members if not m.get("is_prime")]
    partner_risks = await asyncio.gather(
        *[assess_partner_risk(p, opportunity) for p in subs]
    )

    high_risk = [r for r in partner_risks if r["risk_level"] in ("high", "critical")]
    avg_risk = sum(r["risk_score"] for r in partner_risks) / max(1, len(partner_risks))

    # Check for OCI within team
    oci_check = await _check_team_oci(team_members, opportunity)

    # Dependency risk – any single partner > 40% of work
    dependency_risk = any(
        float(m.get("work_share_pct", 0) or 0) > 40 for m in subs
    )

    return {
        "team_risk_score": round(avg_risk, 1),
        "team_risk_level": _score_to_level(avg_risk),
        "individual_partner_risks": partner_risks,
        "high_risk_partners": high_risk,
        "oci_issues": oci_check,
        "dependency_risk": dependency_risk,
        "recommendations": _team_risk_recommendations(high_risk, oci_check, dependency_risk),
    }


# ── Internal helpers ──────────────────────────────────────────────────────────

def _score_to_level(score: float) -> str:
    if score >= 7:
        return "critical"
    if score >= 5:
        return "high"
    if score >= 3:
        return "medium"
    return "low"


def _risk_recommendation(level: str) -> str:
    recommendations = {
        "low": "Partner looks good – proceed with teaming discussions",
        "medium": "Proceed with caution – address identified risk factors",
        "high": "Consider alternative partners – significant risk factors identified",
        "critical": "Do not proceed without resolving critical risk factors",
    }
    return recommendations.get(level, "Review risk factors before proceeding")


def _team_risk_recommendations(
    high_risk: list,
    oci: dict,
    dependency: bool,
) -> list[str]:
    recs = []
    for p in high_risk[:2]:
        recs.append(
            f"Address risk for {p.get('partner_name', 'partner')}: "
            f"{', '.join(m for m in p.get('mitigations', [])[:1])}"
        )
    if oci.get("has_oci"):
        recs.append("Resolve OCI issues before finalizing team")
    if dependency:
        recs.append("Reduce dependency risk – no single partner should exceed 40% work share")
    return recs or ["Team risk is acceptable – proceed with team formation"]


async def _check_team_oci(team: list[dict], opportunity: dict) -> dict:
    """Quick OCI check across team members."""
    try:
        from apps.legal.services.oci_assessor import assess_oci_risk

        oci_results = []
        for member in team:
            result = await assess_oci_risk(
                company_name=member.get("company_name", ""),
                opportunity_id=opportunity.get("id", ""),
                work_description=opportunity.get("description", ""),
            )
            if result.get("oci_risk") not in ("none", None):
                oci_results.append(result)

        return {
            "has_oci": bool(oci_results),
            "oci_count": len(oci_results),
            "oci_details": oci_results,
        }
    except Exception:
        return {"has_oci": False, "oci_count": 0, "oci_details": []}
