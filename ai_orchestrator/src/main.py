import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.observability.tracing import flush_langfuse, init_langfuse, init_langsmith

logger = logging.getLogger("ai_orchestrator")
logging.basicConfig(level=logging.INFO)

# Background task handle for the stage trigger listener
_stage_listener_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    global _stage_listener_task
    logger.info("AI Orchestrator starting up...")

    # Initialise LLM observability backends.
    init_langfuse()
    init_langsmith()

    # Start the stage trigger listener — subscribes to Redis for deal stage
    # change events and dispatches the configured agent chains automatically.
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    try:
        from src.graphs.stage_trigger_graph import listen_for_stage_changes
        _stage_listener_task = asyncio.create_task(listen_for_stage_changes(redis_url))
        logger.info("Stage trigger listener started (Redis: %s)", redis_url)
    except Exception:
        logger.exception("Failed to start stage trigger listener")

    logger.info("Agent registry and stage trigger listener initialized.")
    yield

    logger.info("AI Orchestrator shutting down...")
    # Cancel the stage listener gracefully
    if _stage_listener_task and not _stage_listener_task.done():
        _stage_listener_task.cancel()
        try:
            await _stage_listener_task
        except asyncio.CancelledError:
            pass
    # Drain any pending Langfuse events before the process exits.
    await flush_langfuse()


app = FastAPI(
    title="AI Deal Manager - AI Orchestrator",
    description="AI agent orchestration service with LangGraph, MCP, and RAG capabilities",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS Middleware ──────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health Check ─────────────────────────────────────────────────────────────

@app.get("/ai/health")
async def health_check():
    """Health check endpoint for the AI Orchestrator service."""
    return {
        "status": "ok",
        "service": "ai_orchestrator",
        "version": "1.0.0",
    }


# ── Router Includes ──────────────────────────────────────────────────────────

from src.routers import agents, research, stream, visualize

app.include_router(agents.router, prefix="", tags=["agents"])
app.include_router(research.router, prefix="", tags=["research"])
app.include_router(stream.router, prefix="", tags=["stream"])
app.include_router(visualize.router, prefix="", tags=["visualization"])

logger.info("Routes registered: /ai/agents, /ai/research, /ai/stream, /ai/graphs")
