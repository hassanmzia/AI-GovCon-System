"""FastAPI router for SSE streaming endpoints."""
import asyncio
import json
import logging
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

logger = logging.getLogger("ai_orchestrator.routers.stream")

router = APIRouter()

# Timeout in seconds to wait for new events before sending a keepalive ping
_KEEPALIVE_INTERVAL = 15
# Maximum time (seconds) to keep a stream open when the run is idle
_STREAM_TIMEOUT = 300


async def _event_generator(run_id: str) -> AsyncGenerator[str, None]:
    """
    Yield SSE-formatted events from the per-run asyncio Queue.

    Events are formatted as:
        data: <json>\n\n
    """
    from src.routers.agents import run_event_queues, _runs

    # Validate that the run exists
    if run_id not in _runs and run_id not in run_event_queues:
        yield f"data: {json.dumps({'event': 'error', 'data': {'error': f'Run {run_id} not found'}})}\n\n"
        return

    # Create the queue if the run was created before the stream was opened
    if run_id not in run_event_queues:
        run_event_queues[run_id] = asyncio.Queue()

    queue = run_event_queues[run_id]
    elapsed = 0.0

    # Send initial connection confirmation
    yield f"data: {json.dumps({'event': 'connected', 'data': {'run_id': run_id}})}\n\n"

    while elapsed < _STREAM_TIMEOUT:
        try:
            event = await asyncio.wait_for(queue.get(), timeout=_KEEPALIVE_INTERVAL)
        except asyncio.TimeoutError:
            # Send keepalive comment to prevent connection timeout
            elapsed += _KEEPALIVE_INTERVAL
            yield ": keepalive\n\n"
            # Check if the run has already finished without putting a done event
            run = _runs.get(run_id)
            if run and run["status"] in ("completed", "failed"):
                yield f"data: {json.dumps({'event': 'done', 'data': run['result']})}\n\n"
                break
            continue

        elapsed = 0.0  # reset timeout on activity
        event_name = event.get("event", "message")
        payload = json.dumps({"event": event_name, "data": event.get("data", {})})
        yield f"data: {payload}\n\n"

        # Stop streaming when a terminal event is received
        if event_name in ("done", "error"):
            break


@router.get("/ai/stream/{run_id}", tags=["stream"])
async def stream_agent_events(run_id: str) -> StreamingResponse:
    """
    SSE stream of agent thinking events for a given run_id.

    Clients should connect with:
        EventSource('/ai/stream/<run_id>')

    Events emitted:
        connected  - Initial connection acknowledgment
        thinking   - Intermediate reasoning steps
        done       - Run completed (includes final result)
        error      - Run failed (includes error message)
    """
    return StreamingResponse(
        _event_generator(run_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )
