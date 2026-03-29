"""Workforce & HR Intelligence AI Agent using LangGraph."""

import logging
import os
from typing import Annotated, Any

import operator

import httpx
from src.llm_provider import get_chat_model
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from typing_extensions import TypedDict

from src.agents.base import BaseAgent

logger = logging.getLogger("ai_orchestrator.agents.workforce")

DJANGO_API_URL = os.getenv("DJANGO_API_URL", "http://django-api:8001")
DJANGO_SERVICE_TOKEN = os.getenv("DJANGO_SERVICE_TOKEN", "")


# ── State ─────────────────────────────────────────────────────────────────────


class WorkforceState(TypedDict):
    deal_id: str
    pipeline_deals: list[dict]
    employees: list[dict]
    assignments: list[dict]
    demand_forecast: dict
    labor_needs_analysis: str
    recommendations: list[dict]
    messages: Annotated[list, operator.add]


# ── Django API helpers ────────────────────────────────────────────────────────


def _auth_headers() -> dict[str, str]:
    token = DJANGO_SERVICE_TOKEN
    return {"Authorization": f"Bearer {token}"} if token else {}


async def _fetch_pipeline_deals() -> list[dict]:
    """Fetch deals in active pipeline stages."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{DJANGO_API_URL}/api/deals/deals/",
                params={
                    "stage__in": "capture_plan,proposal_dev,red_team,final_review,submit,post_submit,award_pending",
                    "ordering": "-win_probability",
                },
                headers=_auth_headers(),
            )
            resp.raise_for_status()
            return resp.json().get("results", [])
    except Exception as exc:
        logger.warning("Could not fetch pipeline deals: %s", exc)
        return []


async def _fetch_employees() -> list[dict]:
    """Fetch active employees."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{DJANGO_API_URL}/api/workforce/employees/",
                params={"is_active": "true", "ordering": "name"},
                headers=_auth_headers(),
            )
            resp.raise_for_status()
            return resp.json().get("results", [])
    except Exception as exc:
        logger.warning("Could not fetch employees: %s", exc)
        return []


async def _fetch_assignments() -> list[dict]:
    """Fetch active assignments."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{DJANGO_API_URL}/api/workforce/assignments/",
                params={"is_active": "true"},
                headers=_auth_headers(),
            )
            resp.raise_for_status()
            return resp.json().get("results", [])
    except Exception as exc:
        logger.warning("Could not fetch assignments: %s", exc)
        return []


async def _fetch_demand_forecast() -> dict:
    """Fetch the computed demand forecast from the analytics endpoint."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{DJANGO_API_URL}/api/workforce/analytics/demand-forecast/",
                headers=_auth_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.warning("Could not fetch demand forecast: %s", exc)
        return {}


# ── LLM ───────────────────────────────────────────────────────────────────────


def _get_llm():
    return get_chat_model(max_tokens=2048)


# ── Graph nodes ───────────────────────────────────────────────────────────────


async def load_pipeline_context(state: WorkforceState) -> dict:
    """Load deal pipeline, employees, and active assignments."""
    logger.info("Loading workforce pipeline context")
    pipeline_deals, employees, assignments = (
        await _fetch_pipeline_deals(),
        await _fetch_employees(),
        await _fetch_assignments(),
    )
    return {
        "pipeline_deals": pipeline_deals,
        "employees": employees,
        "assignments": assignments,
        "messages": [
            HumanMessage(
                content=(
                    f"Loaded {len(pipeline_deals)} pipeline deals, "
                    f"{len(employees)} employees, {len(assignments)} assignments"
                )
            )
        ],
    }


