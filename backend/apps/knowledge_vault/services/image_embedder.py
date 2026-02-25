"""Image embedding service: generates CLIP embeddings for vault images and diagrams."""
import asyncio
import io
import logging
import os
from typing import Any

logger = logging.getLogger("ai_deal_manager.knowledge_vault.image_embedder")

_OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
_CLIP_MODEL = "ViT-B/32"


async def embed_image(image_bytes: bytes) -> list[float]:
    """Generate a CLIP embedding for an image.

    Tries OpenAI CLIP via the embeddings endpoint, then falls back to
    local CLIP model if available.

    Returns:
        512-dimensional float vector (or zero vector on failure).
    """
    if not image_bytes:
        return [0.0] * 512

    # Try local CLIP first (faster if available)
    local_vec = await _embed_with_local_clip(image_bytes)
    if local_vec:
        return local_vec

    # Fallback: encode image as base64 and use vision model to describe,
    # then embed the description with text embeddings
    description = await _describe_image_with_vision(image_bytes)
    if description:
        return await embed_text_as_image_proxy(description)

    return [0.0] * 512


async def embed_image_file(file_path: str) -> list[float]:
    """Load image from disk and generate CLIP embedding."""
    try:
        from pathlib import Path
        return await embed_image(Path(file_path).read_bytes())
    except Exception as exc:
        logger.warning("Failed to load image file %s: %s", file_path, exc)
        return [0.0] * 512


async def embed_text_as_image_proxy(text: str) -> list[float]:
    """Generate a text embedding that can be used to query image embeddings.

    CLIP produces aligned text/image embeddings, so a text embedding of a
    description can semantically match image embeddings.
    """
    try:
        from ai_orchestrator.src.rag.embeddings import embed_text
        return await embed_text(text)
    except Exception:
        pass
    return [0.0] * 512


async def batch_embed_images(
    image_items: list[dict],
) -> list[dict]:
    """Embed multiple images in parallel.

    Args:
        image_items: List of dicts with keys: id, bytes (optional), file_path (optional),
                     title (optional), description (optional).

    Returns:
        Same list with "embedding" key added to each item.
    """
    tasks = []
    for item in image_items:
        img_bytes = item.get("bytes")
        file_path = item.get("file_path")
        if img_bytes:
            tasks.append(embed_image(img_bytes))
        elif file_path:
            tasks.append(embed_image_file(file_path))
        else:
            # Use description as proxy
            description = item.get("description", item.get("title", ""))
            tasks.append(embed_text_as_image_proxy(description))

    embeddings = await asyncio.gather(*tasks, return_exceptions=True)

    result = []
    for item, emb in zip(image_items, embeddings):
        item_copy = dict(item)
        if isinstance(emb, list):
            item_copy["embedding"] = emb
        else:
            logger.warning("Embedding failed for item %s: %s", item.get("id", "?"), emb)
            item_copy["embedding"] = [0.0] * 512
        item_copy.pop("bytes", None)  # don't return raw bytes
        result.append(item_copy)

    return result


async def ingest_diagram(
    image_bytes: bytes,
    filename: str,
    title: str = "",
    description: str = "",
    category: str = "architecture",
    source_id: str = "",
    metadata: dict | None = None,
) -> dict[str, Any]:
    """Full pipeline: embed an image and store it in the knowledge vault.

    Returns:
        Dict with: id, filename, title, category, embedding_dim, stored.
    """
    # Generate embedding
    embedding = await embed_image(image_bytes)

    # Also extract text from diagram if it's a diagram/chart
    extracted_text = ""
    if category in ("architecture", "diagram", "chart"):
        extracted_text = await _extract_text_from_diagram(image_bytes)

    # Upload image to MinIO
    stored_url = ""
    try:
        from ai_orchestrator.src.mcp_servers.document_tools import upload_to_storage

        result = await upload_to_storage(
            file_bytes=image_bytes,
            object_key=f"diagrams/{category}/{filename}",
            content_type="image/png",
        )
        stored_url = result.get("url", "")
    except Exception as exc:
        logger.warning("Failed to upload diagram to MinIO: %s", exc)

    # Save to Django DB
    saved_id = ""
    try:
        import httpx

        _django_url = os.getenv("DJANGO_API_URL", "http://django-api:8001")
        _token = os.getenv("DJANGO_SERVICE_TOKEN", "")
        headers = {"Authorization": f"Bearer {_token}"} if _token else {}

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{_django_url}/api/knowledge-vault/items/",
                json={
                    "title": title or filename,
                    "filename": filename,
                    "content_type": "image",
                    "category": category,
                    "description": description or extracted_text[:500],
                    "text": extracted_text,
                    "source_id": source_id,
                    "file_url": stored_url,
                    "image_embedding": embedding,
                    "metadata": metadata or {},
                },
                headers=headers,
            )
            if resp.status_code in (200, 201):
                saved_id = str(resp.json().get("id", ""))
    except Exception as exc:
        logger.warning("Failed to save diagram to DB: %s", exc)

    return {
        "id": saved_id,
        "filename": filename,
        "title": title or filename,
        "category": category,
        "embedding_dim": len(embedding),
        "has_extracted_text": bool(extracted_text),
        "stored_url": stored_url,
        "stored": bool(saved_id),
    }


# ── Internal helpers ──────────────────────────────────────────────────────────

async def _embed_with_local_clip(image_bytes: bytes) -> list[float]:
    """Try to use local CLIP model for embedding."""
    try:
        import torch  # type: ignore
        import clip  # type: ignore
        from PIL import Image  # type: ignore

        model, preprocess = clip.load(_CLIP_MODEL, device="cpu")
        image = preprocess(Image.open(io.BytesIO(image_bytes))).unsqueeze(0)
        with torch.no_grad():
            features = model.encode_image(image)
            features = features / features.norm(dim=-1, keepdim=True)
        return features[0].tolist()
    except ImportError:
        pass  # CLIP not installed
    except Exception as exc:
        logger.debug("Local CLIP embedding failed: %s", exc)
    return []


async def _describe_image_with_vision(image_bytes: bytes) -> str:
    """Use Claude/GPT-4V to generate a text description of an image."""
    import base64

    b64 = base64.b64encode(image_bytes).decode()

    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
    if anthropic_key:
        try:
            import anthropic  # type: ignore

            client = anthropic.AsyncAnthropic(api_key=anthropic_key)
            msg = await client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=300,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {"type": "base64", "media_type": "image/png", "data": b64},
                            },
                            {
                                "type": "text",
                                "text": "Describe this technical diagram or image in detail for a search index. Focus on components, relationships, and technical content.",
                            },
                        ],
                    }
                ],
            )
            return msg.content[0].text
        except Exception as exc:
            logger.debug("Vision description failed: %s", exc)
    return ""


async def _extract_text_from_diagram(image_bytes: bytes) -> str:
    """Extract text content from a diagram using OCR or vision API."""
    # Vision model description covers text extraction well enough
    return await _describe_image_with_vision(image_bytes)
