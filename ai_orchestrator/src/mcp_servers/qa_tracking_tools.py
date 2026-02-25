"""MCP tool server: Q&A lifecycle management, CO answer impact mapping, vendor question strategy."""
import logging
import os
from typing import Any

import httpx

logger = logging.getLogger("ai_orchestrator.mcp.qa_tracking")

_DJANGO_URL = os.getenv("DJANGO_API_URL", "http://django-api:8001")
_SERVICE_TOKEN = os.getenv("DJANGO_SERVICE_TOKEN", "")


def _headers() -> dict:
    return {"Authorization": f"Bearer {_SERVICE_TOKEN}"} if _SERVICE_TOKEN else {}


async def list_clarification_questions(
    deal_id: str,
    status: str | None = None,
    category: str | None = None,
) -> list[dict[str, Any]]:
    """List clarification questions for a deal.

    Args:
        deal_id: Deal UUID.
        status: Optional filter ("pending", "submitted", "answered", "withdrawn").
        category: Optional category filter (e.g. "technical", "pricing", "terms").

    Returns:
        List of question dicts with text, status, category, rfp_section_ref, and answer (if available).
    """
    try:
        params: dict[str, Any] = {"deal_id": deal_id}
        if status:
            params["status"] = status
        if category:
            params["category"] = category

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{_DJANGO_URL}/api/communications/questions/",
                params=params,
                headers=_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("Q&A list failed for deal %s: %s", deal_id, exc)
        return []


async def add_clarification_question(
    deal_id: str,
    question_text: str,
    category: str,
    rfp_section_ref: str | None = None,
    priority: int = 5,
    information_value: str | None = None,
) -> dict[str, Any]:
    """Add a clarification question to the Q&A tracker.

    Args:
        deal_id: Deal UUID.
        question_text: The question to ask.
        category: Category ("technical", "pricing", "terms", "scope", "evaluation").
        rfp_section_ref: RFP section reference (e.g. "Section L.3.2").
        priority: Priority 1-10 (10 = highest).
        information_value: Why this information is valuable.

    Returns:
        Created question dict with ID.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{_DJANGO_URL}/api/communications/questions/",
                json={
                    "deal_id": deal_id,
                    "question_text": question_text,
                    "category": category,
                    "rfp_section_ref": rfp_section_ref,
                    "priority": priority,
                    "information_value": information_value or "",
                },
                headers=_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("Add question failed: %s", exc)
        return {"error": str(exc)}


async def record_co_answer(
    question_id: str,
    answer_text: str,
    source_document: str | None = None,
    amendment_number: str | None = None,
) -> dict[str, Any]:
    """Record a Contracting Officer (CO) answer to a clarification question.

    Args:
        question_id: Question UUID.
        answer_text: The CO's answer.
        source_document: Source document reference (e.g. "Amendment 2").
        amendment_number: Amendment number if applicable.

    Returns:
        Updated question dict with answer and impact analysis.
    """
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{_DJANGO_URL}/api/communications/questions/{question_id}/answer/",
                json={
                    "answer_text": answer_text,
                    "source_document": source_document,
                    "amendment_number": amendment_number,
                },
                headers=_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("Record CO answer failed for %s: %s", question_id, exc)
        return {"question_id": question_id, "error": str(exc)}


async def analyze_answer_impact(
    answer_id: str,
    deal_id: str,
) -> dict[str, Any]:
    """Analyze how a CO answer impacts the proposal strategy and compliance matrix.

    Args:
        answer_id: Answer UUID.
        deal_id: Deal UUID.

    Returns:
        Dict with compliance_matrix_changes, pricing_impacts, scope_changes, risk_changes.
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{_DJANGO_URL}/api/communications/answers/{answer_id}/analyze-impact/",
                json={"deal_id": deal_id},
                headers=_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("Answer impact analysis failed: %s", exc)
        return {
            "answer_id": answer_id,
            "compliance_matrix_changes": [],
            "pricing_impacts": [],
            "scope_changes": [],
            "risk_changes": [],
            "error": str(exc),
        }


async def generate_question_strategy(
    deal_id: str,
    rfp_text: str | None = None,
    max_questions: int = 20,
) -> dict[str, Any]:
    """Generate a prioritized list of clarification questions using AI.

    Analyzes the RFP and deal context to identify the highest-value questions
    to ask the CO, ranked by information value.

    Args:
        deal_id: Deal UUID.
        rfp_text: Optional RFP text (loaded from deal if not provided).
        max_questions: Maximum questions to generate.

    Returns:
        Dict with questions (ranked list), strategy_notes, submission_deadline.
    """
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{_DJANGO_URL}/api/communications/question-strategy/",
                json={
                    "deal_id": deal_id,
                    "rfp_text": rfp_text or "",
                    "max_questions": max_questions,
                },
                headers=_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("Question strategy generation failed: %s", exc)
        return {
            "deal_id": deal_id,
            "questions": [],
            "strategy_notes": "",
            "error": str(exc),
        }


async def get_qa_summary(deal_id: str) -> dict[str, Any]:
    """Get a summary of Q&A activity for a deal.

    Returns:
        Dict with total_questions, answered_count, pending_count, high_impact_answers.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{_DJANGO_URL}/api/communications/qa-summary/{deal_id}/",
                headers=_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("Q&A summary failed for %s: %s", deal_id, exc)
        return {
            "deal_id": deal_id,
            "total_questions": 0,
            "answered_count": 0,
            "pending_count": 0,
            "high_impact_answers": [],
            "error": str(exc),
        }


async def draft_vendor_questions_email(
    deal_id: str,
    questions: list[dict[str, Any]],
) -> dict[str, Any]:
    """Draft a formatted vendor questions email from a list of questions.

    Args:
        deal_id: Deal UUID.
        questions: List of question dicts with text and category.

    Returns:
        Dict with subject, body, formatted_questions.
    """
    from src.mcp_servers.email_tools import draft_email

    # Format questions
    formatted = []
    for i, q in enumerate(questions, 1):
        cat = q.get("category", "General")
        text = q.get("question_text", "")
        ref = q.get("rfp_section_ref", "")
        line = f"Q{i}. [{cat}]"
        if ref:
            line += f" (Re: {ref})"
        line += f" {text}"
        formatted.append(line)

    return await draft_email(
        email_type="rfp_clarification",
        context={
            "deal_id": deal_id,
            "questions": formatted,
            "question_count": len(questions),
        },
    )
