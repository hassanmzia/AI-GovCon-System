"""Knowledge vault ingestion pipeline: upload → chunking → embedding → storage."""
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


async def ingest_document(
    file_content: bytes,
    filename: str,
    title: str,
    category: str,
    content_type: str = "text",
    tags: list[str] | None = None,
    source_url: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Full ingestion pipeline: parse → chunk → embed → store.

    Args:
        file_content: Raw file bytes.
        filename: Original filename.
        title: Display title.
        category: Knowledge category (e.g. "architecture", "legal", "pricing").
        content_type: Content type ("text", "markdown", "code", "image").
        tags: Optional tags list.
        source_url: Optional source URL.
        metadata: Optional additional metadata.

    Returns:
        Dict with vault_item_id, chunk_count, status.
    """
    from apps.knowledge_vault.models import KnowledgeVault, KnowledgeChunk  # type: ignore

    # Parse document
    text = await _parse_file(file_content, filename, content_type)
    if not text and content_type != "image":
        return {"status": "failed", "error": "Could not extract text from document"}

    # Upload to MinIO
    object_key = await _upload_to_storage(file_content, filename)

    # Create vault item
    vault_item = KnowledgeVault.objects.create(
        title=title,
        category=category,
        content_type=content_type,
        content=text[:10000],  # Store preview
        tags=tags or [],
        source_url=source_url,
        file_path=object_key,
        metadata=metadata or {},
    )

    # Chunk and embed
    chunks = await _chunk_and_store(text, vault_item, content_type, filename)

    # Generate image embedding if image
    if content_type == "image":
        await _embed_image(file_content, vault_item)

    return {
        "vault_item_id": str(vault_item.id),
        "title": title,
        "category": category,
        "chunk_count": len(chunks),
        "object_key": object_key,
        "status": "ingested",
    }


async def ingest_url(
    url: str,
    title: str,
    category: str,
    tags: list[str] | None = None,
) -> dict[str, Any]:
    """Ingest a web URL into the knowledge vault.

    Args:
        url: URL to fetch and ingest.
        title: Display title.
        category: Knowledge category.
        tags: Optional tags.

    Returns:
        Ingestion result dict.
    """
    import httpx

    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            resp = await client.get(url)
            html = resp.text

        # Extract text from HTML
        try:
            from bs4 import BeautifulSoup  # type: ignore

            soup = BeautifulSoup(html, "html.parser")
            for tag in soup(["script", "style", "nav", "footer"]):
                tag.decompose()
            text = soup.get_text(separator="\n", strip=True)
        except ImportError:
            text = html

        return await ingest_document(
            file_content=text.encode("utf-8"),
            filename=f"{title.replace(' ', '_')[:50]}.txt",
            title=title,
            category=category,
            content_type="text",
            tags=tags,
            source_url=url,
        )
    except Exception as exc:
        logger.error("URL ingestion failed for %s: %s", url, exc)
        return {"status": "failed", "error": str(exc), "url": url}


async def re_embed_vault_item(vault_item_id: str) -> dict[str, Any]:
    """Re-generate embeddings for an existing vault item (e.g. after model upgrade).

    Args:
        vault_item_id: KnowledgeVault UUID.

    Returns:
        Dict with chunks_updated, status.
    """
    try:
        from apps.knowledge_vault.models import KnowledgeVault, KnowledgeChunk  # type: ignore

        item = KnowledgeVault.objects.get(id=vault_item_id)
        chunks = KnowledgeChunk.objects.filter(vault_item=item)
        updated = 0
        for chunk in chunks:
            embedding = await _embed_text(chunk.text)
            chunk.text_embedding = embedding
            chunk.save(update_fields=["text_embedding"])
            updated += 1

        return {"vault_item_id": vault_item_id, "chunks_updated": updated, "status": "re-embedded"}
    except Exception as exc:
        logger.error("Re-embedding failed for %s: %s", vault_item_id, exc)
        return {"vault_item_id": vault_item_id, "status": "failed", "error": str(exc)}


# ── Internal helpers ──────────────────────────────────────────────────────────

async def _parse_file(content: bytes, filename: str, content_type: str) -> str:
    """Extract text from file content."""
    if content_type == "image":
        return ""

    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else "txt"

    if ext == "pdf":
        try:
            import pdfplumber, io  # type: ignore

            with pdfplumber.open(io.BytesIO(content)) as pdf:
                return "\n\n".join(p.extract_text() or "" for p in pdf.pages)
        except Exception:
            pass
    elif ext in ("docx", "doc"):
        try:
            from docx import Document  # type: ignore
            import io

            doc = Document(io.BytesIO(content))
            return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
        except Exception:
            pass
    elif ext in ("xlsx", "xls"):
        try:
            import openpyxl, io  # type: ignore

            wb = openpyxl.load_workbook(io.BytesIO(content), data_only=True)
            rows = []
            for sheet in wb.worksheets:
                for row in sheet.iter_rows(values_only=True):
                    rows.append(" | ".join(str(v or "") for v in row))
            return "\n".join(rows)
        except Exception:
            pass

    # Default: decode as text
    try:
        return content.decode("utf-8", errors="replace")
    except Exception:
        return ""


async def _upload_to_storage(content: bytes, filename: str) -> str:
    """Upload file to MinIO and return object key."""
    import uuid

    object_key = f"knowledge-vault/{uuid.uuid4().hex[:8]}_{filename[:80]}"
    try:
        from minio import Minio  # type: ignore

        endpoint = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
        client = Minio(
            endpoint.replace("http://", "").replace("https://", ""),
            access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
            secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
            secure=endpoint.startswith("https"),
        )
        bucket = os.getenv("MINIO_BUCKET", "deal-manager")
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)

        import io

        client.put_object(bucket, object_key, io.BytesIO(content), length=len(content))
    except Exception as exc:
        logger.warning("MinIO upload failed for %s: %s", filename, exc)
    return object_key


async def _chunk_and_store(
    text: str,
    vault_item: Any,
    content_type: str,
    filename: str,
) -> list[Any]:
    """Chunk text, generate embeddings, and store KnowledgeChunk records."""
    if not text:
        return []

    from apps.knowledge_vault.models import KnowledgeChunk  # type: ignore

    try:
        from ai_orchestrator.src.rag.chunker import chunk_document
        from ai_orchestrator.src.rag.embeddings import embed_batch
    except ImportError:
        logger.warning("AI orchestrator chunker not available; using simple chunking")
        # Simple fallback: one chunk per 2000 chars
        chunks_text = [text[i:i+2000] for i in range(0, len(text), 1800)]
        from django.db import transaction

        created = []
        with transaction.atomic():
            for i, chunk_text in enumerate(chunks_text[:100]):
                chunk = KnowledgeChunk.objects.create(
                    vault_item=vault_item,
                    text=chunk_text,
                    chunk_index=i,
                    content_type=content_type,
                    text_embedding=[0.0] * 1536,
                )
                created.append(chunk)
        return created

    chunks = chunk_document(text, source_id=str(vault_item.id), content_type=content_type)
    if not chunks:
        return []

    texts = [c.text for c in chunks]
    embeddings = await embed_batch(texts)

    from django.db import transaction

    created = []
    with transaction.atomic():
        for chunk, embedding in zip(chunks, embeddings):
            chunk_obj = KnowledgeChunk.objects.create(
                vault_item=vault_item,
                text=chunk.text,
                chunk_index=chunk.chunk_index,
                content_type=chunk.content_type,
                metadata=chunk.metadata,
                text_embedding=embedding,
            )
            created.append(chunk_obj)

    logger.info("Stored %d chunks for vault item %s", len(created), vault_item.id)
    return created


async def _embed_text(text: str) -> list[float]:
    try:
        from ai_orchestrator.src.rag.embeddings import embed_text

        return await embed_text(text)
    except Exception:
        return [0.0] * 1536


async def _embed_image(image_bytes: bytes, vault_item: Any) -> None:
    try:
        from ai_orchestrator.src.rag.embeddings import embed_image
        from apps.knowledge_vault.models import KnowledgeChunk  # type: ignore

        embedding = await embed_image(image_bytes)
        KnowledgeChunk.objects.create(
            vault_item=vault_item,
            text=vault_item.title,
            chunk_index=0,
            content_type="image",
            image_embedding=embedding,
            text_embedding=[0.0] * 1536,
        )
    except Exception as exc:
        logger.warning("Image embedding failed for vault item %s: %s", vault_item.id, exc)
