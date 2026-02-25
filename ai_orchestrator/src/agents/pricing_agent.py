"""Pricing AI Agent using LangGraph."""
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

logger = logging.getLogger("ai_orchestrator.agents.pricing")

DJANGO_API_URL = os.getenv("DJANGO_API_URL", "http://django-api:8001")
DJANGO_SERVICE_TOKEN = os.getenv("DJANGO_SERVICE_TOKEN", "")


# ── State ─────────────────────────────────────────────────────────────────────

class PricingState(TypedDict):
    deal_id: str
    deal: dict
    cost_model: dict
    market_intelligence: list
    price_to_win_estimate: dict
    scenarios: list[dict]
    recommended_scenario: dict
    pricing_strategy: str
    risk_factors: list[str]
    negotiation_guidance: str
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


async def _fetch_cost_model(deal_id: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{DJANGO_API_URL}/api/pricing/cost-models/?deal={deal_id}&ordering=-version&limit=1",
                headers=_auth_headers(),
            )
            resp.raise_for_status()
            results = resp.json().get("results", [])
            return results[0] if results else {}
    except Exception as exc:
        logger.warning("Could not fetch cost model for deal %s: %s", deal_id, exc)
        return {}


async def _fetch_market_intelligence() -> list:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{DJANGO_API_URL}/api/pricing/pricing-intelligence/?ordering=-data_date&limit=20",
                headers=_auth_headers(),
            )
            resp.raise_for_status()
            return resp.json().get("results", [])
    except Exception as exc:
        logger.warning("Could not fetch market intelligence: %s", exc)
        return []


# ── LLM ───────────────────────────────────────────────────────────────────────

def _get_llm() -> ChatAnthropic:
    return ChatAnthropic(
        model="claude-sonnet-4-6",
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        max_tokens=2048,
    )


# ── Graph nodes ───────────────────────────────────────────────────────────────

async def load_pricing_context(state: PricingState) -> dict:
    """Fetch deal, cost model, and market intelligence."""
    logger.info("Loading pricing context for deal %s", state["deal_id"])
    deal, cost_model, market_intelligence = (
        await _fetch_deal(state["deal_id"]),
        await _fetch_cost_model(state["deal_id"]),
        await _fetch_market_intelligence(),
    )
    return {
        "deal": deal,
        "cost_model": cost_model,
        "market_intelligence": market_intelligence,
        "messages": [HumanMessage(content=f"Analyzing pricing for deal: {deal.get('title', state['deal_id'])}")],
    }


async def analyze_price_to_win(state: PricingState) -> dict:
    """Claude analyzes competitor pricing and recommends a price-to-win."""
    logger.info("Analyzing price-to-win for deal %s", state["deal_id"])
    llm = _get_llm()

    system = SystemMessage(
        content=(
            "You are a pricing analyst and capture manager expert specializing in U.S. "
            "government contracting. Your goal is to recommend a price-to-win (PTW) "
            "that maximises the expected value (price × win probability). "
            "Be specific about competitor price ranges and your win probability estimate."
        )
    )
    human = HumanMessage(
        content=(
            f"Deal: {state['deal']}\n\n"
            f"Cost Model: {state['cost_model']}\n\n"
            f"Market Intelligence: {state['market_intelligence']}\n\n"
            "Provide:\n"
            "1. Recommended price-to-win with justification\n"
            "2. Estimated competitor price range (low / median / high)\n"
            "3. Win probability at recommended price (0.0–1.0)\n"
            "4. Key pricing risks\n"
        )
    )

    try:
        response = await llm.ainvoke([system, human])
        content = response.content
    except Exception as exc:
        logger.error("LLM failed in analyze_price_to_win: %s", exc)
        content = "Price-to-win analysis unavailable due to API error."

    # Extract a simple win-probability from the response
    win_prob = 0.5
    for token in content.split():
        try:
            val = float(token.strip(",.()%"))
            if token.endswith("%"):
                val /= 100
            if 0.0 < val <= 1.0:
                win_prob = val
                break
        except ValueError:
            pass

    return {
        "price_to_win_estimate": {
            "analysis": content,
            "win_probability": win_prob,
        },
        "messages": [HumanMessage(content=f"PTW analysis complete. Win prob: {win_prob:.1%}")],
    }


async def generate_pricing_scenarios(state: PricingState) -> dict:
    """Claude generates and compares pricing scenarios across strategy types."""
    logger.info("Generating pricing scenarios for deal %s", state["deal_id"])
    llm = _get_llm()

    system = SystemMessage(
        content=(
            "You are a senior pricing strategist for a government contracting firm. "
            "Generate and compare pricing scenarios across different strategies. "
            "For each scenario provide a clear total price, margin, and win probability."
        )
    )
    human = HumanMessage(
        content=(
            f"Deal: {state['deal']}\n\n"
            f"Cost Model: {state['cost_model']}\n\n"
            f"Price-to-Win Estimate:\n{state['price_to_win_estimate']}\n\n"
            "Generate 4–6 pricing scenarios with these strategy types: "
            "Floor, Aggressive, Competitive, Value-Based, Maximum Profit.\n"
            "For each provide:\n"
            "- Strategy name\n"
            "- Total price\n"
            "- Margin percentage\n"
            "- Win probability\n"
            "- Expected value (price × P(win))\n"
            "- Pros and cons\n"
        )
    )

    try:
        response = await llm.ainvoke([system, human])
        content = response.content
    except Exception as exc:
        logger.error("LLM failed in generate_pricing_scenarios: %s", exc)
        content = "Scenario generation unavailable due to API error."

    # Parse scenarios from response — store as raw text for now
    scenarios = [{"analysis": content}]

    return {
        "scenarios": scenarios,
        "messages": [HumanMessage(content="Pricing scenarios generated.")],
    }


