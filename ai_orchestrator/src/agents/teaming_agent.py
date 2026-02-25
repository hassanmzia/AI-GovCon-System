"""Teaming AI Agent using LangGraph."""
import logging
import os
from typing import Annotated, Any
import operator

import httpx
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from typing_extensions import TypedDict

from src.agents.base import BaseAgent

logger = logging.getLogger("ai_orchestrator.agents.teaming")

DJANGO_API_URL = os.getenv("DJANGO_API_URL", "http://django-api:8001")
DJANGO_SERVICE_TOKEN = os.getenv("DJANGO_SERVICE_TOKEN", "")


# ── State ─────────────────────────────────────────────────────────────────────

class TeamingState(TypedDict):
    deal_id: str
    deal: dict
    opportunity: dict
    existing_partners: list[dict]
    capability_gaps: list[str]
    partner_recommendations: list[dict]
    teaming_structure: str
    risk_assessment: str
    negotiation_priorities: list[str]
    messages: Annotated[list, operator.add]


# ── Django API helpers ────────────────────────────────────────────────────────

def _auth_headers() -> dict[str, str]:
    token = DJANGO_SERVICE_TOKEN
    return {"Authorization": f"Bearer {token}"} if token else {}


async def _fetch_deal(deal_id: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{DJANGO_API_URL}/api/deals/{deal_id}/",
                headers=_auth_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.warning("Could not fetch deal %s: %s", deal_id, exc)
        return {"id": deal_id, "title": "Unknown Deal"}


async def _fetch_existing_partners(deal_id: str) -> list:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{DJANGO_API_URL}/api/teaming/partnerships/?deal={deal_id}",
                headers=_auth_headers(),
            )
            resp.raise_for_status()
            return resp.json().get("results", [])
    except Exception as exc:
        logger.warning("Could not fetch partners for deal %s: %s", deal_id, exc)
        return []


async def _fetch_opportunity(opportunity_id: str) -> dict:
    if not opportunity_id:
        return {}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{DJANGO_API_URL}/api/opportunities/{opportunity_id}/",
                headers=_auth_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.warning("Could not fetch opportunity %s: %s", opportunity_id, exc)
        return {}


# ── LLM ───────────────────────────────────────────────────────────────────────

def _get_llm() -> ChatAnthropic:
    return ChatAnthropic(
        model="claude-sonnet-4-6",
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        max_tokens=2048,
    )


# ── Graph nodes ───────────────────────────────────────────────────────────────

async def load_teaming_context(state: TeamingState) -> dict:
    """Fetch deal, opportunity, and existing teaming partners."""
    logger.info("Loading teaming context for deal %s", state["deal_id"])
    deal = await _fetch_deal(state["deal_id"])
    opportunity_id = deal.get("opportunity") or deal.get("opportunity_id", "")
    opportunity, existing_partners = (
        await _fetch_opportunity(str(opportunity_id) if opportunity_id else ""),
        await _fetch_existing_partners(state["deal_id"]),
    )
    return {
        "deal": deal,
        "opportunity": opportunity,
        "existing_partners": existing_partners,
        "messages": [
            HumanMessage(content=f"Analyzing teaming strategy for: {deal.get('title', state['deal_id'])}")
        ],
    }


async def identify_capability_gaps(state: TeamingState) -> dict:
    """Claude identifies capability gaps that require teaming partners."""
    logger.info("Identifying capability gaps for deal %s", state["deal_id"])
    llm = _get_llm()

    system = SystemMessage(
        content=(
            "You are a capture manager and business development expert in U.S. government "
            "contracting. Analyse an opportunity against existing teaming partners to "
            "identify capability gaps that require additional partners or subcontractors."
        )
    )
    human = HumanMessage(
        content=(
            f"Deal: {state['deal']}\n\n"
            f"Opportunity Requirements: {state['opportunity']}\n\n"
            f"Existing Partners: {state['existing_partners']}\n\n"
            "Identify:\n"
            "1. Key technical capabilities required by this opportunity\n"
            "2. Capabilities already covered by existing partners\n"
            "3. Capability gaps that need to be filled\n"
            "4. Compliance/certification requirements (clearances, CMMC, etc.)\n"
            "Format gaps as a numbered list."
        )
    )

    try:
        response = await llm.ainvoke([system, human])
        content = response.content
    except Exception as exc:
        logger.error("LLM failed in identify_capability_gaps: %s", exc)
        content = "Capability gap analysis unavailable due to API error."

    gaps = [
        line.split(".", 1)[-1].strip()
        for line in content.split("\n")
        if line.strip() and line.strip()[0].isdigit() and "." in line
    ]
    if not gaps:
        gaps = [content.strip()]

    return {
        "capability_gaps": gaps,
        "messages": [HumanMessage(content=f"Identified {len(gaps)} capability gap(s).")],
    }


