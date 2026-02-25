"""MCP tool server: Stage transitions, task management, and deal workflow operations."""
import logging
import os
from typing import Any

import httpx

logger = logging.getLogger("ai_orchestrator.mcp.workflow")

_DJANGO_URL = os.getenv("DJANGO_API_URL", "http://django-api:8001")
_SERVICE_TOKEN = os.getenv("DJANGO_SERVICE_TOKEN", "")


def _headers() -> dict:
    return {"Authorization": f"Bearer {_SERVICE_TOKEN}"} if _SERVICE_TOKEN else {}


async def get_deal(deal_id: str) -> dict[str, Any]:
    """Fetch full deal detail including stage, tasks, approvals, and team.

    Args:
        deal_id: Deal UUID.

    Returns:
        Full deal dict with all related data.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{_DJANGO_URL}/api/deals/{deal_id}/",
                headers=_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("Deal fetch failed for %s: %s", deal_id, exc)
        return {"id": deal_id, "error": str(exc)}


async def list_deals(
    stage: str | None = None,
    owner_id: str | None = None,
    priority: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """List deals with optional filtering.

    Args:
        stage: Filter by pipeline stage.
        owner_id: Filter by deal owner user ID.
        priority: Filter by priority ("critical", "high", "medium", "low").
        limit: Max results.

    Returns:
        List of deal summary dicts.
    """
    try:
        params: dict[str, Any] = {"limit": limit}
        if stage:
            params["stage"] = stage
        if owner_id:
            params["owner"] = owner_id
        if priority:
            params["priority"] = priority

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{_DJANGO_URL}/api/deals/",
                params=params,
                headers=_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("Deal list failed: %s", exc)
        return []


async def transition_deal_stage(
    deal_id: str,
    target_stage: str,
    reason: str = "",
    ai_recommendation: str = "",
    confidence: float = 0.0,
) -> dict[str, Any]:
    """Request a deal stage transition (subject to HITL approval).

    Args:
        deal_id: Deal UUID.
        target_stage: Target pipeline stage.
        reason: Reason for the transition.
        ai_recommendation: AI's recommendation text.
        confidence: AI confidence score (0-1).

    Returns:
        Dict with status ("transitioned", "pending_approval"), approval_id if pending.
    """
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{_DJANGO_URL}/api/deals/{deal_id}/transition/",
                json={
                    "target_stage": target_stage,
                    "reason": reason,
                    "ai_recommendation": ai_recommendation,
                    "ai_confidence": confidence,
                },
                headers=_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("Stage transition failed for deal %s: %s", deal_id, exc)
        return {"deal_id": deal_id, "error": str(exc), "status": "failed"}


async def create_task(
    deal_id: str,
    title: str,
    description: str = "",
    assigned_to: str | None = None,
    due_date: str | None = None,
    task_type: str = "general",
    priority: str = "medium",
) -> dict[str, Any]:
    """Create a task for a deal.

    Args:
        deal_id: Deal UUID.
        title: Task title.
        description: Optional task description.
        assigned_to: User ID to assign to.
        due_date: Due date (ISO format string, e.g. "2024-12-31").
        task_type: Task type ("general", "review", "approval", "research", "writing", "qa").
        priority: Priority ("low", "medium", "high", "critical").

    Returns:
        Created task dict with ID.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{_DJANGO_URL}/api/deals/{deal_id}/tasks/",
                json={
                    "title": title,
                    "description": description,
                    "assigned_to": assigned_to,
                    "due_date": due_date,
                    "task_type": task_type,
                    "priority": priority,
                },
                headers=_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("Task creation failed for deal %s: %s", deal_id, exc)
        return {"error": str(exc)}


async def complete_task(task_id: str, notes: str = "") -> dict[str, Any]:
    """Mark a task as completed.

    Args:
        task_id: Task UUID.
        notes: Optional completion notes.

    Returns:
        Updated task dict.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{_DJANGO_URL}/api/deals/tasks/{task_id}/complete/",
                json={"notes": notes},
                headers=_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("Task completion failed for %s: %s", task_id, exc)
        return {"task_id": task_id, "error": str(exc)}


async def get_pending_approvals(deal_id: str | None = None) -> list[dict[str, Any]]:
    """Fetch pending HITL approval requests.

    Args:
        deal_id: Optional deal UUID to filter by.

    Returns:
        List of pending approval dicts with type, recommendation, confidence, and context.
    """
    try:
        params: dict[str, Any] = {"status": "pending"}
        if deal_id:
            params["deal_id"] = deal_id

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{_DJANGO_URL}/api/deals/approvals/",
                params=params,
                headers=_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("Pending approvals fetch failed: %s", exc)
        return []


async def submit_approval_recommendation(
    deal_id: str,
    approval_type: str,
    recommendation: str,
    rationale: str,
    confidence: float,
    context_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Submit an AI approval recommendation for human review.

    This creates a pending approval that will be shown to the user in the UI.

    Args:
        deal_id: Deal UUID.
        approval_type: Type of approval needed:
            "bid_no_bid", "stage_transition", "pricing_approval",
            "teaming_approval", "submission_approval".
        recommendation: AI recommendation ("approve", "reject", "conditional").
        rationale: Explanation of the recommendation.
        confidence: Confidence score (0-1).
        context_data: Additional context for the human reviewer.

    Returns:
        Created approval dict with ID and status.
    """
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{_DJANGO_URL}/api/deals/{deal_id}/approvals/",
                json={
                    "approval_type": approval_type,
                    "ai_recommendation": recommendation,
                    "ai_rationale": rationale,
                    "ai_confidence": confidence,
                    "context_data": context_data or {},
                },
                headers=_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("Approval submission failed: %s", exc)
        return {"deal_id": deal_id, "error": str(exc)}


async def update_deal_field(
    deal_id: str,
    field_updates: dict[str, Any],
) -> dict[str, Any]:
    """Update one or more fields on a deal record.

    Args:
        deal_id: Deal UUID.
        field_updates: Dict of field_name → new_value to update.

    Returns:
        Updated deal dict.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.patch(
                f"{_DJANGO_URL}/api/deals/{deal_id}/",
                json=field_updates,
                headers=_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("Deal update failed for %s: %s", deal_id, exc)
        return {"deal_id": deal_id, "error": str(exc)}


async def get_deal_timeline(deal_id: str) -> list[dict[str, Any]]:
    """Get the stage history and key events timeline for a deal.

    Returns:
        List of timeline events with timestamp, event_type, description, and actor.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{_DJANGO_URL}/api/deals/{deal_id}/timeline/",
                headers=_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("Deal timeline fetch failed for %s: %s", deal_id, exc)
        return []


async def check_bid_gate_prerequisites(deal_id: str) -> dict[str, Any]:
    """Check if all bid gate prerequisites are satisfied for a deal.

    Verifies: strategy review, capture plan, legal review, pricing estimate, team confirmation.

    Returns:
        Dict with ready (bool), passed_checks, failed_checks, overall_readiness_score.
    """
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{_DJANGO_URL}/api/deals/{deal_id}/bid-gate-check/",
                headers=_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("Bid gate check failed for %s: %s", deal_id, exc)
        return {
            "deal_id": deal_id,
            "ready": False,
            "passed_checks": [],
            "failed_checks": [],
            "error": str(exc),
        }
