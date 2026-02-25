"""Security control mapper: maps requirements to NIST/CMMC/FedRAMP controls."""
import logging
import re
from typing import Any

logger = logging.getLogger("ai_deal_manager.security.control_mapper")

# ── Control databases (embedded for offline use) ───────────────────────────────

NIST_800_53_CONTROLS = {
    "AC-1": {"family": "Access Control", "title": "Policy and Procedures", "impact": ["low", "moderate", "high"]},
    "AC-2": {"family": "Access Control", "title": "Account Management", "impact": ["low", "moderate", "high"]},
    "AC-3": {"family": "Access Control", "title": "Access Enforcement", "impact": ["low", "moderate", "high"]},
    "AC-17": {"family": "Access Control", "title": "Remote Access", "impact": ["low", "moderate", "high"]},
    "AU-2": {"family": "Audit and Accountability", "title": "Event Logging", "impact": ["low", "moderate", "high"]},
    "AU-12": {"family": "Audit and Accountability", "title": "Audit Record Generation", "impact": ["low", "moderate", "high"]},
    "CA-3": {"family": "Assessment, Authorization", "title": "Information Exchange", "impact": ["low", "moderate", "high"]},
    "CM-2": {"family": "Configuration Management", "title": "Baseline Configuration", "impact": ["low", "moderate", "high"]},
    "CM-6": {"family": "Configuration Management", "title": "Configuration Settings", "impact": ["low", "moderate", "high"]},
    "CM-7": {"family": "Configuration Management", "title": "Least Functionality", "impact": ["low", "moderate", "high"]},
    "IA-2": {"family": "Identification and Authentication", "title": "Identification and Authentication (Organizational Users)", "impact": ["low", "moderate", "high"]},
    "IA-5": {"family": "Identification and Authentication", "title": "Authenticator Management", "impact": ["low", "moderate", "high"]},
    "IR-4": {"family": "Incident Response", "title": "Incident Handling", "impact": ["low", "moderate", "high"]},
    "IR-6": {"family": "Incident Response", "title": "Incident Reporting", "impact": ["low", "moderate", "high"]},
    "MA-2": {"family": "Maintenance", "title": "Controlled Maintenance", "impact": ["low", "moderate", "high"]},
    "MP-2": {"family": "Media Protection", "title": "Media Access", "impact": ["low", "moderate", "high"]},
    "PE-2": {"family": "Physical and Environmental", "title": "Physical Access Authorizations", "impact": ["low", "moderate", "high"]},
    "PL-2": {"family": "Planning", "title": "System Security and Privacy Plans", "impact": ["low", "moderate", "high"]},
    "PS-3": {"family": "Personnel Security", "title": "Personnel Screening", "impact": ["low", "moderate", "high"]},
    "RA-3": {"family": "Risk Assessment", "title": "Risk Assessment", "impact": ["low", "moderate", "high"]},
    "SA-9": {"family": "System and Services Acquisition", "title": "External System Services", "impact": ["low", "moderate", "high"]},
    "SC-7": {"family": "System and Communications Protection", "title": "Boundary Protection", "impact": ["low", "moderate", "high"]},
    "SC-8": {"family": "System and Communications Protection", "title": "Transmission Confidentiality and Integrity", "impact": ["moderate", "high"]},
    "SC-28": {"family": "System and Communications Protection", "title": "Protection of Information at Rest", "impact": ["moderate", "high"]},
    "SI-2": {"family": "System and Information Integrity", "title": "Flaw Remediation", "impact": ["low", "moderate", "high"]},
    "SI-3": {"family": "System and Information Integrity", "title": "Malicious Code Protection", "impact": ["low", "moderate", "high"]},
}

# CMMC Level 2 → NIST 800-171 practice mapping (subset)
CMMC_L2_PRACTICES = {
    "AC.L2-3.1.1": "AC-2",
    "AC.L2-3.1.2": "AC-3",
    "AC.L2-3.1.3": "AC-17",
    "AU.L2-3.3.1": "AU-2",
    "AU.L2-3.3.2": "AU-12",
    "CM.L2-3.4.1": "CM-2",
    "CM.L2-3.4.2": "CM-6",
    "IA.L2-3.5.3": "IA-2",
    "IR.L2-3.6.1": "IR-4",
    "MP.L2-3.8.3": "MP-2",
    "SC.L2-3.13.1": "SC-7",
    "SC.L2-3.13.8": "SC-8",
    "SI.L2-3.14.1": "SI-2",
    "SI.L2-3.14.2": "SI-3",
}

