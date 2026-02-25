"""Marketing & Sales Expert Agent using LangGraph."""
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

logger = logging.getLogger("ai_orchestrator.agents.marketing")

DJANGO_API_URL = os.getenv("DJANGO_API_URL", "http://django-api:8001")
DJANGO_SERVICE_TOKEN = os.getenv("DJANGO_SERVICE_TOKEN", "")


# ── State ─────────────────────────────────────────────────────────────────────

class MarketingState(TypedDict):
    deal_id: str
    opportunity: dict
    rfp_requirements: list
    company_strategy: dict
    competitors: list
    value_proposition: str
    win_themes: list[str]
    discriminators: list[str]
    ghost_strategies: list[str]
    executive_summary_draft: str
    pwin_assessment: float
    messages: Annotated[list, operator.add]


# ── LLM ───────────────────────────────────────────────────────────────────────

def _get_llm() -> ChatAnthropic:
    return ChatAnthropic(
        model="claude-sonnet-4-6",
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        max_tokens=3000,
    )


# ── Django API helpers ────────────────────────────────────────────────────────

def _auth_headers() -> dict[str, str]:
    token = DJANGO_SERVICE_TOKEN
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


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


async def _fetch_opportunity_for_deal(deal: dict) -> dict:
    opportunity_id = deal.get("opportunity") or deal.get("opportunity_id")
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


async def _fetch_company_strategy() -> dict:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{DJANGO_API_URL}/api/strategy/current/",
                headers=_auth_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.warning("Could not fetch company strategy: %s", exc)
        return {
            "focus_areas": ["technology modernization", "cybersecurity", "cloud migration"],
            "differentiators": ["proven past performance", "cleared workforce", "agile delivery"],
        }


# ── Graph nodes ───────────────────────────────────────────────────────────────

async def load_deal_context(state: MarketingState) -> dict:
    """Fetch deal, opportunity, and RFP from Django API."""
    logger.info("Loading deal context for deal %s", state["deal_id"])

    deal = await _fetch_deal(state["deal_id"])
    opportunity = await _fetch_opportunity_for_deal(deal)
    company_strategy = await _fetch_company_strategy()

    # Extract RFP requirements from opportunity or deal
    rfp_requirements = (
        opportunity.get("requirements", [])
        or deal.get("rfp_requirements", [])
        or []
    )

    return {
        "opportunity": opportunity or deal,
        "rfp_requirements": rfp_requirements,
        "company_strategy": company_strategy,
        "messages": [
            HumanMessage(content=f"Loaded context for deal: {deal.get('title', state['deal_id'])}")
        ],
    }


async def analyze_competitive_landscape(state: MarketingState) -> dict:
    """Claude profiles likely competitors."""
    logger.info("Analyzing competitive landscape for deal %s", state["deal_id"])
    llm = _get_llm()

    system = SystemMessage(
        content=(
            "You are a competitive intelligence analyst specializing in government contracting. "
            "Profile likely competitors for a government contract opportunity. "
            "Analyze their strengths, weaknesses, likely strategies, and win probability."
        )
    )
    human = HumanMessage(
        content=(
            f"Deal ID: {state['deal_id']}\n"
            f"Opportunity:\n{state['opportunity']}\n\n"
            f"RFP Requirements:\n{state['rfp_requirements'][:10]}\n\n"
            "Identify and profile 3-5 likely competitors. For each provide:\n"
            "- company_name: Company name\n"
            "- strengths: Key competitive strengths\n"
            "- weaknesses: Known weaknesses or gaps\n"
            "- likely_strategy: Their probable approach to this bid\n"
            "- threat_level: low|medium|high\n"
        )
    )

    try:
        response = await llm.ainvoke([system, human])
        content = response.content
    except Exception as exc:
        logger.error("LLM call failed in analyze_competitive_landscape: %s", exc)
        content = "Competitive analysis unavailable due to API error."

    # Parse competitor profiles
    competitors = []
    current_competitor: dict[str, str] = {}
    for line in content.split("\n"):
        line = line.strip()
        if not line:
            if current_competitor:
                competitors.append(current_competitor)
                current_competitor = {}
            continue
        for field in ("company_name", "strengths", "weaknesses", "likely_strategy", "threat_level"):
            if line.lower().startswith(f"{field}:"):
                current_competitor[field] = line.split(":", 1)[-1].strip()
                break
    if current_competitor:
        competitors.append(current_competitor)

    if not competitors:
        competitors = [{"company_name": "Major Competitors", "strengths": content[:300], "threat_level": "medium"}]

    return {
        "competitors": competitors,
        "messages": [HumanMessage(content=f"Competitive landscape analysis: {len(competitors)} competitors profiled.")],
    }


