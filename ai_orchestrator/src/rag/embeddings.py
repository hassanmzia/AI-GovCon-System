"""Embedding model wrapper for the AI orchestrator RAG pipeline."""
import logging
import os
from typing import Any

logger = logging.getLogger("ai_orchestrator.rag.embeddings")

_EMBEDDING_DIM = 1536  # text-embedding-3-small / claude fallback


async def embed_text(text: str) -> list[float]:
    """Return a 1536-d embedding for *text* using OpenAI or Anthropic.

    Falls back to a zero-vector when no API key is available so that
    unit-tests and CI environments don't need live credentials.
    """
    # ── OpenAI ─────────────────────────────────────────────────────────────
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        try:
            import openai  # type: ignore

            client = openai.AsyncOpenAI(api_key=openai_key)
            resp = await client.embeddings.create(
                input=text,
                model="text-embedding-3-small",
            )
            return resp.data[0].embedding
        except Exception as exc:
            logger.warning("OpenAI embed failed: %s", exc)

    # ── Anthropic voyage-2 (via voyageai SDK) ─────────────────────────────
    voyage_key = os.getenv("VOYAGE_API_KEY")
    if voyage_key:
        try:
            import voyageai  # type: ignore

            vo = voyageai.AsyncClient(api_key=voyage_key)
            result = await vo.embed([text], model="voyage-2", input_type="document")
            vec = result.embeddings[0]
            # Pad or truncate to _EMBEDDING_DIM
            vec = (vec + [0.0] * _EMBEDDING_DIM)[:_EMBEDDING_DIM]
            return vec
        except Exception as exc:
            logger.warning("Voyage embed failed: %s", exc)

    logger.debug("No embedding API key set; returning zero vector.")
    return [0.0] * _EMBEDDING_DIM


async def embed_batch(texts: list[str], batch_size: int = 50) -> list[list[float]]:
    """Embed a list of texts in batches, returning a parallel list of vectors."""
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        try:
            import openai  # type: ignore

            client = openai.AsyncOpenAI(api_key=openai_key)
            all_embeddings: list[list[float]] = []
            for i in range(0, len(texts), batch_size):
                chunk = texts[i : i + batch_size]
                resp = await client.embeddings.create(
                    input=chunk,
                    model="text-embedding-3-small",
                )
                all_embeddings.extend([d.embedding for d in resp.data])
            return all_embeddings
        except Exception as exc:
            logger.warning("OpenAI batch embed failed: %s", exc)

    # Fall back to sequential single calls
    results = []
    for text in texts:
        results.append(await embed_text(text))
    return results


async def embed_image(image_bytes: bytes) -> list[float]:
    """Return a 512-d CLIP embedding for *image_bytes*.

    Requires the `transformers` + `Pillow` packages and a local CLIP model.
    Falls back to a zero vector when the model is unavailable.
    """
    try:
        import io

        from PIL import Image  # type: ignore
        from transformers import CLIPModel, CLIPProcessor  # type: ignore

        model_name = os.getenv("CLIP_MODEL", "openai/clip-vit-base-patch32")
        processor = CLIPProcessor.from_pretrained(model_name)
        model = CLIPModel.from_pretrained(model_name)

        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        inputs = processor(images=image, return_tensors="pt")
        image_features = model.get_image_features(**inputs)
        vec = image_features[0].detach().tolist()
        return vec
    except Exception as exc:
        logger.warning("CLIP image embed failed: %s", exc)
        return [0.0] * 512


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    if len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)
