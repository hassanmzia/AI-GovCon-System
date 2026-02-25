import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger("ai_orchestrator")
logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info("AI Orchestrator starting up...")
    logger.info("Initializing agent registry and MCP connections...")
    # TODO: Initialize LangGraph agents, MCP server connections, RAG pipeline
    yield
    logger.info("AI Orchestrator shutting down...")


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
