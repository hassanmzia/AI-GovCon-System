"""Q&A lifecycle management service."""
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


async def get_questions(
    deal_id: str,
    status: str | None = None,
    category: str | None = None,
) -> list[dict[str, Any]]:
    """Get clarification questions for a deal.

    Returns:
        List of question dicts.
    """
    try:
        from apps.communications.models import ClarificationQuestion  # type: ignore

        qs = ClarificationQuestion.objects.filter(deal_id=deal_id)
        if status:
            qs = qs.filter(status=status)
        if category:
            qs = qs.filter(category=category)

        return list(qs.order_by("-priority", "created_at").values())
    except Exception as exc:
        logger.error("Q&A get failed: %s", exc)
        return []


async def add_question(
    deal_id: str,
    question_text: str,
    category: str,
    rfp_section_ref: str | None = None,
    priority: int = 5,
    information_value: str = "",
) -> dict[str, Any]:
    """Add a clarification question to the tracker.

    Returns:
        Created question dict.
    """
    try:
        from apps.communications.models import ClarificationQuestion  # type: ignore

        question = ClarificationQuestion.objects.create(
            deal_id=deal_id,
            question_text=question_text,
            category=category,
            rfp_section_ref=rfp_section_ref or "",
            priority=priority,
            information_value=information_value,
            status="pending",
        )
        return {
            "id": str(question.id),
            "deal_id": deal_id,
            "question_text": question_text,
            "category": category,
            "priority": priority,
            "status": "pending",
        }
    except Exception as exc:
        logger.error("Add question failed: %s", exc)
        return {"error": str(exc)}


async def record_answer(
    question_id: str,
    answer_text: str,
    source_document: str = "",
    amendment_number: str = "",
) -> dict[str, Any]:
    """Record a CO answer for a question.

    Returns:
        Updated question with answer.
    """
    try:
        from apps.communications.models import ClarificationQuestion, ClarificationAnswer  # type: ignore

        question = ClarificationQuestion.objects.get(id=question_id)
        answer = ClarificationAnswer.objects.create(
            question=question,
            answer_text=answer_text,
            source_document=source_document,
            amendment_number=amendment_number,
            received_date=datetime.now(timezone.utc).date(),
        )
        question.status = "answered"
        question.save(update_fields=["status"])

        return {
            "question_id": question_id,
            "answer_id": str(answer.id),
            "answer_text": answer_text,
            "status": "answered",
        }
    except Exception as exc:
        logger.error("Record answer failed: %s", exc)
        return {"question_id": question_id, "error": str(exc)}


async def get_qa_summary(deal_id: str) -> dict[str, Any]:
    """Get Q&A activity summary for a deal.

    Returns:
        Summary dict with counts and key metrics.
    """
    try:
        from apps.communications.models import ClarificationQuestion  # type: ignore

        questions = ClarificationQuestion.objects.filter(deal_id=deal_id)
        total = questions.count()
        answered = questions.filter(status="answered").count()
        pending = questions.filter(status="pending").count()
        submitted = questions.filter(status="submitted").count()

        high_priority = list(
            questions.filter(priority__gte=8).order_by("-priority").values("id", "question_text", "status")[:5]
        )

        return {
            "deal_id": deal_id,
            "total_questions": total,
            "answered_count": answered,
            "pending_count": pending,
            "submitted_count": submitted,
            "answer_rate": round(answered / max(1, total) * 100, 1),
            "high_priority_questions": high_priority,
        }
    except Exception as exc:
        logger.error("Q&A summary failed: %s", exc)
        return {
            "deal_id": deal_id,
            "total_questions": 0,
            "answered_count": 0,
            "pending_count": 0,
            "error": str(exc),
        }
