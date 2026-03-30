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


class SolutionArchitectRunRequest(BaseModel):
    deal_id: str
    opportunity_id: str


class MarketingRunRequest(BaseModel):
    deal_id: str
    context: dict[str, Any] = {}


class DealAgentRunRequest(BaseModel):
    """Generic request for deal-scoped agents (capture, red-team, compliance, learning, etc.)."""
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

        if result.get("error"):
            await _fail_run(run_id, result["error"])
        else:
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

        if result.get("error"):
            await _fail_run(run_id, result["error"])
        else:
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

        if result.get("error"):
            await _fail_run(run_id, result["error"])
        else:
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

        if result.get("error"):
            await _fail_run(run_id, result["error"])
        else:
            await _finalize_run(run_id, result)
    except Exception as exc:
        logger.exception("Marketing agent run %s failed", run_id)
        await _fail_run(run_id, str(exc))


async def _run_solution_architect_agent(run_id: str, input_data: dict) -> None:
    try:
        from src.agents.solution_architect_agent import SolutionArchitectAgent

        q = run_event_queues.get(run_id)
        if q:
            await q.put({"event": "thinking", "data": {"message": "Starting solution architecture design..."}})

        agent = SolutionArchitectAgent()
        result = await agent.run(input_data)

        if result.get("error"):
            await _fail_run(run_id, result["error"])
        else:
            await _finalize_run(run_id, result)
    except Exception as exc:
        logger.exception("Solution architect agent run %s failed", run_id)
        await _fail_run(run_id, str(exc))


# ── Generic agent runner for deal-scoped agents ──────────────────────────────

_AGENT_REGISTRY: dict[str, tuple[str, str, str]] = {
    # slug -> (module_path, class_name, description)
    "solution-architect": ("src.agents.solution_architect_agent", "SolutionArchitectAgent", "Starting solution architecture design..."),
    "capture": ("src.agents.capture_agent", "CaptureAgent", "Generating capture plan..."),
    "red-team": ("src.agents.red_team_agent", "RedTeamAgent", "Running adversarial red team review..."),
    "compliance": ("src.agents.compliance_agent", "ComplianceAgent", "Verifying compliance matrix..."),
    "learning": ("src.agents.learning_agent", "LearningAgent", "Analyzing win/loss patterns..."),
    "rfp-analyst": ("src.agents.rfp_analyst_agent", "RFPAnalystAgent", "Parsing RFP requirements..."),
    "past-performance": ("src.agents.past_performance_agent", "PastPerformanceAgent", "Matching past performance records..."),
    "proposal-writer": ("src.agents.proposal_writer_agent", "ProposalWriterAgent", "Drafting proposal sections..."),
    "pricing": ("src.agents.pricing_agent", "PricingAgent", "Building pricing scenarios..."),
    "qa": ("src.agents.qa_agent", "QAAgent", "Running quality checks..."),
    "contract": ("src.agents.contract_agent", "ContractAgent", "Generating contract..."),
    "teaming": ("src.agents.teaming_agent", "TeamingAgent", "Identifying teaming partners..."),
    "submission": ("src.agents.submission_agent", "SubmissionAgent", "Packaging submission..."),
    "strategy": ("src.agents.strategy_agent", "StrategyAgent", "Running strategy analysis..."),
    "research": ("src.agents.research_agent", "ResearchAgent", "Running research..."),
    "legal": ("src.agents.legal_agent", "LegalAgent", "Running legal review..."),
    "marketing": ("src.agents.marketing_agent", "MarketingAgent", "Running marketing analysis..."),
}


async def _run_generic_agent(run_id: str, agent_slug: str, input_data: dict) -> None:
    """Generic runner that loads any agent from the registry."""
    reg = _AGENT_REGISTRY.get(agent_slug)
    if not reg:
        await _fail_run(run_id, f"Unknown agent type: {agent_slug}")
        return

    module_path, class_name, thinking_msg = reg

    try:
        import importlib
        mod = importlib.import_module(module_path)
        agent_cls = getattr(mod, class_name)

        q = run_event_queues.get(run_id)
        if q:
            await q.put({"event": "thinking", "data": {"message": thinking_msg}})

        agent = agent_cls()
        result = await agent.run(input_data)

        if result.get("error"):
            await _fail_run(run_id, result["error"])
        else:
            await _finalize_run(run_id, result)
    except Exception as exc:
        logger.exception("%s agent run %s failed", agent_slug, run_id)
        await _fail_run(run_id, str(exc))


# ── Endpoints ─────────────────────────────────────────────────────────────────
# NOTE: Specific agent routes MUST come before the generic {agent_type} route
# because FastAPI matches top-down. The generic catch-all goes last.


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


@router.post("/ai/agents/solution-architect/run", response_model=AgentRunResponse, tags=["agents"])
async def run_solution_architect_agent(
    request: SolutionArchitectRunRequest,
    background_tasks: BackgroundTasks,
) -> AgentRunResponse:
    """Run the Solution Architect Agent for a deal."""
    run_id = str(uuid.uuid4())
    _create_run(run_id)
    input_data = {
        "deal_id": request.deal_id,
        "opportunity_id": request.opportunity_id,
    }
    background_tasks.add_task(_run_solution_architect_agent, run_id, input_data)
    return AgentRunResponse(run_id=run_id, status="running")


# Generic deal-scoped agent endpoint (catch-all — must be LAST)
@router.post("/ai/agents/{agent_type}/run", response_model=AgentRunResponse, tags=["agents"])
async def run_deal_agent(
    agent_type: str,
    request: DealAgentRunRequest,
    background_tasks: BackgroundTasks,
) -> AgentRunResponse:
    """Run any deal-scoped agent by type slug (capture, red-team, compliance, etc.)."""
    if agent_type not in _AGENT_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Agent type '{agent_type}' not found")
    run_id = str(uuid.uuid4())
    _create_run(run_id)
    input_data = {"deal_id": request.deal_id, **request.context}
    background_tasks.add_task(_run_generic_agent, run_id, agent_type, input_data)
    return AgentRunResponse(run_id=run_id, status="running")


@router.get("/ai/agents/runs/{run_id}", response_model=AgentRunResponse, tags=["agents"])
async def get_agent_run(run_id: str) -> AgentRunResponse:
    """Get the status and result of an agent run."""
    run = _runs.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")
    return AgentRunResponse(run_id=run_id, status=run["status"], result=run["result"])


# ── LLM Config ───────────────────────────────────────────────────────────────

@router.get("/ai/llm-config", tags=["config"])
async def get_llm_config():
    """Return the current LLM provider configuration (for debugging)."""
    from src.llm_provider import get_provider_info
    return get_provider_info()
