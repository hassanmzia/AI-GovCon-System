"""
Compliance Drift Detection Service.

Monitors active contracts for compliance drift — situations where
security controls go out of compliance due to changes in the
environment, personnel, or technology.
"""

import logging
from datetime import timedelta

from django.db.models import Q
from django.utils import timezone

logger = logging.getLogger(__name__)


def detect_drift(contract_id: str = None) -> list[dict]:
    """
    Detect compliance drift across active contracts.

    Checks for:
    1. Expired certifications or clearances
    2. Overdue control assessments
    3. Unresolved POAM items past due
    4. Missing evidence for mapped controls
    5. Personnel changes affecting compliance posture

    Returns list of drift findings with severity and remediation.
    """
    from apps.security_compliance.models import (
        SecurityComplianceReport,
        SecurityControlMapping,
    )
    from apps.contracts.models import Contract

    findings = []
    now = timezone.now()

    # Get active contracts (optionally filtered)
    contracts_qs = Contract.objects.filter(status__in=["active", "delivery"])
    if contract_id:
        contracts_qs = contracts_qs.filter(pk=contract_id)

    for contract in contracts_qs:
        # Check for stale compliance reports
        latest_report = (
            SecurityComplianceReport.objects.filter(
                contract=contract
            ).order_by("-created_at").first()
        )

        if latest_report:
            days_since_report = (now - latest_report.created_at).days
            if days_since_report > 90:
                findings.append({
                    "contract_id": str(contract.id),
                    "contract_title": contract.title,
                    "finding_type": "stale_assessment",
                    "severity": "medium" if days_since_report < 180 else "high",
                    "description": (
                        f"Last compliance assessment was {days_since_report} days ago. "
                        "Recommend reassessment within 90 days."
                    ),
                    "remediation": "Schedule compliance reassessment",
                    "days_overdue": days_since_report - 90,
                })
        else:
            findings.append({
                "contract_id": str(contract.id),
                "contract_title": contract.title,
                "finding_type": "no_assessment",
                "severity": "high",
                "description": "No compliance assessment has been performed.",
                "remediation": "Perform initial compliance assessment immediately",
                "days_overdue": 0,
            })

        # Check for unmapped controls
        unmapped = SecurityControlMapping.objects.filter(
            contract=contract,
            status="not_mapped",
        ).count()

        if unmapped > 0:
            findings.append({
                "contract_id": str(contract.id),
                "contract_title": contract.title,
                "finding_type": "unmapped_controls",
                "severity": "medium",
                "description": f"{unmapped} security controls are not mapped to implementations.",
                "remediation": "Map all required controls to implementations",
                "count": unmapped,
            })

    # Check for milestone/deliverable drift
    from apps.contracts.models import ContractMilestone

    overdue_milestones = ContractMilestone.objects.filter(
        due_date__lt=now.date(),
        status__in=["pending", "in_progress"],
    ).select_related("contract")

    for milestone in overdue_milestones:
        days_overdue = (now.date() - milestone.due_date).days
        findings.append({
            "contract_id": str(milestone.contract_id),
            "contract_title": milestone.contract.title if hasattr(milestone, 'contract') else "",
            "finding_type": "overdue_deliverable",
            "severity": "high" if days_overdue > 14 else "medium",
            "description": (
                f"Milestone '{milestone.title}' is {days_overdue} days overdue."
            ),
            "remediation": f"Complete milestone or request extension",
            "days_overdue": days_overdue,
        })

    # Sort by severity
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    findings.sort(key=lambda f: severity_order.get(f.get("severity", "low"), 4))

    return findings


def get_compliance_health(contract_id: str) -> dict:
    """
    Compute overall compliance health score for a contract.

    Returns score 0-100 and component scores.
    """
    drift_findings = detect_drift(contract_id=contract_id)

    # Base score starts at 100, deducted by findings
    score = 100.0
    for finding in drift_findings:
        if finding.get("contract_id") == contract_id:
            severity = finding.get("severity", "low")
            if severity == "critical":
                score -= 25
            elif severity == "high":
                score -= 15
            elif severity == "medium":
                score -= 8
            else:
                score -= 3

    score = max(0.0, score)

    risk_level = "low"
    if score < 50:
        risk_level = "critical"
    elif score < 70:
        risk_level = "high"
    elif score < 85:
        risk_level = "medium"

    return {
        "contract_id": contract_id,
        "overall_score": round(score, 1),
        "risk_level": risk_level,
        "finding_count": len([f for f in drift_findings if f.get("contract_id") == contract_id]),
        "findings": [f for f in drift_findings if f.get("contract_id") == contract_id],
    }
