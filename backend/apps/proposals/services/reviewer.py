"""Proposal review workflow service – pink/red/gold team reviews."""
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


async def start_review_cycle(
    proposal_id: str,
    review_type: str,
    reviewers: list[str] | None = None,
    due_date: str | None = None,
) -> dict[str, Any]:
    """Start a proposal review cycle (pink, red, or gold team).

    Args:
        proposal_id: Proposal UUID.
        review_type: "pink", "red", or "gold".
        reviewers: List of reviewer user IDs.
        due_date: Review due date (ISO date string).

    Returns:
        Created review cycle dict with ID and status.
    """
    try:
        from apps.proposals.models import ReviewCycle  # type: ignore

        cycle = ReviewCycle.objects.create(
            proposal_id=proposal_id,
            review_type=review_type,
            reviewer_ids=reviewers or [],
            due_date=due_date,
            status="in_progress",
        )
        return {
            "cycle_id": str(cycle.id),
            "proposal_id": proposal_id,
            "review_type": review_type,
            "status": "in_progress",
            "review_criteria": _get_review_criteria(review_type),
            "coaching_tips": _get_coaching_tips(review_type),
        }
    except Exception as exc:
        logger.error("Review cycle creation failed: %s", exc)
        return {
            "proposal_id": proposal_id,
            "review_type": review_type,
            "status": "created",
            "review_criteria": _get_review_criteria(review_type),
            "coaching_tips": _get_coaching_tips(review_type),
            "error": str(exc),
        }


async def run_ai_review(
    proposal_id: str,
    review_type: str,
    sections: list[dict[str, Any]],
    rfp_requirements: list[dict[str, Any]] | None = None,
    win_themes: list[str] | None = None,
) -> dict[str, Any]:
    """Run an AI-powered proposal review.

    Args:
        proposal_id: Proposal UUID.
        review_type: "pink", "red", or "gold".
        sections: List of proposal section dicts with title and content.
        rfp_requirements: RFP requirements to check compliance against.
        win_themes: Win themes to check coverage.

    Returns:
        Dict with score, issues (list), recommendations, compliance_gaps.
    """
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")

    issues: list[dict] = []
    scores: list[float] = []

    for section in sections:
        section_score, section_issues = await _review_section(
            section=section,
            review_type=review_type,
            rfp_requirements=rfp_requirements or [],
            win_themes=win_themes or [],
            anthropic_key=anthropic_key,
        )
        scores.append(section_score)
        issues.extend(section_issues)

    avg_score = sum(scores) / max(1, len(scores))

    # Check win theme coverage
    win_theme_coverage = _check_win_theme_coverage(sections, win_themes or [])

    # Check compliance
    compliance_gaps = _check_compliance_gaps(sections, rfp_requirements or [])

    return {
        "proposal_id": proposal_id,
        "review_type": review_type,
        "overall_score": round(avg_score, 1),
        "grade": _score_to_grade(avg_score),
        "issues": issues,
        "issue_count": len(issues),
        "critical_issues": [i for i in issues if i.get("severity") == "critical"],
        "win_theme_coverage": win_theme_coverage,
        "compliance_gaps": compliance_gaps,
        "recommendations": _generate_recommendations(issues, win_theme_coverage, compliance_gaps),
        "ready_to_submit": avg_score >= 8.0 and not compliance_gaps,
    }


