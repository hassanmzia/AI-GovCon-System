"""MCP tool server: pgvector-based semantic similarity search for RAG."""
import logging
import os
from typing import Any

logger = logging.getLogger("ai_orchestrator.mcp.vector_search")

_DB_URL = os.getenv("DATABASE_URL", "")
_DEFAULT_LIMIT = 10
_DEFAULT_THRESHOLD = 0.65


async def semantic_search(
    query: str,
    table: str = "knowledge_vault_knowledgechunk",
    embedding_column: str = "text_embedding",
    text_column: str = "text",
    extra_filters: dict | None = None,
    limit: int = _DEFAULT_LIMIT,
    threshold: float = _DEFAULT_THRESHOLD,
) -> list[dict[str, Any]]:
    """Perform a pgvector cosine-similarity search.

    Args:
        query: Natural-language query to embed and search.
        table: Fully-qualified table name to search (Django app_model format).
        embedding_column: Name of the vector column.
        text_column: Name of the text content column.
        extra_filters: Optional SQL equality filters (column → value dict).
        limit: Max number of results to return.
        threshold: Minimum cosine similarity score (0-1).

    Returns:
        List of result dicts, each containing text, similarity, and metadata.
    """
    from src.rag.embeddings import embed_text

    query_vec = await embed_text(query)
    return await _vector_search(
        query_vec=query_vec,
        table=table,
        embedding_column=embedding_column,
        text_column=text_column,
        extra_filters=extra_filters or {},
        limit=limit,
        threshold=threshold,
    )


async def search_knowledge_vault(
    query: str,
    category: str | None = None,
    content_type: str | None = None,
    limit: int = _DEFAULT_LIMIT,
) -> list[dict[str, Any]]:
    """Search the multimodal knowledge vault for *query*.

    Args:
        query: Free-text search query.
        category: Optional category filter (e.g. "architecture", "legal").
        content_type: Optional content type filter (e.g. "text", "image", "code").
        limit: Max results.

    Returns:
        Ranked list of matching knowledge vault chunks.
    """
    filters: dict[str, Any] = {}
    if category:
        filters["category"] = category
    if content_type:
        filters["content_type"] = content_type

    return await semantic_search(
        query=query,
        table="knowledge_vault_knowledgechunk",
        embedding_column="text_embedding",
        extra_filters=filters,
        limit=limit,
    )


async def search_past_performance(
    query: str,
    min_contract_value: float | None = None,
    limit: int = _DEFAULT_LIMIT,
) -> list[dict[str, Any]]:
    """Find relevant past performance projects for *query*.

    Returns ranked past performance records with relevance scores.
    """
    filters: dict[str, Any] = {}
    results = await semantic_search(
        query=query,
        table="past_performance_pastperformance",
        embedding_column="embedding",
        text_column="narrative",
        extra_filters=filters,
        limit=limit * 2,  # over-fetch then filter
    )
    if min_contract_value is not None:
        results = [
            r for r in results
            if float(r.get("contract_value", 0) or 0) >= min_contract_value
        ]
    return results[:limit]


async def search_proposals(
    query: str,
    section_type: str | None = None,
    limit: int = _DEFAULT_LIMIT,
) -> list[dict[str, Any]]:
    """Search historical proposal sections for relevant content.

    Useful for finding proven language and approaches from winning proposals.
    """
    filters: dict[str, Any] = {}
    if section_type:
        filters["section_type"] = section_type

    return await semantic_search(
        query=query,
        table="proposals_proposalsection",
        embedding_column="embedding",
        text_column="content",
        extra_filters=filters,
        limit=limit,
    )


async def search_rfp_requirements(
    query: str,
    rfp_document_id: str | None = None,
    requirement_type: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Search RFP requirements by semantic similarity.

    Args:
        query: Search query (e.g. "technical evaluation criteria").
        rfp_document_id: Limit search to a specific RFP document.
        requirement_type: Filter by type (e.g. "shall", "should", "evaluation").
        limit: Max results.
    """
    filters: dict[str, Any] = {}
    if rfp_document_id:
        filters["rfp_document_id"] = rfp_document_id
    if requirement_type:
        filters["requirement_type"] = requirement_type

    return await semantic_search(
        query=query,
        table="rfp_rfprequirement",
        embedding_column="embedding",
        text_column="text",
        extra_filters=filters,
        limit=limit,
    )


# ── Internal pgvector query ────────────────────────────────────────────────────

async def _vector_search(
    query_vec: list[float],
    table: str,
    embedding_column: str,
    text_column: str,
    extra_filters: dict,
    limit: int,
    threshold: float,
) -> list[dict[str, Any]]:
    """Execute a pgvector cosine similarity query against *table*."""
    if not _DB_URL:
        logger.warning("DATABASE_URL not set; returning empty search results")
        return []

    try:
        import asyncpg  # type: ignore

        vec_str = "[" + ",".join(str(v) for v in query_vec) + "]"

        where_clauses = [f"1 - ({embedding_column} <=> '{vec_str}'::vector) >= {threshold}"]
        params: list[Any] = []
        param_idx = 1
        for col, val in extra_filters.items():
            where_clauses.append(f"{col} = ${param_idx}")
            params.append(val)
            param_idx += 1

        where_sql = " AND ".join(where_clauses)
        sql = f"""
            SELECT *, 1 - ({embedding_column} <=> '{vec_str}'::vector) AS similarity
            FROM {table}
            WHERE {where_sql}
            ORDER BY similarity DESC
            LIMIT {limit}
        """

        conn = await asyncpg.connect(_DB_URL)
        try:
            rows = await conn.fetch(sql, *params)
            return [dict(r) for r in rows]
        finally:
            await conn.close()

    except Exception as exc:
        logger.error("pgvector search failed on %s: %s", table, exc)
        return []
