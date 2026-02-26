"""
Centralised observability for the AI Orchestrator.

Two complementary backends are supported and independently enabled:

Langfuse
    Production LLM observability — cost, latency, token counts, prompt
    management, and evaluation dashboards.
    Activated when LANGFUSE_SECRET_KEY is present in the environment.
    Docs: https://langfuse.com/docs/integrations/langchain

LangSmith
    LangGraph-native tracing — every graph.ainvoke() call is automatically
    traced with full node-by-node visibility, state transitions, and agent
    decisions when LANGCHAIN_TRACING_V2=true is set.  No code changes are
    required for existing LangGraph graphs; LangChain picks up the env vars
    automatically on import.  Best for debugging graph workflows.
    Docs: https://docs.smith.langchain.com/

Why both?
    Langfuse owns production cost/token observability and custom dashboards.
    LangSmith owns deep LangGraph workflow debugging and evaluation harnesses.
    They complement each other: Langfuse for "what did it cost / was it good?",
    LangSmith for "exactly which node produced that output?".

Public API
----------
init_langfuse()          — call once at app startup
init_langsmith()         — call once at app startup
get_callbacks(...)       — returns list of active LangChain callback handlers
build_llm(...)           — ChatAnthropic pre-wired with callbacks
flush_langfuse()         — call at app shutdown to drain pending events
"""

import logging
import os
from typing import Any

logger = logging.getLogger("ai_orchestrator.observability")

# ---------------------------------------------------------------------------
# Langfuse
# ---------------------------------------------------------------------------

_langfuse_client = None


def init_langfuse() -> None:
    """Initialise the Langfuse SDK client.  Safe to call more than once."""
    global _langfuse_client
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    if not secret_key:
        logger.info("Langfuse disabled — LANGFUSE_SECRET_KEY not set")
        return
    try:
        from langfuse import Langfuse  # type: ignore[import]

        _langfuse_client = Langfuse(
            secret_key=secret_key,
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY", ""),
            host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
        )
        logger.info(
            "Langfuse initialised (host=%s)",
            os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
        )
    except Exception as exc:
        logger.warning("Langfuse init failed — continuing without it: %s", exc)


def _langfuse_callback(
    session_id: str | None = None,
    trace_name: str | None = None,
    metadata: dict[str, Any] | None = None,
):
    """
    Return a per-request Langfuse LangChain CallbackHandler.

    Each handler creates its own trace in Langfuse, tagged with the
    session_id (typically deal_id) and agent trace_name.  Returns None
    if Langfuse is disabled or instantiation fails.
    """
    if _langfuse_client is None:
        return None
    try:
        from langfuse.callback import CallbackHandler  # type: ignore[import]

        return CallbackHandler(
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY", ""),
            host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
            session_id=session_id,
            trace_name=trace_name,
            metadata=metadata or {},
        )
    except Exception as exc:
        logger.debug("Langfuse CallbackHandler creation failed: %s", exc)
        return None


async def flush_langfuse() -> None:
    """Flush pending Langfuse events to the API.  Call on application shutdown."""
    if _langfuse_client is None:
        return
    try:
        _langfuse_client.flush()
        logger.info("Langfuse events flushed")
    except Exception as exc:
        logger.warning("Langfuse flush failed: %s", exc)


# ---------------------------------------------------------------------------
# LangSmith
# ---------------------------------------------------------------------------


def init_langsmith() -> None:
    """
    Validate and announce LangSmith tracing configuration.

    LangChain reads LANGCHAIN_TRACING_V2 and LANGCHAIN_API_KEY from the
    environment automatically — this function just validates the config and
    logs the result.  No code changes are required for existing LangGraph
    graphs; every graph.ainvoke() will be traced automatically when the env
    vars are present.
    """
    tracing_on = os.getenv("LANGCHAIN_TRACING_V2", "").lower() in ("true", "1")
    api_key = os.getenv("LANGCHAIN_API_KEY", "")
    project = os.getenv("LANGCHAIN_PROJECT", "ai-govcon-system")

    if not tracing_on:
        logger.info("LangSmith disabled — set LANGCHAIN_TRACING_V2=true to enable")
        return
    if not api_key:
        logger.warning(
            "LangSmith: LANGCHAIN_TRACING_V2=true but LANGCHAIN_API_KEY is missing"
        )
        return

    # Ensure the project name is explicitly set so all runs are grouped.
    os.environ.setdefault("LANGCHAIN_PROJECT", project)
    logger.info("LangSmith tracing enabled (project=%s)", project)


def _langsmith_callback(trace_name: str | None = None):
    """
    Return a LangSmith LangChainTracer for explicit callback passing.

    This is only needed when you want per-invocation project / run-name
    control.  For most cases, setting LANGCHAIN_TRACING_V2=true is enough
    because LangChain auto-attaches tracing to every LLM/graph call.
    """
    if os.getenv("LANGCHAIN_TRACING_V2", "").lower() not in ("true", "1"):
        return None
    if not os.getenv("LANGCHAIN_API_KEY"):
        return None
    try:
        from langchain_core.tracers.langchain import LangChainTracer  # type: ignore[import]

        return LangChainTracer(
            project_name=os.getenv("LANGCHAIN_PROJECT", "ai-govcon-system"),
        )
    except Exception as exc:
        logger.debug("LangChainTracer creation failed: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Unified helpers
# ---------------------------------------------------------------------------


def get_callbacks(
    session_id: str | None = None,
    trace_name: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> list:
    """
    Return a list of active LangChain callback handlers.

    Pass the result as the ``callbacks`` argument to any ChatAnthropic
    invocation or LangGraph graph run to get automatic tracing in both
    Langfuse and LangSmith.

    Example::

        # Instrument a single LLM call
        llm = ChatAnthropic(..., callbacks=get_callbacks(session_id=deal_id))
        resp = await llm.ainvoke(messages)

        # Instrument an entire LangGraph graph execution
        result = await graph.ainvoke(
            state,
            config={"callbacks": get_callbacks(session_id=deal_id, trace_name="compliance")},
        )
    """
    callbacks: list = []

    lf = _langfuse_callback(
        session_id=session_id,
        trace_name=trace_name,
        metadata=metadata,
    )
    if lf is not None:
        callbacks.append(lf)

    ls = _langsmith_callback(trace_name=trace_name)
    if ls is not None:
        callbacks.append(ls)

    return callbacks


def build_llm(
    max_tokens: int = 3000,
    execution_id: str | None = None,
    agent_name: str | None = None,
):
    """
    Construct a ChatAnthropic instance pre-wired with observability callbacks.

    Agents that call this helper automatically get:
    - Langfuse cost/latency/token tracking grouped by session and agent
    - LangSmith trace visibility for every LLM call

    Example::

        llm = build_llm(max_tokens=2000, execution_id=deal_id, agent_name="compliance_agent")
        resp = await llm.ainvoke([SystemMessage(content=system), HumanMessage(content=human)])
    """
    from langchain_anthropic import ChatAnthropic  # type: ignore[import]

    callbacks = get_callbacks(
        session_id=execution_id,
        trace_name=agent_name,
        metadata={"agent": agent_name} if agent_name else None,
    )
    return ChatAnthropic(
        model="claude-sonnet-4-6",
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        max_tokens=max_tokens,
        callbacks=callbacks if callbacks else None,
    )