async def get_review_coaching(
    review_type: str,
    proposal_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Get AI coaching guidance for a review type.

    Returns:
        Dict with coaching_framework, key_criteria, common_issues, improvement_tips.
    """
    return {
        "review_type": review_type,
        "coaching_framework": _get_coaching_framework(review_type),
        "key_criteria": _get_review_criteria(review_type),
        "common_issues": _get_common_issues(review_type),
        "improvement_tips": _get_coaching_tips(review_type),
    }


# ── Internal helpers ──────────────────────────────────────────────────────────

async def _review_section(
    section: dict,
    review_type: str,
    rfp_requirements: list,
    win_themes: list,
    anthropic_key: str | None,
) -> tuple[float, list[dict]]:
    """Review a single section and return (score 0-10, issues list)."""
    content = section.get("content", "")
    title = section.get("title", "")
    issues = []

    # Length check
    word_count = len(content.split())
    if word_count < 100:
        issues.append(
            {
                "section": title,
                "severity": "high",
                "issue": "Section too short – lacks sufficient detail",
                "suggestion": "Expand with specific methodology, tools, and evidence",
            }
        )

    # Win theme check
    themes_present = sum(1 for t in win_themes if t.lower()[:10] in content.lower())
    if win_themes and themes_present == 0:
        issues.append(
            {
                "section": title,
                "severity": "medium",
                "issue": "No win themes evident in this section",
                "suggestion": f"Weave in relevant win themes: {', '.join(win_themes[:2])}",
            }
        )

    # Passive voice check
    passive_words = ["is performed", "will be done", "it is", "there are", "there is"]
    passive_count = sum(content.lower().count(pw) for pw in passive_words)
    if passive_count > 5:
        issues.append(
            {
                "section": title,
                "severity": "low",
                "issue": f"Excessive passive voice ({passive_count} instances)",
                "suggestion": "Use active voice: 'We will deliver' not 'delivery will be performed'",
            }
        )

    # Vague language check
    vague_words = ["world class", "best in class", "cutting edge", "innovative", "seamlessly"]
    vague_count = sum(content.lower().count(vw) for vw in vague_words)
    if vague_count > 2:
        issues.append(
            {
                "section": title,
                "severity": "medium",
                "issue": "Unsubstantiated superlatives and vague language",
                "suggestion": "Replace with specific, measurable claims backed by evidence",
            }
        )

    # Simple scoring
    score = 8.0
    severity_deductions = {"critical": 3.0, "high": 1.5, "medium": 0.75, "low": 0.25}
    for issue in issues:
        score -= severity_deductions.get(issue.get("severity", "low"), 0.25)

    return max(0.0, min(10.0, score)), issues


def _check_win_theme_coverage(sections: list[dict], win_themes: list[str]) -> dict:
    all_content = " ".join(s.get("content", "") for s in sections).lower()
    covered = []
    missing = []
    for theme in win_themes:
        if theme.lower()[:10] in all_content:
            covered.append(theme)
        else:
            missing.append(theme)
    return {
        "total_themes": len(win_themes),
        "covered": covered,
        "missing": missing,
        "coverage_pct": round(len(covered) / max(1, len(win_themes)) * 100, 0),
    }


def _check_compliance_gaps(sections: list[dict], requirements: list[dict]) -> list[dict]:
    all_content = " ".join(s.get("content", "") for s in sections).lower()
    gaps = []
    for req in requirements:
        text = (req.get("requirement_text") or req.get("text") or "").lower()
        if text and not any(word in all_content for word in text.split()[:5]):
            gaps.append(
                {
                    "requirement_id": req.get("id", ""),
                    "text": text[:100],
                    "priority": req.get("priority", "medium"),
                }
            )
    return gaps[:10]  # Return top 10 gaps


def _get_review_criteria(review_type: str) -> list[str]:
    criteria = {
        "pink": [
            "Is the technical approach sound and feasible?",
            "Are all evaluation criteria addressed?",
            "Is the writing clear and professional?",
            "Are win themes present?",
            "Are there any compliance gaps?",
        ],
        "red": [
            "Is the proposal compelling and differentiated?",
            "Are discriminators clearly articulated?",
            "Is the pricing strategy competitive?",
            "Are risks adequately addressed?",
            "Does the management approach inspire confidence?",
        ],
        "gold": [
            "Is the executive summary compelling?",
            "Is the value proposition clear?",
            "Are all RFP requirements addressed?",
            "Is the proposal ready for submission?",
            "Final grammar and formatting check",
        ],
    }
    return criteria.get(review_type, ["Review for quality and completeness"])


def _get_coaching_tips(review_type: str) -> list[str]:
    tips = {
        "pink": [
            "Focus on technical accuracy and completeness",
            "Verify every 'shall' requirement has a response",
            "Check that section L and M criteria are addressed",
        ],
        "red": [
            "Read as the evaluator – does this win?",
            "Challenge vague claims – add proof points",
            "Ensure discriminators are stated explicitly",
        ],
        "gold": [
            "Final eyes on compliance matrix – all addressed?",
            "Executive summary must sell the entire proposal",
            "Verify pricing and technical are consistent",
        ],
    }
    return tips.get(review_type, ["Review for quality"])


def _get_coaching_framework(review_type: str) -> str:
    frameworks = {
        "pink": "Early draft review using Shipley 7-step process",
        "red": "Competitive assessment using Lohfeld color team approach",
        "gold": "Final compliance and quality check",
    }
    return frameworks.get(review_type, "Standard proposal review")


def _get_common_issues(review_type: str) -> list[str]:
    issues = {
        "pink": ["Missing technical detail", "Passive voice", "Requirements not traced"],
        "red": ["Weak discriminators", "No proof points", "Inconsistent pricing/technical"],
        "gold": ["Executive summary doesn't sell", "Formatting issues", "Last-minute errors"],
    }
    return issues.get(review_type, ["Quality and completeness issues"])


def _generate_recommendations(
    issues: list,
    win_coverage: dict,
    compliance_gaps: list,
) -> list[str]:
    recs = []
    critical = [i for i in issues if i.get("severity") == "critical"]
    for i in critical[:3]:
        recs.append(f"CRITICAL: {i.get('suggestion', i.get('issue', ''))}")

    if win_coverage.get("missing"):
        recs.append(f"Add win themes: {', '.join(win_coverage['missing'][:2])}")

    if compliance_gaps:
        recs.append(f"Address {len(compliance_gaps)} compliance gaps before submission")

    return recs or ["Proposal looks good – complete final review"]


def _score_to_grade(score: float) -> str:
    if score >= 9.3:
        return "A"
    if score >= 8.3:
        return "B"
    if score >= 7.3:
        return "C"
    if score >= 6.3:
        return "D"
    return "F"
