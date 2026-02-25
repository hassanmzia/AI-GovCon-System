"""MCP tool server: Security control mapping, SSP generation, compliance analysis."""
import logging
import os
from typing import Any

import httpx

logger = logging.getLogger("ai_orchestrator.mcp.security_compliance")

_DJANGO_URL = os.getenv("DJANGO_API_URL", "http://django-api:8001")
_SERVICE_TOKEN = os.getenv("DJANGO_SERVICE_TOKEN", "")


def _headers() -> dict:
    return {"Authorization": f"Bearer {_SERVICE_TOKEN}"} if _SERVICE_TOKEN else {}


async def search_security_controls(
    query: str,
    framework: str | None = None,
    family: str | None = None,
    baseline: str | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Search security controls across frameworks by semantic similarity.

    Args:
        query: Security requirement or capability description.
        framework: Filter by framework ("NIST_800_53", "NIST_800_171", "FedRAMP",
                   "CMMC", "HIPAA", "HITRUST", "SOC2").
        family: Control family filter (e.g. "AC", "IA", "AU", "SC").
        baseline: FedRAMP/NIST baseline ("low", "moderate", "high").
        limit: Max results.

    Returns:
        List of matching controls with ID, title, description, and guidance.
    """
    try:
        params: dict[str, Any] = {"q": query, "limit": limit}
        if framework:
            params["framework"] = framework
        if family:
            params["family"] = family
        if baseline:
            params["baseline"] = baseline

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{_DJANGO_URL}/api/security/controls/",
                params=params,
                headers=_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.warning("Security control search API failed, using vector search: %s", exc)

    from src.mcp_servers.vector_search import semantic_search

    filters: dict[str, Any] = {}
    if framework:
        filters["framework"] = framework
    if family:
        filters["family"] = family

    return await semantic_search(
        query=query,
        table="security_compliance_securitycontrol",
        embedding_column="embedding",
        text_column="description",
        extra_filters=filters,
        limit=limit,
    )


async def map_requirement_to_controls(
    requirement_text: str,
    applicable_frameworks: list[str] | None = None,
    limit_per_framework: int = 3,
) -> dict[str, Any]:
    """Map a security requirement to relevant security controls across frameworks.

    Args:
        requirement_text: The security requirement to map (e.g. "encrypt data at rest").
        applicable_frameworks: Frameworks to check (defaults to common federal frameworks).
        limit_per_framework: Max controls per framework.

    Returns:
        Dict with requirement, control_mappings (by framework), confidence scores.
    """
    frameworks = applicable_frameworks or ["NIST_800_53", "NIST_800_171", "FedRAMP", "CMMC"]

    mappings: dict[str, list[dict]] = {}
    for fw in frameworks:
        controls = await search_security_controls(
            query=requirement_text, framework=fw, limit=limit_per_framework
        )
        mappings[fw] = controls

    return {
        "requirement": requirement_text,
        "control_mappings": mappings,
        "frameworks_checked": frameworks,
        "total_controls_found": sum(len(v) for v in mappings.values()),
    }


async def generate_ssp_section(
    deal_id: str,
    section_type: str,
    control_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Generate a System Security Plan (SSP) section.

    Args:
        deal_id: Deal UUID.
        section_type: SSP section to generate:
            "system_identification", "system_environment", "interconnections",
            "control_implementation", "continuous_monitoring", "poam",
            "incident_response", "configuration_management", "contingency", "access_control".
        control_ids: Specific control IDs to include (generates all applicable if None).

    Returns:
        Dict with section_type, content (markdown), control_count, status.
    """
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{_DJANGO_URL}/api/security/ssp/{deal_id}/generate-section/",
                json={"section_type": section_type, "control_ids": control_ids or []},
                headers=_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("SSP section generation failed: %s", exc)
        return {
            "deal_id": deal_id,
            "section_type": section_type,
            "content": f"[{section_type} section to be generated]",
            "error": str(exc),
        }


async def assess_cmmc_readiness(
    deal_id: str,
    target_level: int = 2,
) -> dict[str, Any]:
    """Assess CMMC readiness for an opportunity.

    Args:
        deal_id: Deal UUID.
        target_level: CMMC level (1, 2, or 3).

    Returns:
        Dict with readiness_score, practices_met, practices_gaps, estimated_timeline.
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{_DJANGO_URL}/api/security/cmmc-readiness/",
                json={"deal_id": deal_id, "target_level": target_level},
                headers=_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("CMMC readiness assessment failed: %s", exc)
        return {
            "deal_id": deal_id,
            "target_level": target_level,
            "readiness_score": None,
            "practices_met": [],
            "practices_gaps": [],
            "error": str(exc),
        }


async def framework_crosswalk(
    source_framework: str,
    target_frameworks: list[str],
    control_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Generate a cross-walk matrix between security frameworks.

    Args:
        source_framework: Source framework (e.g. "NIST_800_53").
        target_frameworks: Target frameworks to cross-walk to.
        control_ids: Optional specific controls to cross-walk.

    Returns:
        Dict with source_framework, crosswalk_matrix (source_control → target_controls).
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{_DJANGO_URL}/api/security/framework-crosswalk/",
                json={
                    "source_framework": source_framework,
                    "target_frameworks": target_frameworks,
                    "control_ids": control_ids or [],
                },
                headers=_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("Framework crosswalk failed: %s", exc)
        return {
            "source_framework": source_framework,
            "target_frameworks": target_frameworks,
            "crosswalk_matrix": {},
            "error": str(exc),
        }


async def analyze_compliance_gaps(
    deal_id: str,
    identified_requirements: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Identify compliance gaps for a deal.

    Args:
        deal_id: Deal UUID.
        identified_requirements: Pre-identified requirements list (fetched from deal if None).

    Returns:
        Dict with gaps (list), risk_ratings, recommended_mitigations, poam_candidates.
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{_DJANGO_URL}/api/security/gap-analysis/{deal_id}/",
                json={"requirements": identified_requirements or []},
                headers=_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("Compliance gap analysis failed for %s: %s", deal_id, exc)
        return {
            "deal_id": deal_id,
            "gaps": [],
            "risk_ratings": {},
            "error": str(exc),
        }


async def draft_security_narrative(
    control_id: str,
    system_description: str,
    implementation_details: str | None = None,
) -> dict[str, Any]:
    """Draft an SSP-style implementation narrative for a security control.

    Args:
        control_id: Control ID (e.g. "AC-2", "IA-5", "CMMC-2.1.1").
        system_description: Description of the system being secured.
        implementation_details: Optional existing implementation notes.

    Returns:
        Dict with control_id, narrative, implementation_status, evidence_types.
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{_DJANGO_URL}/api/security/draft-narrative/",
                json={
                    "control_id": control_id,
                    "system_description": system_description,
                    "implementation_details": implementation_details or "",
                },
                headers=_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("Security narrative draft failed for %s: %s", control_id, exc)
        return {
            "control_id": control_id,
            "narrative": f"[Implementation narrative for {control_id} to be drafted]",
            "error": str(exc),
        }


async def search_compliance_evidence(
    control_id: str,
    evidence_types: list[str] | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Search the compliance evidence library for reusable evidence artifacts.

    Args:
        control_id: Security control ID.
        evidence_types: Filter by type ("policy", "procedure", "config", "test_result", "audit_report").
        limit: Max results.

    Returns:
        List of evidence artifacts with title, type, description, and file reference.
    """
    try:
        params: dict[str, Any] = {"control_id": control_id, "limit": limit}
        if evidence_types:
            params["types"] = ",".join(evidence_types)

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{_DJANGO_URL}/api/security/evidence/",
                params=params,
                headers=_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("Evidence search failed for %s: %s", control_id, exc)
        return []
