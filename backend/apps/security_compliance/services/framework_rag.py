"""Framework RAG: retrieves security framework guidance from the knowledge vault."""
import logging
from typing import Any

logger = logging.getLogger("ai_deal_manager.security.framework_rag")


async def search_framework_guidance(
    query: str,
    frameworks: list[str] | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Search security framework guidance using RAG.

    Args:
        query: Natural language query about a security requirement or topic.
        frameworks: List of framework names to filter by (e.g., ["NIST_800_53", "CMMC"]).
        limit: Max results.

    Returns:
        Ranked list of matching guidance chunks.
    """
    try:
        from ai_orchestrator.src.mcp_servers.vector_search import semantic_search

        filters: dict = {}
        if frameworks:
            filters["framework"] = frameworks[0]  # primary framework filter

        results = await semantic_search(
            query=query,
            table="security_compliance_securityframework",
            embedding_column="embedding",
            text_column="content",
            extra_filters=filters,
            limit=limit,
        )
        return results
    except Exception as exc:
        logger.warning("Framework RAG search failed: %s", exc)

    # Fallback: use embedded control knowledge
    return _fallback_keyword_search(query, frameworks, limit)


async def get_control_guidance(
    control_id: str,
    framework: str = "NIST_800_53",
) -> dict[str, Any]:
    """Get implementation guidance for a specific control."""
    results = await search_framework_guidance(
        query=f"{control_id} implementation guidance",
        frameworks=[framework],
        limit=3,
    )

    guidance_text = "\n\n".join(r.get("text", r.get("content", "")) for r in results if r)

    # Enrich with embedded control data
    from backend.apps.security_compliance.services.control_mapper import get_control_details

    ctrl = get_control_details(control_id)

    return {
        "control_id": control_id,
        "framework": framework,
        "title": ctrl.get("title", ""),
        "family": ctrl.get("family", ""),
        "retrieved_guidance": results,
        "guidance_text": guidance_text,
        "implementation_tips": _get_implementation_tips(control_id),
    }


async def search_compliance_requirements(
    topic: str,
    framework: str = "NIST_800_53",
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Search for specific compliance requirements by topic."""
    return await search_framework_guidance(
        query=f"{framework} {topic} requirements",
        frameworks=[framework],
        limit=limit,
    )


# ── Embedded guidance tips ────────────────────────────────────────────────────

_IMPLEMENTATION_TIPS: dict[str, list[str]] = {
    "AC-2": [
        "Implement automated account provisioning and de-provisioning workflows",
        "Establish 90-day review cadence for privileged accounts",
        "Use role-based access control (RBAC) aligned to least privilege",
    ],
    "AC-17": [
        "Use VPN or Zero Trust Network Access (ZTNA) for remote connections",
        "Enforce MFA for all remote access",
        "Log all remote access sessions",
    ],
    "AU-2": [
        "Enable logging for: authentication, authorization, privilege use, and system events",
        "Ensure log integrity with write-once or SIEM forwarding",
        "Define log retention of at least 90 days online, 1 year archived",
    ],
    "CM-2": [
        "Maintain golden images for OS and application baselines",
        "Use SCAP/STIG benchmarks for hardening",
        "Document all deviations with approval records",
    ],
    "IA-2": [
        "Deploy phishing-resistant MFA (FIDO2/WebAuthn preferred)",
        "Disable legacy authentication protocols (NTLM, basic auth)",
        "Integrate with PIV/CAC for federal systems",
    ],
    "SC-7": [
        "Implement network segmentation with documented trust zones",
        "Deploy NGFW with application-layer inspection",
        "Enable micro-segmentation for CUI systems",
    ],
    "SI-2": [
        "Establish 30-day patch SLA for critical vulnerabilities",
        "Run weekly vulnerability scans with automated remediation tickets",
        "Maintain patch exception process with CISO approval",
    ],
}


def _get_implementation_tips(control_id: str) -> list[str]:
    return _IMPLEMENTATION_TIPS.get(control_id.upper(), [])


def _fallback_keyword_search(
    query: str,
    frameworks: list[str] | None,
    limit: int,
) -> list[dict[str, Any]]:
    """Keyword-based fallback when vector search is unavailable."""
    from backend.apps.security_compliance.services.control_mapper import (
        NIST_800_53_CONTROLS,
        KEYWORD_TO_FAMILIES,
    )

    query_lower = query.lower()
    matched_families: set[str] = set()
    for keyword, families in KEYWORD_TO_FAMILIES.items():
        if keyword in query_lower:
            matched_families.update(families)

    results = []
    for ctrl_id, ctrl in NIST_800_53_CONTROLS.items():
        if ctrl_id.split("-")[0] in matched_families:
            results.append({
                "control_id": ctrl_id,
                "text": f"{ctrl['title']} ({ctrl['family']})",
                "content": f"NIST 800-53 {ctrl_id}: {ctrl['title']}",
                "framework": "NIST_800_53",
                "similarity": 0.7,
            })
            if len(results) >= limit:
                break
    return results
