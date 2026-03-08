"""Tests for FastAPI routers: health endpoint, agent run endpoints, status polling."""
import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from src.routers.agents import (
    AgentRunResponse,
    _create_run,
    _fail_run,
    _finalize_run,
    _runs,
    run_event_queues,
)


# ── Fixture: patch lifespan to skip observability init ───────────────────────


@pytest.fixture
def app():
    """Import the FastAPI app with lifespan observability calls mocked out."""
    with patch("src.observability.tracing.init_langfuse"), \
         patch("src.observability.tracing.init_langsmith"), \
         patch("src.observability.tracing.flush_langfuse", new_callable=AsyncMock):
        from src.main import app as _app
        yield _app


@pytest.fixture
def reset_runs():
    """Clear the in-memory run store before and after each test."""
    _runs.clear()
    run_event_queues.clear()
    yield
    _runs.clear()
    run_event_queues.clear()


# ── Health endpoint ──────────────────────────────────────────────────────────


class TestHealthEndpoint:
    @pytest.mark.asyncio
    async def test_health_returns_ok(self, app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/ai/health")
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "ok"
            assert data["service"] == "ai_orchestrator"
            assert data["version"] == "1.0.0"

    @pytest.mark.asyncio
    async def test_health_is_get_only(self, app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/ai/health")
            assert resp.status_code == 405


# ── Strategy agent run endpoint ──────────────────────────────────────────────


class TestStrategyRunEndpoint:
    @pytest.mark.asyncio
    async def test_run_returns_run_id_and_running_status(self, app, reset_runs):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/ai/agents/strategy/run",
                json={"opportunity_id": "opp-123", "context": {"key": "value"}},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert "run_id" in data
            assert data["status"] == "running"
            # run_id should be a valid UUID
            uuid.UUID(data["run_id"])

    @pytest.mark.asyncio
    async def test_run_creates_entry_in_runs_store(self, app, reset_runs):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/ai/agents/strategy/run",
                json={"opportunity_id": "opp-456"},
            )
            run_id = resp.json()["run_id"]
            assert run_id in _runs
            assert _runs[run_id]["status"] == "running"

    @pytest.mark.asyncio
    async def test_run_requires_opportunity_id(self, app, reset_runs):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/ai/agents/strategy/run", json={})
            assert resp.status_code == 422  # validation error


# ── Research agent run endpoint ──────────────────────────────────────────────


class TestResearchRunEndpoint:
    @pytest.mark.asyncio
    async def test_run_returns_running(self, app, reset_runs):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/ai/agents/research/run",
                json={"query": "DoD cybersecurity requirements", "research_type": "market_analysis"},
            )
            assert resp.status_code == 200
            assert resp.json()["status"] == "running"

    @pytest.mark.asyncio
    async def test_research_defaults(self, app, reset_runs):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/ai/agents/research/run",
                json={"query": "cloud migration trends"},
            )
            assert resp.status_code == 200


# ── Legal agent run endpoint ────────────────────────────────────────────────


class TestLegalRunEndpoint:
    @pytest.mark.asyncio
    async def test_run_returns_running(self, app, reset_runs):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/ai/agents/legal/run",
                json={"deal_id": "deal-001", "rfp_text": "sample RFP", "review_type": "rfp_review"},
            )
            assert resp.status_code == 200
            assert resp.json()["status"] == "running"


# ── Solution Architect agent run endpoint ────────────────────────────────────


class TestSolutionArchitectRunEndpoint:
    @pytest.mark.asyncio
    async def test_run_returns_running(self, app, reset_runs):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/ai/agents/solution-architect/run",
                json={"deal_id": "deal-002", "opportunity_id": "opp-789"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "running"
            uuid.UUID(data["run_id"])


# ── Marketing agent run endpoint ────────────────────────────────────────────


class TestMarketingRunEndpoint:
    @pytest.mark.asyncio
    async def test_run_returns_running(self, app, reset_runs):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/ai/agents/marketing/run",
                json={"deal_id": "deal-003"},
            )
            assert resp.status_code == 200
            assert resp.json()["status"] == "running"


# ── Agent run status polling ─────────────────────────────────────────────────


class TestRunStatusPolling:
    @pytest.mark.asyncio
    async def test_get_running_status(self, app, reset_runs):
        run_id = str(uuid.uuid4())
        _create_run(run_id)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(f"/ai/agents/runs/{run_id}")
            assert resp.status_code == 200
            data = resp.json()
            assert data["run_id"] == run_id
            assert data["status"] == "running"
            assert data["result"] == {}

    @pytest.mark.asyncio
    async def test_get_completed_status(self, app, reset_runs):
        run_id = str(uuid.uuid4())
        _create_run(run_id)
        await _finalize_run(run_id, {"summary": "Analysis complete", "score": 0.85})
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(f"/ai/agents/runs/{run_id}")
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "completed"
            assert data["result"]["summary"] == "Analysis complete"
            assert data["result"]["score"] == 0.85

    @pytest.mark.asyncio
    async def test_get_failed_status(self, app, reset_runs):
        run_id = str(uuid.uuid4())
        _create_run(run_id)
        await _fail_run(run_id, "LLM API timeout")
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(f"/ai/agents/runs/{run_id}")
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "failed"
            assert "LLM API timeout" in data["result"]["error"]

    @pytest.mark.asyncio
    async def test_get_nonexistent_run_returns_404(self, app, reset_runs):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(f"/ai/agents/runs/{uuid.uuid4()}")
            assert resp.status_code == 404
            assert "not found" in resp.json()["detail"].lower()


# ── Internal helpers ─────────────────────────────────────────────────────────


class TestRunHelpers:
    def test_create_run_initializes_status(self, reset_runs):
        _create_run("run-abc")
        assert _runs["run-abc"]["status"] == "running"
        assert _runs["run-abc"]["result"] == {}
        assert "run-abc" in run_event_queues

    @pytest.mark.asyncio
    async def test_finalize_run_updates_status(self, reset_runs):
        _create_run("run-def")
        await _finalize_run("run-def", {"answer": 42})
        assert _runs["run-def"]["status"] == "completed"
        assert _runs["run-def"]["result"]["answer"] == 42

    @pytest.mark.asyncio
    async def test_finalize_run_pushes_done_event(self, reset_runs):
        _create_run("run-ghi")
        await _finalize_run("run-ghi", {"done": True})
        q = run_event_queues["run-ghi"]
        event = q.get_nowait()
        assert event["event"] == "done"
        assert event["data"]["done"] is True

    @pytest.mark.asyncio
    async def test_fail_run_updates_status(self, reset_runs):
        _create_run("run-jkl")
        await _fail_run("run-jkl", "something broke")
        assert _runs["run-jkl"]["status"] == "failed"
        assert "something broke" in _runs["run-jkl"]["result"]["error"]

    @pytest.mark.asyncio
    async def test_fail_run_pushes_error_event(self, reset_runs):
        _create_run("run-mno")
        await _fail_run("run-mno", "timeout")
        q = run_event_queues["run-mno"]
        event = q.get_nowait()
        assert event["event"] == "error"
        assert "timeout" in event["data"]["error"]
