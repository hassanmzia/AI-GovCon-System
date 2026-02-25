"""Company AI Strategy Agent using LangGraph."""
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

logger = logging.getLogger("ai_orchestrator.agents.strategy")

DJANGO_API_URL = os.getenv("DJANGO_API_URL", "http://django-api:8001")
DJANGO_SERVICE_TOKEN = os.getenv("DJANGO_SERVICE_TOKEN", "")


# ── State ─────────────────────────────────────────────────────────────────────

class StrategyState(TypedDict):
    opportunity_id: str
    opportunity: dict
    company_strategy: dict
    active_portfolio: list
    strategic_score: float
    bid_recommendation: str  # "BID" | "NO_BID" | "CONDITIONAL_BID"
    strategic_rationale: str
    win_themes: list[str]
    portfolio_impact: str
    resource_impact: str
    messages: Annotated[list, operator.add]


# ── Django API helpers ────────────────────────────────────────────────────────

def _auth_headers() -> dict[str, str]:
    token = DJANGO_SERVICE_TOKEN
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


async def _fetch_opportunity(opportunity_id: str) -> dict:
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
        return {"id": opportunity_id, "title": "Unknown Opportunity", "description": ""}


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
            "target_agencies": [],
            "revenue_goals": {},
        }


async def _fetch_active_portfolio() -> list:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{DJANGO_API_URL}/api/deals/?status=active",
                headers=_auth_headers(),
            )
            resp.raise_for_status()
            return resp.json().get("results", [])
    except Exception as exc:
        logger.warning("Could not fetch active portfolio: %s", exc)
        return []


# ── LLM ───────────────────────────────────────────────────────────────────────

def _get_llm() -> ChatAnthropic:
    return ChatAnthropic(
        model="claude-sonnet-4-6",
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        max_tokens=2048,
    )


# ── Graph nodes ───────────────────────────────────────────────────────────────

async def load_context(state: StrategyState) -> dict:
    """Fetch opportunity, strategy, and portfolio from Django API."""
    logger.info("Loading context for opportunity %s", state["opportunity_id"])
    opportunity = await _fetch_opportunity(state["opportunity_id"])
    company_strategy = await _fetch_company_strategy()
    active_portfolio = await _fetch_active_portfolio()
    return {
        "opportunity": opportunity,
        "company_strategy": company_strategy,
        "active_portfolio": active_portfolio,
        "messages": [
            HumanMessage(content=f"Analyzing opportunity: {opportunity.get('title', state['opportunity_id'])}")
        ],
    }


async def assess_alignment(state: StrategyState) -> dict:
    """Use Claude to assess strategic alignment of the opportunity."""
    logger.info("Assessing strategic alignment")
    llm = _get_llm()

    system = SystemMessage(
        content=(
            "You are a senior business strategy consultant specializing in government contracting. "
            "Evaluate how well a given opportunity aligns with the company's strategic direction. "
            "Return a concise assessment including a strategic score from 0.0 to 1.0."
        )
    )
    human = HumanMessage(
        content=(
            f"Opportunity:\n{state['opportunity']}\n\n"
            f"Company Strategy:\n{state['company_strategy']}\n\n"
            "Assess the strategic alignment. Provide:\n"
            "1. Strategic score (0.0-1.0)\n"
            "2. Key alignment factors\n"
            "3. Any misalignment concerns\n"
        )
    )

    try:
        response = await llm.ainvoke([system, human])
        content = response.content
    except Exception as exc:
        logger.error("LLM call failed in assess_alignment: %s", exc)
        content = "Strategic alignment assessment unavailable due to API error."

    # Parse a rough score from the response text
    score = 0.7  # default
    for token in content.split():
        try:
            val = float(token.strip(",.()"))
            if 0.0 <= val <= 1.0:
                score = val
                break
        except ValueError:
            pass

    return {
        "strategic_score": score,
        "messages": [HumanMessage(content=f"Alignment assessment complete. Score: {score}")],
    }


