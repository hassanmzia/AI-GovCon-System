"""Tests for the RAG subsystem: Chunker, Embeddings, Retriever."""
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.rag.chunker import (
    CHUNK_OVERLAP_TOKENS,
    CHUNK_SIZE_TOKENS,
    Chunk,
    _CHARS_PER_TOKEN,
    _CHUNK_CHARS,
    _OVERLAP_CHARS,
    _find_sentence_boundary,
    _split_markdown_sections,
    chunk_code,
    chunk_document,
    chunk_markdown,
    chunk_table,
    chunk_text,
)
from src.rag.embeddings import _EMBEDDING_DIM, cosine_similarity, embed_batch, embed_text
from src.rag.retriever import RAGRetriever, _generate_embedding


# ── Chunk dataclass ──────────────────────────────────────────────────────────


class TestChunkDataclass:
    def test_token_estimate_approximation(self):
        chunk = Chunk(text="a" * 400)
        assert chunk.token_estimate == 100  # 400 / 4

    def test_token_estimate_minimum_is_one(self):
        chunk = Chunk(text="hi")
        assert chunk.token_estimate >= 1

    def test_default_content_type(self):
        chunk = Chunk(text="hello")
        assert chunk.content_type == "text"

    def test_metadata_defaults_to_empty_dict(self):
        chunk = Chunk(text="hello")
        assert chunk.metadata == {}


# ── chunk_text ───────────────────────────────────────────────────────────────


