"""FAR/DFARS compliance checker for deals and proposals."""
import logging
from typing import Any

logger = logging.getLogger(__name__)


async def run_compliance_check(
    deal_id: str,
    check_types: list[str] | None = None,
) -> dict[str, Any]:
    """Run comprehensive FAR/DFARS compliance checks for a deal.

    Check types:
        representations, cas, tina, buy_american, section_889,
        cmmc, sca_dba, eeo, small_business, ethics

    Returns:
        Dict with overall_compliant, issues, recommendations, next_steps.
    """
    if check_types is None:
        check_types = [
            "representations", "buy_american", "section_889",
            "small_business", "ethics",
        ]

    all_issues: list[dict] = []
    check_results: dict[str, Any] = {}

    for check_type in check_types:
        handler = _CHECK_HANDLERS.get(check_type)
        if handler:
            result = await handler(deal_id)
            check_results[check_type] = result
            if result.get("issues"):
                all_issues.extend(result["issues"])
        else:
            logger.warning("Unknown check type: %s", check_type)
            check_results[check_type] = {"status": "skipped", "reason": "Unknown check type"}

    critical_issues = [i for i in all_issues if i.get("severity") == "critical"]
    high_issues = [i for i in all_issues if i.get("severity") == "high"]

    return {
        "deal_id": deal_id,
        "checks_run": check_types,
        "check_results": check_results,
        "all_issues": all_issues,
        "critical_issues": critical_issues,
        "high_issues": high_issues,
        "overall_compliant": len(critical_issues) == 0,
        "compliance_score": _compute_compliance_score(all_issues, check_types),
        "recommendations": _build_compliance_recommendations(all_issues),
    }


async def check_representations(deal_id: str) -> dict[str, Any]:
    """Check that required representations and certifications are in order."""
    required_reps = [
        {"name": "Certification of Independent Price Determination", "far_ref": "52.203-2"},
        {"name": "Contractor Code of Business Ethics and Conduct", "far_ref": "52.203-13"},
        {"name": "Affirmative Action Compliance", "far_ref": "52.222-26"},
        {"name": "Small Business Program Representations", "far_ref": "52.219-1"},
    ]
    # In production: query deal record for completed reps
    return {
        "status": "requires_review",
        "required_representations": required_reps,
        "issues": [
            {
                "type": "representations",
                "severity": "medium",
                "description": "Verify all required representations are current in SAM.gov",
                "far_reference": "FAR 4.1200",
            }
        ],
    }


async def check_buy_american(deal_id: str) -> dict[str, Any]:
    """Check Buy American Act compliance."""
    return {
        "status": "requires_review",
        "applicable_clauses": ["FAR 52.225-1", "FAR 52.225-3"],
        "issues": [
            {
                "type": "buy_american",
                "severity": "medium",
                "description": "Verify all products are domestic end products or qualify for exceptions",
                "far_reference": "FAR Part 25",
            }
        ],
    }


async def check_section_889(deal_id: str) -> dict[str, Any]:
    """Check Section 889 compliance (banned telecom equipment)."""
    return {
        "status": "requires_review",
        "banned_companies": [
            "Huawei Technologies",
            "ZTE Corporation",
            "Hytera Communications",
            "Hangzhou Hikvision",
            "Dahua Technology",
        ],
        "applicable_clause": "DFARS 252.204-7018",
        "issues": [
            {
                "type": "section_889",
                "severity": "high",
                "description": "Certify no covered telecommunications equipment in supply chain",
                "far_reference": "FAR 52.204-25, DFARS 252.204-7018",
            }
        ],
    }


async def check_small_business(deal_id: str) -> dict[str, Any]:
    """Check small business compliance and subcontracting plan requirements."""
    return {
        "status": "requires_review",
        "goals": {
            "overall_sb": "23%",
            "sdb": "5%",
            "wosb": "5%",
            "hubzone": "3%",
            "sdvosb": "3%",
        },
        "issues": [
            {
                "type": "small_business",
                "severity": "medium",
                "description": "Ensure Individual Subcontracting Plan (ISP) meets agency goals",
                "far_reference": "FAR 52.219-9",
            }
        ],
    }


async def check_cmmc(deal_id: str) -> dict[str, Any]:
    """Check CMMC requirements for DoD contracts."""
    return {
        "status": "requires_assessment",
        "applicable_clause": "DFARS 252.204-7019, 252.204-7020",
        "issues": [
            {
                "type": "cmmc",
                "severity": "high",
                "description": "Determine required CMMC level and assess current posture",
                "far_reference": "DFARS 252.204-7021",
            }
        ],
    }


# ── Handlers map ──────────────────────────────────────────────────────────────

_CHECK_HANDLERS = {
    "representations": check_representations,
    "buy_american": check_buy_american,
    "section_889": check_section_889,
    "small_business": check_small_business,
    "cmmc": check_cmmc,
}


def _compute_compliance_score(issues: list[dict], checks_run: list[str]) -> float:
    if not checks_run:
        return 1.0
    max_deductions = len(checks_run) * 10  # 10 points per check
    deductions = sum(
        {"critical": 10, "high": 7, "medium": 3, "low": 1}.get(i.get("severity", "low"), 1)
        for i in issues
    )
    score = max(0.0, 1.0 - (deductions / max(1, max_deductions)))
    return round(score, 2)


def _build_compliance_recommendations(issues: list[dict]) -> list[str]:
    recs = []
    for issue in issues:
        if issue.get("severity") in ("critical", "high"):
            recs.append(
                f"[{issue.get('severity', 'HIGH').upper()}] {issue.get('description', '')} "
                f"({issue.get('far_reference', '')})"
            )
    if not recs:
        recs.append("Complete all compliance verifications before proposal submission")
    return recs[:5]