async def analyze_portfolio_impact(state: StrategyState) -> dict:
    """Claude analyzes how this opportunity affects the current portfolio balance."""
    logger.info("Analyzing portfolio impact")
    llm = _get_llm()

    portfolio_summary = [
        {"title": d.get("title", ""), "value": d.get("value", 0)}
        for d in state["active_portfolio"][:10]  # Limit to top 10 for context
    ]

    system = SystemMessage(
        content=(
            "You are a portfolio management expert for a government contracting firm. "
            "Analyze how adding a new opportunity affects the company's portfolio balance, "
            "resource utilization, and risk profile."
        )
    )
    human = HumanMessage(
        content=(
            f"New Opportunity:\n{state['opportunity']}\n\n"
            f"Active Portfolio ({len(state['active_portfolio'])} contracts):\n{portfolio_summary}\n\n"
            "Provide:\n"
            "1. Portfolio balance impact (diversification, concentration risk)\n"
            "2. Resource impact assessment\n"
            "3. Overall recommendation for portfolio fit\n"
        )
    )

    try:
        response = await llm.ainvoke([system, human])
        content = response.content
    except Exception as exc:
        logger.error("LLM call failed in analyze_portfolio_impact: %s", exc)
        content = "Portfolio impact analysis unavailable due to API error."

    # Split the response into portfolio_impact and resource_impact sections
    lines = content.split("\n")
    resource_lines = []
    portfolio_lines = []
    in_resource_section = False
    for line in lines:
        lower = line.lower()
        if "resource" in lower:
            in_resource_section = True
        if in_resource_section:
            resource_lines.append(line)
        else:
            portfolio_lines.append(line)

    return {
        "portfolio_impact": "\n".join(portfolio_lines) if portfolio_lines else content,
        "resource_impact": "\n".join(resource_lines) if resource_lines else "See portfolio impact section.",
        "messages": [HumanMessage(content="Portfolio impact analysis complete.")],
    }


async def generate_recommendation(state: StrategyState) -> dict:
    """Claude generates BID/NO_BID/CONDITIONAL_BID with rationale."""
    logger.info("Generating bid recommendation")
    llm = _get_llm()

    system = SystemMessage(
        content=(
            "You are a capture manager and chief strategy officer for a government contracting firm. "
            "Based on strategic analysis, make a clear bid/no-bid recommendation. "
            "Your recommendation must be exactly one of: BID, NO_BID, or CONDITIONAL_BID."
        )
    )
    human = HumanMessage(
        content=(
            f"Opportunity:\n{state['opportunity']}\n\n"
            f"Strategic Score: {state['strategic_score']}\n"
            f"Portfolio Impact:\n{state['portfolio_impact']}\n"
            f"Resource Impact:\n{state['resource_impact']}\n\n"
            "Provide:\n"
            "1. Recommendation (BID / NO_BID / CONDITIONAL_BID) - state this clearly on the first line\n"
            "2. Strategic rationale (3-5 sentences)\n"
            "3. Key conditions (if CONDITIONAL_BID)\n"
        )
    )

    try:
        response = await llm.ainvoke([system, human])
        content = response.content
    except Exception as exc:
        logger.error("LLM call failed in generate_recommendation: %s", exc)
        content = "BID\nRecommendation unavailable due to API error."

    # Extract recommendation from first line
    first_line = content.split("\n")[0].upper()
    recommendation = "BID"
    for option in ("NO_BID", "CONDITIONAL_BID", "BID"):
        if option in first_line:
            recommendation = option
            break

    return {
        "bid_recommendation": recommendation,
        "strategic_rationale": content,
        "messages": [HumanMessage(content=f"Recommendation: {recommendation}")],
    }


