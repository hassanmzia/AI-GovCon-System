import logging

from celery import shared_task

logger = logging.getLogger(__name__)


def _get_embedding_sync(text: str) -> list:
    """Synchronous wrapper around the async embed_text helper."""
    import asyncio

    async def _embed():
        try:
            from ai_orchestrator.src.rag.embeddings import embed_text
            return await embed_text(text)
        except Exception:
            return [0.0] * 1536

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, _embed())
                return future.result()
        return loop.run_until_complete(_embed())
    except Exception:
        return [0.0] * 1536


def _chunk_text(text: str, chunk_size: int = 512, overlap: int = 64) -> list:
    """Simple word-boundary text chunker (fallback when AI orchestrator unavailable)."""
    words = text.split()
    if not words:
        return []
    chunks = []
    step = max(chunk_size - overlap, 1)
    for i in range(0, len(words), step):
        chunk = " ".join(words[i: i + chunk_size])
        if chunk:
            chunks.append(chunk)
    return chunks


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def ingest_document(self, document_id: str):
    """
    Process a KnowledgeDocument: chunk the content, generate embeddings per chunk,
    and store KnowledgeChunk records ready for RAG retrieval.
    """
    from apps.knowledge_vault.models import KnowledgeChunk, KnowledgeDocument

    try:
        doc = KnowledgeDocument.objects.get(pk=document_id)
    except KnowledgeDocument.DoesNotExist:
        logger.error("ingest_document: document %s not found", document_id)
        return

    logger.info("Ingesting document %s: %s", document_id, doc.title)

    try:
        text = doc.content
        if not text.strip():
            logger.warning("Document %s has empty content — skipping", document_id)
            return {"status": "skipped", "reason": "empty_content"}

        chunks = _chunk_text(text, chunk_size=512, overlap=64)
        stored = 0
        for idx, chunk_piece in enumerate(chunks):
            embedding = _get_embedding_sync(chunk_piece)
            KnowledgeChunk.objects.update_or_create(
                document=doc,
                chunk_index=idx,
                defaults={
                    "text": chunk_piece,
                    "content_type": "text",
                    "text_embedding": embedding,
                    "token_count": len(chunk_piece.split()),
                },
            )
            stored += 1

        if doc.status == "draft":
            doc.status = "approved"
            doc.save(update_fields=["status", "updated_at"])

        logger.info("Ingested document %s: %d chunks stored", document_id, stored)
        return {"document_id": document_id, "chunks": stored}

    except Exception as exc:
        logger.error("ingest_document failed for %s: %s", document_id, exc)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def ingest_image(self, document_id: str, image_url: str, image_type: str = "diagram"):
    """
    Process an image associated with a KnowledgeDocument: generate a CLIP embedding
    and an AI text description, then store as a KnowledgeChunk.
    """
    from apps.knowledge_vault.models import KnowledgeChunk, KnowledgeDocument
    from apps.knowledge_vault.services.image_embedder import embed_image

    try:
        doc = KnowledgeDocument.objects.get(pk=document_id)
    except KnowledgeDocument.DoesNotExist:
        logger.error("ingest_image: document %s not found", document_id)
        return

    logger.info("Ingesting image for document %s: %s", document_id, image_url)

    try:
        result = embed_image(image_url=image_url)

        last_chunk = (
            KnowledgeChunk.objects.filter(document=doc).order_by("-chunk_index").first()
        )
        chunk_index = (last_chunk.chunk_index + 1) if last_chunk else 0

        KnowledgeChunk.objects.create(
            document=doc,
            chunk_index=chunk_index,
            text=result.get("description", ""),
            content_type="image",
            image_url=image_url,
            image_type=image_type,
            image_embedding=result.get("embedding"),
            text_embedding=[0.0] * 1536,
            token_count=0,
            metadata={"clip_model": result.get("model", "clip")},
        )

        logger.info("Image ingested for document %s at chunk %d", document_id, chunk_index)
        return {"document_id": document_id, "chunk_index": chunk_index}

    except Exception as exc:
        logger.error("ingest_image failed for document %s: %s", document_id, exc)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=120)
def reindex_vault(self):
    """
    Bulk reindex: find all approved KnowledgeDocuments with no KnowledgeChunk
    records and enqueue ingest_document tasks for each.
    """
    from apps.knowledge_vault.models import KnowledgeChunk, KnowledgeDocument

    all_docs = KnowledgeDocument.objects.filter(status="approved")
    indexed_ids = KnowledgeChunk.objects.filter(
        document__isnull=False
    ).values_list("document_id", flat=True).distinct()

    unindexed = all_docs.exclude(id__in=indexed_ids)
    count = unindexed.count()
    logger.info("reindex_vault: %d documents need indexing", count)

    queued = 0
    for doc in unindexed.iterator():
        ingest_document.delay(str(doc.id))
        queued += 1

    logger.info("reindex_vault: queued %d ingestion tasks", queued)
    return {"queued": queued}


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def ingest_solutioning_framework(self, framework_id: str):
    """
    Chunk and embed all sections of a SolutioningFramework for RAG retrieval.
    """
    from apps.knowledge_vault.models import KnowledgeChunk, SolutioningFramework

    try:
        framework = SolutioningFramework.objects.get(pk=framework_id)
    except SolutioningFramework.DoesNotExist:
        logger.error(
            "ingest_solutioning_framework: framework %s not found", framework_id
        )
        return

    logger.info("Ingesting solutioning framework %s: %s", framework_id, framework.name)

    sections = framework.sections or {}
    text_parts = [f"Framework: {framework.name}\n{framework.description}\n"]
    for section_name, section_content in sections.items():
        text_parts.append(f"## {section_name}\n{section_content}")

    full_text = "\n\n".join(text_parts)
    chunks = _chunk_text(full_text, chunk_size=512, overlap=64)

    stored = 0
    for idx, chunk_piece in enumerate(chunks):
        embedding = _get_embedding_sync(chunk_piece)
        KnowledgeChunk.objects.update_or_create(
            solutioning_framework=framework,
            chunk_index=idx,
            defaults={
                "text": chunk_piece,
                "content_type": "text",
                "text_embedding": embedding,
                "token_count": len(chunk_piece.split()),
                "document": None,
                "vault_item": None,
            },
        )
        stored += 1

    logger.info("Solutioning framework %s ingested: %d chunks", framework_id, stored)
    return {"framework_id": framework_id, "chunks": stored}
