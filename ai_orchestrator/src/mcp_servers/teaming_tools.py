"""MCP tool server: Partner search, team composition, SB analysis, work-share optimization."""
import logging
import os
from typing import Any

import httpx

logger = logging.getLogger("ai_orchestrator.mcp.teaming")

_DJANGO_URL = os.getenv("DJANGO_API_URL", "http://django-api:8001")
_SERVICE_TOKEN = os.getenv("DJANGO_SERVICE_TOKEN", "")


def _headers() -> dict:
    return {"Authorization": f"Bearer {_SERVICE_TOKEN}"} if _SERVICE_TOKEN else {}


async def search_partners(
    capability_query: str,
    naics: list[str] | None = None,
    clearance_level: str | None = None,
    sb_status: list[str] | None = None,
    exclude_competitors: list[str] | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Search the partner database for teaming candidates.

    Args:
        capability_query: Description of capabilities needed.
        naics: NAICS codes required.
        clearance_level: Minimum clearance level ("Secret", "TS", "TS/SCI").
        sb_status: Required SB certifications (e.g. ["SDB", "WOSB", "HUBZone"]).
        exclude_competitors: Company names to exclude (conflict / competitor list).
        limit: Max results.

    Returns:
        List of matching partners ranked by relevance and reliability score.
    """
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                f"{_DJANGO_URL}/api/teaming/partners/search/",
                json={
                    "query": capability_query,
                    "naics": naics or [],
                    "clearance_level": clearance_level,
                    "sb_status": sb_status or [],
                    "exclude": exclude_competitors or [],
                    "limit": limit,
                },
                headers=_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("Partner search failed: %s", exc)
        return []


async def get_partner_profile(partner_id: str) -> dict[str, Any]:
    """Fetch complete partner profile including capabilities, past performance, and risk indicators.

    Args:
        partner_id: Partner UUID from the teaming database.

    Returns:
        Full partner profile dict with capabilities, clearances, SB status, CPARS, reliability score.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{_DJANGO_URL}/api/teaming/partners/{partner_id}/",
                headers=_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("Partner profile fetch failed for %s: %s", partner_id, exc)
        return {"id": partner_id, "error": str(exc)}


async def optimize_team_composition(
    opportunity_id: str,
    required_capabilities: list[str],
    sb_goals: dict[str, float] | None = None,
    max_partners: int = 4,
) -> dict[str, Any]:
    """Recommend optimal team composition for an opportunity.

    Args:
        opportunity_id: Opportunity UUID.
        required_capabilities: List of capability areas needed.
        sb_goals: SB goal targets (e.g. {"SDB": 0.05, "WOSB": 0.05}).
        max_partners: Maximum number of teaming partners (excluding prime).

    Returns:
        Dict with recommended_team, work_share_matrix, sb_compliance, risk_score.
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{_DJANGO_URL}/api/teaming/optimize/",
                json={
                    "opportunity_id": opportunity_id,
                    "required_capabilities": required_capabilities,
                    "sb_goals": sb_goals or {},
                    "max_partners": max_partners,
                },
                headers=_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("Team optimization failed for %s: %s", opportunity_id, exc)
        return {"opportunity_id": opportunity_id, "error": str(exc)}


async def analyze_sb_compliance(
    team: list[dict[str, Any]],
    contract_value: float,
    rfp_sb_goals: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Analyze small business compliance for a proposed team.

    Args:
        team: List of team members with name, sb_status, work_share_percent.
        contract_value: Total contract value.
        rfp_sb_goals: SB goals from the RFP (e.g. {"overall": 0.23, "SDB": 0.05}).

    Returns:
        Dict with compliance_status, participation_by_category, gaps, recommendations.
    """
    # Standard SB goals
    standard_goals = {"overall": 0.23, "SDB": 0.05, "WOSB": 0.05, "HUBZone": 0.03, "SDVOSB": 0.03}
    goals = rfp_sb_goals or standard_goals

    participation: dict[str, float] = {cat: 0.0 for cat in goals}
    for member in team:
        if member.get("is_prime"):
            continue
        work_pct = float(member.get("work_share_percent", 0)) / 100.0
        for sb_cert in member.get("sb_certifications", []):
            if sb_cert in participation:
                participation[sb_cert] += work_pct
        if any(member.get("sb_certifications", [])):
            participation["overall"] = participation.get("overall", 0) + work_pct

    gaps = {}
    for cat, target in goals.items():
        actual = participation.get(cat, 0.0)
        if actual < target:
            gaps[cat] = {"target": target, "actual": actual, "shortfall": target - actual}

    recommendations = []
    for cat, gap in gaps.items():
        recommendations.append(
            f"Add a {cat} partner contributing at least {gap['shortfall']*100:.1f}% of work share"
        )

    return {
        "compliance_status": "compliant" if not gaps else "non_compliant",
        "participation_by_category": participation,
        "goals": goals,
        "gaps": gaps,
        "recommendations": recommendations,
        "contract_value": contract_value,
    }


async def generate_teaming_agreement(
    prime_name: str,
    partner_name: str,
    agreement_type: str = "teaming",
    deal_id: str | None = None,
    work_scope: str | None = None,
) -> dict[str, Any]:
    """Generate a teaming agreement document.

    Args:
        prime_name: Prime contractor company name.
        partner_name: Subcontractor/partner company name.
        agreement_type: "nda", "loi", "teaming", "subcontract".
        deal_id: Optional deal UUID for context.
        work_scope: Description of partner's work scope.

    Returns:
        Dict with document_text (draft), key_terms, next_steps.
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{_DJANGO_URL}/api/teaming/generate-agreement/",
                json={
                    "prime_name": prime_name,
                    "partner_name": partner_name,
                    "agreement_type": agreement_type,
                    "deal_id": deal_id,
                    "work_scope": work_scope or "",
                },
                headers=_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("Agreement generation failed: %s", exc)
        return {
            "prime_name": prime_name,
            "partner_name": partner_name,
            "agreement_type": agreement_type,
            "document_text": _agreement_template(prime_name, partner_name, agreement_type),
            "error": str(exc),
        }


async def assess_teaming_risk(
    partner_id: str,
    deal_id: str | None = None,
) -> dict[str, Any]:
    """Assess risk for a specific teaming partner.

    Args:
        partner_id: Partner UUID.
        deal_id: Optional deal UUID for context.

    Returns:
        Dict with risk_score (0-10), risk_factors, mitigations.
    """
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                f"{_DJANGO_URL}/api/teaming/risk-assessment/",
                json={"partner_id": partner_id, "deal_id": deal_id},
                headers=_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("Teaming risk assessment failed: %s", exc)
        return {
            "partner_id": partner_id,
            "risk_score": None,
            "risk_factors": [],
            "error": str(exc),
        }


async def check_oci_for_team(
    team_members: list[dict[str, Any]],
    opportunity_id: str,
) -> dict[str, Any]:
    """Check for OCI issues within the proposed team.

    Args:
        team_members: List of team member dicts with company_name and role.
        opportunity_id: Opportunity UUID.

    Returns:
        Dict with oci_issues (list), affected_members, recommendations.
    """
    issues = []
    for member in team_members:
        from src.mcp_servers.legal_tools import oci_assessment

        result = await oci_assessment(
            company_name=member.get("company_name", ""),
            opportunity_id=opportunity_id,
        )
        if result.get("oci_risk") not in ("none", "low", None):
            issues.append(
                {
                    "company": member.get("company_name"),
                    "oci_risk": result.get("oci_risk"),
                    "oci_types": result.get("oci_types", []),
                }
            )

    return {
        "opportunity_id": opportunity_id,
        "oci_issues": issues,
        "team_clear": len(issues) == 0,
        "recommendations": [
            f"Address OCI for {i['company']}: {', '.join(i['oci_types'])}" for i in issues
        ],
    }


# ── Internal helpers ──────────────────────────────────────────────────────────

def _agreement_template(prime: str, partner: str, agreement_type: str) -> str:
    if agreement_type == "nda":
        return f"""MUTUAL NON-DISCLOSURE AGREEMENT

This Agreement is entered into between {prime} ("Prime") and {partner} ("Partner").

1. PURPOSE: The parties wish to explore a teaming arrangement and may exchange confidential information.
2. CONFIDENTIAL INFORMATION: Each party agrees to protect the other's confidential information.
3. TERM: This agreement is effective for 3 years from the date of execution.
4. GOVERNING LAW: This agreement shall be governed by the laws of the United States.

[Signature blocks to be added]
"""
    if agreement_type == "teaming":
        return f"""TEAMING AGREEMENT

This Teaming Agreement is entered into between {prime} ("Prime") and {partner} ("Subcontractor").

1. PURPOSE: Explore and pursue contract opportunities together.
2. ROLES: Prime will serve as the prime contractor; Partner will serve as subcontractor.
3. WORK SHARE: To be defined per opportunity.
4. EXCLUSIVITY: Limited to the specific opportunity identified herein.
5. TERM: This agreement expires 18 months from execution or upon contract award, whichever is later.

[Key terms and signatures to be completed]
"""
    return f"[{agreement_type.upper()} TEMPLATE FOR {prime} AND {partner}]"