async def generate_win_themes(state: StrategyState) -> dict:
    """Claude generates 3-5 deal-specific win themes."""
    logger.info("Generating win themes")
    llm = _get_llm()

    system = SystemMessage(
        content=(
            "You are a proposal expert and capture manager specializing in government contracts. "
            "Generate compelling, customer-centric win themes that differentiate the company "
            "and directly address evaluation criteria."
        )
    )
    human = HumanMessage(
        content=(
            f"Opportunity:\n{state['opportunity']}\n\n"
            f"Company Strategy:\n{state['company_strategy']}\n\n"
            f"Bid Recommendation: {state['bid_recommendation']}\n"
            f"Strategic Rationale:\n{state['strategic_rationale']}\n\n"
            "Generate 3-5 specific, compelling win themes for this opportunity. "
            "Each win theme should be one concise sentence. "
            "Format as a numbered list."
        )
    )

    try:
        response = await llm.ainvoke([system, human])
        content = response.content
    except Exception as exc:
        logger.error("LLM call failed in generate_win_themes: %s", exc)
        content = "1. Win theme generation unavailable due to API error."

    # Parse numbered list into individual themes
    win_themes = []
    for line in content.split("\n"):
        line = line.strip()
        if line and line[0].isdigit() and "." in line:
            theme = line.split(".", 1)[-1].strip()
            if theme:
                win_themes.append(theme)

    if not win_themes:
        win_themes = [content.strip()]

    return {
        "win_themes": win_themes,
        "messages": [HumanMessage(content=f"Generated {len(win_themes)} win themes.")],
    }


# ── Graph builder ─────────────────────────────────────────────────────────────

def build_strategy_graph() -> StateGraph:
    """Construct and compile the strategy LangGraph workflow."""
    workflow = StateGraph(StrategyState)

    workflow.add_node("load_context", load_context)
    workflow.add_node("assess_alignment", assess_alignment)
    workflow.add_node("analyze_portfolio_impact", analyze_portfolio_impact)
    workflow.add_node("generate_recommendation", generate_recommendation)
    workflow.add_node("generate_win_themes", generate_win_themes)

    workflow.set_entry_point("load_context")
    workflow.add_edge("load_context", "assess_alignment")
    workflow.add_edge("assess_alignment", "analyze_portfolio_impact")
    workflow.add_edge("analyze_portfolio_impact", "generate_recommendation")
    workflow.add_edge("generate_recommendation", "generate_win_themes")
    workflow.add_edge("generate_win_themes", END)

    return workflow.compile()


# Compiled graph instance (exported for src/graphs/strategy_graph.py)
strategy_graph = build_strategy_graph()


# ── Agent class ───────────────────────────────────────────────────────────────

class StrategyAgent(BaseAgent):
    """LangGraph-based Company AI Strategy Agent."""

    agent_name = "strategy_agent"

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Run strategy analysis for an opportunity.

        Args:
            input_data: Must contain 'opportunity_id'. Optional context keys are merged.

        Returns:
            dict with keys: opportunity_id, bid_recommendation, strategic_score,
            strategic_rationale, win_themes, portfolio_impact, resource_impact.
        """
        opportunity_id = input_data.get("opportunity_id", "")
        if not opportunity_id:
            return {"error": "opportunity_id is required"}

        initial_state: StrategyState = {
            "opportunity_id": opportunity_id,
            "opportunity": {},
            "company_strategy": {},
            "active_portfolio": [],
            "strategic_score": 0.0,
            "bid_recommendation": "",
            "strategic_rationale": "",
            "win_themes": [],
            "portfolio_impact": "",
            "resource_impact": "",
            "messages": [],
        }

        try:
            await self.emit_event(
                "thinking",
                {"message": f"Starting strategy analysis for opportunity {opportunity_id}"},
                execution_id=opportunity_id,
            )
            final_state = await strategy_graph.ainvoke(initial_state)
            await self.emit_event(
                "output",
                {"recommendation": final_state["bid_recommendation"]},
                execution_id=opportunity_id,
            )
            return {
                "opportunity_id": final_state["opportunity_id"],
                "bid_recommendation": final_state["bid_recommendation"],
                "strategic_score": final_state["strategic_score"],
                "strategic_rationale": final_state["strategic_rationale"],
                "win_themes": final_state["win_themes"],
                "portfolio_impact": final_state["portfolio_impact"],
                "resource_impact": final_state["resource_impact"],
            }
        except Exception as exc:
            logger.exception("StrategyAgent.run failed for opportunity %s", opportunity_id)
            await self.emit_event("error", {"error": str(exc)}, execution_id=opportunity_id)
            return {"error": str(exc), "opportunity_id": opportunity_id}
