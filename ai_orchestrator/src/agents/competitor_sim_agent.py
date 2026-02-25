"""
Competitor Simulation Agent — Models competitor behaviour and generates ghost strategies.

Uses historical FPDS (Federal Procurement Data System) data and win/loss
analyses to build competitor profiles, simulate pricing/bidding scenarios,
and generate ghost strategy recommendations for capture teams.
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

logger = logging.getLogger("ai_orchestrator.agents.competitor_sim")

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


def _get_llm() -> ChatAnthropic:
    return ChatAnthropic(
        model="claude-sonnet-4-6",
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        max_tokens=4096,
    )


class CompetitorSimState(TypedDict):
    deal_id: str
    deal: dict
    opportunity: dict
    win_loss_history: list[dict]
    fpds_data: list[dict]
    competitor_profiles: list[dict]
    simulation_results: list[dict]
    ghost_strategies: list[dict]
    messages: list


async def load_competitor_data(state: CompetitorSimState) -> dict:
    """Load deal context, win/loss history, and FPDS data for competitor analysis."""
    deal_id = state["deal_id"]

    # Load the deal and opportunity details
    deal = await _get(f"/api/deals/{deal_id}/", default={})
    opp_id = deal.get("opportunity", "")
    opp = await _get(f"/api/opportunities/{opp_id}/", default={}) if opp_id else {}

    # Load win/loss analyses with competitor data
    wl_data = await _get("/api/analytics/win-loss/", default={})
    wl_records = wl_data.get("results", []) if isinstance(wl_data, dict) else []

    # Attempt to load FPDS data (may come from an external MCP server)
    fpds_data: list[dict] = []
    agency = opp.get("agency", "")
    naics = opp.get("naics_code", "")
    if agency or naics:
        try:
            from src.mcp_servers.competitive_intel_tools import get_fpds_awards
            fpds_data = await get_fpds_awards(agency=agency, naics=naics)
            if not isinstance(fpds_data, list):
                fpds_data = []
        except Exception:
            logger.debug("FPDS data tools not available, proceeding with win/loss data only")

    return {
        "deal": deal,
        "opportunity": opp,
        "win_loss_history": wl_records,
        "fpds_data": fpds_data,
        "messages": [
            HumanMessage(
                content=(
                    f"Loaded deal context, {len(wl_records)} win/loss records, "
                    f"{len(fpds_data)} FPDS award records"
                )
            )
        ],
    }


async def build_profiles(state: CompetitorSimState) -> dict:
    """Build competitor profiles from win/loss history and FPDS data."""
    llm = _get_llm()

    wl_records = state.get("win_loss_history", [])
    fpds_data = state.get("fpds_data", [])
    opp = state.get("opportunity", {})

    # Extract competitor names and aggregate data
    competitor_agg: dict[str, dict] = {}
    for record in wl_records:
        name = record.get("competitor_name", "").strip()
        if not name:
            continue
        if name not in competitor_agg:
            competitor_agg[name] = {
                "name": name,
                "wins_against_us": 0,
                "losses_against_us": 0,
                "avg_price": [],
                "loss_reasons": [],
                "win_themes": [],
            }
        if record.get("outcome") == "lost":
            competitor_agg[name]["wins_against_us"] += 1
            price = record.get("competitor_price")
            if price:
                competitor_agg[name]["avg_price"].append(float(price))
            reason = record.get("primary_loss_reason", "")
            if reason:
                competitor_agg[name]["loss_reasons"].append(reason)
        elif record.get("outcome") == "won":
            competitor_agg[name]["losses_against_us"] += 1
            themes = record.get("win_themes", [])
            competitor_agg[name]["win_themes"].extend(themes)

    # Enrich with FPDS data
    for award in fpds_data:
        vendor = award.get("vendor_name", "").strip()
        if vendor and vendor in competitor_agg:
            competitor_agg[vendor].setdefault("fpds_awards", []).append({
                "contract_number": award.get("contract_number", ""),
                "value": award.get("value"),
                "agency": award.get("agency", ""),
                "date": award.get("award_date", ""),
            })

    # Build summary for each competitor
    profiles_input = []
    for name, data in competitor_agg.items():
        avg_price = (
            round(sum(data["avg_price"]) / len(data["avg_price"]), 2)
            if data["avg_price"] else None
        )
        profiles_input.append({
            "name": name,
            "wins_against_us": data["wins_against_us"],
            "losses_against_us": data["losses_against_us"],
            "avg_price": avg_price,
            "top_loss_reasons": data["loss_reasons"][:5],
            "fpds_award_count": len(data.get("fpds_awards", [])),
        })

    # Use LLM to generate enriched profiles with strategic insights
    if profiles_input:
        try:
            resp = await llm.ainvoke([
                SystemMessage(content=(
                    "You are a GovCon competitive intelligence analyst. "
                    "For each competitor, generate a strategic profile including:\n"
                    "1. Strengths (based on win patterns)\n"
                    "2. Weaknesses (based on our wins against them)\n"
                    "3. Likely pricing strategy\n"
                    "4. Technical approach tendencies\n"
                    "5. Threat level (HIGH / MEDIUM / LOW)\n\n"
                    "Return one profile per competitor in a structured format."
                )),
                HumanMessage(content=(
                    f"Opportunity context:\n"
                    f"  Agency: {opp.get('agency', 'N/A')}\n"
                    f"  NAICS: {opp.get('naics_code', 'N/A')}\n"
                    f"  Value: {opp.get('estimated_value', 'N/A')}\n\n"
                    f"Competitor data:\n{profiles_input}"
                )),
            ])
            enrichment_text = resp.content
        except Exception as exc:
            logger.error("Competitor profile enrichment failed: %s", exc)
            enrichment_text = ""

        # Attach LLM analysis to profiles
        for profile in profiles_input:
            profile["llm_analysis"] = enrichment_text
    else:
        profiles_input = []

    return {
        "competitor_profiles": profiles_input,
        "messages": [HumanMessage(content=f"Built {len(profiles_input)} competitor profiles")],
    }


async def simulate_scenarios(state: CompetitorSimState) -> dict:
    """Simulate competitive bid scenarios based on competitor profiles."""
    llm = _get_llm()

    profiles = state.get("competitor_profiles", [])
    deal = state.get("deal", {})
    opp = state.get("opportunity", {})

    estimated_value = deal.get("estimated_value") or opp.get("estimated_value")

    if not profiles:
        return {
            "simulation_results": [{
                "scenario": "baseline",
                "note": "No competitor profiles available for simulation",
            }],
            "messages": [HumanMessage(content="Skipped simulation — no competitor data")],
        }

    try:
        resp = await llm.ainvoke([
            SystemMessage(content=(
                "You are a GovCon pricing and strategy simulation analyst. "
                "Given the competitor profiles and opportunity context, simulate "
                "three competitive bid scenarios:\n"
                "1. AGGRESSIVE — Competitors bid below cost, win on price\n"
                "2. BALANCED — Competitors at market rates, best-value decision\n"
                "3. TECHNICAL — Competitors focus on technical superiority\n\n"
                "For each scenario, provide:\n"
                "- Expected competitor price range\n"
                "- Our recommended price point\n"
                "- Win probability under this scenario\n"
                "- Key risk factors\n"
                "- Recommended response strategy\n"
                "Format each scenario clearly."
            )),
            HumanMessage(content=(
                f"Opportunity:\n"
                f"  Title: {deal.get('title', 'N/A')}\n"
                f"  Estimated value: {estimated_value}\n"
                f"  Agency: {opp.get('agency', 'N/A')}\n\n"
                f"Competitor profiles: {profiles}"
            )),
        ])
        simulation_text = resp.content
    except Exception as exc:
        logger.error("Competitive simulation failed: %s", exc)
        simulation_text = "Simulation unavailable."

    # Parse scenarios from LLM output
    scenarios = _parse_scenarios(simulation_text)

    return {
        "simulation_results": scenarios,
        "messages": [HumanMessage(content=f"Simulated {len(scenarios)} competitive scenarios")],
    }


async def generate_ghost_strategies(state: CompetitorSimState) -> dict:
    """Generate ghost strategy recommendations for the capture team."""
    llm = _get_llm()

    profiles = state.get("competitor_profiles", [])
    simulations = state.get("simulation_results", [])
    deal = state.get("deal", {})
    opp = state.get("opportunity", {})

    try:
        resp = await llm.ainvoke([
            SystemMessage(content=(
                "You are a senior GovCon capture strategist. Generate 'ghost strategies' — "
                "specific counter-positioning strategies against each key competitor. "
                "For each ghost strategy:\n"
                "1. Target competitor name\n"
                "2. Their likely approach (technical and pricing)\n"
                "3. Our counter-positioning strategy\n"
                "4. Key discriminators to emphasise\n"
                "5. Ghost team talking points (what evaluators should think)\n"
                "6. Risk mitigations\n\n"
                "Also provide an overall Ghost Strategy Summary with the top 5 "
                "actions the capture team should take immediately."
            )),
            HumanMessage(content=(
                f"Deal: {deal.get('title', 'N/A')}\n"
                f"Agency: {opp.get('agency', 'N/A')}\n"
                f"NAICS: {opp.get('naics_code', 'N/A')}\n"
                f"Value: {opp.get('estimated_value', 'N/A')}\n\n"
                f"Competitor Profiles:\n{profiles}\n\n"
                f"Simulation Results:\n{simulations}"
            )),
        ])
        ghost_text = resp.content
    except Exception as exc:
        logger.error("Ghost strategy generation failed: %s", exc)
        ghost_text = "Ghost strategies unavailable."

    # Parse ghost strategies
    strategies = _parse_ghost_strategies(ghost_text, profiles)

    return {
        "ghost_strategies": strategies,
        "messages": [HumanMessage(content=f"Generated {len(strategies)} ghost strategies")],
    }


def _parse_scenarios(text: str) -> list[dict]:
    """Parse competitive scenarios from LLM output."""
    scenarios = []
    scenario_names = ["AGGRESSIVE", "BALANCED", "TECHNICAL"]
    current_name = ""
    current_content: list[str] = []

    for line in text.split("\n"):
        upper = line.strip().upper()
        matched = False
        for name in scenario_names:
            if name in upper and len(line.strip()) < 80:
                # Save previous scenario
                if current_name:
                    scenarios.append({
                        "scenario": current_name.lower(),
                        "analysis": "\n".join(current_content).strip(),
                    })
                current_name = name
                current_content = []
                matched = True
                break
        if not matched:
            current_content.append(line)

    # Save last scenario
    if current_name:
        scenarios.append({
            "scenario": current_name.lower(),
            "analysis": "\n".join(current_content).strip(),
        })

    # Fallback if parsing fails
    if not scenarios:
        scenarios.append({
            "scenario": "combined",
            "analysis": text,
        })

    return scenarios


def _parse_ghost_strategies(text: str, profiles: list[dict]) -> list[dict]:
    """Parse ghost strategies from LLM output."""
    strategies = []

    # Create one strategy entry per competitor
    for profile in profiles:
        name = profile.get("name", "Unknown")
        # Try to extract the section relevant to this competitor
        strategies.append({
            "competitor": name,
            "threat_level": _extract_threat_level(text, name),
            "strategy_text": text,
            "wins_against_us": profile.get("wins_against_us", 0),
            "losses_against_us": profile.get("losses_against_us", 0),
        })

    # If no profiles, still return the full analysis
    if not strategies:
        strategies.append({
            "competitor": "General",
            "threat_level": "medium",
            "strategy_text": text,
        })

    return strategies


def _extract_threat_level(text: str, competitor_name: str) -> str:
    """Extract threat level for a competitor from LLM text."""
    # Look for threat level near competitor name
    lower = text.lower()
    name_lower = competitor_name.lower()
    idx = lower.find(name_lower)
    if idx >= 0:
        # Check a window around the competitor name for threat indicators
        window = lower[max(0, idx - 200): idx + 500]
        if "high" in window and ("threat" in window or "risk" in window):
            return "high"
        elif "low" in window and ("threat" in window or "risk" in window):
            return "low"
    return "medium"


def build_competitor_sim_graph() -> StateGraph:
    wf = StateGraph(CompetitorSimState)
    wf.add_node("load_competitor_data", load_competitor_data)
    wf.add_node("build_profiles", build_profiles)
    wf.add_node("simulate_scenarios", simulate_scenarios)
    wf.add_node("generate_ghost_strategies", generate_ghost_strategies)
    wf.set_entry_point("load_competitor_data")
    wf.add_edge("load_competitor_data", "build_profiles")
    wf.add_edge("build_profiles", "simulate_scenarios")
    wf.add_edge("simulate_scenarios", "generate_ghost_strategies")
    wf.add_edge("generate_ghost_strategies", END)
    return wf.compile()


competitor_sim_graph = build_competitor_sim_graph()


class CompetitorSimAgent(BaseAgent):
    """AI agent that simulates competitor behaviour and generates ghost strategies."""

    agent_name = "competitor_sim_agent"

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        deal_id = input_data.get("deal_id", "")
        if not deal_id:
            return {"error": "deal_id is required"}

        initial: CompetitorSimState = {
            "deal_id": deal_id,
            "deal": {},
            "opportunity": {},
            "win_loss_history": [],
            "fpds_data": [],
            "competitor_profiles": [],
            "simulation_results": [],
            "ghost_strategies": [],
            "messages": [],
        }
        try:
            await self.emit_event("thinking", {
                "message": f"Running competitor simulation for deal {deal_id}",
            })
            result = await competitor_sim_graph.ainvoke(initial)
            await self.emit_event("output", {
                "status": "competitor_sim_complete",
                "profiles_count": len(result.get("competitor_profiles", [])),
                "strategies_count": len(result.get("ghost_strategies", [])),
            })
            return {
                "deal_id": deal_id,
                "competitor_profiles": result.get("competitor_profiles", []),
                "simulation_results": result.get("simulation_results", []),
                "ghost_strategies": result.get("ghost_strategies", []),
                "status": "generated",
            }
        except Exception as exc:
            logger.exception("CompetitorSimAgent.run failed for deal %s", deal_id)
            await self.emit_event("error", {"error": str(exc)})
            return {"error": str(exc), "deal_id": deal_id}
