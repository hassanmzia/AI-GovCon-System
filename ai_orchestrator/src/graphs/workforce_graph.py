"""
Workforce Graph — Dedicated orchestration graph for workforce planning workflows.

Wraps the WorkforceAgent's internal LangGraph workflow, adding:
  - Persistence of demand forecasts to Django
  - Hiring requisition creation for critical gaps
  - Integration with the stage trigger system for contract-award events

Usage:
    from src.graphs.workforce_graph import workforce_graph

    result = await workforce_graph.ainvoke({"trigger": "new_contract", "deal_id": "abc123"})
"""

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger("ai_orchestrator.graphs.workforce")

DJANGO_API_URL = os.getenv("DJANGO_API_URL", "http://django-api:8001")
DJANGO_SERVICE_TOKEN = os.getenv("DJANGO_SERVICE_TOKEN", "")

# Minimum gap threshold to trigger automatic hiring requisition
AUTO_REQUISITION_GAP_THRESHOLD = 2.0


def _auth_headers() -> dict[str, str]:
    t = DJANGO_SERVICE_TOKEN
    return {"Authorization": f"Bearer {t}"} if t else {}


async def _post(path: str, data: dict) -> Any:
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                f"{DJANGO_API_URL}{path}",
                json=data,
                headers=_auth_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.warning("API POST %s failed: %s", path, exc)
        return None


async def _patch(path: str, data: dict) -> Any:
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
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


async def _create_hiring_requisitions(gaps: dict, deal_id: str | None = None) -> list[dict]:
    """
    Auto-create hiring requisitions for labor categories with a critical gap.

    Args:
        gaps:    dict of {labor_category: gap_fte} (positive = shortage)
        deal_id: optional deal that triggered this requisition

    Returns:
        List of created requisition dicts.
    """
    requisitions = []
    for labor_category, gap in gaps.items():
        if not isinstance(gap, (int, float)) or gap < AUTO_REQUISITION_GAP_THRESHOLD:
            continue
        headcount_needed = max(1, round(gap))
        req = await _post("/api/workforce/hiring-requisitions/", {
            "labor_category": labor_category,
            "headcount_needed": headcount_needed,
            "priority": "high" if gap >= 4 else "medium",
            "status": "open",
            "justification": (
                f"Pipeline-driven demand gap of {gap:.1f} FTEs in {labor_category}. "
                f"Auto-created by workforce planning agent."
            ),
            "source_deal": deal_id,
        })
        if req and not req.get("error"):
            requisitions.append(req)
            logger.info("Created hiring requisition for %s (%d HC needed)", labor_category, headcount_needed)

    return requisitions


async def _persist_forecast(forecast: dict) -> None:
    """Persist the demand forecast snapshot to the analytics API."""
    if not forecast:
        return
    await _post("/api/workforce/analytics/forecast-snapshots/", {
        "forecast_data": forecast,
        "source": "ai_workforce_agent",
    })


class WorkforceGraph:
    """
    Top-level workforce planning graph.

    Wraps the WorkforceAgent and adds:
    - Forecast persistence
    - Automatic hiring requisition creation for critical gaps
    - Deal-context awareness for contract-award triggers
    """

    async def ainvoke(self, input_data: dict) -> dict:
        """
        Run the full workforce planning workflow.

        Args:
            input_data: dict with optional keys:
                deal_id (str)           – Scope to a specific deal's context
                trigger (str)           – Event that triggered this run
                                          ("new_contract", "pipeline_update", "scheduled")
                auto_requisition (bool) – Auto-create hiring reqs (default: True)
                persist_forecast (bool) – Persist forecast snapshot (default: True)

        Returns:
            dict with keys: demand_forecast, recommendations, requisitions_created,
                            labor_needs_analysis, status
        """
        from src.agents.workforce_agent import WorkforceAgent

        deal_id = input_data.get("deal_id", "")
        trigger = input_data.get("trigger", "manual")
        auto_req = input_data.get("auto_requisition", True)
        persist = input_data.get("persist_forecast", True)

        logger.info("WorkforceGraph triggered by '%s' for deal=%s", trigger, deal_id or "all")

        agent = WorkforceAgent()
        result = await agent.run({"deal_id": deal_id})

        if result.get("error"):
            logger.error("WorkforceGraph agent failed: %s", result["error"])
            return {**result, "status": "failed", "requisitions_created": []}

        # Persist forecast snapshot
        forecast = result.get("demand_forecast", {})
        if persist:
            try:
                await _persist_forecast(forecast)
            except Exception as exc:
                logger.warning("Failed to persist forecast: %s", exc)

        # Auto-create hiring requisitions for critical gaps
        requisitions_created = []
        if auto_req:
            gaps = forecast.get("gaps", {})
            if gaps:
                try:
                    requisitions_created = await _create_hiring_requisitions(gaps, deal_id or None)
                except Exception as exc:
                    logger.warning("Failed to create hiring requisitions: %s", exc)

        return {
            **result,
            "status": "completed",
            "trigger": trigger,
            "requisitions_created": requisitions_created,
            "requisition_count": len(requisitions_created),
        }


async def run_scheduled_workforce_analysis() -> dict:
    """
    Run a full workforce planning cycle on a schedule (e.g., weekly).

    Returns summary of the run including gaps identified and requisitions created.
    """
    graph = WorkforceGraph()
    result = await graph.ainvoke({
        "trigger": "scheduled",
        "auto_requisition": True,
        "persist_forecast": True,
    })

    forecast = result.get("demand_forecast", {})
    gaps = forecast.get("gaps", {})
    critical_gaps = {k: v for k, v in gaps.items() if isinstance(v, (int, float)) and v >= AUTO_REQUISITION_GAP_THRESHOLD}

    return {
        "status": result.get("status", "unknown"),
        "employees_analyzed": result.get("employee_count", 0),
        "pipeline_deals": result.get("pipeline_deals_count", 0),
        "critical_gap_categories": list(critical_gaps.keys()),
        "requisitions_created": result.get("requisition_count", 0),
        "recommendation_categories": len(result.get("recommendations", [])),
    }


# Module-level graph instance
workforce_graph = WorkforceGraph()
