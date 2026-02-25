"""
Capture Agent — Generates capture plans for deals entering the capture stage.

Pulls from competitive intelligence, teaming analysis, and strategy
to create a comprehensive capture plan document.
"""

import logging
import os
from typing import Any

import httpx
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from typing_extensions import TypedDict

from src.agents.base import BaseAgent

logger = logging.getLogger("ai_orchestrator.agents.capture")

DJANGO_API_URL = os.getenv("DJANGO_API_URL", "http://django-api:8001")
DJANGO_SERVICE_TOKEN = os.getenv("DJANGO_SERVICE_TOKEN", "")


def _auth_headers() -> dict[str, str]:
    t = DJANGO_SERVICE_TOKEN
    return {"Authorization": f"Bearer {t}"} if t else {}


async def _get(path: str, default: Any = None) -> Any:
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{DJANGO_API_URL}{path}", headers=_auth_headers())
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.warning("API GET %s failed: %s", path, exc)
        return default


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


def _get_llm() -> ChatAnthropic:
    return ChatAnthropic(
        model="claude-sonnet-4-6",
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        max_tokens=4096,
    )


class CaptureState(TypedDict):
    deal_id: str
    deal: dict
    opportunity: dict
    company_profile: dict
    competitive_intel: dict
    strategy_assessment: dict
    capture_plan: dict
    messages: list


async def load_context(state: CaptureState) -> dict:
    """Load deal, opportunity, and related intelligence."""
    deal_id = state["deal_id"]
    deal = await _get(f"/api/deals/{deal_id}/", default={})
    opp_id = deal.get("opportunity", "")
    opp = await _get(f"/api/opportunities/{opp_id}/", default={}) if opp_id else {}
    profile = await _get("/api/opportunities/company-profile/primary/", default={})

    return {
        "deal": deal,
        "opportunity": opp,
        "company_profile": profile,
        "messages": [HumanMessage(content=f"Loaded capture context for: {deal.get('title', deal_id)}")],
    }


async def gather_intelligence(state: CaptureState) -> dict:
    """Gather competitive intelligence for capture planning."""
    opp = state.get("opportunity", {})
    agency = opp.get("agency", "")
    naics = opp.get("naics_code", "")

    intel = {"competitors": [], "market_context": "", "agency_insights": ""}

    # Try to gather competitive intelligence
    try:
        from src.mcp_servers.competitive_intel_tools import get_competitors_for_agency
        competitors = await get_competitors_for_agency(agency=agency, naics=naics)
        intel["competitors"] = competitors if isinstance(competitors, list) else []
    except Exception:
        logger.debug("Competitive intel tools not available, using LLM inference")

    return {
        "competitive_intel": intel,
        "messages": [HumanMessage(content="Gathered competitive intelligence")],
    }


async def generate_capture_plan(state: CaptureState) -> dict:
    """Generate the capture plan using LLM."""
    llm = _get_llm()

    try:
        resp = await llm.ainvoke([
            SystemMessage(content=(
                "You are a senior GovCon capture manager generating a capture plan. "
                "Create a comprehensive capture plan with the following sections:\n"
                "1. Win Strategy (2-3 paragraphs)\n"
                "2. Competitive Landscape (identify top 3-5 competitors, strengths/weaknesses)\n"
                "3. Teaming Strategy (potential partners and why)\n"
                "4. Pricing Approach (high-level pricing strategy)\n"
                "5. Technical Approach Summary (key solution elements)\n"
                "6. Key Differentiators (3-5 bullet points)\n"
                "7. Action Items (10 specific capture actions with owners)\n"
                "8. Risk Assessment (top 5 risks with mitigations)\n"
                "Be specific and actionable. Use government contracting terminology."
            )),
            HumanMessage(content=(
                f"Deal: {state.get('deal', {}).get('title', 'N/A')}\n\n"
                f"Opportunity:\n{_summarize_opp(state.get('opportunity', {}))}\n\n"
                f"Company Profile:\n{_summarize_profile(state.get('company_profile', {}))}\n\n"
                f"Competitive Intelligence:\n{state.get('competitive_intel', {})}\n\n"
                "Generate a comprehensive capture plan."
            )),
        ])
        content = resp.content
    except Exception as exc:
        logger.error("Capture plan generation failed: %s", exc)
        return {"capture_plan": {}, "messages": [HumanMessage(content="Capture plan generation failed")]}

    # Parse the structured response into fields
    plan = _parse_capture_plan(content)

    return {
        "capture_plan": plan,
        "messages": [HumanMessage(content="Capture plan generated")],
    }


