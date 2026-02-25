"""Portfolio analyzer – pipeline health, concentration risk, strategic alignment."""
import logging
from typing import Any

logger = logging.getLogger(__name__)


async def analyze_portfolio(
    company_strategy: dict[str, Any],
    active_deals: list[dict[str, Any]],
) -> dict[str, Any]:
    """Analyze pipeline health vs. strategic goals.

    Args:
        company_strategy: Company strategy dict.
        active_deals: List of active deal dicts.

    Returns:
        Dict with pipeline_health, concentration_risk, strategic_alignment,
               recommendations, capacity_utilization.
    """
    if not active_deals:
        return _empty_portfolio()

    # Pipeline health metrics
    pipeline_value = sum(float(d.get("estimated_value", 0) or 0) for d in active_deals)
    by_stage = _group_by_field(active_deals, "stage")
    by_agency = _group_by_field(active_deals, "agency_name")
    by_naics = _group_by_field(active_deals, "naics_code")

    # Concentration risk
    concentration = _compute_concentration_risk(by_agency, by_naics, pipeline_value, active_deals)

    # Strategic alignment
    alignment = _compute_strategic_alignment(active_deals, company_strategy)

    # Win probability weighted pipeline
    weighted_value = sum(
        float(d.get("estimated_value", 0) or 0) * float(d.get("win_probability", 0.3) or 0.3)
        for d in active_deals
    )

    # Revenue target tracking
    annual_target = float(
        (company_strategy or {}).get("annual_revenue_target", 10_000_000) or 10_000_000
    )
    pipeline_coverage = pipeline_value / max(1, annual_target)

    # Stage distribution
    healthy_stages = {"capture", "proposal_dev", "red_team", "final_review"}
    early_stage = sum(len(v) for k, v in by_stage.items() if k in {"intake", "qualify", "bid_no_bid"})
    active_pursuit = sum(len(v) for k, v in by_stage.items() if k in healthy_stages)

    pipeline_health = _score_pipeline_health(
        pipeline_coverage=pipeline_coverage,
        concentration=concentration,
        alignment_score=alignment["score"],
        active_pursuit_ratio=active_pursuit / max(1, len(active_deals)),
    )

    return {
        "pipeline_value": pipeline_value,
        "weighted_pipeline_value": weighted_value,
        "deal_count": len(active_deals),
        "pipeline_health": pipeline_health,
        "pipeline_coverage_ratio": round(pipeline_coverage, 2),
        "deals_by_stage": {k: len(v) for k, v in by_stage.items()},
        "deals_by_agency": {k: len(v) for k, v in by_agency.items()},
        "deals_by_naics": {k: len(v) for k, v in by_naics.items()},
        "concentration_risk": concentration,
        "strategic_alignment": alignment,
        "revenue_target": annual_target,
        "target_coverage_pct": round(pipeline_coverage * 100, 1),
        "recommendations": _generate_recommendations(
            pipeline_health, concentration, alignment, pipeline_coverage
        ),
    }


async def track_strategic_goals(
    company_strategy: dict[str, Any],
    outcomes: list[dict[str, Any]],
) -> dict[str, Any]:
    """Track progress against strategic goals.

    Args:
        company_strategy: Strategy with goals list.
        outcomes: Recent deal outcomes.

    Returns:
        Dict with goals (list with progress), on_track (bool), lagging_goals.
    """
    goals = company_strategy.get("strategic_goals", [])
    tracked = []

    for goal in goals:
        goal_type = goal.get("metric", "")
        target = float(goal.get("target_value", 0) or 0)

        # Compute current value based on goal type
        if goal_type == "annual_revenue":
            current = sum(
                float(o.get("contract_value", 0) or 0)
                for o in outcomes
                if o.get("outcome_type") == "win"
            )
        elif goal_type == "win_rate":
            wins = sum(1 for o in outcomes if o.get("outcome_type") == "win")
            total = sum(1 for o in outcomes if o.get("outcome_type") in ("win", "loss"))
            current = (wins / max(1, total)) * 100
        elif goal_type == "new_agency_count":
            agencies = set(o.get("agency_name") for o in outcomes if o.get("outcome_type") == "win")
            current = len(agencies)
        else:
            current = 0

        progress = (current / max(1, target)) * 100

        tracked.append(
            {
                **goal,
                "current_value": round(current, 2),
                "progress_pct": round(progress, 1),
                "on_track": progress >= 75,
                "status": "on_track" if progress >= 75 else "at_risk" if progress >= 50 else "lagging",
            }
        )

    lagging = [g for g in tracked if g["status"] == "lagging"]

    return {
        "goals": tracked,
        "on_track": all(g["on_track"] for g in tracked),
        "lagging_goals": lagging,
        "goal_count": len(tracked),
        "on_track_count": sum(1 for g in tracked if g["on_track"]),
    }


# ── Internal helpers ──────────────────────────────────────────────────────────

def _group_by_field(deals: list[dict], field: str) -> dict[str, list]:
    groups: dict[str, list] = {}
    for d in deals:
        key = d.get(field) or "Unknown"
        groups.setdefault(key, []).append(d)
    return groups