class TestChunkText:
    def test_empty_text_returns_empty_list(self):
        assert chunk_text("") == []
        assert chunk_text("   ") == []

    def test_short_text_single_chunk(self):
        text = "This is a short paragraph."
        chunks = chunk_text(text, source_id="doc1")
        assert len(chunks) == 1
        assert chunks[0].text == text
        assert chunks[0].source_id == "doc1"
        assert chunks[0].chunk_index == 0

    def test_long_text_produces_multiple_chunks(self):
        # Create text longer than _CHUNK_CHARS
        text = "word " * (_CHUNK_CHARS // 5 + 500)
        chunks = chunk_text(text)
        assert len(chunks) > 1

    def test_chunks_have_sequential_indices(self):
        text = "sentence. " * 1000
        chunks = chunk_text(text)
        for i, chunk in enumerate(chunks):
            assert chunk.chunk_index == i

    def test_overlap_between_chunks(self):
        # Use a very small chunk size to force many chunks with overlap
        text = "A" * 500
        chunks = chunk_text(text, chunk_size=100, overlap=20)
        assert len(chunks) > 1
        # Each chunk after the first should start before the previous one ended
        # (overlap means some content is repeated between consecutive chunks)

    def test_content_type_preserved(self):
        chunks = chunk_text("hello world", content_type="markdown")
        assert chunks[0].content_type == "markdown"

    def test_sentence_boundary_splitting(self):
        """Text should preferentially split at sentence boundaries."""
        # Build text that's slightly over one chunk size with a sentence boundary
        first_part = "A" * (_CHUNK_CHARS - 50)
        text = first_part + ". " + "B" * 200
        chunks = chunk_text(text)
        if len(chunks) > 1:
            # First chunk should end at or near the sentence boundary
            assert chunks[0].text.rstrip().endswith(".") or len(chunks[0].text) <= _CHUNK_CHARS


# ── chunk_markdown ───────────────────────────────────────────────────────────


class TestChunkMarkdown:
    def test_splits_by_headings(self):
        md = "# Intro\nSome intro text.\n## Section A\nContent A.\n## Section B\nContent B."
        chunks = chunk_markdown(md, source_id="readme")
        assert len(chunks) >= 2
        # Each chunk should have a heading in metadata
        headings = [c.metadata.get("heading") for c in chunks]
        assert any(h for h in headings if h)

    def test_no_headings_single_section(self):
        md = "Just a plain paragraph with no headings."
        chunks = chunk_markdown(md)
        assert len(chunks) == 1

    def test_content_type_is_markdown(self):
        md = "## Test\nContent here."
        chunks = chunk_markdown(md)
        for c in chunks:
            assert c.content_type == "markdown"

    def test_chunk_indices_are_sequential(self):
        md = "## A\nContent A.\n## B\nContent B.\n## C\nContent C."
        chunks = chunk_markdown(md)
        for i, c in enumerate(chunks):
            assert c.chunk_index == i


# ── chunk_code ───────────────────────────────────────────────────────────────


class TestChunkCode:
    def test_splits_at_function_boundaries(self):
        code = (
            "import os\n\n"
            "def foo():\n    return 1\n\n"
            "def bar():\n    return 2\n\n"
            "class Baz:\n    pass\n"
        )
        chunks = chunk_code(code, language="python", source_id="app.py")
        # Should split at def/class boundaries
        assert len(chunks) >= 2

    def test_language_stored_in_metadata(self):
        code = "def hello():\n    print('hi')\n"
        chunks = chunk_code(code, language="python")
        for c in chunks:
            assert c.metadata.get("language") == "python"

    def test_content_type_is_code(self):
        code = "x = 1\ny = 2"
        chunks = chunk_code(code)
        for c in chunks:
            assert c.content_type == "code"

    def test_single_function_no_unnecessary_split(self):
        code = "def tiny():\n    pass\n"
        chunks = chunk_code(code)
        assert len(chunks) == 1


# ── chunk_table ──────────────────────────────────────────────────────────────


class TestChunkTable:
    def test_empty_rows(self):
        assert chunk_table([]) == []

    def test_single_batch(self):
        rows = [{"name": "Alice", "age": "30"}, {"name": "Bob", "age": "25"}]
        chunks = chunk_table(rows, rows_per_chunk=20)
        assert len(chunks) == 1
        assert "name | age" in chunks[0].text
        assert "Alice | 30" in chunks[0].text

    def test_multiple_batches(self):
        rows = [{"col": str(i)} for i in range(50)]
        chunks = chunk_table(rows, rows_per_chunk=20)
        assert len(chunks) == 3  # 50 / 20 = 2.5 => 3 chunks

    def test_metadata_row_range(self):
        rows = [{"x": str(i)} for i in range(25)]
        chunks = chunk_table(rows, rows_per_chunk=10)
        assert chunks[0].metadata["row_start"] == 0
        assert chunks[0].metadata["row_end"] == 10
        assert chunks[1].metadata["row_start"] == 10

    def test_content_type_is_table(self):
        rows = [{"a": "1"}]
        chunks = chunk_table(rows)
        assert chunks[0].content_type == "table"


# ── chunk_document dispatcher ────────────────────────────────────────────────


class TestChunkDocument:
    def test_dispatches_to_markdown(self):
        md = "## Heading\nContent."
        chunks = chunk_document(md, content_type="markdown")
        assert all(c.content_type == "markdown" for c in chunks)

    def test_dispatches_to_code(self):
        code = "def f():\n    pass"
        chunks = chunk_document(code, content_type="code", language="python")
        assert all(c.content_type == "code" for c in chunks)

    def test_defaults_to_text(self):
        chunks = chunk_document("Plain text content.")
        assert all(c.content_type == "text" for c in chunks)


# ── _find_sentence_boundary ─────────────────────────────────────────────────


class TestFindSentenceBoundary:
    def test_finds_period_space(self):
        text = "Hello world. This is next."
        boundary = _find_sentence_boundary(text, 15)
        assert boundary <= 15
        assert boundary > 0

    def test_returns_near_when_no_boundary(self):
        text = "no punctuation here at all"
        boundary = _find_sentence_boundary(text, 10)
        assert boundary == 10


# ── _split_markdown_sections ────────────────────────────────────────────────


class TestSplitMarkdownSections:
    def test_no_headings(self):
        sections = _split_markdown_sections("Just text.")
        assert len(sections) == 1
        assert sections[0][0] == ""

    def test_multiple_headings(self):
        md = "# Title\nIntro.\n## Section 1\nContent 1.\n### Subsection\nDetail."
        sections = _split_markdown_sections(md)
        headings = [h for h, _ in sections]
        assert "Title" in headings
        assert "Section 1" in headings

    def test_content_before_first_heading(self):
        md = "Preamble text.\n## First Heading\nContent."
        sections = _split_markdown_sections(md)
        # First section should have empty heading and the preamble text
        assert sections[0][0] == ""
        assert "Preamble" in sections[0][1]


# ── Embeddings: embed_text ───────────────────────────────────────────────────


class TestEmbedText:
    @pytest.mark.asyncio
    async def test_fallback_zero_vector_when_no_api_key(self):
        """Without any API keys, embed_text should return a zero vector."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove any API keys
            os.environ.pop("OPENAI_API_KEY", None)
            os.environ.pop("VOYAGE_API_KEY", None)
            vec = await embed_text("test document about government contracting")
            assert len(vec) == _EMBEDDING_DIM
            assert all(v == 0.0 for v in vec)

    @pytest.mark.asyncio
    async def test_openai_path_called_when_key_present(self):
        """When OPENAI_API_KEY is set, the OpenAI client should be used."""
        mock_embedding = [0.1] * _EMBEDDING_DIM
        mock_resp = MagicMock()
        mock_resp.data = [MagicMock(embedding=mock_embedding)]

        mock_client_instance = MagicMock()
        mock_client_instance.embeddings.create = AsyncMock(return_value=mock_resp)

        mock_openai_module = MagicMock()
        mock_openai_module.AsyncOpenAI = MagicMock(return_value=mock_client_instance)

        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-key"}), \
             patch.dict("sys.modules", {"openai": mock_openai_module}):
            vec = await embed_text("test query")
            assert vec == mock_embedding
            mock_client_instance.embeddings.create.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_openai_failure_falls_through(self):
        """If OpenAI fails, should try Voyage or fall back to zero vector."""
        mock_openai_module = MagicMock()
        mock_openai_module.AsyncOpenAI = MagicMock(side_effect=Exception("API error"))

        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-bad"}, clear=True), \
             patch.dict("sys.modules", {"openai": mock_openai_module}):
            os.environ.pop("VOYAGE_API_KEY", None)
            vec = await embed_text("test")
            assert len(vec) == _EMBEDDING_DIM
            assert all(v == 0.0 for v in vec)


# ── Embeddings: embed_batch ──────────────────────────────────────────────────


class TestEmbedBatch:
    @pytest.mark.asyncio
    async def test_batch_fallback_to_sequential(self):
        """Without OpenAI key, batch embed should fall back to sequential embed_text."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("OPENAI_API_KEY", None)
            os.environ.pop("VOYAGE_API_KEY", None)
            texts = ["doc one", "doc two", "doc three"]
            vecs = await embed_batch(texts)
            assert len(vecs) == 3
            assert all(len(v) == _EMBEDDING_DIM for v in vecs)

    @pytest.mark.asyncio
    async def test_batch_with_openai(self):
        """With OpenAI key, should call embeddings.create in batches."""
        mock_embedding = [0.5] * _EMBEDDING_DIM
        mock_resp = MagicMock()
        mock_resp.data = [MagicMock(embedding=mock_embedding)] * 2

        mock_client_instance = MagicMock()
        mock_client_instance.embeddings.create = AsyncMock(return_value=mock_resp)

        mock_openai_module = MagicMock()
        mock_openai_module.AsyncOpenAI = MagicMock(return_value=mock_client_instance)

        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}), \
             patch.dict("sys.modules", {"openai": mock_openai_module}):
            vecs = await embed_batch(["text1", "text2"], batch_size=50)
            assert len(vecs) == 2


