import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.observability.tracing import flush_langfuse, init_langfuse, init_langsmith

logger = logging.getLogger("ai_orchestrator")
logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info("AI Orchestrator starting up...")

    # Initialise LLM observability backends.
    # Langfuse: cost/latency/token tracking — enabled when LANGFUSE_SECRET_KEY is set.
    # LangSmith: LangGraph-native tracing — enabled when LANGCHAIN_TRACING_V2=true.
    init_langfuse()
    init_langsmith()

    logger.info("Initializing agent registry and MCP connections...")
    # TODO: Initialize LangGraph agents, MCP server connections, RAG pipeline
    yield

    logger.info("AI Orchestrator shutting down...")
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

from src.routers import agents, research, stream

app.include_router(agents.router, prefix="", tags=["agents"])
app.include_router(research.router, prefix="", tags=["research"])
app.include_router(stream.router, prefix="", tags=["stream"])

logger.info("Routes registered: /ai/agents, /ai/research, /ai/stream")