def _compute_concentration_risk(
    by_agency: dict,
    by_naics: dict,
    total_value: float,
    deals: list,
) -> dict:
    # Agency concentration
    agency_values = {}
    for agency, agency_deals in by_agency.items():
        agency_values[agency] = sum(float(d.get("estimated_value", 0) or 0) for d in agency_deals)

    top_agency = max(agency_values.items(), key=lambda x: x[1], default=("Unknown", 0))
    top_agency_pct = top_agency[1] / max(1, total_value) * 100

    # NAICS concentration
    naics_counts = {k: len(v) for k, v in by_naics.items()}
    top_naics = max(naics_counts.items(), key=lambda x: x[1], default=("Unknown", 0))
    top_naics_pct = top_naics[1] / max(1, len(deals)) * 100

    # Herfindahl-Hirschman Index (HHI) for agency concentration
    hhi = sum((v / max(1, total_value) * 100) ** 2 for v in agency_values.values())

    return {
        "top_agency": top_agency[0],
        "top_agency_pct": round(top_agency_pct, 1),
        "top_naics": top_naics[0],
        "top_naics_pct": round(top_naics_pct, 1),
        "hhi_score": round(hhi, 0),
        "risk_level": "high" if top_agency_pct > 60 else "medium" if top_agency_pct > 40 else "low",
        "diversification_needed": top_agency_pct > 50,
    }


def _compute_strategic_alignment(deals: list[dict], strategy: dict) -> dict:
    if not strategy:
        return {"score": 0.5, "aligned_count": 0, "misaligned_count": 0}

    target_agencies = [a.lower() for a in (strategy.get("target_agencies") or [])]
    target_naics = strategy.get("target_naics") or []
    target_domains = [d.lower() for d in (strategy.get("target_domains") or [])]

    aligned = 0
    misaligned = 0

    for deal in deals:
        agency = (deal.get("agency_name") or "").lower()
        naics = deal.get("naics_code") or ""
        desc = (deal.get("description") or "").lower()

        is_aligned = (
            any(a in agency for a in target_agencies)
            or naics in target_naics
            or any(d in desc for d in target_domains)
        )

        if is_aligned:
            aligned += 1
        else:
            misaligned += 1

    total = max(1, len(deals))
    score = aligned / total

    return {
        "score": round(score, 2),
        "aligned_count": aligned,
        "misaligned_count": misaligned,
        "alignment_pct": round(score * 100, 1),
        "assessment": "strong" if score > 0.8 else "moderate" if score > 0.5 else "weak",
    }


def _score_pipeline_health(
    pipeline_coverage: float,
    concentration: dict,
    alignment_score: float,
    active_pursuit_ratio: float,
) -> dict:
    score = 0.0
    issues = []
    strengths = []

    # Coverage check (target 3× revenue target in pipeline)
    if pipeline_coverage >= 3.0:
        score += 30
        strengths.append("Pipeline value exceeds 3× annual revenue target")
    elif pipeline_coverage >= 2.0:
        score += 20
    elif pipeline_coverage >= 1.0:
        score += 10
        issues.append("Pipeline coverage below 2× target – pursue more opportunities")
    else:
        issues.append("CRITICAL: Pipeline too thin – immediate action required")

    # Concentration
    if concentration.get("risk_level") == "low":
        score += 25
        strengths.append("Well-diversified agency portfolio")
    elif concentration.get("risk_level") == "medium":
        score += 15
        issues.append("Moderate concentration risk – diversify into additional agencies")
    else:
        score += 5
        issues.append("HIGH concentration risk – over-dependence on single agency")

    # Strategic alignment
    score += int(alignment_score * 25)
    if alignment_score < 0.5:
        issues.append("Many deals outside strategic focus – review bid decisions")

    # Active pursuit ratio
    score += int(active_pursuit_ratio * 20)

    health_level = "excellent" if score >= 80 else "good" if score >= 60 else "fair" if score >= 40 else "poor"

    return {
        "score": score,
        "level": health_level,
        "issues": issues,
        "strengths": strengths,
    }


def _generate_recommendations(
    health: dict,
    concentration: dict,
    alignment: dict,
    coverage: float,
) -> list[str]:
    recs = []
    if coverage < 2.0:
        recs.append("Increase pipeline to achieve 2-3× annual revenue target")
    if concentration.get("diversification_needed"):
        recs.append(f"Diversify away from {concentration.get('top_agency')} – currently {concentration.get('top_agency_pct')}% of pipeline")
    if alignment.get("assessment") == "weak":
        recs.append("Realign bid decisions with company strategy – many deals outside target markets")
    return recs or ["Pipeline is healthy – maintain current pursuit strategy"]


def _empty_portfolio() -> dict:
    return {
        "pipeline_value": 0,
        "deal_count": 0,
        "pipeline_health": {"score": 0, "level": "poor", "issues": ["No active deals"], "strengths": []},
        "concentration_risk": {"risk_level": "n/a"},
        "strategic_alignment": {"score": 0},
        "recommendations": ["Build pipeline by pursuing new opportunities"],
    }
