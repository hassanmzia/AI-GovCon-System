"""Document chunking utilities for the RAG pipeline.

Supports text, markdown, code, and table content types.
Produces chunks suitable for embedding and pgvector storage.
"""
import logging
import re
from dataclasses import dataclass, field
from typing import Literal

logger = logging.getLogger("ai_orchestrator.rag.chunker")

ContentType = Literal["text", "markdown", "code", "table", "image"]


@dataclass
class Chunk:
    text: str
    content_type: ContentType = "text"
    chunk_index: int = 0
    source_id: str = ""
    metadata: dict = field(default_factory=dict)

    @property
    def token_estimate(self) -> int:
        """Rough token count (4 chars ≈ 1 token)."""
        return max(1, len(self.text) // 4)


# ── Configuration ─────────────────────────────────────────────────────────────

CHUNK_SIZE_TOKENS = 512
CHUNK_OVERLAP_TOKENS = 64
_CHARS_PER_TOKEN = 4
_CHUNK_CHARS = CHUNK_SIZE_TOKENS * _CHARS_PER_TOKEN
_OVERLAP_CHARS = CHUNK_OVERLAP_TOKENS * _CHARS_PER_TOKEN


# ── Core chunking ─────────────────────────────────────────────────────────────

def chunk_text(
    text: str,
    source_id: str = "",
    content_type: ContentType = "text",
    chunk_size: int = _CHUNK_CHARS,
    overlap: int = _OVERLAP_CHARS,
) -> list[Chunk]:
    """Split *text* into overlapping fixed-size chunks."""
    if not text or not text.strip():
        return []

    text = text.strip()
    chunks: list[Chunk] = []
    start = 0
    idx = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))
        # Try to break at a sentence boundary
        if end < len(text):
            boundary = _find_sentence_boundary(text, end)
            if boundary > start:
                end = boundary

        chunk_text_part = text[start:end].strip()
        if chunk_text_part:
            chunks.append(
                Chunk(
                    text=chunk_text_part,
                    content_type=content_type,
                    chunk_index=idx,
                    source_id=source_id,
                )
            )
            idx += 1

        start = end - overlap
        if start >= end:  # safety guard
            break

    return chunks


def chunk_markdown(text: str, source_id: str = "") -> list[Chunk]:
    """Split markdown by headings first, then by size within each section."""
    sections = _split_markdown_sections(text)
    chunks: list[Chunk] = []
    idx = 0
    for heading, content in sections:
        section_text = (f"## {heading}\n\n" if heading else "") + content.strip()
        sub = chunk_text(section_text, source_id=source_id, content_type="markdown")
        for c in sub:
            c.chunk_index = idx
            c.metadata["heading"] = heading
            chunks.append(c)
            idx += 1
    return chunks


def chunk_code(code: str, language: str = "", source_id: str = "") -> list[Chunk]:
    """Split code files by function/class boundaries, then by size."""
    # Try to split at top-level def/class lines
    lines = code.splitlines(keepends=True)
    sections: list[str] = []
    current: list[str] = []

    for line in lines:
        if re.match(r"^(def |class |async def )", line) and current:
            sections.append("".join(current))
            current = [line]
        else:
            current.append(line)
    if current:
        sections.append("".join(current))

    chunks: list[Chunk] = []
    idx = 0
    for section in sections:
        sub = chunk_text(section, source_id=source_id, content_type="code")
        for c in sub:
            c.chunk_index = idx
            if language:
                c.metadata["language"] = language
            chunks.append(c)
            idx += 1
    return chunks


def chunk_table(
    rows: list[dict],
    source_id: str = "",
    rows_per_chunk: int = 20,
) -> list[Chunk]:
    """Convert table rows to text chunks."""
    if not rows:
        return []

    headers = list(rows[0].keys())
    chunks: list[Chunk] = []
    idx = 0

    for i in range(0, len(rows), rows_per_chunk):
        batch = rows[i : i + rows_per_chunk]
        lines = [" | ".join(headers)]
        lines.append("-" * 40)
        for row in batch:
            lines.append(" | ".join(str(row.get(h, "")) for h in headers))
        chunks.append(
            Chunk(
                text="\n".join(lines),
                content_type="table",
                chunk_index=idx,
                source_id=source_id,
                metadata={"row_start": i, "row_end": i + len(batch)},
            )
        )
        idx += 1
    return chunks


def chunk_document(
    content: str,
    source_id: str = "",
    content_type: ContentType = "text",
    language: str = "",
) -> list[Chunk]:
    """Dispatch to the right chunker based on *content_type*."""
    if content_type == "markdown":
        return chunk_markdown(content, source_id=source_id)
    if content_type == "code":
        return chunk_code(content, language=language, source_id=source_id)
    return chunk_text(content, source_id=source_id, content_type=content_type)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _find_sentence_boundary(text: str, near: int) -> int:
    """Find the nearest sentence end (. ! ?) before or at *near*."""
    window = text[max(0, near - 200) : near]
    for ch in (".\n", "!\n", "?\n", ". ", "! ", "? "):
        pos = window.rfind(ch)
        if pos != -1:
            return max(0, near - 200) + pos + len(ch)
    return near


def _split_markdown_sections(text: str) -> list[tuple[str, str]]:
    """Split markdown at H2/H3 headings. Returns (heading, content) pairs."""
    pattern = re.compile(r"^#{1,3} (.+)$", re.MULTILINE)
    matches = list(pattern.finditer(text))

    if not matches:
        return [("", text)]

    sections: list[tuple[str, str]] = []
    # Content before first heading
    if matches[0].start() > 0:
        sections.append(("", text[: matches[0].start()]))

    for i, match in enumerate(matches):
        heading = match.group(1)
        start = match.end() + 1
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections.append((heading, text[start:end]))

    return sections