# Keywords that map to control families
KEYWORD_TO_FAMILIES = {
    "access": ["AC"],
    "authentication": ["IA"],
    "audit": ["AU"],
    "log": ["AU"],
    "configuration": ["CM"],
    "incident": ["IR"],
    "patch": ["SI"],
    "vulnerability": ["RA", "SI"],
    "encryption": ["SC"],
    "backup": ["CP"],
    "continuity": ["CP"],
    "personnel": ["PS"],
    "training": ["AT"],
    "physical": ["PE"],
    "supply chain": ["SA"],
    "boundary": ["SC"],
    "firewall": ["SC"],
    "mfa": ["IA"],
    "multi-factor": ["IA"],
    "zero trust": ["AC", "SC"],
    "fedramp": ["CA", "SA"],
    "cmmc": ["AC", "IA", "CM", "AU", "IR", "SC", "SI"],
}


def map_requirement_to_controls(
    requirement_text: str,
    framework: str = "NIST_800_53",
    impact_level: str = "moderate",
) -> dict[str, Any]:
    """Map a requirement statement to relevant security controls.

    Args:
        requirement_text: The security requirement text.
        framework: "NIST_800_53", "CMMC_L2", "CMMC_L3", "FedRAMP_Moderate".
        impact_level: "low", "moderate", "high".

    Returns:
        Dict with: requirement, matched_controls, control_families, gaps.
    """
    req_lower = requirement_text.lower()

    # Find matching families from keywords
    matched_families: set[str] = set()
    for keyword, families in KEYWORD_TO_FAMILIES.items():
        if keyword in req_lower:
            matched_families.update(families)

    # Find specific control IDs mentioned
    mentioned_controls = re.findall(r"\b([A-Z]{2}-\d+(?:\(\d+\))?)\b", requirement_text)

    # Get controls from matched families
    matched_controls = []
    for ctrl_id, ctrl_info in NIST_800_53_CONTROLS.items():
        family_prefix = ctrl_id.split("-")[0]
        if (
            family_prefix in matched_families
            or ctrl_id in mentioned_controls
        ) and impact_level in ctrl_info.get("impact", []):
            matched_controls.append({
                "control_id": ctrl_id,
                "family": ctrl_info["family"],
                "title": ctrl_info["title"],
                "framework": framework,
                "impact_level": impact_level,
            })

    # Check CMMC mappings if requested
    cmmc_practices = []
    if framework.startswith("CMMC"):
        for practice, nist_ctrl in CMMC_L2_PRACTICES.items():
            nist_family = nist_ctrl.split("-")[0]
            if nist_family in matched_families:
                cmmc_practices.append(practice)

    return {
        "requirement": requirement_text[:200],
        "framework": framework,
        "impact_level": impact_level,
        "matched_controls": matched_controls,
        "control_count": len(matched_controls),
        "control_families": sorted(matched_families),
        "cmmc_practices": cmmc_practices,
        "explicitly_mentioned": mentioned_controls,
    }


def map_requirement_list(
    requirements: list[str | dict],
    framework: str = "NIST_800_53",
    impact_level: str = "moderate",
) -> list[dict[str, Any]]:
    """Map a list of requirements to controls."""
    results = []
    for req in requirements:
        text = req if isinstance(req, str) else req.get("text", req.get("requirement", ""))
        if text:
            results.append(map_requirement_to_controls(text, framework, impact_level))
    return results


def get_control_details(control_id: str) -> dict[str, Any]:
    """Get details for a specific NIST 800-53 control."""
    ctrl = NIST_800_53_CONTROLS.get(control_id.upper())
    if not ctrl:
        return {"error": f"Control {control_id} not found"}
    return {
        "control_id": control_id,
        **ctrl,
        "cmmc_practice": next(
            (p for p, n in CMMC_L2_PRACTICES.items() if n == control_id), None
        ),
    }


def get_controls_by_family(
    family: str,
    impact_level: str = "moderate",
) -> list[dict[str, Any]]:
    """Get all controls for a given family at a given impact level."""
    return [
        {"control_id": cid, **info}
        for cid, info in NIST_800_53_CONTROLS.items()
        if cid.startswith(family.upper()) and impact_level in info.get("impact", [])
    ]
