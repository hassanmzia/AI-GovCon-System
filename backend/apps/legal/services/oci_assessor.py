"""OCI (Organizational Conflict of Interest) assessment service."""
import logging
from typing import Any

logger = logging.getLogger(__name__)

# OCI types per FAR 9.505
_OCI_TYPES = {
    "biased_ground_rules": "Biased Ground Rules – contractor helped draft specs",
    "impaired_objectivity": "Impaired Objectivity – evaluating own work",
    "unequal_access": "Unequal Access to Information – access to non-public info",
}


async def assess_oci_risk(
    company_name: str,
    opportunity_id: str,
    work_description: str = "",
    past_contracts: list[dict] | None = None,
) -> dict[str, Any]:
    """Assess OCI risk for a company pursuing an opportunity.

    FAR 9.5 defines three types of OCI:
    1. Biased Ground Rules (helped draft specs/SOW)
    2. Impaired Objectivity (evaluating own work)
    3. Unequal Access to Information (non-public info advantage)

    Args:
        company_name: Company name.
        opportunity_id: Opportunity UUID.
        work_description: Description of the work to be performed.
        past_contracts: List of the company's past contracts at this agency.

    Returns:
        Dict with oci_risk, oci_types_identified, mitigation_plan, requires_disclosure.
    """
    oci_types_found: list[dict] = []
    work_lower = work_description.lower()

    # Biased ground rules check
    if any(kw in work_lower for kw in ["advisory", "consulting", "requirements", "specs", "scope of work", "rfp"]):
        oci_types_found.append(
            {
                "type": "biased_ground_rules",
                "description": _OCI_TYPES["biased_ground_rules"],
                "risk_level": "high",
                "evidence": "Work description suggests possible involvement in requirements development",
                "mitigation": "Provide firewall memo and written certification of no prior involvement",
            }
        )

    # Impaired objectivity check
    if any(kw in work_lower for kk in [["evaluation", "assessment", "testing", "audit", "review"]] for kw in kk):
        oci_types_found.append(
            {
                "type": "impaired_objectivity",
                "description": _OCI_TYPES["impaired_objectivity"],
                "risk_level": "medium",
                "evidence": "Work involves evaluation or assessment functions",
                "mitigation": "Assess whether company or affiliate work is being evaluated",
            }
        )

    # Unequal access check
    has_incumbency = any(
        c.get("agency_id") == opportunity_id or "incumbent" in str(c.get("description", "")).lower()
        for c in (past_contracts or [])
    )
    if has_incumbency:
        oci_types_found.append(
            {
                "type": "unequal_access",
                "description": _OCI_TYPES["unequal_access"],
                "risk_level": "high",
                "evidence": "Company may have had access to non-public information as incumbent",
                "mitigation": "Assess whether a firewall or exclusion is required per FAR 9.505-4",
            }
        )

    overall_risk = "none"
    if any(o["risk_level"] == "high" for o in oci_types_found):
        overall_risk = "high"
    elif oci_types_found:
        overall_risk = "medium"

    mitigation_plan = _build_mitigation_plan(oci_types_found)

    return {
        "company_name": company_name,
        "opportunity_id": opportunity_id,
        "oci_risk": overall_risk,
        "oci_types_identified": oci_types_found,
        "oci_count": len(oci_types_found),
        "requires_disclosure": overall_risk in ("medium", "high"),
        "mitigation_plan": mitigation_plan,
        "far_references": ["FAR 9.504", "FAR 9.505", "FAR 9.506"],
        "recommended_actions": _build_recommended_actions(oci_types_found, overall_risk),
    }


def _build_mitigation_plan(oci_types: list[dict]) -> str:
    if not oci_types:
        return "No OCI identified. Document analysis for record."

    parts = ["OCI Mitigation Plan:\n"]
    for oci in oci_types:
        parts.append(f"• {oci['type'].replace('_', ' ').title()}: {oci['mitigation']}")

    parts.append("\nRequired Documentation:")
    parts.append("• Written OCI analysis memo")
    parts.append("• Firewall procedures (if applicable)")
    parts.append("• Contracting Officer notification letter")
    parts.append("• Personnel recusal agreements")

    return "\n".join(parts)


def _build_recommended_actions(oci_types: list[dict], risk: str) -> list[str]:
    if risk == "none":
        return ["Document OCI screening analysis for proposal files"]
    actions = [
        "Consult legal counsel immediately",
        "Prepare written OCI disclosure for Contracting Officer",
        "Establish internal firewall procedures if proceeding",
        "Document all steps taken to mitigate OCI",
    ]
    if risk == "high":
        actions.insert(0, "STOP: Obtain legal clearance before proceeding with bid")
    return actions
