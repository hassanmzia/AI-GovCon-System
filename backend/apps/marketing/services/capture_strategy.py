"""Capture strategy service – win themes, discriminators, ghost strategies, messaging."""
import logging
from typing import Any

logger = logging.getLogger(__name__)


async def generate_capture_strategy(
    deal: dict[str, Any],
    opportunity: dict[str, Any],
    company_strategy: dict[str, Any] | None = None,
    competitor_profiles: list[dict[str, Any]] | None = None,
    agency_profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate a comprehensive capture strategy for a deal.

    Args:
        deal: Deal dict.
        opportunity: Opportunity dict.
        company_strategy: Company strategy dict.
        competitor_profiles: List of competitor profile dicts.
        agency_profile: Agency intelligence profile.

    Returns:
        Capture strategy with value_prop, win_themes, discriminators, ghost_strategies,
        teaming_strategy, messaging_guide, and P(win) assessment.
    """
    opp_title = opportunity.get("title", "Unknown Opportunity")
    agency_name = opportunity.get("agency_name", opportunity.get("department", "Agency"))

    win_themes = _generate_win_themes(opportunity, company_strategy)
    discriminators = _generate_discriminators(company_strategy, competitor_profiles or [])
    ghost_strategies = _generate_ghost_strategies(competitor_profiles or [])

    p_win = _estimate_win_probability(
        deal=deal,
        opportunity=opportunity,
        competitor_count=len(competitor_profiles or []),
        agency_profile=agency_profile,
    )

    return {
        "deal_id": deal.get("id", ""),
        "opportunity_title": opp_title,
        "agency": agency_name,
        "value_proposition": _craft_value_proposition(opportunity, company_strategy),
        "win_themes": win_themes,
        "discriminators": discriminators,
        "ghost_strategies": ghost_strategies,
        "counter_strategies": _generate_counters(competitor_profiles or []),
        "teaming_strategy": _recommend_teaming(opportunity),
        "messaging_guide": _build_messaging_guide(win_themes, discriminators),
        "p_win_assessment": p_win,
        "key_evaluation_criteria": _extract_eval_criteria(opportunity),
        "engagement_plan": _build_engagement_plan(agency_profile),
        "b_and_p_roi_analysis": _estimate_bnp_roi(deal, p_win),
        "shipley_framework_applied": True,
    }


async def generate_win_themes(
    opportunity: dict[str, Any],
    company_strategy: dict[str, Any] | None = None,
    count: int = 5,
) -> list[dict[str, Any]]:
    """Generate compelling win themes for a proposal.

    Args:
        opportunity: Opportunity context.
        company_strategy: Company strategy for alignment.
        count: Number of win themes to generate.

    Returns:
        List of win theme dicts with theme, rationale, and supporting_evidence.
    """
    themes = _generate_win_themes(opportunity, company_strategy)
    return [
        {
            "theme": theme,
            "rationale": f"Addresses key agency need in {opportunity.get('title', 'this opportunity')}",
            "supporting_evidence": "Past performance and demonstrated capability",
            "evaluation_criterion": "Technical Approach",
        }
        for theme in themes[:count]
    ]


async def craft_executive_summary(
    deal: dict[str, Any],
    win_themes: list[str],
    value_proposition: str,
    technical_approach_summary: str,
) -> dict[str, Any]:
    """Craft a Shipley-method executive summary for a proposal.

    Returns:
        Dict with summary_text, word_count, win_themes_addressed, key_differentiators.
    """
    opp = deal.get("opportunity_title", deal.get("title", "this opportunity"))
    agency = deal.get("agency_name", "the Government")

    summary_paragraphs = [
        f"[Company Name] is uniquely positioned to deliver outstanding results for {agency}'s {opp}. "
        f"{value_proposition}",
        "",
        "Our approach is distinguished by:",
    ]
    for theme in win_themes[:3]:
        summary_paragraphs.append(f"• **{theme}**: Demonstrated expertise and proven methodology.")

    summary_paragraphs.extend(
        [
            "",
            f"Our technical approach centers on {technical_approach_summary}",
            "",
            "We are committed to delivering exceptional value, on time and within budget, "
            "with zero defects and full regulatory compliance.",
        ]
    )

    summary_text = "\n".join(summary_paragraphs)

    return {
        "summary_text": summary_text,
        "word_count": len(summary_text.split()),
        "win_themes_addressed": len(win_themes),
        "key_differentiators": win_themes[:3],
        "shipley_compliant": True,
    }


async def estimate_win_probability(
    deal: dict[str, Any],
    opportunity: dict[str, Any],
    factors: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Estimate probability of win for a deal.

    Args:
        deal: Deal dict.
        opportunity: Opportunity dict.
        factors: Override specific factors.

    Returns:
        Dict with p_win (0-1), confidence, key_factors, recommendations.
    """
    return _estimate_win_probability(deal, opportunity, 3, None)


# ── Internal helpers ──────────────────────────────────────────────────────────

def _craft_value_proposition(opp: dict, strategy: dict | None) -> str:
    title = opp.get("title", "this opportunity")
    agency = opp.get("agency_name", "the Government")
    return (
        f"We deliver mission-critical solutions to {agency} through proven expertise, "
        f"innovative technology, and an unwavering commitment to quality. "
        f"Our team brings the ideal combination of domain expertise, technical capabilities, "
        f"and past performance to successfully execute {title}."
    )


def _generate_win_themes(opp: dict, strategy: dict | None) -> list[str]:
    base_themes = [
        "Deep domain expertise and proven past performance",
        "Innovative technical approach leveraging modern technology",
        "Dedicated team with relevant clearances and certifications",
        "Strong program management and quality assurance",
        "Competitive pricing with superior value",
    ]
    naics = opp.get("naics_code", "")
    if naics.startswith("541"):
        base_themes.insert(0, "Elite IT and technology services with measurable mission impact")
    if opp.get("set_aside"):
        base_themes.append("Small business agility with large business resources")

    return base_themes[:5]


def _generate_discriminators(strategy: dict | None, competitors: list[dict]) -> list[str]:
    discriminators = [
        "Proven transition-in methodology with zero mission degradation",
        "Proprietary tools and accelerators that reduce cost and delivery time",
        "Senior-level personnel committed for the full period of performance",
        "Integrated quality management system with continuous improvement",
    ]
    return discriminators


def _generate_ghost_strategies(competitors: list[dict]) -> list[str]:
    if not competitors:
        return ["Emphasize unique qualifications that large competitors cannot match"]
    strategies = []
    for comp in competitors[:3]:
        name = comp.get("company_name", "Competitors")
        strategies.append(
            f"Highlight our agility and dedicated team vs. {name}'s large company overhead"
        )
    return strategies


def _generate_counters(competitors: list[dict]) -> list[str]:
    return [
        "If competitors claim lower cost: emphasize total cost of ownership and risk",
        "If competitors claim more experience: emphasize our specialized domain focus",
        "If competitors claim larger team: emphasize senior staff commitment and retention",
    ]


def _estimate_win_probability(
    deal: dict,
    opp: dict,
    competitor_count: int,
    agency_profile: dict | None,
) -> dict:
    # Start with 1/(competitors+1) base rate
    base_pwin = 1.0 / max(1, competitor_count + 1)

    # Adjust for fit score
    fit = float(deal.get("fit_score", 0.5) or 0.5)
    base_pwin *= (0.5 + fit)

    # Adjust for agency relationship
    rel_score = float((agency_profile or {}).get("relationship_score", 5) or 5) / 10
    base_pwin *= (0.8 + 0.4 * rel_score)

    # Cap at reasonable bounds
    p_win = max(0.05, min(0.85, base_pwin))

    return {
        "p_win": round(p_win, 2),
        "confidence": "medium",
        "base_rate": round(1.0 / max(1, competitor_count + 1), 2),
        "key_factors": {
            "fit_score": fit,
            "agency_relationship": rel_score,
            "estimated_competitors": competitor_count,
        },
        "recommendations": [
            "Conduct gate review before investing further",
            "Pursue agency engagement to improve relationship score",
        ],
    }


def _recommend_teaming(opp: dict) -> dict:
    set_aside = opp.get("set_aside", "")
    return {
        "recommended_structure": "prime" if not set_aside else "sb_prime",
        "sb_needed": bool(set_aside),
        "specialty_gap": "Assess after reviewing full RFP requirements",
        "recommendation": "Evaluate teaming needs after RFP release",
    }


def _build_messaging_guide(win_themes: list, discriminators: list) -> dict:
    return {
        "primary_message": win_themes[0] if win_themes else "Mission success through proven expertise",
        "supporting_messages": win_themes[1:3],
        "proof_points": discriminators,
        "tone": "confident, solution-focused, mission-oriented",
        "avoid": ["vague promises", "unsupported superlatives", "jargon"],
    }


def _extract_eval_criteria(opp: dict) -> list[str]:
    description = opp.get("description", "")
    criteria = []
    if "technical" in description.lower():
        criteria.append("Technical Approach")
    if "management" in description.lower() or "past performance" in description.lower():
        criteria.append("Management Approach")
    criteria.extend(["Past Performance", "Price/Cost"])
    return list(dict.fromkeys(criteria))  # deduplicate preserving order


def _build_engagement_plan(agency_profile: dict | None) -> list[dict]:
    return [
        {"action": "Request capability briefing with program office", "timeline": "T-120 days"},
        {"action": "Attend agency industry day", "timeline": "Upon announcement"},
        {"action": "Submit RFI response to shape requirements", "timeline": "T-90 days"},
        {"action": "Request site visit if applicable", "timeline": "T-60 days"},
        {"action": "Submit clarification questions", "timeline": "Per RFP deadline"},
    ]


def _estimate_bnp_roi(deal: dict, p_win_data: dict) -> dict:
    estimated_value = float(deal.get("estimated_value", 1_000_000) or 1_000_000)
    p_win = p_win_data.get("p_win", 0.3)
    # Estimate B&P cost as 0.5-2% of contract value
    bnp_estimate = estimated_value * 0.01
    expected_revenue = estimated_value * p_win
    roi = (expected_revenue - bnp_estimate) / max(1, bnp_estimate)

    return {
        "estimated_bnp_cost": round(bnp_estimate, 0),
        "expected_revenue": round(expected_revenue, 0),
        "expected_profit": round(expected_revenue * 0.10, 0),
        "roi": round(roi, 2),
        "recommendation": "Pursue" if roi > 5 else "Evaluate carefully",
    }