async def craft_value_proposition(state: MarketingState) -> dict:
    """Claude creates a compelling value proposition."""
    logger.info("Crafting value proposition for deal %s", state["deal_id"])
    llm = _get_llm()

    competitors_text = "\n".join(
        f"- {c.get('company_name', 'Unknown')}: {c.get('strengths', '')}"
        for c in state.get("competitors", [])
    )

    system = SystemMessage(
        content=(
            "You are a capture manager and proposal expert for a government contracting firm. "
            "Craft compelling value propositions that differentiate the company, "
            "address customer needs, and are hard for competitors to match."
        )
    )
    human = HumanMessage(
        content=(
            f"Opportunity:\n{state['opportunity']}\n\n"
            f"Company Strategy & Differentiators:\n{state['company_strategy']}\n\n"
            f"Key Competitors:\n{competitors_text or 'Not yet identified'}\n\n"
            f"RFP Requirements:\n{state['rfp_requirements'][:5]}\n\n"
            "Craft a compelling value proposition (2-3 paragraphs) that:\n"
            "1. Directly addresses the customer's mission needs\n"
            "2. Highlights unique company differentiators\n"
            "3. Creates clear separation from competitors\n"
            "4. Is specific and quantified where possible\n"
        )
    )

    try:
        response = await llm.ainvoke([system, human])
        value_proposition = response.content
    except Exception as exc:
        logger.error("LLM call failed in craft_value_proposition: %s", exc)
        value_proposition = "Value proposition generation unavailable due to API error."

    # Extract discriminators from value proposition
    discriminators = []
    for line in value_proposition.split("\n"):
        line = line.strip()
        if line.startswith("-") or (line and line[0].isdigit() and "." in line):
            discriminator = line.lstrip("-").split(".", 1)[-1].strip()
            if discriminator and len(discriminator) > 10:
                discriminators.append(discriminator)
                if len(discriminators) >= 5:
                    break

    if not discriminators:
        discriminators = ["Proven past performance", "Mission-focused team", "Agile delivery approach"]

    return {
        "value_proposition": value_proposition,
        "discriminators": discriminators,
        "messages": [HumanMessage(content="Value proposition crafted.")],
    }


async def generate_win_themes(state: MarketingState) -> dict:
    """Claude generates 3-5 win themes tied to evaluation criteria."""
    logger.info("Generating win themes for deal %s", state["deal_id"])
    llm = _get_llm()

    system = SystemMessage(
        content=(
            "You are a proposal expert specializing in winning government contracts. "
            "Generate customer-focused win themes that directly tie to evaluation criteria, "
            "resonate with the Source Selection Authority, and differentiate from competitors."
        )
    )
    human = HumanMessage(
        content=(
            f"Opportunity:\n{state['opportunity']}\n\n"
            f"Value Proposition:\n{state['value_proposition']}\n\n"
            f"Key Discriminators: {', '.join(state['discriminators'][:5])}\n\n"
            f"Competitors:\n{[c.get('company_name') for c in state['competitors'][:3]]}\n\n"
            "Generate 3-5 compelling win themes. Each theme should:\n"
            "1. Be tied to a specific evaluation criterion\n"
            "2. Be customer-benefit focused (not company-capability focused)\n"
            "3. Be provable and supportable in the proposal\n"
            "4. Be difficult for competitors to match\n\n"
            "Format as a numbered list. Each theme is one clear, compelling sentence."
        )
    )

    try:
        response = await llm.ainvoke([system, human])
        content = response.content
    except Exception as exc:
        logger.error("LLM call failed in generate_win_themes: %s", exc)
        content = "1. Win theme generation unavailable due to API error."

    # Parse win themes
    win_themes = []
    for line in content.split("\n"):
        line = line.strip()
        if line and line[0].isdigit() and "." in line:
            theme = line.split(".", 1)[-1].strip()
            if theme:
                win_themes.append(theme)

    if not win_themes:
        win_themes = [content.strip()]

    # Generate ghost strategies (strategies to weaken competitors)
    ghost_strategies = [
        f"Emphasize continuous monitoring and support that {c.get('company_name', 'competitors')} typically lack"
        for c in state.get("competitors", [])[:3]
    ]
    if not ghost_strategies:
        ghost_strategies = ["Emphasize proven track record with similar agencies", "Highlight cleared workforce availability"]

    return {
        "win_themes": win_themes,
        "ghost_strategies": ghost_strategies,
        "messages": [HumanMessage(content=f"Generated {len(win_themes)} win themes.")],
    }


