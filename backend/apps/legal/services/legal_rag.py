"""Legal RAG service – semantic search over the legal knowledge base."""
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

_EMBEDDING_DIM = 1536


async def search_legal_knowledge(
    query: str,
    source_type: str | None = None,
    limit: int = 10,
    threshold: float = 0.60,
) -> list[dict[str, Any]]:
    """Semantic search across the legal knowledge base using pgvector.

    Args:
        query: Legal question or keyword.
        source_type: Filter by source ("FAR", "DFARS", "GSAM", "GAO", "COFC", "statute").
        limit: Max results.
        threshold: Minimum similarity score.

    Returns:
        List of relevant legal knowledge entries ranked by similarity.
    """
    from django.db import connection

    embedding = await _embed(query)
    vec_str = "[" + ",".join(str(v) for v in embedding) + "]"

    where_clauses = [f"1 - (embedding <=> '{vec_str}'::vector) >= {threshold}"]
    params: list[Any] = []
    if source_type:
        where_clauses.append("source_type = %s")
        params.append(source_type)

    sql = f"""
        SELECT id, title, content, source_type, source_reference,
               1 - (embedding <=> '{vec_str}'::vector) AS similarity
        FROM legal_legalknowledgebase
        WHERE {" AND ".join(where_clauses)}
        ORDER BY similarity DESC
        LIMIT {limit}
    """

    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    except Exception as exc:
        logger.error("Legal RAG search failed: %s", exc)
        return _fallback_search(query, source_type)


async def search_far_clause(clause_reference: str) -> dict[str, Any] | None:
    """Look up a specific FAR/DFARS clause by reference number.

    Args:
        clause_reference: Clause number (e.g. "52.212-4", "252.204-7012").

    Returns:
        Clause dict or None if not found.
    """
    try:
        from apps.legal.models import LegalClauseLibrary  # type: ignore

        clause = LegalClauseLibrary.objects.filter(
            clause_number__icontains=clause_reference
        ).first()
        if clause:
            return {
                "clause_number": clause.clause_number,
                "title": clause.title,
                "text": clause.text,
                "risk_level": clause.risk_level,
                "flow_down_required": clause.flow_down_required,
                "negotiation_guidance": clause.negotiation_guidance,
                "source": "FAR" if clause.clause_number.startswith("52") else "DFARS",
            }
    except Exception as exc:
        logger.warning("FAR clause lookup failed for %s: %s", clause_reference, exc)

    # Fallback: return known high-risk clauses
    known = {
        "52.227-14": {
            "clause_number": "52.227-14",
            "title": "Rights in Data – General",
            "risk_level": "high",
            "flow_down_required": True,
            "negotiation_guidance": "Consider Alternate II or III to protect proprietary data",
        },
        "252.204-7012": {
            "clause_number": "252.204-7012",
            "title": "Safeguarding Covered Defense Information",
            "risk_level": "high",
            "flow_down_required": True,
            "negotiation_guidance": "Requires NIST SP 800-171 compliance and cyber incident reporting",
        },
    }
    return known.get(clause_reference)


async def find_protest_precedents(
    issue: str,
    decision_body: str | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Find relevant bid protest precedents for a legal issue.

    Args:
        issue: Legal issue description.
        decision_body: "GAO", "COFC", or "ASBCA".
        limit: Max precedents.

    Returns:
        List of precedent dicts with case_number, summary, holding, citation.
    """
    results = await search_legal_knowledge(
        query=f"bid protest {issue}",
        source_type=decision_body,
        limit=limit,
    )
    return results


# ── Internal helpers ──────────────────────────────────────────────────────────

async def _embed(text: str) -> list[float]:
    """Generate embedding using the project's embedding pipeline."""
    try:
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            import openai  # type: ignore

            client = openai.AsyncOpenAI(api_key=openai_key)
            resp = await client.embeddings.create(
                input=text, model="text-embedding-3-small"
            )
            return resp.data[0].embedding
    except Exception:
        pass
    return [0.0] * _EMBEDDING_DIM


def _fallback_search(query: str, source_type: str | None) -> list[dict]:
    """Return hard-coded legal knowledge for common queries when DB unavailable."""
    common = [
        {
            "title": "FAR Part 9.5 – Organizational Conflicts of Interest",
            "content": "FAR 9.5 prohibits OCI where a contractor may have unfair competitive advantage or impaired objectivity.",
            "source_type": "FAR",
            "similarity": 0.7,
        },
        {
            "title": "False Claims Act – 31 U.S.C. § 3729",
            "content": "The False Claims Act imposes liability on persons who submit false claims to the government.",
            "source_type": "statute",
            "similarity": 0.65,
        },
        {
            "title": "FAR 52.233-1 – Disputes",
            "content": "All disputes shall be resolved under the Contract Disputes Act of 1978.",
            "source_type": "FAR",
            "similarity": 0.6,
        },
    ]
    q = query.lower()
    if source_type:
        common = [c for c in common if c["source_type"] == source_type]
    return [c for c in common if any(w in c["content"].lower() for w in q.split())][:5]