async def recommend_partners(state: TeamingState) -> dict:
    """Claude recommends teaming partner profiles to fill the identified gaps."""
    logger.info("Recommending teaming partners for deal %s", state["deal_id"])
    llm = _get_llm()

    system = SystemMessage(
        content=(
            "You are a teaming and partnership strategist in U.S. government contracting. "
            "Recommend ideal partner profiles for each capability gap, considering small "
            "business requirements, past performance, and strategic fit."
        )
    )
    human = HumanMessage(
        content=(
            f"Deal: {state['deal']}\n\n"
            f"Capability Gaps:\n{state['capability_gaps']}\n\n"
            f"Opportunity: {state['opportunity']}\n\n"
            "For each capability gap provide:\n"
            "1. Ideal partner profile (company type, size, certifications)\n"
            "2. Key qualifications to look for\n"
            "3. Suggested relationship type (subcontractor / joint venture / consultant)\n"
            "4. Estimated workshare percentage\n"
            "Format as numbered recommendations."
        )
    )

    try:
        response = await llm.ainvoke([system, human])
        content = response.content
    except Exception as exc:
        logger.error("LLM failed in recommend_partners: %s", exc)
        content = "Partner recommendations unavailable due to API error."

    recommendations = [{"analysis": content}]

    return {
        "partner_recommendations": recommendations,
        "messages": [HumanMessage(content="Partner recommendations generated.")],
    }


async def design_teaming_structure(state: TeamingState) -> dict:
    """Claude designs the optimal teaming structure and risk assessment."""
    logger.info("Designing teaming structure for deal %s", state["deal_id"])
    llm = _get_llm()

    system = SystemMessage(
        content=(
            "You are a chief capture officer specialising in complex government contract "
            "team formation. Design the optimal teaming structure and identify key risks."
        )
    )
    human = HumanMessage(
        content=(
            f"Deal: {state['deal']}\n\n"
            f"Existing Partners: {state['existing_partners']}\n\n"
            f"Partner Recommendations:\n{state['partner_recommendations']}\n\n"
            "Provide:\n"
            "1. Recommended teaming structure (prime + subs / JV / etc.)\n"
            "2. Workshare allocation strategy\n"
            "3. Key risks in the teaming arrangement\n"
            "4. Top 3 negotiation priorities for teaming agreements\n"
            "5. Small business compliance strategy\n"
        )
    )

    try:
        response = await llm.ainvoke([system, human])
        content = response.content
    except Exception as exc:
        logger.error("LLM failed in design_teaming_structure: %s", exc)
        content = "Teaming structure design unavailable due to API error."

    # Extract negotiation priorities
    priorities = [
        line.strip("- •").strip()
        for line in content.split("\n")
        if line.strip().startswith(("-", "•", "4.")) or "negotiat" in line.lower()
    ][:5]

    return {
        "teaming_structure": content,
        "risk_assessment": content,
        "negotiation_priorities": priorities,
        "messages": [HumanMessage(content="Teaming structure designed.")],
    }


# ── Graph builder ─────────────────────────────────────────────────────────────

def build_teaming_graph() -> StateGraph:
    """Construct and compile the teaming LangGraph workflow."""
    workflow = StateGraph(TeamingState)

    workflow.add_node("load_teaming_context", load_teaming_context)
    workflow.add_node("identify_capability_gaps", identify_capability_gaps)
    workflow.add_node("recommend_partners", recommend_partners)
    workflow.add_node("design_teaming_structure", design_teaming_structure)

    workflow.set_entry_point("load_teaming_context")
    workflow.add_edge("load_teaming_context", "identify_capability_gaps")
    workflow.add_edge("identify_capability_gaps", "recommend_partners")
    workflow.add_edge("recommend_partners", "design_teaming_structure")
    workflow.add_edge("design_teaming_structure", END)

    return workflow.compile()


teaming_graph = build_teaming_graph()


# ── Agent class ───────────────────────────────────────────────────────────────

class TeamingAgent(BaseAgent):
    """LangGraph-based Teaming AI Agent."""

    agent_name = "teaming_agent"

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Run teaming analysis for a deal.

        Args:
            input_data: Must contain 'deal_id'.

        Returns:
            dict with keys: deal_id, capability_gaps, partner_recommendations,
            teaming_structure, risk_assessment, negotiation_priorities.
        """
        deal_id = input_data.get("deal_id", "")
        if not deal_id:
            return {"error": "deal_id is required"}

        initial_state: TeamingState = {
            "deal_id": deal_id,
            "deal": {},
            "opportunity": {},
            "existing_partners": [],
            "capability_gaps": [],
            "partner_recommendations": [],
            "teaming_structure": "",
            "risk_assessment": "",
            "negotiation_priorities": [],
            "messages": [],
        }

        try:
            await self.emit_event(
                "thinking",
                {"message": f"Starting teaming analysis for deal {deal_id}"},
                execution_id=deal_id,
            )
            final_state = await teaming_graph.ainvoke(initial_state)
            await self.emit_event(
                "output",
                {"gaps_found": len(final_state["capability_gaps"])},
                execution_id=deal_id,
            )
            return {
                "deal_id": final_state["deal_id"],
                "capability_gaps": final_state["capability_gaps"],
                "partner_recommendations": final_state["partner_recommendations"],
                "teaming_structure": final_state["teaming_structure"],
                "risk_assessment": final_state["risk_assessment"],
                "negotiation_priorities": final_state["negotiation_priorities"],
            }
        except Exception as exc:
            logger.exception("TeamingAgent.run failed for deal %s", deal_id)
            await self.emit_event("error", {"error": str(exc)}, execution_id=deal_id)
            return {"error": str(exc), "deal_id": deal_id}