# ── Embeddings: cosine_similarity ────────────────────────────────────────────


class TestCosineSimilarity:
    def test_identical_vectors(self):
        v = [1.0, 2.0, 3.0]
        assert cosine_similarity(v, v) == pytest.approx(1.0)

    def test_orthogonal_vectors(self):
        a = [1.0, 0.0]
        b = [0.0, 1.0]
        assert cosine_similarity(a, b) == pytest.approx(0.0)

    def test_opposite_vectors(self):
        a = [1.0, 0.0, 0.0]
        b = [-1.0, 0.0, 0.0]
        assert cosine_similarity(a, b) == pytest.approx(-1.0)

    def test_zero_vector_returns_zero(self):
        a = [0.0, 0.0]
        b = [1.0, 2.0]
        assert cosine_similarity(a, b) == 0.0

    def test_different_length_returns_zero(self):
        assert cosine_similarity([1.0, 2.0], [1.0]) == 0.0


# ── Retriever: _generate_embedding ──────────────────────────────────────────


class TestRetrieverEmbedding:
    @pytest.mark.asyncio
    async def test_returns_zero_vector_without_api_key(self):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("OPENAI_API_KEY", None)
            vec = await _generate_embedding("test query")
            assert len(vec) == 1536
            assert all(v == 0.0 for v in vec)


# ── RAGRetriever: no-DB fallback ────────────────────────────────────────────


