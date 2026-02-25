"""MCP tool server: Multimodal knowledge vault search (text + image/diagram)."""
import logging
import os
from typing import Any

import httpx

logger = logging.getLogger("ai_orchestrator.mcp.knowledge_vault")

_DJANGO_URL = os.getenv("DJANGO_API_URL", "http://django-api:8001")
_SERVICE_TOKEN = os.getenv("DJANGO_SERVICE_TOKEN", "")


def _headers() -> dict:
    return {"Authorization": f"Bearer {_SERVICE_TOKEN}"} if _SERVICE_TOKEN else {}


async def search_knowledge(
    query: str,
    category: str | None = None,
    content_types: list[str] | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Search the knowledge vault using semantic similarity over text content.

    Args:
        query: Natural-language search query.
        category: Optional category filter (e.g. "architecture", "legal", "pricing").
        content_types: List of content types to include (e.g. ["text", "code"]).
        limit: Maximum results to return.

    Returns:
        List of matching knowledge vault items with relevance scores.
    """
    from src.mcp_servers.vector_search import search_knowledge_vault

    results = await search_knowledge_vault(
        query=query, category=category, limit=limit
    )
    if content_types:
        results = [r for r in results if r.get("content_type") in content_types]
    return results[:limit]


async def search_reference_architectures(
    query: str,
    technology: str | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Find reference architecture documents matching *query*.

    Returns architecture docs with full text, diagrams, and relevance scores.
    """
    from src.mcp_servers.vector_search import search_knowledge_vault

    results = await search_knowledge_vault(
        query=query, category="architecture", limit=limit * 2
    )
    if technology:
        results = [
            r for r in results
            if technology.lower() in (r.get("tags") or "").lower()
            or technology.lower() in (r.get("text") or "").lower()
        ]
    return results[:limit]


async def search_design_patterns(
    query: str,
    pattern_type: str | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Search design patterns and best practices.

    Args:
        query: What you're looking for (e.g. "microservices event-driven").
        pattern_type: Optional type filter (e.g. "agentic", "rag", "integration").
        limit: Max results.
    """
    from src.mcp_servers.vector_search import search_knowledge_vault

    effective_query = f"{pattern_type or ''} design pattern: {query}".strip()
    results = await search_knowledge_vault(
        query=effective_query, category="patterns", limit=limit * 2
    )
    if pattern_type:
        results = [
            r for r in results
            if pattern_type.lower() in (r.get("tags") or "").lower()
        ]
    return results[:limit]


async def search_diagrams(
    query: str,
    diagram_type: str | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Search for diagrams and visual assets in the knowledge vault.

    Uses CLIP image embeddings for visual similarity when available.

    Args:
        query: Description of the diagram you're looking for.
        diagram_type: Optional type filter (e.g. "architecture", "data-flow", "sequence").
        limit: Max results.

    Returns:
        List of matching diagrams with image_url, alt_text, and similarity score.
    """
    from src.mcp_servers.vector_search import semantic_search

    results = await semantic_search(
        query=query,
        table="knowledge_vault_knowledgechunk",
        embedding_column="image_embedding",
        text_column="alt_text",
        extra_filters={"content_type": "image"},
        limit=limit,
    )
    if not results:
        # Fall back to text search
        results = await search_knowledge_vault(
            query=f"{diagram_type or ''} diagram: {query}", limit=limit
        )
        results = [r for r in results if r.get("content_type") == "image"]

    if diagram_type:
        results = [
            r for r in results
            if diagram_type.lower() in (r.get("tags") or "").lower()
            or diagram_type.lower() in (r.get("alt_text") or "").lower()
        ]
    return results[:limit]


async def search_past_proposals(
    query: str,
    section_type: str | None = None,
    min_score: float | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Find relevant sections from past winning proposals.

    Args:
        query: The type of content or theme you need (e.g. "zero-trust security approach").
        section_type: Optional section filter ("technical", "management", "past_performance").
        min_score: Minimum proposal score to filter by (0-100).
        limit: Max results.
    """
    from src.mcp_servers.vector_search import search_proposals

    results = await search_proposals(query=query, section_type=section_type, limit=limit)
    if min_score is not None:
        results = [r for r in results if float(r.get("score", 0) or 0) >= min_score]
    return results[:limit]


async def add_knowledge_item(
    title: str,
    content: str,
    category: str,
    content_type: str = "text",
    tags: list[str] | None = None,
    source_url: str | None = None,
) -> dict[str, Any]:
    """Add a new item to the knowledge vault.

    Args:
        title: Display title for the knowledge item.
        content: Full text content.
        category: Category (e.g. "architecture", "legal", "pricing").
        content_type: Type of content ("text", "code", "markdown", "image").
        tags: Optional list of tags.
        source_url: Optional source URL.

    Returns:
        Created knowledge vault item with ID.
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{_DJANGO_URL}/api/knowledge-vault/items/",
                json={
                    "title": title,
                    "content": content,
                    "category": category,
                    "content_type": content_type,
                    "tags": tags or [],
                    "source_url": source_url,
                },
                headers=_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("Knowledge vault add failed: %s", exc)
        return {"error": str(exc)}


async def get_knowledge_item(item_id: str) -> dict[str, Any]:
    """Retrieve a specific knowledge vault item by ID."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{_DJANGO_URL}/api/knowledge-vault/items/{item_id}/",
                headers=_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("Knowledge vault get failed for %s: %s", item_id, exc)
        return {"error": str(exc), "id": item_id}