async def craft_executive_summary(state: MarketingState) -> dict:
    """Claude writes a draft executive summary."""
    logger.info("Crafting executive summary for deal %s", state["deal_id"])
    llm = _get_llm()

    win_themes_text = "\n".join(f"{i+1}. {t}" for i, t in enumerate(state.get("win_themes", [])))
    discriminators_text = "\n".join(f"- {d}" for d in state.get("discriminators", []))

    system = SystemMessage(
        content=(
            "You are a senior proposal writer specializing in government contract executive summaries. "
            "Write compelling, customer-focused executive summaries that win contracts. "
            "The executive summary should make the Source Selection Authority want to select your company."
        )
    )
    human = HumanMessage(
        content=(
            f"Opportunity:\n{state['opportunity']}\n\n"
            f"Win Themes:\n{win_themes_text}\n\n"
            f"Key Discriminators:\n{discriminators_text}\n\n"
            f"Value Proposition:\n{state['value_proposition'][:1000]}\n\n"
            "Write a 3-4 paragraph draft executive summary that:\n"
            "1. Opens with the customer's mission need and your solution\n"
            "2. Presents your win themes compellingly\n"
            "3. Highlights key differentiators and past performance\n"
            "4. Closes with a strong value statement\n\n"
            "Write in second person ('you/your mission') to center the customer."
        )
    )

    try:
        response = await llm.ainvoke([system, human])
        executive_summary = response.content
    except Exception as exc:
        logger.error("LLM call failed in craft_executive_summary: %s", exc)
        executive_summary = "Executive summary generation unavailable due to API error."

    # Calculate pWin assessment based on strategic score and competitive landscape
    num_competitors = len(state.get("competitors", []))
    high_threat_count = sum(
        1 for c in state.get("competitors", [])
        if c.get("threat_level", "").lower() == "high"
    )
    base_pwin = 1.0 / max(num_competitors + 1, 2)
    pwin_adjustment = max(0.0, 0.1 - (high_threat_count * 0.05))
    pwin_assessment = round(min(0.95, base_pwin + pwin_adjustment + 0.2), 2)  # 0.2 company confidence

    return {
        "executive_summary_draft": executive_summary,
        "pwin_assessment": pwin_assessment,
        "messages": [HumanMessage(content=f"Executive summary drafted. pWin estimate: {pwin_assessment:.0%}")],
    }


# ── Graph builder ─────────────────────────────────────────────────────────────

def build_marketing_graph() -> StateGraph:
    """Construct and compile the marketing LangGraph workflow."""
    workflow = StateGraph(MarketingState)

    workflow.add_node("load_deal_context", load_deal_context)
    workflow.add_node("analyze_competitive_landscape", analyze_competitive_landscape)
    workflow.add_node("craft_value_proposition", craft_value_proposition)
    workflow.add_node("generate_win_themes", generate_win_themes)
    workflow.add_node("craft_executive_summary", craft_executive_summary)

    workflow.set_entry_point("load_deal_context")
    workflow.add_edge("load_deal_context", "analyze_competitive_landscape")
    workflow.add_edge("analyze_competitive_landscape", "craft_value_proposition")
    workflow.add_edge("craft_value_proposition", "generate_win_themes")
    workflow.add_edge("generate_win_themes", "craft_executive_summary")
    workflow.add_edge("craft_executive_summary", END)

    return workflow.compile()


# Compiled graph instance
marketing_graph = build_marketing_graph()


# ── Agent class ───────────────────────────────────────────────────────────────

class MarketingAgent(BaseAgent):
    """LangGraph-based Marketing & Sales Expert Agent."""

    agent_name = "marketing_agent"

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Run marketing/capture strategy for a deal.

        Args:
            input_data: Must contain 'deal_id'. Optional context keys are merged.

        Returns:
            dict with keys: deal_id, value_proposition, win_themes, discriminators,
            ghost_strategies, executive_summary_draft, pwin_assessment, competitors.
        """
        deal_id = input_data.get("deal_id", "")
        if not deal_id:
            return {"error": "deal_id is required"}

        initial_state: MarketingState = {
            "deal_id": deal_id,
            "opportunity": {},
            "rfp_requirements": [],
            "company_strategy": {},
            "competitors": [],
            "value_proposition": "",
            "win_themes": [],
            "discriminators": [],
            "ghost_strategies": [],
            "executive_summary_draft": "",
            "pwin_assessment": 0.0,
            "messages": [],
        }

        try:
            await self.emit_event(
                "thinking",
                {"message": f"Starting marketing analysis for deal {deal_id}"},
                execution_id=deal_id,
            )
            final_state = await marketing_graph.ainvoke(initial_state)
            await self.emit_event(
                "output",
                {"pwin": final_state["pwin_assessment"]},
                execution_id=deal_id,
            )
            return {
                "deal_id": final_state["deal_id"],
                "value_proposition": final_state["value_proposition"],
                "win_themes": final_state["win_themes"],
                "discriminators": final_state["discriminators"],
                "ghost_strategies": final_state["ghost_strategies"],
                "executive_summary_draft": final_state["executive_summary_draft"],
                "pwin_assessment": final_state["pwin_assessment"],
                "competitors": final_state["competitors"],
            }
        except Exception as exc:
            logger.exception("MarketingAgent.run failed for deal %s", deal_id)
            await self.emit_event("error", {"error": str(exc)}, execution_id=deal_id)
            return {"error": str(exc), "deal_id": deal_id}