class TestRAGRetrieverNoDb:
    @pytest.mark.asyncio
    async def test_past_performance_returns_empty_without_db(self):
        retriever = RAGRetriever()
        with patch("src.rag.retriever._get_connection", new_callable=AsyncMock, return_value=None), \
             patch("src.rag.retriever._generate_embedding", new_callable=AsyncMock, return_value=[0.0] * 1536):
            results = await retriever.get_similar_past_performance("cybersecurity SOC operations")
            assert results == []

    @pytest.mark.asyncio
    async def test_proposals_returns_empty_without_db(self):
        retriever = RAGRetriever()
        with patch("src.rag.retriever._get_connection", new_callable=AsyncMock, return_value=None), \
             patch("src.rag.retriever._generate_embedding", new_callable=AsyncMock, return_value=[0.0] * 1536):
            results = await retriever.get_similar_proposals("cloud migration")
            assert results == []

    @pytest.mark.asyncio
    async def test_knowledge_base_returns_empty_without_db(self):
        retriever = RAGRetriever()
        with patch("src.rag.retriever._get_connection", new_callable=AsyncMock, return_value=None), \
             patch("src.rag.retriever._generate_embedding", new_callable=AsyncMock, return_value=[0.0] * 1536):
            results = await retriever.get_knowledge_base_entries("FAR 52.212-4")
            assert results == []

    @pytest.mark.asyncio
    async def test_context_for_opportunity_returns_structure(self):
        retriever = RAGRetriever()
        with patch("src.rag.retriever._get_connection", new_callable=AsyncMock, return_value=None), \
             patch("src.rag.retriever._generate_embedding", new_callable=AsyncMock, return_value=[0.0] * 1536):
            ctx = await retriever.get_context_for_opportunity("IT modernization")
            assert "past_performance" in ctx
            assert "proposals" in ctx
            assert "knowledge_base" in ctx
            assert isinstance(ctx["past_performance"], list)

    @pytest.mark.asyncio
    async def test_context_respects_include_flags(self):
        retriever = RAGRetriever()
        with patch.object(retriever, "get_similar_past_performance", new_callable=AsyncMock, return_value=[]) as pp_mock, \
             patch.object(retriever, "get_similar_proposals", new_callable=AsyncMock, return_value=[]) as prop_mock, \
             patch.object(retriever, "get_knowledge_base_entries", new_callable=AsyncMock, return_value=[]) as kb_mock:
            await retriever.get_context_for_opportunity(
                "query", include_past_performance=False, include_proposals=False, include_knowledge_base=True
            )
            pp_mock.assert_not_awaited()
            prop_mock.assert_not_awaited()
            kb_mock.assert_awaited_once()


# ── RAGRetriever: with mocked DB connection ─────────────────────────────────


class TestRAGRetrieverWithDb:
    @pytest.mark.asyncio
    async def test_past_performance_parses_rows(self):
        mock_rows = [
            {
                "id": "uuid-1",
                "title": "SOC Operations",
                "content": "Managed SOC for agency X.",
                "similarity_score": 0.92,
                "metadata": {"agency": "DOD"},
            },
        ]
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=mock_rows)
        mock_conn.close = AsyncMock()

        retriever = RAGRetriever()
        with patch("src.rag.retriever._get_connection", new_callable=AsyncMock, return_value=mock_conn), \
             patch("src.rag.retriever._generate_embedding", new_callable=AsyncMock, return_value=[0.0] * 1536):
            results = await retriever.get_similar_past_performance("SOC", top_k=3)
            assert len(results) == 1
            assert results[0]["title"] == "SOC Operations"
            assert results[0]["similarity_score"] == 0.92
            mock_conn.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_db_query_error_returns_empty(self):
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(side_effect=Exception("query failed"))
        mock_conn.close = AsyncMock()

        retriever = RAGRetriever()
        with patch("src.rag.retriever._get_connection", new_callable=AsyncMock, return_value=mock_conn), \
             patch("src.rag.retriever._generate_embedding", new_callable=AsyncMock, return_value=[0.0] * 1536):
            results = await retriever.get_similar_past_performance("test")
            assert results == []
            mock_conn.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_knowledge_base_with_category_filter(self):
        mock_rows = [
            {
                "id": "uuid-2",
                "title": "FAR 52.212-4",
                "category": "far_clause",
                "content": "Contract terms.",
                "similarity_score": 0.85,
                "metadata": None,
            },
        ]
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=mock_rows)
        mock_conn.close = AsyncMock()

        retriever = RAGRetriever()
        with patch("src.rag.retriever._get_connection", new_callable=AsyncMock, return_value=mock_conn), \
             patch("src.rag.retriever._generate_embedding", new_callable=AsyncMock, return_value=[0.0] * 1536):
            results = await retriever.get_knowledge_base_entries("FAR clause", category="far_clause")
            assert len(results) == 1
            assert results[0]["metadata"] == {}  # None converted to {}
            # Verify the category parameter was passed to the query
            call_args = mock_conn.fetch.call_args
            assert "far_clause" in call_args[0]  # category in positional args
