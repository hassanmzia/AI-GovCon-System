"""Multimodal RAG: retrieval-augmented generation combining text and image search."""
import asyncio
import logging
import os
from typing import Any

logger = logging.getLogger("ai_deal_manager.knowledge_vault.multimodal_rag")

_DJANGO_API_URL = os.getenv("DJANGO_API_URL", "http://django-api:8001")
_SERVICE_TOKEN = os.getenv("DJANGO_SERVICE_TOKEN", "")


def _headers() -> dict:
    return {"Authorization": f"Bearer {_SERVICE_TOKEN}"} if _SERVICE_TOKEN else {}


async def multimodal_rag_query(
    query: str,
    modalities: list[str] | None = None,
    category: str | None = None,
    top_k: int = 10,
) -> dict[str, Any]:
    """Perform a multimodal RAG query across text and image content.

    Args:
        query: Natural language query.
        modalities: List of modalities to search: "text", "image", "code", "diagram".
                    Defaults to ["text", "image"].
        category: Optional category filter (e.g. "architecture", "past_performance").
        top_k: Number of results per modality.

    Returns:
        Dict with: query, text_results, image_results, synthesized_context.
    """
    modalities = modalities or ["text", "image"]

    tasks = []
    if "text" in modalities or "code" in modalities:
        tasks.append(_text_search(query, category=category, limit=top_k))
    else:
        tasks.append(_empty_results())

    if "image" in modalities or "diagram" in modalities:
        tasks.append(_image_search(query, limit=min(top_k, 5)))
    else:
        tasks.append(_empty_results())

    text_results, image_results = await asyncio.gather(*tasks, return_exceptions=True)

    if isinstance(text_results, Exception):
        logger.warning("Text RAG search failed: %s", text_results)
        text_results = []
    if isinstance(image_results, Exception):
        logger.warning("Image RAG search failed: %s", image_results)
        image_results = []

    synthesized = _synthesize_context(query, text_results, image_results)

    return {
        "query": query,
        "modalities": modalities,
        "category": category,
        "text_results": text_results,
        "image_results": image_results,
        "result_count": len(text_results) + len(image_results),
        "synthesized_context": synthesized,
    }


async def retrieve_for_proposal_section(
    section_type: str,
    rfp_requirements: list[dict],
    win_themes: list[str],
    top_k: int = 8,
) -> dict[str, Any]:
    """Retrieve relevant knowledge vault content for a proposal section.

    Combines multiple queries to build rich context for section generation.
    """
    # Build targeted queries for this section
    section_queries = _build_section_queries(section_type, rfp_requirements, win_themes)

    all_results: list[dict] = []
    seen_ids: set = set()

    for sq in section_queries[:3]:  # limit to 3 queries to avoid overloading
        try:
            results = await _text_search(sq, limit=top_k)
            for r in results:
                rid = r.get("id") or r.get("chunk_id", "")
                if rid and rid not in seen_ids:
                    seen_ids.add(rid)
                    all_results.append(r)
        except Exception as exc:
            logger.warning("Section retrieval failed for query %r: %s", sq, exc)

    # Rank and deduplicate
    all_results.sort(key=lambda x: x.get("similarity", 0), reverse=True)

    return {
        "section_type": section_type,
        "retrieved_chunks": all_results[:top_k],
        "chunk_count": len(all_results[:top_k]),
        "context_text": _build_context_text(all_results[:top_k]),
    }


async def find_reference_architectures(
    technology: str,
    use_case: str | None = None,
) -> list[dict[str, Any]]:
    """Find reference architecture diagrams and documentation from the vault."""
    query = f"reference architecture {technology}"
    if use_case:
        query += f" {use_case}"

    text_results = await _text_search(query, category="architecture", limit=5)
    image_results = await _image_search(query, limit=3)

    combined = []
    for r in text_results:
        r["result_type"] = "text"
        combined.append(r)
    for r in image_results:
        r["result_type"] = "image"
        combined.append(r)

    return combined


# ── Internal helpers ──────────────────────────────────────────────────────────

async def _text_search(
    query: str,
    category: str | None = None,
    limit: int = 10,
) -> list[dict]:
    """Delegate to vector_search MCP tool."""
    try:
        from ai_orchestrator.src.mcp_servers.vector_search import search_knowledge_vault

        return await search_knowledge_vault(
            query=query,
            category=category,
            limit=limit,
        )
    except Exception:
        pass

    # Fallback: direct pgvector query via Django API
    try:
        import httpx

        params: dict = {"q": query, "limit": limit}
        if category:
            params["category"] = category
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{_DJANGO_API_URL}/api/knowledge-vault/search/",
                params=params,
                headers=_headers(),
            )
            if resp.status_code == 200:
                return resp.json().get("results", [])
    except Exception as exc:
        logger.warning("Knowledge vault API search failed: %s", exc)

    return []


async def _image_search(query: str, limit: int = 5) -> list[dict]:
    """Search for images/diagrams using CLIP embeddings."""
    try:
        from ai_orchestrator.src.mcp_servers.image_search_tools import search_images_by_text

        return await search_images_by_text(query=query, limit=limit)
    except Exception as exc:
        logger.warning("Image search failed: %s", exc)
    return []


async def _empty_results() -> list:
    return []


def _synthesize_context(
    query: str,
    text_results: list[dict],
    image_results: list[dict],
) -> str:
    """Build a synthesized context string from retrieved results."""
    parts = []
    if text_results:
        parts.append(f"## Retrieved Text Context ({len(text_results)} chunks)\n")
        for i, r in enumerate(text_results[:5], 1):
            text = r.get("text", r.get("content", ""))[:400]
            source = r.get("source_id", r.get("title", f"Source {i}"))
            parts.append(f"[{i}] {source}:\n{text}\n")

    if image_results:
        parts.append(f"\n## Retrieved Diagrams/Images ({len(image_results)} items)\n")
        for r in image_results[:3]:
            title = r.get("title", r.get("filename", "Diagram"))
            parts.append(f"- {title}")

    return "\n".join(parts)


def _build_section_queries(
    section_type: str,
    rfp_requirements: list[dict],
    win_themes: list[str],
) -> list[str]:
    """Generate targeted search queries for a proposal section."""
    base_queries = {
        "executive_summary": ["executive summary win themes government proposal"],
        "technical_approach": ["technical approach methodology architecture design"],
        "management_approach": ["program management approach organizational structure"],
        "past_performance": ["past performance relevant experience similar projects"],
        "staffing_plan": ["staffing plan key personnel qualifications team"],
        "transition_plan": ["transition plan knowledge transfer phase-in"],
        "quality_plan": ["quality assurance plan QMP metrics"],
        "risk_management": ["risk management mitigation plan contingency"],
        "security_approach": ["security approach NIST CMMC zero trust FedRAMP"],
    }

    queries = base_queries.get(section_type, [section_type.replace("_", " ")])

    # Add requirement-specific queries
    for req in rfp_requirements[:2]:
        text = req.get("text", req.get("requirement", ""))
        if text and len(text) > 20:
            queries.append(text[:200])

    return queries


def _build_context_text(chunks: list[dict]) -> str:
    """Concatenate chunk text into a single context block."""
    parts = []
    for i, chunk in enumerate(chunks, 1):
        text = chunk.get("text", chunk.get("content", ""))
        source = chunk.get("source_id", chunk.get("title", f"Chunk {i}"))
        if text:
            parts.append(f"[Source: {source}]\n{text}")
    return "\n\n---\n\n".join(parts)
