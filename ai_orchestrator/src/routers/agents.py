"""FastAPI router for agent endpoints."""
import asyncio
import logging
import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

logger = logging.getLogger("ai_orchestrator.routers.agents")

router = APIRouter()

# In-memory store for agent runs: {run_id: {"status": ..., "result": ...}}
_runs: dict[str, dict[str, Any]] = {}

# Per-run event queues for SSE streaming
run_event_queues: dict[str, asyncio.Queue] = {}


# ── Request/Response Models ───────────────────────────────────────────────────

class StrategyRunRequest(BaseModel):
    opportunity_id: str
    context: dict[str, Any] = {}


class ResearchRunRequest(BaseModel):
    query: str
    research_type: str = "market_analysis"
    context: dict[str, Any] = {}


class LegalRunRequest(BaseModel):
    deal_id: str
    rfp_text: str = ""
    contract_text: str = ""
    review_type: str = "rfp_review"


class MarketingRunRequest(BaseModel):
    deal_id: str
    context: dict[str, Any] = {}


class AgentRunResponse(BaseModel):
    run_id: str
    status: str  # "running" | "completed" | "failed"
    result: dict[str, Any] = {}


# ── Helper: create a run entry and event queue ────────────────────────────────

def _create_run(run_id: str) -> None:
    _runs[run_id] = {"status": "running", "result": {}}
    run_event_queues[run_id] = asyncio.Queue()


async def _finalize_run(run_id: str, result: dict[str, Any]) -> None:
    _runs[run_id] = {"status": "completed", "result": result}
    q = run_event_queues.get(run_id)
    if q:
        await q.put({"event": "done", "data": result})


async def _fail_run(run_id: str, error: str) -> None:
    _runs[run_id] = {"status": "failed", "result": {"error": error}}
    q = run_event_queues.get(run_id)
    if q:
        await q.put({"event": "error", "data": {"error": error}})


# ── Background task helpers ───────────────────────────────────────────────────

async def _run_strategy_agent(run_id: str, input_data: dict) -> None:
    try:
        from src.agents.strategy_agent import StrategyAgent

        q = run_event_queues.get(run_id)
        if q:
            await q.put({"event": "thinking", "data": {"message": "Starting strategy analysis..."}})

        agent = StrategyAgent()
        result = await agent.run(input_data)
        await _finalize_run(run_id, result)
    except Exception as exc:
        logger.exception("Strategy agent run %s failed", run_id)
        await _fail_run(run_id, str(exc))


async def _run_research_agent(run_id: str, input_data: dict) -> None:
    try:
        from src.agents.research_agent import ResearchAgent

        q = run_event_queues.get(run_id)
        if q:
            await q.put({"event": "thinking", "data": {"message": "Starting deep research..."}})

        agent = ResearchAgent()
        result = await agent.run(input_data)
        await _finalize_run(run_id, result)
    except Exception as exc:
        logger.exception("Research agent run %s failed", run_id)
        await _fail_run(run_id, str(exc))


async def _run_legal_agent(run_id: str, input_data: dict) -> None:
    try:
        from src.agents.legal_agent import LegalAgent

        q = run_event_queues.get(run_id)
        if q:
            await q.put({"event": "thinking", "data": {"message": "Starting legal review..."}})

        agent = LegalAgent()
        result = await agent.run(input_data)
        await _finalize_run(run_id, result)
    except Exception as exc:
        logger.exception("Legal agent run %s failed", run_id)
        await _fail_run(run_id, str(exc))


async def _run_marketing_agent(run_id: str, input_data: dict) -> None:
    try:
        from src.agents.marketing_agent import MarketingAgent

        q = run_event_queues.get(run_id)
        if q:
            await q.put({"event": "thinking", "data": {"message": "Starting marketing analysis..."}})

        agent = MarketingAgent()
        result = await agent.run(input_data)
        await _finalize_run(run_id, result)
    except Exception as exc:
        logger.exception("Marketing agent run %s failed", run_id)
        await _fail_run(run_id, str(exc))


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/ai/agents/strategy/run", response_model=AgentRunResponse, tags=["agents"])
async def run_strategy_agent(
    request: StrategyRunRequest,
    background_tasks: BackgroundTasks,
) -> AgentRunResponse:
    """Run strategy analysis for an opportunity."""
    run_id = str(uuid.uuid4())
    _create_run(run_id)
    input_data = {"opportunity_id": request.opportunity_id, **request.context}
    background_tasks.add_task(_run_strategy_agent, run_id, input_data)
    return AgentRunResponse(run_id=run_id, status="running")


@router.post("/ai/agents/research/run", response_model=AgentRunResponse, tags=["agents"])
async def run_research_agent(
    request: ResearchRunRequest,
    background_tasks: BackgroundTasks,
) -> AgentRunResponse:
    """Run deep research on a topic."""
    run_id = str(uuid.uuid4())
    _create_run(run_id)
    input_data = {
        "query": request.query,
        "research_type": request.research_type,
        **request.context,
    }
    background_tasks.add_task(_run_research_agent, run_id, input_data)
    return AgentRunResponse(run_id=run_id, status="running")


@router.post("/ai/agents/legal/run", response_model=AgentRunResponse, tags=["agents"])
async def run_legal_agent(
    request: LegalRunRequest,
    background_tasks: BackgroundTasks,
) -> AgentRunResponse:
    """Run legal review for a deal/contract."""
    run_id = str(uuid.uuid4())
    _create_run(run_id)
    input_data = {
        "deal_id": request.deal_id,
        "rfp_text": request.rfp_text,
        "contract_text": request.contract_text,
        "review_type": request.review_type,
    }
    background_tasks.add_task(_run_legal_agent, run_id, input_data)
    return AgentRunResponse(run_id=run_id, status="running")


@router.post("/ai/agents/marketing/run", response_model=AgentRunResponse, tags=["agents"])
async def run_marketing_agent(
    request: MarketingRunRequest,
    background_tasks: BackgroundTasks,
) -> AgentRunResponse:
    """Run marketing/capture strategy for a deal."""
    run_id = str(uuid.uuid4())
    _create_run(run_id)
    input_data = {"deal_id": request.deal_id, **request.context}
    background_tasks.add_task(_run_marketing_agent, run_id, input_data)
    return AgentRunResponse(run_id=run_id, status="running")


@router.get("/ai/agents/runs/{run_id}", response_model=AgentRunResponse, tags=["agents"])
async def get_agent_run(run_id: str) -> AgentRunResponse:
    """Get the status and result of an agent run."""
    run = _runs.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")
    return AgentRunResponse(run_id=run_id, status=run["status"], result=run["result"])
