import logging

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_proposal_section(self, proposal_id: str, section_id: str):
    """
    Generate AI draft content for a single proposal section.
    """
    from apps.proposals.models import Proposal, ProposalSection

    try:
        section = ProposalSection.objects.select_related(
            "proposal", "proposal__deal"
        ).get(pk=section_id)
    except ProposalSection.DoesNotExist:
        logger.error("generate_proposal_section: section %s not found", section_id)
        return

    deal = section.proposal.deal
    logger.info(
        "Generating section '%s' for proposal %s (deal %s)",
        section.title,
        proposal_id,
        deal.id,
    )

    try:
        import asyncio
        from ai_orchestrator.src.agents.proposal_writer_agent import ProposalWriterAgent

        agent = ProposalWriterAgent()
        result = asyncio.run(
            agent.run(
                deal_id=str(deal.id),
                section_id=str(section.id),
                section_title=section.title,
                volume=section.volume,
            )
        )

        draft = result.get("draft", "")
        if draft:
            section.ai_draft = draft
            section.status = "ai_drafted"
            section.word_count = len(draft.split())
            section.save(update_fields=["ai_draft", "status", "word_count", "updated_at"])
            logger.info(
                "Section '%s' drafted: %d words", section.title, section.word_count
            )

        return {"section_id": str(section.id), "word_count": section.word_count}

    except Exception as exc:
        logger.error("generate_proposal_section failed for section %s: %s", section_id, exc)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def generate_all_proposal_sections(self, proposal_id: str):
    """
    Enqueue section generation tasks for every not-started section of a proposal.
    """
    from apps.proposals.models import Proposal, ProposalSection

    try:
        proposal = Proposal.objects.get(pk=proposal_id)
    except Proposal.DoesNotExist:
        logger.error("generate_all_proposal_sections: proposal %s not found", proposal_id)
        return

    sections = ProposalSection.objects.filter(
        proposal=proposal, status="not_started"
    )
    count = 0
    for section in sections:
        generate_proposal_section.delay(proposal_id, str(section.id))
        count += 1

    logger.info(
        "Enqueued %d section generation tasks for proposal %s", count, proposal_id
    )
    return {"enqueued": count}


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def run_proposal_compliance_check(self, proposal_id: str):
    """
    Cross-check all proposal sections against the RFP requirements matrix
    and update the proposal's compliance_percentage.
    """
    from apps.proposals.models import Proposal, ProposalSection
    from apps.rfp.models import RFPRequirement

    try:
        proposal = Proposal.objects.select_related("deal").get(pk=proposal_id)
    except Proposal.DoesNotExist:
        logger.error("run_proposal_compliance_check: proposal %s not found", proposal_id)
        return

    deal = proposal.deal
    requirements = RFPRequirement.objects.filter(rfp__deal=deal)
    total = requirements.count()

    if total == 0:
        logger.info(
            "No RFP requirements found for deal %s — skipping compliance check", deal.id
        )
        return {"total": 0, "compliant": 0}

    sections_text = " ".join(
        ProposalSection.objects.filter(proposal=proposal)
        .values_list("final_content", flat=True)
    )

    compliant = 0
    for req in requirements:
        keywords = (req.requirement_text or "").lower().split()[:5]
        if any(kw in sections_text.lower() for kw in keywords if len(kw) > 4):
            compliant += 1

    pct = round((compliant / total) * 100, 1) if total else 0.0
    proposal.total_requirements = total
    proposal.compliant_count = compliant
    proposal.compliance_percentage = pct
    proposal.save(
        update_fields=["total_requirements", "compliant_count", "compliance_percentage", "updated_at"]
    )

    logger.info(
        "Compliance check for proposal %s: %d/%d (%.1f%%)", proposal_id, compliant, total, pct
    )
    return {"total": total, "compliant": compliant, "pct": pct}


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def initiate_review_cycle(self, proposal_id: str, review_type: str):
    """
    Create a ReviewCycle record and notify assigned reviewers.
    review_type: 'pink' | 'red' | 'gold'
    """
    from apps.core.models import Notification
    from apps.proposals.models import Proposal, ReviewCycle

    try:
        proposal = Proposal.objects.select_related("deal").get(pk=proposal_id)
    except Proposal.DoesNotExist:
        logger.error("initiate_review_cycle: proposal %s not found", proposal_id)
        return

    cycle, created = ReviewCycle.objects.get_or_create(
        proposal=proposal,
        review_type=review_type,
        defaults={"status": "in_progress", "scheduled_date": timezone.now()},
    )

    if not created:
        cycle.status = "in_progress"
        cycle.scheduled_date = timezone.now()
        cycle.save(update_fields=["status", "scheduled_date", "updated_at"])

    # Map review type to proposal status
    status_map = {"pink": "pink_team", "red": "red_team", "gold": "gold_team"}
    proposal.status = status_map.get(review_type, proposal.status)
    proposal.save(update_fields=["status", "updated_at"])

    logger.info(
        "Review cycle '%s' initiated for proposal %s (deal %s)",
        review_type,
        proposal_id,
        proposal.deal.id,
    )
    return {"review_id": str(cycle.id), "review_type": review_type, "created": created}
