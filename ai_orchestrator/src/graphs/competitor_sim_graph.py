"""
Competitor Simulation Graph — Dedicated orchestration graph for competitive intelligence.

This module is a thin re-export / wrapper around the CompetitorSimAgent's
internal LangGraph workflow, making it importable as a top-level graph
for use in:
  - Stage-triggered automated workflows (capture_plan stage)
  - Manual API-triggered competitive analysis requests
  - Scheduled nightly competitive landscape refreshes

Usage:
    from src.graphs.competitor_sim_graph import competitor_sim_graph

    result = await competitor_sim_graph.ainvoke({"deal_id": "abc123"})
"""

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger("ai_orchestrator.graphs.competitor_sim")

DJANGO_API_URL = os.getenv("DJANGO_API_URL", "http://django-api:8001")
DJANGO_SERVICE_TOKEN = os.getenv("DJANGO_SERVICE_TOKEN", "")


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


class CompetitorSimGraph:
    """
    Top-level competitor simulation graph.

    Wraps the CompetitorSimAgent's compiled LangGraph workflow and adds
    post-processing to persist results to the Django backend.
    """

    async def ainvoke(self, input_data: dict) -> dict:
        """
        Run the full competitor simulation workflow.

        Args:
            input_data: dict with keys:
                deal_id (required)  – The deal to analyze
                persist (bool)      – Whether to persist results (default: True)

        Returns:
            dict with keys: deal_id, competitor_profiles, simulation_results,
                            ghost_strategies, status
        """
        from src.agents.competitor_sim_agent import CompetitorSimAgent

        deal_id = input_data.get("deal_id", "")
        persist = input_data.get("persist", True)

        if not deal_id:
            return {"error": "deal_id is required", "status": "failed"}

        agent = CompetitorSimAgent()
        result = await agent.run({"deal_id": deal_id})

        if result.get("error"):
            logger.error("CompetitorSimGraph failed for deal %s: %s", deal_id, result["error"])
            return result

        # Optionally persist ghost strategies to Django
        if persist and result.get("ghost_strategies"):
            try:
                await _post(f"/api/deals/{deal_id}/competitive-intel/", {
                    "competitor_profiles": result.get("competitor_profiles", []),
                    "simulation_results": result.get("simulation_results", []),
                    "ghost_strategies": result.get("ghost_strategies", []),
                    "source": "ai_competitor_sim",
                })
                logger.info("Persisted competitor sim results for deal %s", deal_id)
            except Exception as exc:
                logger.warning("Failed to persist competitor sim for deal %s: %s", deal_id, exc)

        return result


async def run_nightly_competitive_refresh(agency: str | None = None, naics: str | None = None) -> dict:
    """
    Run a competitive landscape refresh for all active pipeline deals.

    Optionally filter by agency or NAICS code. Used for scheduled nightly runs.

    Returns:
        {
            "deals_processed": int,
            "profiles_generated": int,
            "errors": list[str],
        }
    """
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            params: dict = {"stage__in": "capture_plan,proposal_dev,red_team"}
            if agency:
                params["agency"] = agency
            resp = await client.get(
                f"{DJANGO_API_URL}/api/deals/",
                params=params,
                headers=_auth_headers(),
            )
            resp.raise_for_status()
            deals = resp.json().get("results", [])
    except Exception as exc:
        logger.error("Failed to fetch deals for nightly refresh: %s", exc)
        return {"deals_processed": 0, "profiles_generated": 0, "errors": [str(exc)]}

    graph = CompetitorSimGraph()
    errors = []
    profiles_generated = 0

    for deal in deals:
        deal_id = str(deal.get("id", ""))
        if not deal_id:
            continue
        try:
            result = await graph.ainvoke({"deal_id": deal_id, "persist": True})
            profiles_generated += len(result.get("competitor_profiles", []))
        except Exception as exc:
            logger.error("Nightly refresh failed for deal %s: %s", deal_id, exc)
            errors.append(f"deal:{deal_id} — {exc}")

    return {
        "deals_processed": len(deals),
        "profiles_generated": profiles_generated,
        "errors": errors,
    }


# Module-level graph instance
competitor_sim_graph = CompetitorSimGraph()
