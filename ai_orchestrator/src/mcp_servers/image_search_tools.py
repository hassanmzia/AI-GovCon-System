"""MCP tool server: CLIP-based image and diagram similarity search."""
import base64
import logging
import os
from typing import Any

logger = logging.getLogger("ai_orchestrator.mcp.image_search")

_DJANGO_URL = os.getenv("DJANGO_API_URL", "http://django-api:8001")
_SERVICE_TOKEN = os.getenv("DJANGO_SERVICE_TOKEN", "")


def _headers() -> dict:
    return {"Authorization": f"Bearer {_SERVICE_TOKEN}"} if _SERVICE_TOKEN else {}


async def search_images_by_text(
    text_query: str,
    image_category: str | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Search images/diagrams using a text query (CLIP cross-modal search).

    Finds visually relevant diagrams and images whose content matches *text_query*.

    Args:
        text_query: Description of the image you're looking for
                    (e.g. "microservices architecture with API gateway").
        image_category: Optional filter ("architecture", "data_flow", "network", "process").
        limit: Max results.

    Returns:
        List of matching image records with image_url, alt_text, similarity, and metadata.
    """
    from src.rag.embeddings import embed_text
    from src.mcp_servers.vector_search import _vector_search

    # Generate text embedding for cross-modal search
    query_vec = await embed_text(text_query)

    # Pad or truncate to CLIP dimension (512) if needed
    clip_dim = 512
    if len(query_vec) > clip_dim:
        query_vec = query_vec[:clip_dim]
    elif len(query_vec) < clip_dim:
        query_vec = query_vec + [0.0] * (clip_dim - len(query_vec))

    filters: dict[str, Any] = {"content_type": "image"}
    if image_category:
        filters["category"] = image_category

    results = await _vector_search(
        query_vec=query_vec,
        table="knowledge_vault_knowledgechunk",
        embedding_column="image_embedding",
        text_column="alt_text",
        extra_filters=filters,
        limit=limit,
        threshold=0.3,  # Lower threshold for cross-modal search
    )
    return results


async def search_images_by_image(
    image_bytes: bytes | None = None,
    image_b64: str | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Find similar images to a given image using CLIP embeddings.

    Args:
        image_bytes: Image bytes (PNG, JPG, SVG).
        image_b64: Base64-encoded image (alternative to image_bytes).
        limit: Max results.

    Returns:
        List of similar image records ranked by visual similarity.
    """
    from src.rag.embeddings import embed_image
    from src.mcp_servers.vector_search import _vector_search

    if image_b64 and not image_bytes:
        image_bytes = base64.b64decode(image_b64)

    if not image_bytes:
        return []

    query_vec = await embed_image(image_bytes)

    results = await _vector_search(
        query_vec=query_vec,
        table="knowledge_vault_knowledgechunk",
        embedding_column="image_embedding",
        text_column="alt_text",
        extra_filters={"content_type": "image"},
        limit=limit,
        threshold=0.3,
    )
    return results


async def get_diagram_gallery(
    diagram_type: str | None = None,
    technology: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Browse the diagram gallery with optional filtering.

    Args:
        diagram_type: Filter by diagram type ("c4_context", "c4_container",
                      "data_flow", "sequence", "architecture", "network").
        technology: Filter by technology stack mention.
        limit: Max results.

    Returns:
        List of diagram records with thumbnail_url, title, type, and metadata.
    """
    import httpx

    try:
        params: dict[str, Any] = {"content_type": "image", "limit": limit}
        if diagram_type:
            params["diagram_type"] = diagram_type
        if technology:
            params["technology"] = technology

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{_DJANGO_URL}/api/knowledge-vault/diagrams/",
                params=params,
                headers=_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.warning("Diagram gallery fetch failed: %s", exc)
        return []


async def add_diagram_to_vault(
    title: str,
    image_bytes: bytes,
    alt_text: str,
    diagram_type: str,
    technology_tags: list[str] | None = None,
    source: str | None = None,
) -> dict[str, Any]:
    """Add a new diagram to the knowledge vault with CLIP embedding.

    Args:
        title: Diagram title.
        image_bytes: Raw image bytes.
        alt_text: Accessible description / alt text.
        diagram_type: Type of diagram ("architecture", "data_flow", etc.).
        technology_tags: Technology tags.
        source: Source URL or reference.

    Returns:
        Created knowledge vault item with ID and image_url.
    """
    from src.rag.embeddings import embed_image
    from src.mcp_servers.document_tools import upload_to_storage

    import uuid
    filename = f"diagrams/{uuid.uuid4().hex[:8]}_{title.replace(' ', '_')[:30]}.png"

    # Upload image to MinIO
    upload = await upload_to_storage(image_bytes, filename, "image/png")
    image_url = upload.get("url", "")

    # Generate CLIP embedding
    image_embedding = await embed_image(image_bytes)

    # Save to knowledge vault via Django
    import httpx

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{_DJANGO_URL}/api/knowledge-vault/items/",
                json={
                    "title": title,
                    "content": alt_text,
                    "category": "diagrams",
                    "content_type": "image",
                    "tags": technology_tags or [],
                    "source_url": source,
                    "image_url": image_url,
                    "alt_text": alt_text,
                    "diagram_type": diagram_type,
                    "image_embedding": image_embedding,
                },
                headers=_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("Add diagram to vault failed: %s", exc)
        return {
            "title": title,
            "image_url": image_url,
            "error": str(exc),
        }


async def extract_diagram_text(
    image_bytes: bytes | None = None,
    image_b64: str | None = None,
) -> dict[str, Any]:
    """Extract text labels and descriptions from a diagram using OCR/vision AI.

    Args:
        image_bytes: Raw image bytes.
        image_b64: Base64-encoded image.

    Returns:
        Dict with extracted_text, labels, components.
    """
    if image_b64 and not image_bytes:
        image_bytes = base64.b64decode(image_b64)

    if not image_bytes:
        return {"extracted_text": "", "labels": [], "components": []}

    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if anthropic_key:
        try:
            import anthropic

            client = anthropic.AsyncAnthropic(api_key=anthropic_key)
            b64 = base64.b64encode(image_bytes).decode()
            message = await client.messages.create(
                model="claude-opus-4-6",
                max_tokens=1024,
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
                                "text": "Extract all text labels, component names, and descriptions from this diagram. List them as JSON: {extracted_text, labels, components}",
                            },
                        ],
                    }
                ],
            )
            import json

            content = message.content[0].text
            try:
                return json.loads(content)
            except Exception:
                return {"extracted_text": content, "labels": [], "components": []}
        except Exception as exc:
            logger.warning("Vision extraction failed: %s", exc)

    return {"extracted_text": "", "labels": [], "components": []}
