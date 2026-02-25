"""MCP tool server: Legal RAG search, clause library, compliance checks, OCI, protests."""
import logging
import os
from typing import Any

import httpx

logger = logging.getLogger("ai_orchestrator.mcp.legal")

_DJANGO_URL = os.getenv("DJANGO_API_URL", "http://django-api:8001")
_SERVICE_TOKEN = os.getenv("DJANGO_SERVICE_TOKEN", "")


def _headers() -> dict:
    return {"Authorization": f"Bearer {_SERVICE_TOKEN}"} if _SERVICE_TOKEN else {}


async def legal_rag_search(
    query: str,
    source_type: str | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Semantic search across the legal knowledge base.

    Args:
        query: Legal question or topic to search.
        source_type: Filter by source type ("FAR", "DFARS", "GAO", "COFC", "statute", "regulation").
        limit: Max results.

    Returns:
        List of relevant legal knowledge entries with source, text, and relevance.
    """
    from src.mcp_servers.vector_search import semantic_search

    results = await semantic_search(
        query=query,
        table="legal_legalknowledgebase",
        embedding_column="embedding",
        text_column="content",
        extra_filters={"source_type": source_type} if source_type else {},
        limit=limit,
    )
    return results


async def clause_library_search(
    query: str,
    risk_level: str | None = None,
    requires_flow_down: bool | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Search the FAR/DFARS clause library.

    Args:
        query: Clause topic or reference number (e.g. "52.212-4" or "termination for convenience").
        risk_level: Filter by risk level ("low", "medium", "high", "critical").
        requires_flow_down: If True, only return flow-down required clauses.
        limit: Max results.

    Returns:
        List of matching clauses with risk level, negotiation guidance, and flow-down flags.
    """
    try:
        params: dict[str, Any] = {"q": query, "limit": limit}
        if risk_level:
            params["risk_level"] = risk_level
        if requires_flow_down is not None:
            params["flow_down"] = str(requires_flow_down).lower()

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{_DJANGO_URL}/api/legal/clauses/",
                params=params,
                headers=_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("Clause library search failed: %s", exc)
        return _fallback_clause_search(query)


async def contract_review(
    contract_text: str,
    contract_type: str = "prime",
    review_aspects: list[str] | None = None,
) -> dict[str, Any]:
    """Perform AI-assisted contract review.

    Args:
        contract_text: Full contract text to review.
        contract_type: Type of contract ("prime", "subcontract", "teaming", "nda", "task_order").
        review_aspects: Specific aspects to focus on (e.g. ["liability", "termination", "IP"]).

    Returns:
        Dict with risk_summary, clause_analysis, red_flags, recommendations.
    """
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{_DJANGO_URL}/api/legal/contract-review/",
                json={
                    "contract_text": contract_text,
                    "contract_type": contract_type,
                    "review_aspects": review_aspects or [],
                },
                headers=_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("Contract review API failed: %s", exc)
        return {
            "error": str(exc),
            "risk_summary": "Review could not be completed",
            "red_flags": [],
            "recommendations": [],
        }


async def compliance_check(
    deal_id: str,
    check_types: list[str] | None = None,
) -> dict[str, Any]:
    """Run FAR/DFARS compliance checks for a deal.

    Args:
        deal_id: Deal UUID.
        check_types: Optional list of check types to run:
            ["representations", "cas", "tina", "buy_american", "section_889",
             "cmmc", "sca_dba", "eeo", "small_business"]

    Returns:
        Dict with compliant (bool), issues (list), recommendations (list).
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{_DJANGO_URL}/api/legal/compliance-check/",
                json={"deal_id": deal_id, "check_types": check_types or []},
                headers=_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("Compliance check failed for deal %s: %s", deal_id, exc)
        return {
            "deal_id": deal_id,
            "compliant": None,
            "issues": [],
            "error": str(exc),
        }


async def loophole_detection(
    rfp_text: str,
    focus_areas: list[str] | None = None,
) -> dict[str, Any]:
    """Scan RFP text for ambiguities, loopholes, and favorable interpretations.

    Args:
        rfp_text: Full RFP text to analyze.
        focus_areas: Areas to focus on (e.g. ["scope", "evaluation_criteria", "pricing"]).

    Returns:
        Dict with ambiguities, favorable_interpretations, unfavorable_clauses, protest_grounds.
    """
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{_DJANGO_URL}/api/legal/loophole-detection/",
                json={"rfp_text": rfp_text, "focus_areas": focus_areas or []},
                headers=_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("Loophole detection failed: %s", exc)
        return {
            "ambiguities": [],
            "favorable_interpretations": [],
            "unfavorable_clauses": [],
            "protest_grounds": [],
            "error": str(exc),
        }


async def risk_assessment(
    contract_text: str | None = None,
    deal_id: str | None = None,
    risk_categories: list[str] | None = None,
) -> dict[str, Any]:
    """Assess legal risk for a contract or deal.

    Args:
        contract_text: Contract text to analyze (alternative to deal_id).
        deal_id: Deal UUID for context-aware risk assessment.
        risk_categories: Categories to assess: ["false_claims", "oci", "key_personnel",
            "pricing", "subcontracting", "buy_american", "section_889", "cmmc"].

    Returns:
        Dict with overall_risk (low/medium/high/critical), risk_items, mitigations.
    """
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{_DJANGO_URL}/api/legal/risk-assessment/",
                json={
                    "contract_text": contract_text,
                    "deal_id": deal_id,
                    "risk_categories": risk_categories or [],
                },
                headers=_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("Risk assessment failed: %s", exc)
        return {
            "overall_risk": "unknown",
            "risk_items": [],
            "mitigations": [],
            "error": str(exc),
        }


async def oci_assessment(
    company_name: str,
    opportunity_id: str,
    work_description: str | None = None,
) -> dict[str, Any]:
    """Assess Organizational Conflict of Interest (OCI) risk.

    Args:
        company_name: Offeror company name.
        opportunity_id: Opportunity UUID.
        work_description: Description of the work to be performed.

    Returns:
        Dict with oci_risk (none/low/medium/high), oci_types, mitigation_plan.
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{_DJANGO_URL}/api/legal/oci-assessment/",
                json={
                    "company_name": company_name,
                    "opportunity_id": opportunity_id,
                    "work_description": work_description or "",
                },
                headers=_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("OCI assessment failed: %s", exc)
        return {
            "oci_risk": "unknown",
            "oci_types": [],
            "mitigation_plan": "",
            "error": str(exc),
        }


async def protest_precedent_search(
    issue: str,
    agency: str | None = None,
    decision_body: str | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Search bid protest precedents relevant to *issue*.

    Args:
        issue: Legal issue to research (e.g. "best value tradeoff documentation").
        agency: Optional agency to filter by.
        decision_body: Filter by body ("GAO", "COFC", "BCA").
        limit: Max results.

    Returns:
        List of precedent decisions with case number, summary, and holding.
    """
    from src.mcp_servers.vector_search import semantic_search

    filters: dict[str, Any] = {"document_type": "protest_decision"}
    if decision_body:
        filters["source"] = decision_body

    results = await semantic_search(
        query=f"bid protest: {issue}",
        table="legal_legalknowledgebase",
        embedding_column="embedding",
        text_column="content",
        extra_filters=filters,
        limit=limit,
    )
    return results


async def web_legal_search(
    query: str,
    jurisdiction: str = "federal",
    limit: int = 5,
) -> dict[str, Any]:
    """Search the web for legal information and regulations.

    Args:
        query: Legal search query.
        jurisdiction: "federal", "state", or specific state name.
        limit: Max results.

    Returns:
        Dict with query, results (list of {title, url, snippet}).
    """
    from src.mcp_servers.web_research_tools import web_search

    enhanced_query = f"federal government contract law {query} FAR DFARS"
    if jurisdiction != "federal":
        enhanced_query = f"{jurisdiction} law {query}"

    return await web_search(enhanced_query, num_results=limit)


# ── Internal helpers ──────────────────────────────────────────────────────────

def _fallback_clause_search(query: str) -> list[dict]:
    """Return common FAR clauses matching *query* when DB is unavailable."""
    common_clauses = [
        {
            "clause_number": "52.212-4",
            "title": "Contract Terms and Conditions – Commercial Products and Commercial Services",
            "risk_level": "medium",
            "flow_down_required": True,
        },
        {
            "clause_number": "52.215-2",
            "title": "Audit and Records – Negotiation",
            "risk_level": "medium",
            "flow_down_required": False,
        },
        {
            "clause_number": "52.227-14",
            "title": "Rights in Data – General",
            "risk_level": "high",
            "flow_down_required": True,
        },
        {
            "clause_number": "252.204-7012",
            "title": "Safeguarding Covered Defense Information",
            "risk_level": "high",
            "flow_down_required": True,
        },
    ]
    q_lower = query.lower()
    return [c for c in common_clauses if q_lower in c["title"].lower() or q_lower in c["clause_number"]]