async def select_recommended_scenario(state: PricingState) -> dict:
    """Claude selects the single best scenario and explains the recommendation."""
    logger.info("Selecting recommended pricing scenario")
    llm = _get_llm()

    system = SystemMessage(
        content=(
            "You are a chief pricing officer for a government contracting firm. "
            "Select the single best pricing scenario that balances win probability, "
            "margin, and strategic fit. Provide a clear recommendation with rationale."
        )
    )
    human = HumanMessage(
        content=(
            f"Deal: {state['deal']}\n\n"
            f"Pricing Scenarios:\n{state['scenarios']}\n\n"
            f"Price-to-Win Estimate:\n{state['price_to_win_estimate']}\n\n"
            "Select the recommended scenario. Provide:\n"
            "1. Recommended strategy (one of the scenarios above)\n"
            "2. Rationale for the recommendation\n"
            "3. Key pricing risks to mitigate\n"
            "4. Negotiation guidance for price discussions with the customer\n"
        )
    )

    try:
        response = await llm.ainvoke([system, human])
        content = response.content
    except Exception as exc:
        logger.error("LLM failed in select_recommended_scenario: %s", exc)
        content = "Recommendation unavailable due to API error."

    # Extract strategy name from the first line
    lines = content.strip().split("\n")
    pricing_strategy = lines[0].strip() if lines else "Competitive Pricing"

    # Extract risk factors
    risk_factors = [
        line.strip("- •").strip()
        for line in content.split("\n")
        if line.strip().startswith(("-", "•")) and "risk" in line.lower()
    ]

    return {
        "recommended_scenario": {"recommendation": content},
        "pricing_strategy": pricing_strategy,
        "risk_factors": risk_factors,
        "negotiation_guidance": content,
        "messages": [HumanMessage(content=f"Recommended strategy: {pricing_strategy}")],
    }


# ── Graph builder ─────────────────────────────────────────────────────────────

def build_pricing_graph() -> StateGraph:
    """Construct and compile the pricing LangGraph workflow."""
    workflow = StateGraph(PricingState)

    workflow.add_node("load_pricing_context", load_pricing_context)
    workflow.add_node("analyze_price_to_win", analyze_price_to_win)
    workflow.add_node("generate_pricing_scenarios", generate_pricing_scenarios)
    workflow.add_node("select_recommended_scenario", select_recommended_scenario)

    workflow.set_entry_point("load_pricing_context")
    workflow.add_edge("load_pricing_context", "analyze_price_to_win")
    workflow.add_edge("analyze_price_to_win", "generate_pricing_scenarios")
    workflow.add_edge("generate_pricing_scenarios", "select_recommended_scenario")
    workflow.add_edge("select_recommended_scenario", END)

    return workflow.compile()


pricing_graph = build_pricing_graph()


# ── Agent class ───────────────────────────────────────────────────────────────

class PricingAgent(BaseAgent):
    """LangGraph-based Pricing AI Agent."""

    agent_name = "pricing_agent"

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Run pricing analysis for a deal.

        Args:
            input_data: Must contain 'deal_id'.

        Returns:
            dict with keys: deal_id, price_to_win_estimate, scenarios,
            recommended_scenario, pricing_strategy, risk_factors,
            negotiation_guidance.
        """
        deal_id = input_data.get("deal_id", "")
        if not deal_id:
            return {"error": "deal_id is required"}

        initial_state: PricingState = {
            "deal_id": deal_id,
            "deal": {},
            "cost_model": {},
            "market_intelligence": [],
            "price_to_win_estimate": {},
            "scenarios": [],
            "recommended_scenario": {},
            "pricing_strategy": "",
            "risk_factors": [],
            "negotiation_guidance": "",
            "messages": [],
        }

        try:
            await self.emit_event(
                "thinking",
                {"message": f"Starting pricing analysis for deal {deal_id}"},
                execution_id=deal_id,
            )
            final_state = await pricing_graph.ainvoke(initial_state)
            await self.emit_event(
                "output",
                {"strategy": final_state["pricing_strategy"]},
                execution_id=deal_id,
            )
            return {
                "deal_id": final_state["deal_id"],
                "price_to_win_estimate": final_state["price_to_win_estimate"],
                "scenarios": final_state["scenarios"],
                "recommended_scenario": final_state["recommended_scenario"],
                "pricing_strategy": final_state["pricing_strategy"],
                "risk_factors": final_state["risk_factors"],
                "negotiation_guidance": final_state["negotiation_guidance"],
            }
        except Exception as exc:
            logger.exception("PricingAgent.run failed for deal %s", deal_id)
            await self.emit_event("error", {"error": str(exc)}, execution_id=deal_id)
            return {"error": str(exc), "deal_id": deal_id}