async def analyze_labor_needs(state: WorkforceState) -> dict:
    """Use Claude to analyze labor category needs across the pipeline."""
    logger.info("Analyzing labor needs from pipeline")
    llm = _get_llm()

    system = SystemMessage(
        content=(
            "You are a workforce planning analyst for a government contracting firm. "
            "Analyze the deal pipeline and current workforce to identify labor "
            "category needs, skill gaps, and clearance requirements. "
            "Be specific about quantities and timelines."
        )
    )

    # Summarize pipeline for the LLM
    pipeline_summary = []
    for deal in state["pipeline_deals"][:20]:  # Limit context size
        pipeline_summary.append(
            {
                "title": deal.get("title", ""),
                "stage": deal.get("stage", ""),
                "win_probability": deal.get("win_probability", 0),
                "estimated_value": str(deal.get("estimated_value", "")),
            }
        )

    employee_summary = {
        "total_active": len(state["employees"]),
        "by_department": {},
        "by_clearance": {},
    }
    for emp in state["employees"]:
        dept = emp.get("department", "Unknown")
        clr = emp.get("clearance_type", "none")
        employee_summary["by_department"][dept] = (
            employee_summary["by_department"].get(dept, 0) + 1
        )
        employee_summary["by_clearance"][clr] = (
            employee_summary["by_clearance"].get(clr, 0) + 1
        )

    human = HumanMessage(
        content=(
            f"Pipeline Deals:\n{pipeline_summary}\n\n"
            f"Current Workforce:\n{employee_summary}\n\n"
            f"Active Assignments: {len(state['assignments'])}\n\n"
            "Analyze:\n"
            "1. What labor categories are most needed based on the pipeline?\n"
            "2. What clearance levels will be required?\n"
            "3. What skill gaps exist between current workforce and pipeline needs?\n"
            "4. What is the urgency timeline for staffing?\n"
        )
    )

    try:
        response = await llm.ainvoke([system, human])
        analysis = response.content
    except Exception as exc:
        logger.error("LLM failed in analyze_labor_needs: %s", exc)
        analysis = "Labor needs analysis unavailable due to API error."

    return {
        "labor_needs_analysis": analysis,
        "messages": [HumanMessage(content="Labor needs analysis complete.")],
    }


async def forecast_demand(state: WorkforceState) -> dict:
    """Fetch and enrich the computed demand forecast."""
    logger.info("Fetching demand forecast")
    forecast = await _fetch_demand_forecast()
    return {
        "demand_forecast": forecast,
        "messages": [
            HumanMessage(
                content=(
                    f"Demand forecast loaded: "
                    f"{len(forecast.get('forecast', {}))} labor categories, "
                    f"{forecast.get('pipeline_deals', 0)} deals analyzed"
                )
            )
        ],
    }


async def generate_recommendations(state: WorkforceState) -> dict:
    """Generate actionable workforce recommendations using Claude."""
    logger.info("Generating workforce recommendations")
    llm = _get_llm()

    system = SystemMessage(
        content=(
            "You are a chief human resources officer and workforce strategist "
            "for a government contracting firm. Generate specific, actionable "
            "recommendations for workforce planning based on pipeline demand "
            "forecasts and current capacity. Prioritize recommendations by "
            "urgency and impact. Output structured recommendations."
        )
    )

    forecast = state.get("demand_forecast", {})
    gaps = forecast.get("gaps", {})
    capacity = forecast.get("current_capacity", {})
    demand = forecast.get("forecast", {})

    human = HumanMessage(
        content=(
            f"Labor Needs Analysis:\n{state.get('labor_needs_analysis', 'N/A')}\n\n"
            f"Demand Forecast (weighted FTEs by labor category):\n{demand}\n\n"
            f"Current Capacity (employees by labor category):\n{capacity}\n\n"
            f"Gaps (positive = hiring need, negative = surplus):\n{gaps}\n\n"
            f"Pipeline Deals Analyzed: {forecast.get('pipeline_deals', 0)}\n\n"
            "Provide recommendations in these categories:\n"
            "1. Immediate Hiring Needs (next 30 days)\n"
            "2. Short-term Staffing Actions (30-90 days)\n"
            "3. Clearance Sponsorship Priorities\n"
            "4. Skill Development / Training\n"
            "5. Teaming / Subcontractor Strategies\n"
            "6. Risk Mitigation\n"
        )
    )

    try:
        response = await llm.ainvoke([system, human])
        content = response.content
    except Exception as exc:
        logger.error("LLM failed in generate_recommendations: %s", exc)
        content = "Recommendations unavailable due to API error."

    # Parse into structured recommendations
    recommendations = []
    current_category = ""
    current_items = []

    for line in content.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue
        # Detect category headers (numbered items or **bold** headers)
        if stripped.startswith(("1.", "2.", "3.", "4.", "5.", "6.")) or stripped.startswith(
            "**"
        ):
            if current_category and current_items:
                recommendations.append(
                    {"category": current_category, "items": current_items}
                )
            current_category = stripped.strip("*#. 0123456789").strip()
            current_items = []
        elif stripped.startswith(("-", "•")):
            current_items.append(stripped.lstrip("-•").strip())

    if current_category and current_items:
        recommendations.append(
            {"category": current_category, "items": current_items}
        )

    # If parsing didn't produce structured output, return raw text
    if not recommendations:
        recommendations = [{"category": "General", "items": [content]}]

    return {
        "recommendations": recommendations,
        "messages": [
            HumanMessage(
                content=f"Generated {len(recommendations)} recommendation categories."
            )
        ],
    }


