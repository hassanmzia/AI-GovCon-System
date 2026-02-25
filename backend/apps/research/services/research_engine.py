"""Research engine: orchestrates web search, gov DB queries, and report generation."""
import asyncio
import logging
from typing import Any

import httpx

logger = logging.getLogger("ai_deal_manager.research.engine")

_AI_ORCHESTRATOR_URL = __import__("os").getenv("AI_ORCHESTRATOR_URL", "http://ai-orchestrator:8002")
_DJANGO_SERVICE_TOKEN = __import__("os").getenv("DJANGO_SERVICE_TOKEN", "")


def _headers() -> dict:
    return {"Authorization": f"Bearer {_DJANGO_SERVICE_TOKEN}"} if _DJANGO_SERVICE_TOKEN else {}


# ── Research pipeline ─────────────────────────────────────────────────────────

async def run_research(
    topic: str,
    research_type: str = "general",
    deal_id: str | None = None,
    depth: str = "standard",  # "quick" | "standard" | "deep"
) -> dict[str, Any]:
    """Run a full research pipeline for *topic*.

    Args:
        topic: The research subject.
        research_type: One of "general", "competitor", "agency", "technology", "regulatory".
        deal_id: Optional deal context for targeted research.
        depth: Controls how many sources to query and how much synthesis to do.

    Returns:
        Dict with keys: topic, research_type, sources, findings, summary, citations.
    """
    from backend.apps.research.services.web_searcher import search_web
    from backend.apps.research.services.gov_db_searcher import search_gov_databases
    from backend.apps.research.services.report_generator import generate_research_report

    logger.info("Starting research: topic=%r type=%s depth=%s", topic, research_type, depth)

    # Determine search limits based on depth
    web_limit = {"quick": 5, "standard": 10, "deep": 20}.get(depth, 10)
    gov_limit = {"quick": 3, "standard": 8, "deep": 15}.get(depth, 8)

    # Run web and gov searches in parallel
    web_task = search_web(topic, research_type=research_type, limit=web_limit)
    gov_task = search_gov_databases(topic, research_type=research_type, limit=gov_limit)

    web_results, gov_results = await asyncio.gather(web_task, gov_task, return_exceptions=True)

    if isinstance(web_results, Exception):
        logger.warning("Web search failed: %s", web_results)
        web_results = []
    if isinstance(gov_results, Exception):
        logger.warning("Gov DB search failed: %s", gov_results)
        gov_results = []

    all_sources = list(web_results) + list(gov_results)
    logger.info("Collected %d total sources for research", len(all_sources))

    # Generate synthesized report
    report = await generate_research_report(
        topic=topic,
        research_type=research_type,
        sources=all_sources,
        deal_id=deal_id,
    )

    return {
        "topic": topic,
        "research_type": research_type,
        "deal_id": deal_id,
        "depth": depth,
        "source_count": len(all_sources),
        "web_sources": web_results if not isinstance(web_results, Exception) else [],
        "gov_sources": gov_results if not isinstance(gov_results, Exception) else [],
        "findings": report.get("findings", []),
        "summary": report.get("summary", ""),
        "citations": report.get("citations", []),
        "key_facts": report.get("key_facts", []),
    }


async def research_agency(agency_name: str, deal_id: str | None = None) -> dict[str, Any]:
    """Research a specific government agency.

    Returns procurement patterns, key contacts, budget trends, and strategic priorities.
    """
    return await run_research(
        topic=f"{agency_name} government agency procurement strategy budget",
        research_type="agency",
        deal_id=deal_id,
        depth="standard",
    )


async def research_competitor(company_name: str, deal_id: str | None = None) -> dict[str, Any]:
    """Research a specific competitor company."""
    return await run_research(
        topic=f"{company_name} government contracts capabilities past performance",
        research_type="competitor",
        deal_id=deal_id,
        depth="standard",
    )


async def research_technology(technology: str, deal_id: str | None = None) -> dict[str, Any]:
    """Research a specific technology or solution space."""
    return await run_research(
        topic=f"{technology} government federal implementation best practices",
        research_type="technology",
        deal_id=deal_id,
        depth="standard",
    )


async def research_regulatory_requirement(requirement: str) -> dict[str, Any]:
    """Research a regulatory requirement, compliance framework, or policy."""
    return await run_research(
        topic=requirement,
        research_type="regulatory",
        depth="deep",
    )
