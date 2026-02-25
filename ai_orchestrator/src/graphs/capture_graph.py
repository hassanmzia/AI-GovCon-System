"""
Capture Graph — Dedicated orchestration graph for the capture planning workflow.

This module exposes `capture_graph` as a top-level importable entrypoint,
wiring together:
  1. CompetitorSimAgent   — Ghost strategies & competitive landscape
  2. CaptureAgent         — Capture plan generation (win strategy, action items, risks)
  3. RankingAgent         — Re-rank any newly discovered related opportunities

The graph is event-driven and is triggered by a deal entering `capture_plan` stage.
It can also be invoked directly via the REST API for manual capture planning.
"""

import asyncio
import logging
import os
from typing import Any

import httpx
from typing_extensions import TypedDict

logger = logging.getLogger("ai_orchestrator.graphs.capture")

DJANGO_API_URL = os.getenv("DJANGO_API_URL", "http://django-api:8001")
DJANGO_SERVICE_TOKEN = os.getenv("DJANGO_SERVICE_TOKEN", "")


def _auth_headers() -> dict[str, str]:
    t = DJANGO_SERVICE_TOKEN
    return {"Authorization": f"Bearer {t}"} if t else {}


async def _patch(path: str, data: dict) -> Any:
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.patch(
                f"{DJANGO_API_URL}{path}",
                json=data,
                headers=_auth_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.warning("API PATCH %s failed: %s", path, exc)
        return None


class CaptureWorkflowState(TypedDict):
    deal_id: str
    competitor_sim_result: dict
    capture_plan_result: dict
    ranking_result: dict
    status: str
    errors: list[str]


async def run_competitor_simulation(state: CaptureWorkflowState) -> dict:
    """Step 1: Run competitor simulation to inform capture planning."""
    from src.agents.competitor_sim_agent import CompetitorSimAgent

    deal_id = state["deal_id"]
    agent = CompetitorSimAgent()
    try:
        result = await agent.run({"deal_id": deal_id})
        logger.info("Competitor simulation complete for deal %s: %d profiles", deal_id, len(result.get("competitor_profiles", [])))
        return {"competitor_sim_result": result}
    except Exception as exc:
        logger.error("Competitor simulation failed for deal %s: %s", deal_id, exc)
        return {"competitor_sim_result": {}, "errors": state.get("errors", []) + [f"competitor_sim: {exc}"]}


async def run_capture_planning(state: CaptureWorkflowState) -> dict:
    """Step 2: Generate the capture plan using competitor intel."""
    from src.agents.capture_agent import CaptureAgent

    deal_id = state["deal_id"]
    agent = CaptureAgent()
    try:
        result = await agent.run({
            "deal_id": deal_id,
            "competitor_intel": state.get("competitor_sim_result", {}),
        })
        logger.info("Capture plan generated for deal %s", deal_id)
        return {"capture_plan_result": result}
    except Exception as exc:
        logger.error("Capture planning failed for deal %s: %s", deal_id, exc)
        return {"capture_plan_result": {}, "errors": state.get("errors", []) + [f"capture_plan: {exc}"]}


async def update_deal_capture_status(state: CaptureWorkflowState) -> dict:
    """Step 3: Mark the deal's capture plan as AI-generated and complete."""
    deal_id = state["deal_id"]
    capture_result = state.get("capture_plan_result", {})

    if capture_result and not capture_result.get("error"):
        await _patch(f"/api/deals/{deal_id}/", {
            "capture_plan_status": "ai_generated",
            "capture_plan_complete": True,
        })
        status = "completed"
    else:
        status = "partial"

    logger.info("Capture workflow status for deal %s: %s", deal_id, status)
    return {"status": status}


async def run_capture_workflow(deal_id: str) -> dict:
    """
    Execute the full capture workflow for a deal.

    Steps:
      1. Competitor simulation
      2. Capture plan generation
      3. Deal status update

    Returns aggregated results from all steps.
    """
    state: CaptureWorkflowState = {
        "deal_id": deal_id,
        "competitor_sim_result": {},
        "capture_plan_result": {},
        "ranking_result": {},
        "status": "running",
        "errors": [],
    }

    # Execute sequentially (each step informs the next)
    state.update(await run_competitor_simulation(state))
    state.update(await run_capture_planning(state))
    state.update(await update_deal_capture_status(state))

    return {
        "deal_id": deal_id,
        "status": state["status"],
        "competitor_profiles": state["competitor_sim_result"].get("competitor_profiles", []),
        "ghost_strategies": state["competitor_sim_result"].get("ghost_strategies", []),
        "capture_plan": state["capture_plan_result"].get("capture_plan", {}),
        "errors": state["errors"],
    }


# Expose as a callable graph-compatible object
class CaptureGraph:
    """Wrapper exposing capture workflow as a graph-compatible async callable."""

    async def ainvoke(self, input_data: dict) -> dict:
        deal_id = input_data.get("deal_id", "")
        if not deal_id:
            return {"error": "deal_id is required", "status": "failed"}
        return await run_capture_workflow(deal_id)


capture_graph = CaptureGraph()
