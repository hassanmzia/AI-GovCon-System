"""FastAPI router for research endpoints."""
import asyncio
import logging
import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

logger = logging.getLogger("ai_orchestrator.routers.research")

router = APIRouter()

# In-memory store for research projects: {research_id: {"status": ..., "result": ...}}
_research_projects: dict[str, dict[str, Any]] = {}


# ── Request/Response Models ───────────────────────────────────────────────────

class ResearchStartRequest(BaseModel):
    query: str
    research_type: str = "market_analysis"
    context: dict[str, Any] = {}


class ResearchStartResponse(BaseModel):
    id: str
    status: str
    message: str


class ResearchStatusResponse(BaseModel):
    id: str
    status: str  # "pending" | "running" | "completed" | "failed"
    progress: str = ""


class ResearchResultResponse(BaseModel):
    id: str
    status: str
    result: dict[str, Any] = {}


# ── Background task ───────────────────────────────────────────────────────────

async def _run_research_project(research_id: str, input_data: dict) -> None:
    try:
        from src.agents.research_agent import ResearchAgent

        _research_projects[research_id]["status"] = "running"

        agent = ResearchAgent()
        result = await agent.run(input_data)

        _research_projects[research_id]["status"] = "completed"
        _research_projects[research_id]["result"] = result
    except Exception as exc:
        logger.exception("Research project %s failed", research_id)
        _research_projects[research_id]["status"] = "failed"
        _research_projects[research_id]["result"] = {"error": str(exc)}


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/ai/research/start", response_model=ResearchStartResponse, tags=["research"])
async def start_research(
    request: ResearchStartRequest,
    background_tasks: BackgroundTasks,
) -> ResearchStartResponse:
    """Start a deep research project."""
    research_id = str(uuid.uuid4())
    _research_projects[research_id] = {"status": "pending", "result": {}}
    input_data = {
        "query": request.query,
        "research_type": request.research_type,
        **request.context,
    }
    background_tasks.add_task(_run_research_project, research_id, input_data)
    return ResearchStartResponse(
        id=research_id,
        status="pending",
        message="Research project started. Use the status endpoint to poll for completion.",
    )


@router.get("/ai/research/{id}/status", response_model=ResearchStatusResponse, tags=["research"])
async def get_research_status(id: str) -> ResearchStatusResponse:
    """Get the status of a research project."""
    project = _research_projects.get(id)
    if project is None:
        raise HTTPException(status_code=404, detail=f"Research project '{id}' not found")

    status = project["status"]
    progress_map = {
        "pending": "Queued for processing",
        "running": "Research in progress...",
        "completed": "Research completed successfully",
        "failed": "Research failed",
    }
    return ResearchStatusResponse(
        id=id,
        status=status,
        progress=progress_map.get(status, status),
    )


@router.get("/ai/research/{id}/result", response_model=ResearchResultResponse, tags=["research"])
async def get_research_result(id: str) -> ResearchResultResponse:
    """Get the results of a completed research project."""
    project = _research_projects.get(id)
    if project is None:
        raise HTTPException(status_code=404, detail=f"Research project '{id}' not found")

    if project["status"] not in ("completed", "failed"):
        raise HTTPException(
            status_code=202,
            detail=f"Research project is still '{project['status']}'. Try again later.",
        )

    return ResearchResultResponse(
        id=id,
        status=project["status"],
        result=project["result"],
    )