async def persist_plan(state: CaptureState) -> dict:
    """Save the capture plan to Django via API."""
    deal_id = state["deal_id"]
    plan = state.get("capture_plan", {})

    if plan:
        await _patch(f"/api/deals/{deal_id}/capture-plan/", {
            "win_strategy": plan.get("win_strategy", ""),
            "competitive_landscape": plan.get("competitive_landscape", ""),
            "teaming_strategy": plan.get("teaming_strategy", ""),
            "pricing_approach": plan.get("pricing_approach", ""),
            "technical_approach_summary": plan.get("technical_approach_summary", ""),
            "key_differentiators": plan.get("key_differentiators", []),
            "action_items": plan.get("action_items", []),
            "risk_assessment": plan.get("risk_assessment", []),
            "is_ai_generated": True,
        })

    return {
        "messages": [HumanMessage(content="Capture plan persisted")],
    }


def _summarize_opp(opp: dict) -> str:
    return (
        f"Title: {opp.get('title', 'N/A')}\n"
        f"Agency: {opp.get('agency', 'N/A')}\n"
        f"NAICS: {opp.get('naics_code', 'N/A')}\n"
        f"Value: {opp.get('estimated_value', 'N/A')}\n"
        f"Set-Aside: {opp.get('set_aside', 'N/A')}\n"
        f"Description: {opp.get('description', 'N/A')[:500]}"
    )


def _summarize_profile(profile: dict) -> str:
    return (
        f"Company: {profile.get('name', 'N/A')}\n"
        f"NAICS: {profile.get('naics_codes', [])}\n"
        f"Competencies: {profile.get('core_competencies', [])}\n"
        f"Certifications: {profile.get('certifications', [])}"
    )


def _parse_capture_plan(content: str) -> dict:
    """Parse LLM output into structured capture plan fields."""
    plan = {
        "win_strategy": "",
        "competitive_landscape": "",
        "teaming_strategy": "",
        "pricing_approach": "",
        "technical_approach_summary": "",
        "key_differentiators": [],
        "action_items": [],
        "risk_assessment": [],
    }

    sections = content.split("\n\n")
    current_section = ""
    current_content = []

    section_map = {
        "win strategy": "win_strategy",
        "competitive landscape": "competitive_landscape",
        "teaming strategy": "teaming_strategy",
        "pricing approach": "pricing_approach",
        "technical approach": "technical_approach_summary",
    }

    for section in sections:
        section_lower = section.lower().strip()
        matched = False
        for key, field_name in section_map.items():
            if key in section_lower[:50]:
                current_section = field_name
                plan[current_section] = section
                matched = True
                break

        if not matched and current_section:
            plan[current_section] += "\n\n" + section

    # Extract bullet points for list fields
    for line in content.split("\n"):
        stripped = line.strip()
        if stripped.startswith(("-", "•", "*")) and len(stripped) > 5:
            item = stripped.lstrip("-•* ").strip()
            if "differentiator" in content[:content.index(line)].lower()[-200:] if line in content else False:
                plan["key_differentiators"].append(item)

    return plan


def build_capture_graph() -> StateGraph:
    wf = StateGraph(CaptureState)
    wf.add_node("load_context", load_context)
    wf.add_node("gather_intelligence", gather_intelligence)
    wf.add_node("generate_capture_plan", generate_capture_plan)
    wf.add_node("persist_plan", persist_plan)
    wf.set_entry_point("load_context")
    wf.add_edge("load_context", "gather_intelligence")
    wf.add_edge("gather_intelligence", "generate_capture_plan")
    wf.add_edge("generate_capture_plan", "persist_plan")
    wf.add_edge("persist_plan", END)
    return wf.compile()


capture_graph = build_capture_graph()


class CaptureAgent(BaseAgent):
    """AI agent that generates capture plans for deals."""

    agent_name = "capture_agent"

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        deal_id = input_data.get("deal_id", "")
        if not deal_id:
            return {"error": "deal_id is required"}

        initial: CaptureState = {
            "deal_id": deal_id,
            "deal": {},
            "opportunity": {},
            "company_profile": {},
            "competitive_intel": {},
            "strategy_assessment": {},
            "capture_plan": {},
            "messages": [],
        }
        try:
            await self.emit_event("thinking", {"message": f"Generating capture plan for deal {deal_id}"})
            result = await capture_graph.ainvoke(initial)
            await self.emit_event("output", {"status": "capture_plan_generated"})
            return {
                "deal_id": deal_id,
                "capture_plan": result.get("capture_plan", {}),
                "status": "generated",
            }
        except Exception as exc:
            logger.exception("CaptureAgent.run failed for deal %s", deal_id)
            await self.emit_event("error", {"error": str(exc)})
            return {"error": str(exc), "deal_id": deal_id}
