"""
Records agent runs to Django's AIAgentRun model via HTTP API.

This bridges the gap between the orchestrator's in-memory run tracking
and Django's persistent analytics database that the frontend reads.
"""

import logging
import os
import time
from typing import Any

import httpx

logger = logging.getLogger("ai_orchestrator.run_recorder")

DJANGO_API_URL = os.getenv("DJANGO_API_URL", "http://django-api:8001")
DJANGO_SERVICE_TOKEN = os.getenv("DJANGO_SERVICE_TOKEN", "")


def _auth_headers() -> dict[str, str]:
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if DJANGO_SERVICE_TOKEN:
        headers["Authorization"] = f"Bearer {DJANGO_SERVICE_TOKEN}"
    return headers


async def record_run_started(
    run_id: str,
    agent_name: str,
    deal_id: str = "",
    action: str = "run",
) -> None:
    """POST a new AIAgentRun record to Django when an agent starts."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(
                f"{DJANGO_API_URL}/api/analytics/agent-runs/",
                json={
                    "id": run_id,
                    "agent_name": agent_name,
                    "deal_id": deal_id,
                    "action": action,
                    "status": "running",
                },
                headers=_auth_headers(),
            )
            if resp.status_code in (200, 201):
                logger.info("Recorded run start: %s (%s)", run_id, agent_name)
            else:
                logger.warning(
                    "Failed to record run start %s: %s %s",
                    run_id, resp.status_code, resp.text[:200],
                )
    except Exception as exc:
        logger.warning("record_run_started failed for %s: %s", run_id, exc)


async def record_run_completed(
    run_id: str,
    latency_ms: int | None = None,
    success: bool = True,
) -> None:
    """PATCH an AIAgentRun record to mark it completed."""
    try:
        payload: dict[str, Any] = {
            "status": "completed",
            "success": success,
        }
        if latency_ms is not None:
            payload["latency_ms"] = latency_ms

        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.patch(
                f"{DJANGO_API_URL}/api/analytics/agent-runs/{run_id}/",
                json=payload,
                headers=_auth_headers(),
            )
            if resp.status_code in (200, 201):
                logger.info("Recorded run completion: %s", run_id)
            else:
                logger.warning(
                    "Failed to record run completion %s: %s %s",
                    run_id, resp.status_code, resp.text[:200],
                )
    except Exception as exc:
        logger.warning("record_run_completed failed for %s: %s", run_id, exc)


async def record_run_failed(
    run_id: str,
    error: str,
    latency_ms: int | None = None,
) -> None:
    """PATCH an AIAgentRun record to mark it failed."""
    try:
        payload: dict[str, Any] = {
            "status": "failed",
            "success": False,
            "error_message": error[:1000],
        }
        if latency_ms is not None:
            payload["latency_ms"] = latency_ms

        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.patch(
                f"{DJANGO_API_URL}/api/analytics/agent-runs/{run_id}/",
                json=payload,
                headers=_auth_headers(),
            )
            if resp.status_code in (200, 201):
                logger.info("Recorded run failure: %s", run_id)
            else:
                logger.warning(
                    "Failed to record run failure %s: %s %s",
                    run_id, resp.status_code, resp.text[:200],
                )
    except Exception as exc:
        logger.warning("record_run_failed failed for %s: %s", run_id, exc)