# ── Graph builder ─────────────────────────────────────────────────────────────


def build_workforce_graph() -> StateGraph:
    """Construct and compile the workforce planning LangGraph workflow."""
    workflow = StateGraph(WorkforceState)

    workflow.add_node("load_pipeline_context", load_pipeline_context)
    workflow.add_node("analyze_labor_needs", analyze_labor_needs)
    workflow.add_node("forecast_demand", forecast_demand)
    workflow.add_node("generate_recommendations", generate_recommendations)

    workflow.set_entry_point("load_pipeline_context")
    workflow.add_edge("load_pipeline_context", "analyze_labor_needs")
    workflow.add_edge("analyze_labor_needs", "forecast_demand")
    workflow.add_edge("forecast_demand", "generate_recommendations")
    workflow.add_edge("generate_recommendations", END)

    return workflow.compile()


workforce_graph = build_workforce_graph()


# ── Agent class ───────────────────────────────────────────────────────────────


class WorkforceAgent(BaseAgent):
    """LangGraph-based Workforce & HR Intelligence Agent."""

    agent_name = "workforce_agent"

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Run workforce planning analysis.

        Args:
            input_data: Optional dict. May contain 'deal_id' to scope
                        analysis to a specific deal's pipeline context.

        Returns:
            dict with keys: demand_forecast, labor_needs_analysis,
            recommendations, pipeline_deals_count.
        """
        deal_id = input_data.get("deal_id", "")

        initial_state: WorkforceState = {
            "deal_id": deal_id,
            "pipeline_deals": [],
            "employees": [],
            "assignments": [],
            "demand_forecast": {},
            "labor_needs_analysis": "",
            "recommendations": [],
            "messages": [],
        }

        try:
            await self.emit_event(
                "thinking",
                {"message": "Starting workforce planning analysis"},
                execution_id=deal_id or "workforce",
            )
            final_state = await workforce_graph.ainvoke(initial_state)
            await self.emit_event(
                "output",
                {
                    "recommendation_count": len(final_state["recommendations"]),
                    "forecast_categories": len(
                        final_state.get("demand_forecast", {}).get("forecast", {})
                    ),
                },
                execution_id=deal_id or "workforce",
            )
            return {
                "demand_forecast": final_state["demand_forecast"],
                "labor_needs_analysis": final_state["labor_needs_analysis"],
                "recommendations": final_state["recommendations"],
                "pipeline_deals_count": len(final_state["pipeline_deals"]),
                "employee_count": len(final_state["employees"]),
            }
        except Exception as exc:
            logger.exception("WorkforceAgent.run failed")
            await self.emit_event(
                "error",
                {"error": str(exc)},
                execution_id=deal_id or "workforce",
            )
            return {"error": str(exc)}
