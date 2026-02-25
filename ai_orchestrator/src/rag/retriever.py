"""RAG pipeline using pgvector for semantic document retrieval."""
import logging
import os
from typing import Any

logger = logging.getLogger("ai_orchestrator.rag.retriever")

DATABASE_URL = os.getenv("DATABASE_URL", "")


# ── Embedding generation ──────────────────────────────────────────────────────

async def _generate_embedding(text: str) -> list[float]:
    """
    Generate a text embedding vector.

    Uses OpenAI's text-embedding-3-small model when an API key is available.
    Falls back to a zero vector for local/offline environments.

    The vector dimension is 1536 (text-embedding-3-small default).
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.debug("OPENAI_API_KEY not set; returning zero vector for embedding.")
        return [0.0] * 1536

    try:
        import openai  # type: ignore

        client = openai.AsyncOpenAI(api_key=api_key)
        response = await client.embeddings.create(
            input=text,
            model="text-embedding-3-small",
        )
        return response.data[0].embedding
    except Exception as exc:
        logger.warning("Embedding generation failed, returning zero vector: %s", exc)
        return [0.0] * 1536


# ── Database connection helpers ───────────────────────────────────────────────

async def _get_connection():
    """
    Create an asyncpg connection with pgvector registered.

    Returns None if DATABASE_URL is not configured.
    """
    if not DATABASE_URL:
        logger.debug("DATABASE_URL not configured; skipping pgvector connection.")
        return None
    try:
        import asyncpg  # type: ignore
        from pgvector.asyncpg import register_vector  # type: ignore

        conn = await asyncpg.connect(DATABASE_URL)
        await register_vector(conn)
        return conn
    except Exception as exc:
        logger.warning("Could not connect to pgvector database: %s", exc)
        return None


# ── RAG Retriever ─────────────────────────────────────────────────────────────

class RAGRetriever:
    """
    Retrieves relevant documents from pgvector for context injection.

    Used by agents to pull past performance, proposals, and knowledge base entries.
    The retriever supports semantic similarity search via pgvector's <-> distance operator.

    Typical usage:
        retriever = RAGRetriever()
        docs = await retriever.get_similar_past_performance("cybersecurity SOC operations", top_k=5)
    """

    # ── Past performance ──────────────────────────────────────────────────────

    async def get_similar_past_performance(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Search past performance records by semantic similarity.

        Args:
            query: Natural language search query.
            top_k: Number of top results to return.

        Returns:
            List of dicts with keys: title, content, similarity_score, metadata.
        """
        embedding = await _generate_embedding(query)
        conn = await _get_connection()

        if conn is None:
            logger.debug("No DB connection; returning empty past performance results.")
            return []

        try:
            rows = await conn.fetch(
                """
                SELECT
                    id,
                    title,
                    content,
                    metadata,
                    1 - (embedding <-> $1::vector) AS similarity_score
                FROM past_performance
                ORDER BY embedding <-> $1::vector
                LIMIT $2
                """,
                embedding,
                top_k,
            )
            return [
                {
                    "id": str(row["id"]),
                    "title": row["title"],
                    "content": row["content"],
                    "similarity_score": float(row["similarity_score"]),
                    "metadata": dict(row["metadata"]) if row["metadata"] else {},
                }
                for row in rows
            ]
        except Exception as exc:
            logger.error("Error querying past_performance: %s", exc)
            return []
        finally:
            await conn.close()

    # ── Proposals ─────────────────────────────────────────────────────────────

    async def get_similar_proposals(
        self,
        query: str,
        top_k: int = 3,
    ) -> list[dict[str, Any]]:
        """
        Search past proposals for relevant sections.

        Args:
            query: Natural language search query (e.g., a section topic or requirement).
            top_k: Number of top results to return.

        Returns:
            List of dicts with keys: title, content, section, similarity_score, metadata.
        """
        embedding = await _generate_embedding(query)
        conn = await _get_connection()

        if conn is None:
            logger.debug("No DB connection; returning empty proposal results.")
            return []

        try:
            rows = await conn.fetch(
                """
                SELECT
                    id,
                    title,
                    section,
                    content,
                    metadata,
                    1 - (embedding <-> $1::vector) AS similarity_score
                FROM proposal_sections
                ORDER BY embedding <-> $1::vector
                LIMIT $2
                """,
                embedding,
                top_k,
            )
            return [
                {
                    "id": str(row["id"]),
                    "title": row["title"],
                    "section": row["section"],
                    "content": row["content"],
                    "similarity_score": float(row["similarity_score"]),
                    "metadata": dict(row["metadata"]) if row["metadata"] else {},
                }
                for row in rows
            ]
        except Exception as exc:
            logger.error("Error querying proposal_sections: %s", exc)
            return []
        finally:
            await conn.close()

    # ── Knowledge base ────────────────────────────────────────────────────────

    async def get_knowledge_base_entries(
        self,
        query: str,
        top_k: int = 5,
        category: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search the knowledge base (FAR clauses, pricing data, capabilities, etc.).

        Args:
            query: Natural language search query.
            top_k: Number of top results to return.
            category: Optional category filter (e.g., 'far_clause', 'capability', 'pricing').

        Returns:
            List of dicts with keys: title, content, category, similarity_score, metadata.
        """
        embedding = await _generate_embedding(query)
        conn = await _get_connection()

        if conn is None:
            logger.debug("No DB connection; returning empty knowledge base results.")
            return []

        try:
            if category:
                rows = await conn.fetch(
                    """
                    SELECT
                        id,
                        title,
                        category,
                        content,
                        metadata,
                        1 - (embedding <-> $1::vector) AS similarity_score
                    FROM knowledge_base
                    WHERE category = $3
                    ORDER BY embedding <-> $1::vector
                    LIMIT $2
                    """,
                    embedding,
                    top_k,
                    category,
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT
                        id,
                        title,
                        category,
                        content,
                        metadata,
                        1 - (embedding <-> $1::vector) AS similarity_score
                    FROM knowledge_base
                    ORDER BY embedding <-> $1::vector
                    LIMIT $2
                    """,
                    embedding,
                    top_k,
                )
            return [
                {
                    "id": str(row["id"]),
                    "title": row["title"],
                    "category": row["category"],
                    "content": row["content"],
                    "similarity_score": float(row["similarity_score"]),
                    "metadata": dict(row["metadata"]) if row["metadata"] else {},
                }
                for row in rows
            ]
        except Exception as exc:
            logger.error("Error querying knowledge_base: %s", exc)
            return []
        finally:
            await conn.close()

    # ── Convenience: retrieve context for agents ──────────────────────────────

    async def get_context_for_opportunity(
        self,
        query: str,
        include_past_performance: bool = True,
        include_proposals: bool = True,
        include_knowledge_base: bool = True,
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Retrieve all relevant context for an opportunity in a single call.

        Returns:
            dict with keys: past_performance, proposals, knowledge_base
        """
        results: dict[str, list[dict[str, Any]]] = {
            "past_performance": [],
            "proposals": [],
            "knowledge_base": [],
        }

        if include_past_performance:
            results["past_performance"] = await self.get_similar_past_performance(query, top_k=5)
        if include_proposals:
            results["proposals"] = await self.get_similar_proposals(query, top_k=3)
        if include_knowledge_base:
            results["knowledge_base"] = await self.get_knowledge_base_entries(query, top_k=5)

        return results
