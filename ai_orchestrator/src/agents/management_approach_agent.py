"""Management Approach Drafter AI Agent using LangGraph.

Generates the management approach and organizational structure section
of a federal proposal. Integrates teaming partner roles, key personnel,
staffing plan, and risk management approach.

Events: MANAGEMENT_APPROACH_DRAFTED, ORG_CHART_GENERATED, STAFFING_PLAN_CREATED.
"""
import logging
import os
from typing import Annotated, Any
import operator

import httpx
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from typing_extensions import TypedDict

from src.agents.base import BaseAgent
from src.llm_provider import get_chat_model

logger = logging.getLogger("ai_orchestrator.agents.management_approach")

DJANGO_API_URL = os.getenv("DJANGO_API_URL", "http://django-api:8001")
DJANGO_SERVICE_TOKEN = os.getenv("DJANGO_SERVICE_TOKEN", "")


# ── State ─────────────────────────────────────────────────────────────────────

class ManagementApproachState(TypedDict):
    deal_id: str
    deal: dict
    opportunity: dict
    teaming_partners: list[dict]
    key_personnel: list[dict]
    organizational_structure: dict
    staffing_plan: dict
    risk_management: str
    quality_management: str
    transition_plan: str
    management_approach_text: str
    org_chart_description: str
    messages: Annotated[list, operator.add]


# ── Django API helpers ────────────────────────────────────────────────────────

def _auth_headers() -> dict[str, str]:
    token = DJANGO_SERVICE_TOKEN
    return {"Authorization": f"Bearer {token}"} if token else {}


