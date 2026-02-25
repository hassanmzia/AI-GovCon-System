"""SSP generator: produces System Security Plan documents."""
import asyncio
import logging
import os
from typing import Any

logger = logging.getLogger("ai_deal_manager.security.ssp_generator")


async def generate_ssp(
    system_name: str,
    system_description: str,
    organization_name: str,
    impact_level: str = "moderate",
    framework: str = "NIST_800_53",
    current_controls: list[str] | None = None,
    system_owner: str = "",
    authorizing_official: str = "",
) -> dict[str, Any]:
    """Generate a complete System Security Plan.

    Args:
        system_name: Name of the information system.
        system_description: Description of the system and its purpose.
        organization_name: Organization/company name.
        impact_level: "low", "moderate", "high".
        framework: Security framework to use.
        current_controls: List of implemented control IDs.
        system_owner: Name/title of system owner.
        authorizing_official: Name/title of AO.

    Returns:
        Dict with: ssp_document (full text), sections, control_count, docx_bytes.
    """
    from backend.apps.security_compliance.services.cross_walker import get_fedramp_baseline
    from backend.apps.security_compliance.services.gap_analyzer import analyze_compliance_gaps
    from backend.apps.security_compliance.services.narrative_drafter import (
        draft_security_narrative_for_controls,
    )

    # Determine required controls
    required_controls = get_fedramp_baseline(impact_level) if "fedramp" in framework.lower() else _get_nist_baseline(impact_level)
    implemented = current_controls or []

    # Generate gap analysis
    gap_analysis = analyze_compliance_gaps(implemented, required_controls, framework)

    # Generate narratives for implemented controls (batch up to 20)
    controls_to_narrate = implemented[:20]
    narratives_list = await draft_security_narrative_for_controls(
        controls_to_narrate, system_description, organization_name
    )
    narratives = {n["control_id"]: n for n in narratives_list if "control_id" in n}

    # Build SSP sections
    sections = await _build_ssp_sections(
        system_name=system_name,
        system_description=system_description,
        organization_name=organization_name,
        impact_level=impact_level,
        system_owner=system_owner,
        authorizing_official=authorizing_official,
        narratives=narratives,
        gap_analysis=gap_analysis,
    )

    # Assemble full document
    full_text = _assemble_ssp_document(sections)

    # Generate DOCX
    docx_bytes = await _render_ssp_docx(sections, system_name, organization_name)

    return {
        "system_name": system_name,
        "organization_name": organization_name,
        "impact_level": impact_level,
        "framework": framework,
        "sections": sections,
        "ssp_document": full_text,
        "docx_bytes": docx_bytes,
        "control_count": len(required_controls),
        "implemented_count": gap_analysis["implemented_count"],
        "compliance_score": gap_analysis["compliance_score"],
        "gap_analysis": gap_analysis,
    }


