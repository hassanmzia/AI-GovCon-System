"""Bid protest viability assessment and protest strategy advisor."""
import logging
from typing import Any

logger = logging.getLogger(__name__)


async def assess_protest_viability(
    opportunity: dict[str, Any],
    bid_result: dict[str, Any],
    solicitation_issues: list[str] | None = None,
) -> dict[str, Any]:
    """Assess whether a bid protest is viable.

    Args:
        opportunity: Opportunity dict with solicitation details.
        bid_result: Bid result dict (e.g. award notification).
        solicitation_issues: Known issues with the solicitation.

    Returns:
        Dict with viable (bool), grounds (list), confidence, strategy, timeline.
    """
    grounds = []
    solicitation_issues = solicitation_issues or []

    # Evaluation disparities
    if bid_result.get("technical_score_issue"):
        grounds.append(
            {
                "ground": "Unreasonable technical evaluation",
                "description": "Agency's technical evaluation was arbitrary or failed to follow stated criteria",
                "gao_citation": "4 C.F.R. § 21.1",
                "precedent": "Multiple GAO decisions uphold protests of arbitrary technical evaluations",
                "viability": "high",
            }
        )

    # Past performance evaluation
    if bid_result.get("past_performance_issue"):
        grounds.append(
            {
                "ground": "Improper past performance evaluation",
                "description": "Agency failed to evaluate all relevant past performance or misapplied ratings",
                "gao_citation": "FAR 15.305(a)(2)",
                "viability": "medium",
            }
        )

    # Best value tradeoff issues
    if bid_result.get("tradeoff_issue"):
        grounds.append(
            {
                "ground": "Flawed best-value tradeoff",
                "description": "Agency's best-value tradeoff was not consistent with evaluation criteria",
                "gao_citation": "FAR 15.308",
                "viability": "medium",
            }
        )

    # Price realism issues
    if bid_result.get("price_realism_issue"):
        grounds.append(
            {
                "ground": "Price realism evaluation error",
                "description": "Agency failed to conduct proper price realism evaluation",
                "gao_citation": "FAR 15.404-1(d)",
                "viability": "medium",
            }
        )

    # Solicitation ambiguities
    for issue in solicitation_issues:
        grounds.append(
            {
                "ground": f"Solicitation defect: {issue}",
                "description": f"The solicitation was ambiguous or inconsistent regarding: {issue}",
                "gao_citation": "4 C.F.R. § 21.5(b)",
                "viability": "medium",
            }
        )

    # Defective award
    if bid_result.get("awardee_responsibility_issue"):
        grounds.append(
            {
                "ground": "Awardee responsibility question",
                "description": "Agency may not have adequately assessed awardee's responsibility",
                "gao_citation": "FAR 9.103",
                "viability": "low",
            }
        )

    viable = any(g["viability"] == "high" for g in grounds) or len(grounds) >= 2
    confidence = "high" if any(g["viability"] == "high" for g in grounds) else "medium" if grounds else "low"

    return {
        "viable": viable,
        "grounds": grounds,
        "grounds_count": len(grounds),
        "confidence": confidence,
        "protest_strategy": _build_protest_strategy(grounds, viable),
        "timeline": _protest_timeline(),
        "costs_estimate": _estimate_protest_costs(grounds),
        "forum": _recommend_forum(grounds),
        "risks": _identify_protest_risks(),
    }


async def search_protest_precedents_for_issue(
    issue_description: str,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Search protest precedents for a specific legal issue.

    Returns:
        List of relevant GAO/COFC precedent decisions.
    """
    from apps.legal.services.legal_rag import find_protest_precedents

    return await find_protest_precedents(issue_description, limit=limit)


# ── Internal helpers ──────────────────────────────────────────────────────────

def _build_protest_strategy(grounds: list[dict], viable: bool) -> str:
    if not viable or not grounds:
        return "Protest not recommended based on available information. Request debrief instead."

    top_ground = max(grounds, key=lambda g: {"high": 3, "medium": 2, "low": 1}.get(g["viability"], 0))
    return (
        f"Primary ground: {top_ground['ground']}. "
        f"{top_ground['description']}. "
        f"File at GAO within 10 days of award notification. "
        f"Request agency report within 30 days. "
        f"Consider BAFO/discussions issues as additional grounds."
    )


def _protest_timeline() -> dict:
    return {
        "deadline_from_award": "10 calendar days for procuring agency; "
                               "10 days from date initial protest filed for GAO",
        "gao_decision": "100 calendar days from filing (standard)",
        "gao_expedited": "65 calendar days (if urgent)",
        "cofc_timeline": "Typically 6-18 months",
        "automatic_stay": "Award performance is stayed if protest filed within 10 days",
    }


def _estimate_protest_costs(grounds: list[dict]) -> dict:
    base_cost = 25_000  # minimum legal fees
    per_ground = 10_000
    total = base_cost + len(grounds) * per_ground
    return {
        "estimated_legal_fees": total,
        "filing_fee_gao": 0,  # GAO protests are free to file
        "filing_fee_cofc": 350,
        "note": "Estimates vary significantly based on complexity and discovery",
    }


def _recommend_forum(grounds: list[dict]) -> str:
    # GAO is faster and cheaper; COFC is better for systemic issues
    return "GAO (Comptroller General) – faster (100 days), cheaper, stays award automatically"


def _identify_protest_risks() -> list[str]:
    return [
        "Loss of goodwill with contracting agency (long-term relationship impact)",
        "Cost of protest may not be recoverable even if successful",
        "GAO only recommends; agency may override recommendation",
        "Protest may delay start of work if awarded in future",
        "Discovery may reveal weaknesses in our own proposal",
    ]