async def _fetch_deal(deal_id: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{DJANGO_API_URL}/api/deals/deals/{deal_id}/",
                headers=_auth_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.warning("Failed to fetch deal %s: %s", deal_id, exc)
        return {"id": deal_id}


# ── Graph Nodes ───────────────────────────────────────────────────────────────

async def gather_context(state: ManagementApproachState) -> dict:
    """Gather deal context, teaming partners, and key personnel."""
    deal_id = state["deal_id"]
    deal = await _fetch_deal(deal_id)

    # Fetch teaming and staffing data
    teaming_partners = []
    key_personnel = []
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Capture plan may have teaming info
            resp = await client.get(
                f"{DJANGO_API_URL}/api/deals/deals/{deal_id}/artifacts/",
                headers=_auth_headers(),
            )
            if resp.status_code == 200:
                artifacts = resp.json()
                deal["artifacts"] = artifacts
    except Exception as exc:
        logger.warning("Failed to fetch artifacts for deal %s: %s", deal_id, exc)

    return {
        "deal": deal,
        "opportunity": deal.get("opportunity_detail", {}),
        "teaming_partners": teaming_partners,
        "key_personnel": key_personnel,
        "messages": [{"role": "system", "content": f"Gathered context for deal {deal_id}"}],
    }


async def draft_org_structure(state: ManagementApproachState) -> dict:
    """Draft organizational structure and key personnel assignments."""
    llm = get_chat_model(max_tokens=3000)
    deal = state.get("deal", {})
    partners = state.get("teaming_partners", [])

    prompt = f"""You are a federal proposal management consultant. Draft the organizational
structure for a government contract proposal.

Deal: {deal.get('title', 'N/A')}
Opportunity: {deal.get('opportunity_title', 'N/A')}
Teaming Partners: {partners}

Generate:
1. Program Management Office (PMO) structure
2. Key personnel roles and responsibilities
3. Reporting lines and communication channels
4. Teaming partner integration points
5. Organizational chart description (text-based)

Format as clear proposal-ready content suitable for Volume II - Management Approach."""

    resp = await llm.ainvoke([
        SystemMessage(content="You are an expert federal proposal writer specializing in management volumes."),
        HumanMessage(content=prompt),
    ])

    return {
        "organizational_structure": {"description": resp.content},
        "org_chart_description": resp.content[:500],
        "messages": [{"role": "assistant", "content": "Drafted organizational structure"}],
    }


async def draft_staffing_plan(state: ManagementApproachState) -> dict:
    """Draft staffing plan with labor categories and phasing."""
    llm = get_chat_model(max_tokens=3000)
    deal = state.get("deal", {})

    prompt = f"""Draft a staffing plan for a federal contract proposal.

Deal: {deal.get('title', 'N/A')}

Include:
1. Labor category definitions and qualifications
2. Staffing ramp-up and phase-in plan
3. Retention and succession planning
4. Clearance management approach (if applicable)
5. Subcontractor staffing integration

Format as clear proposal-ready content."""

    resp = await llm.ainvoke([
        SystemMessage(content="You are an expert federal proposal writer."),
        HumanMessage(content=prompt),
    ])

    return {
        "staffing_plan": {"description": resp.content},
        "messages": [{"role": "assistant", "content": "Drafted staffing plan"}],
    }


async def draft_management_approach(state: ManagementApproachState) -> dict:
    """Synthesize the full management approach section."""
    llm = get_chat_model(max_tokens=4000)
    deal = state.get("deal", {})
    org = state.get("organizational_structure", {})
    staffing = state.get("staffing_plan", {})

    prompt = f"""Synthesize a complete Management Approach section (Volume II) for a federal
proposal. Integrate the following components:

Deal: {deal.get('title', 'N/A')}
Organizational Structure: {org.get('description', 'N/A')[:2000]}
Staffing Plan: {staffing.get('description', 'N/A')[:2000]}

The Management Approach section must include:
1. Management Philosophy and Approach
2. Organizational Structure (reference org chart)
3. Key Personnel and Qualifications
4. Staffing and Phase-In Plan
5. Risk Management Approach
6. Quality Management/Assurance Plan
7. Transition Plan (if applicable)
8. Communication and Reporting

Write in formal proposal language. Be specific and avoid generic boilerplate."""

    resp = await llm.ainvoke([
        SystemMessage(content="You are an expert federal proposal writer specializing in management volumes for government contracts."),
        HumanMessage(content=prompt),
    ])

    return {
        "management_approach_text": resp.content,
        "risk_management": "Integrated in management approach",
        "quality_management": "Integrated in management approach",
        "messages": [{"role": "assistant", "content": "Synthesized management approach"}],
    }


# ── Graph ─────────────────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    g = StateGraph(ManagementApproachState)
    g.add_node("gather_context", gather_context)
    g.add_node("draft_org_structure", draft_org_structure)
    g.add_node("draft_staffing_plan", draft_staffing_plan)
    g.add_node("draft_management_approach", draft_management_approach)

    g.set_entry_point("gather_context")
    g.add_edge("gather_context", "draft_org_structure")
    g.add_edge("draft_org_structure", "draft_staffing_plan")
    g.add_edge("draft_staffing_plan", "draft_management_approach")
    g.add_edge("draft_management_approach", END)
    return g


_graph = build_graph().compile()


# ── Agent ─────────────────────────────────────────────────────────────────────

class ManagementApproachAgent(BaseAgent):
    agent_name = "management_approach_agent"

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        deal_id = input_data.get("deal_id", "")
        await self.emit_event("thinking", {"message": "Drafting management approach..."}, deal_id)

        initial_state: ManagementApproachState = {
            "deal_id": deal_id,
            "deal": {},
            "opportunity": {},
            "teaming_partners": input_data.get("teaming_partners", []),
            "key_personnel": input_data.get("key_personnel", []),
            "organizational_structure": {},
            "staffing_plan": {},
            "risk_management": "",
            "quality_management": "",
            "transition_plan": "",
            "management_approach_text": "",
            "org_chart_description": "",
            "messages": [],
        }

        result = await _graph.ainvoke(initial_state)

        await self.emit_event("output", {
            "message": "Management approach drafted",
            "sections": ["org_structure", "staffing_plan", "management_approach"],
        }, deal_id)

        return {
            "management_approach": result.get("management_approach_text", ""),
            "organizational_structure": result.get("organizational_structure", {}),
            "staffing_plan": result.get("staffing_plan", {}),
            "org_chart_description": result.get("org_chart_description", ""),
            "risk_management": result.get("risk_management", ""),
            "quality_management": result.get("quality_management", ""),
        }
