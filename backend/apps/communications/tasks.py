import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def process_qa_impacts():
    """
    Process clarification answers that impact proposals.

    Finds all ClarificationAnswers marked as impacts_proposal=True
    that don't yet have QAImpactMapping entries, and creates
    placeholder impact mappings for review.
    """
    from .models import ClarificationAnswer, QAImpactMapping

    answers_with_impact = ClarificationAnswer.objects.filter(
        impacts_proposal=True,
    ).select_related("question").prefetch_related("impact_mappings")

    created_count = 0
    for answer in answers_with_impact:
        if answer.impact_mappings.exists():
            continue

        # Derive the most likely proposal section from the answer text
        answer_text = (answer.answer_text or "").lower()
        question_text = (answer.question.question_text or "").lower() if answer.question else ""
        combined = answer_text + " " + question_text

        # Heuristic section mapping based on keywords
        section_keywords = {
            "Technical Approach / Volume": [
                "technical", "approach", "solution", "architecture", "design",
                "methodology", "technology", "implementation", "system",
            ],
            "Management Approach": [
                "management", "plan", "schedule", "program", "staffing",
                "personnel", "resource", "transition", "key personnel",
            ],
            "Past Performance": [
                "past performance", "experience", "reference", "prior contract",
                "similar work", "history",
            ],
            "Price / Cost Volume": [
                "price", "cost", "rate", "labor", "billing", "invoice",
                "fee", "discount", "ceiling", "not-to-exceed",
            ],
            "Compliance / Certifications": [
                "certification", "compliance", "clearance", "cmmc", "fedramp",
                "nist", "fisma", "security", "cleared",
            ],
        }

        best_section = "General Proposal"
        best_score = 0
        for section, keywords in section_keywords.items():
            score = sum(1 for kw in keywords if kw in combined)
            if score > best_score:
                best_score = score
                best_section = section

        q_num = answer.question.question_number if answer.question else "N/A"

        impact_description = (
            f"Answer to Q{q_num} impacts the '{best_section}' section. "
        )
        if answer_text:
            # Summarise the first 200 chars of the answer
            snippet = answer.answer_text[:200].strip()
            if len(answer.answer_text) > 200:
                snippet += "…"
            impact_description += f"Key content: \"{snippet}\""

        action_required = (
            f"Update '{best_section}' to reflect this clarification. "
            "Verify consistency with existing proposal content."
        )

        QAImpactMapping.objects.create(
            answer=answer,
            proposal_section=best_section,
            impact_description=impact_description,
            action_required=action_required,
            status="pending",
        )
        created_count += 1

    logger.info(
        "process_qa_impacts completed: %d impact mappings created", created_count
    )
    return {"created": created_count}
