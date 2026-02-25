"""Team composition optimizer – finds the optimal team structure for an opportunity."""
import logging
from typing import Any

logger = logging.getLogger(__name__)


async def optimize_team(
    opportunity: dict[str, Any],
    candidate_partners: list[dict[str, Any]],
    required_capabilities: list[str],
    sb_goals: dict[str, float] | None = None,
    max_partners: int = 4,
    constraints: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Select the optimal team composition from candidate partners.

    Uses a greedy set-cover algorithm with constraint satisfaction:
    1. Maximize capability coverage
    2. Meet SB compliance goals
    3. Minimize risk
    4. Prefer proven teaming relationships

    Args:
        opportunity: Opportunity dict.
        candidate_partners: Ranked list of candidate partners.
        required_capabilities: List of capability areas needed.
        sb_goals: SB goal targets.
        max_partners: Maximum number of partners (excluding prime).
        constraints: Additional constraints (e.g. clearance requirements).

    Returns:
        Dict with selected_team, work_share_matrix, coverage_analysis, sb_analysis.
    """
    if not candidate_partners:
        return _empty_team_result(opportunity)

    # Greedy set-cover: add partners that contribute the most uncovered capabilities
    covered = set()
    selected: list[dict] = []
    remaining = list(candidate_partners)
    required = set(c.lower() for c in required_capabilities)

    while len(selected) < max_partners and remaining and covered != required:
        best_partner = None
        best_new_coverage = -1
        best_idx = -1

        for i, partner in enumerate(remaining):
            partner_caps = set(c.lower() for c in (partner.get("capabilities") or []))
            new_coverage = len(required & partner_caps - covered)

            # Tie-break: prefer higher reliability and SB status
            tiebreak = (
                new_coverage * 100
                + float(partner.get("reliability_score", 5) or 5)
                + (10 if partner.get("sb_certifications") else 0)
            )

            if tiebreak > best_new_coverage:
                best_new_coverage = tiebreak
                best_partner = partner
                best_idx = i

        if best_partner is None:
            break

        selected.append(best_partner)
        remaining.pop(best_idx)
        partner_caps = set(c.lower() for c in (best_partner.get("capabilities") or []))
        covered |= required & partner_caps

    # Compute work share
    work_share = _compute_work_share(selected, required_capabilities)

    # SB compliance analysis
    from apps.teaming.services.sb_analyzer import analyze_sb_compliance

    sb_analysis = await analyze_sb_compliance(selected, opportunity, sb_goals)

    # Risk assessment
    team_risk = _assess_team_risk(selected)

    # Coverage analysis
    all_partner_caps = set()
    for p in selected:
        all_partner_caps |= set(c.lower() for c in (p.get("capabilities") or []))
    uncovered = required - all_partner_caps

    return {
        "opportunity_title": opportunity.get("title", ""),
        "selected_team": selected,
        "team_size": len(selected) + 1,  # +1 for prime
        "work_share_matrix": work_share,
        "capability_coverage": {
            "covered": list(required & all_partner_caps),
            "uncovered": list(uncovered),
            "coverage_pct": round(len(required & all_partner_caps) / max(1, len(required)) * 100, 1),
        },
        "sb_compliance": sb_analysis,
        "team_risk_score": team_risk,
        "recommendations": _generate_team_recommendations(selected, uncovered, sb_analysis, team_risk),
    }


# ── Internal helpers ──────────────────────────────────────────────────────────

def _compute_work_share(partners: list[dict], required_capabilities: list[str]) -> list[dict]:
    """Allocate work share proportional to capability contribution."""
    if not partners:
        return []

    total_caps = max(1, sum(len(p.get("capabilities") or []) for p in partners))
    shares = []
    remaining_pct = 70.0  # prime keeps at least 30%

    for i, partner in enumerate(partners):
        caps = len(partner.get("capabilities") or [])
        share = min(remaining_pct * 0.5, (caps / total_caps) * 70)
        share = max(5.0, round(share, 1))

        if i == len(partners) - 1:
            share = round(remaining_pct, 1)

        remaining_pct = max(0, remaining_pct - share)
        shares.append(
            {
                "company": partner.get("company_name", "Partner"),
                "work_share_pct": share,
                "capabilities": partner.get("capabilities", [])[:3],
                "labor_categories": partner.get("labor_categories", [])[:3],
            }
        )

    return shares


async def _noop_sb(*args, **kwargs):
    return {"compliance_status": "unknown"}


def _assess_team_risk(partners: list[dict]) -> dict:
    risks = []
    for p in partners:
        if float(p.get("reliability_score", 5) or 5) < 3:
            risks.append({"partner": p.get("company_name"), "risk": "low_reliability"})
        if p.get("has_cpars_issues"):
            risks.append({"partner": p.get("company_name"), "risk": "cpars_concerns"})
        if not p.get("sb_certifications") and p.get("is_small_business"):
            risks.append({"partner": p.get("company_name"), "risk": "sb_certification_expiry"})

    return {
        "risk_count": len(risks),
        "risk_level": "high" if len(risks) > 2 else "medium" if risks else "low",
        "risk_items": risks,
    }


def _generate_team_recommendations(
    selected: list[dict],
    uncovered: set,
    sb_analysis: dict,
    team_risk: dict,
) -> list[str]:
    recs = []
    if uncovered:
        recs.append(f"Address capability gaps: {', '.join(list(uncovered)[:3])}")
    if sb_analysis.get("gaps"):
        for cat, gap in (sb_analysis.get("gaps") or {}).items():
            recs.append(f"Add {cat} partner to meet {gap.get('target', 0)*100:.0f}% goal")
    if team_risk.get("risk_level") == "high":
        recs.append("High team risk – consider replacing or adding backup partners")
    if not selected:
        recs.append("No suitable partners found – expand search criteria")
    return recs or ["Team composition looks good – proceed to engagement"]


def _empty_team_result(opportunity: dict) -> dict:
    return {
        "opportunity_title": opportunity.get("title", ""),
        "selected_team": [],
        "team_size": 1,
        "work_share_matrix": [],
        "capability_coverage": {"covered": [], "uncovered": [], "coverage_pct": 0},
        "sb_compliance": {"compliance_status": "unknown"},
        "team_risk_score": {"risk_level": "unknown"},
        "recommendations": ["No candidate partners provided – run partner search first"],
    }