async def generate_ssp_section(
    section_name: str,
    system_name: str,
    system_description: str,
    organization_name: str,
    impact_level: str = "moderate",
    control_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Generate a single SSP section."""
    from backend.apps.security_compliance.services.narrative_drafter import (
        draft_security_narrative_for_controls,
    )

    narratives = []
    if control_ids:
        narratives = await draft_security_narrative_for_controls(
            control_ids[:10], system_description, organization_name
        )

    template = _SSP_SECTION_TEMPLATES.get(section_name, "")
    content = template.format(
        system_name=system_name,
        organization_name=organization_name,
        impact_level=impact_level.capitalize(),
        system_description=system_description,
    )

    return {
        "section_name": section_name,
        "content": content,
        "control_narratives": narratives,
        "word_count": len(content.split()),
    }


# ── SSP section templates ─────────────────────────────────────────────────────

_SSP_SECTION_TEMPLATES = {
    "system_overview": """
## 1. System Overview

**System Name:** {system_name}
**Organization:** {organization_name}
**Impact Level:** {impact_level}

### 1.1 System Description
{system_description}

### 1.2 System Purpose
{system_name} supports {organization_name}'s mission by providing information processing
and management capabilities in accordance with applicable federal regulations.

### 1.3 System Boundary
The authorization boundary encompasses all hardware, software, and data flows
within the {system_name} environment as documented in the network diagrams.
""",
    "security_categorization": """
## 2. System Categorization

This system has been categorized as **{impact_level}** impact per FIPS 199 and
NIST SP 800-60 analysis.

| Information Type | Confidentiality | Integrity | Availability |
|-----------------|-----------------|-----------|--------------|
| Mission Data     | {impact_level}  | {impact_level} | {impact_level} |

Overall System Impact Level: **{impact_level}**
""",
    "roles_and_responsibilities": """
## 3. Roles and Responsibilities

| Role | Responsibility |
|------|---------------|
| System Owner | Overall accountability for the system |
| ISSO | Information System Security Officer – day-to-day security |
| AO | Authorizing Official – authorization decision |
| ISSM | Information System Security Manager |

{organization_name} maintains documented role assignments and trains all personnel
with system access on their security responsibilities annually.
""",
}


async def _build_ssp_sections(
    system_name: str,
    system_description: str,
    organization_name: str,
    impact_level: str,
    system_owner: str,
    authorizing_official: str,
    narratives: dict[str, dict],
    gap_analysis: dict,
) -> list[dict[str, Any]]:
    """Build all SSP sections."""
    sections = []

    for section_name, template in _SSP_SECTION_TEMPLATES.items():
        content = template.format(
            system_name=system_name,
            organization_name=organization_name,
            impact_level=impact_level.capitalize(),
            system_description=system_description,
        )
        sections.append({
            "name": section_name,
            "content": content.strip(),
            "word_count": len(content.split()),
        })

    # Add control implementation section
    ctrl_section_parts = ["## 4. Control Implementation Statements\n"]
    for ctrl_id, narrative in narratives.items():
        ctrl_section_parts.append(
            f"### {ctrl_id} – {narrative.get('control_title', '')}\n{narrative.get('narrative', '')}\n"
        )

    # Add gap summary
    ctrl_section_parts.append(
        f"\n### Gap Summary\n"
        f"Compliance Score: {gap_analysis['compliance_score']}%\n"
        f"Missing Controls: {gap_analysis['missing_count']}\n"
    )

    sections.append({
        "name": "control_implementations",
        "content": "\n".join(ctrl_section_parts),
        "word_count": len(" ".join(ctrl_section_parts).split()),
    })

    return sections


def _assemble_ssp_document(sections: list[dict]) -> str:
    header = "# SYSTEM SECURITY PLAN\n\n"
    return header + "\n\n".join(s["content"] for s in sections)


def _get_nist_baseline(impact_level: str) -> list[str]:
    from backend.apps.security_compliance.services.control_mapper import NIST_800_53_CONTROLS

    return [
        cid for cid, info in NIST_800_53_CONTROLS.items()
        if impact_level in info.get("impact", [])
    ]


async def _render_ssp_docx(sections: list[dict], system_name: str, org_name: str) -> bytes:
    """Render SSP as DOCX bytes."""
    try:
        from ai_orchestrator.src.mcp_servers.template_render import render_full_proposal_docx

        section_list = [
            {"title": s["name"].replace("_", " ").title(), "content": s["content"], "level": 1}
            for s in sections
        ]
        result = await render_full_proposal_docx(
            proposal_id=f"ssp_{system_name.lower().replace(' ', '_')}",
            sections=section_list,
            cover_page={
                "opportunity_name": f"System Security Plan – {system_name}",
                "company_name": org_name,
                "date": __import__("datetime").date.today().isoformat(),
            },
        )
        return result.get("docx_bytes", b"")
    except Exception as exc:
        logger.warning("SSP DOCX render failed: %s", exc)
        return b""
