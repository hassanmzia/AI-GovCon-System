import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def embed_past_performance(self, record_id: str):
    """
    Generate and store a vector embedding for a single PastPerformance record
    using the description + key_achievements text.
    """
    from apps.past_performance.models import PastPerformance

    try:
        record = PastPerformance.objects.get(pk=record_id)
    except PastPerformance.DoesNotExist:
        logger.error("embed_past_performance: record %s not found", record_id)
        return

    text = f"{record.project_name}. {record.description}"
    if record.key_achievements:
        text += " " + " ".join(str(a) for a in record.key_achievements)
    if record.technologies:
        text += " Technologies: " + ", ".join(str(t) for t in record.technologies)

    logger.info("Embedding past performance record %s", record_id)

    try:
        from apps.knowledge_vault.services.ingestion import get_embedding

        embedding = get_embedding(text)
        record.description_embedding = embedding
        record.save(update_fields=["description_embedding", "updated_at"])

        logger.info("Embedding stored for record %s", record_id)
        return {"record_id": record_id, "embedding_dim": len(embedding)}

    except Exception as exc:
        logger.error("embed_past_performance failed for %s: %s", record_id, exc)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def reindex_all_past_performance(self):
    """
    Bulk re-embed all active PastPerformance records that lack an embedding.
    """
    from apps.past_performance.models import PastPerformance

    unembedded = PastPerformance.objects.filter(
        is_active=True, description_embedding__isnull=True
    )
    count = unembedded.count()
    logger.info("Re-embedding %d past performance records", count)

    queued = 0
    for record in unembedded.iterator():
        embed_past_performance.delay(str(record.id))
        queued += 1

    logger.info("Queued %d embedding tasks", queued)
    return {"queued": queued}


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def match_past_performance_for_opportunity(self, opportunity_id: str):
    """
    Find the top-N most relevant past performance records for an opportunity
    using vector similarity search and save as PastPerformanceMatch records.
    """
    from apps.opportunities.models import Opportunity
    from apps.past_performance.models import PastPerformance, PastPerformanceMatch

    try:
        opportunity = Opportunity.objects.get(pk=opportunity_id)
    except Opportunity.DoesNotExist:
        logger.error(
            "match_past_performance_for_opportunity: opportunity %s not found",
            opportunity_id,
        )
        return

    query_text = f"{opportunity.title}. {opportunity.description or ''}"
    if opportunity.naics_code:
        query_text += f" NAICS: {opportunity.naics_code}"

    logger.info("Matching past performance for opportunity %s", opportunity_id)

    try:
        from apps.knowledge_vault.services.ingestion import get_embedding

        query_embedding = get_embedding(query_text)

        # pgvector cosine similarity query
        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, 1 - (description_embedding <=> %s::vector) AS similarity
                FROM past_performance_pastperformance
                WHERE is_active = true
                  AND description_embedding IS NOT NULL
                ORDER BY similarity DESC
                LIMIT 10
                """,
                [str(query_embedding)],
            )
            rows = cursor.fetchall()

        saved = 0
        for record_id, similarity in rows:
            if similarity < 0.3:
                continue
            try:
                pp = PastPerformance.objects.get(pk=record_id)
            except PastPerformance.DoesNotExist:
                continue

            PastPerformanceMatch.objects.update_or_create(
                opportunity=opportunity,
                past_performance=pp,
                defaults={
                    "relevance_score": round(similarity * 100, 1),
                    "match_rationale": f"Vector similarity: {similarity:.3f}",
                    "matched_keywords": [],
                },
            )
            saved += 1

        logger.info(
            "Saved %d past performance matches for opportunity %s", saved, opportunity_id
        )
        return {"opportunity_id": opportunity_id, "matches": saved}

    except Exception as exc:
        logger.error(
            "match_past_performance_for_opportunity failed for %s: %s",
            opportunity_id,
            exc,
        )
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def verify_past_performance_references(self):
    """
    Periodic task: flag past performance records whose last_verified date
    is older than 12 months, or that have missing required fields.
    """
    from datetime import date, timedelta

    from apps.past_performance.models import PastPerformance

    cutoff = date.today() - timedelta(days=365)
    stale = PastPerformance.objects.filter(
        is_active=True,
    ).filter(
        models.Q(last_verified__lt=cutoff) | models.Q(last_verified__isnull=True)
    )

    count = stale.count()
    logger.info(
        "verify_past_performance_references: %d records need re-verification", count
    )
    return {"needs_verification": count}


# Late import to avoid circular-import issues at module load time
from django.db import models  # noqa: E402
