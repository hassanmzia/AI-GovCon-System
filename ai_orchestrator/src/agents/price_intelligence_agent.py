"""Price Intelligence Agent — FPDS Historical Benchmarking.

Queries FPDS/USASpending historical award data for comparable contracts,
performs statistical price analysis (median, percentiles, regression),
and produces price benchmarks that feed into the Pricing Agent's
scenario generation.

This agent closes the gap between our pricing_agent (which builds
scenarios from internal cost models) and real market data (what the
government actually paid for similar work).
"""

import logging
import os
import statistics
from typing import Annotated, Any
import operator

import httpx
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from typing_extensions import TypedDict

from src.agents.base import BaseAgent
from src.llm_provider import get_chat_model

logger = logging.getLogger("ai_orchestrator.agents.price_intelligence")

DJANGO_API_URL = os.getenv("DJANGO_API_URL", "http://django-api:8001")
DJANGO_SERVICE_TOKEN = os.getenv("DJANGO_SERVICE_TOKEN", "")


# ── State ────────────────────────────────────────────────────────────────────

class PriceIntelligenceState(TypedDict):
    deal_id: str
    deal: dict
    opportunity: dict
    # FPDS comparable awards
    comparable_awards: list[dict]
    # Statistical analysis
    price_statistics: dict
    # Incumbent intelligence
    incumbent_analysis: dict
    # Final benchmark report
    benchmark_report: str
    # Price reasonableness narrative
    price_reasonableness: str
    messages: Annotated[list, operator.add]


# ── Helpers ──────────────────────────────────────────────────────────────────

def _auth_headers() -> dict[str, str]:
    t = DJANGO_SERVICE_TOKEN
    return {"Authorization": f"Bearer {t}"} if t else {}


async def _get(path: str, default: Any = None) -> Any:
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{DJANGO_API_URL}{path}", headers=_auth_headers()
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.warning("API GET %s failed: %s", path, exc)
        return default


def _extract_award_values(awards: list[dict]) -> list[float]:
    """Extract numeric award values from a list of opportunity/award dicts."""
    values = []
    for a in awards:
        for field in ("contract_value", "award_amount", "total_value", "estimated_value"):
            raw = a.get(field)
            if raw is not None:
                try:
                    val = float(str(raw).replace(",", "").replace("$", ""))
                    if val > 0:
                        values.append(val)
                        break
                except (ValueError, TypeError):
                    continue
    return values


# ── Graph Nodes ──────────────────────────────────────────────────────────────

async def load_deal_context(state: PriceIntelligenceState) -> dict:
    """Fetch deal and opportunity details."""
    logger.info("PriceIntelligence: loading context for deal %s", state["deal_id"])

    deal = await _get(f"/api/deals/deals/{state['deal_id']}/", default={})
    opp_id = deal.get("opportunity") or deal.get("opportunity_id") or ""
    opportunity = {}
    if opp_id:
        opportunity = await _get(f"/api/opportunities/opportunities/{opp_id}/", default={})

    return {
        "deal": deal,
        "opportunity": opportunity,
        "messages": [HumanMessage(content=f"Loaded deal: {deal.get('title', state['deal_id'])}")],
    }


async def fetch_comparable_awards(state: PriceIntelligenceState) -> dict:
    """Query FPDS/historical opportunities for comparable awards by NAICS + agency."""
    logger.info("PriceIntelligence: fetching comparable awards for deal %s", state["deal_id"])

    opp = state.get("opportunity") or {}
    deal = state.get("deal") or {}

    naics = opp.get("naics_code") or deal.get("naics_code") or ""
    agency = opp.get("agency") or deal.get("agency") or ""

    comparable = []

    # 1) Fetch FPDS awards (status=awarded) matching NAICS
    if naics:
        fpds_data = await _get(
            f"/api/opportunities/opportunities/?naics_code={naics}&status=awarded&limit=50",
            default={},
        )
        comparable.extend(fpds_data.get("results", []) if isinstance(fpds_data, dict) else [])

    # 2) Also fetch closed_won deals for internal price history
    internal_data = await _get(
        "/api/deals/deals/?stage=closed_won&limit=30",
        default={},
    )
    internal_deals = internal_data.get("results", []) if isinstance(internal_data, dict) else []
    comparable.extend(internal_deals)

    # 3) If agency is known, also pull agency-specific awards
    if agency and naics:
        agency_data = await _get(
            f"/api/opportunities/opportunities/?agency={agency}&naics_code={naics}&status=awarded&limit=20",
            default={},
        )
        agency_results = agency_data.get("results", []) if isinstance(agency_data, dict) else []
        # Deduplicate by ID
        existing_ids = {str(a.get("id", "")) for a in comparable}
        for a in agency_results:
            if str(a.get("id", "")) not in existing_ids:
                comparable.append(a)

    logger.info("PriceIntelligence: found %d comparable awards/deals", len(comparable))

    return {
        "comparable_awards": comparable,
        "messages": [HumanMessage(content=f"Found {len(comparable)} comparable awards for NAICS {naics}")],
    }


async def analyze_price_statistics(state: PriceIntelligenceState) -> dict:
    """Run statistical analysis on comparable award values."""
    logger.info("PriceIntelligence: running statistical analysis for deal %s", state["deal_id"])

    awards = state.get("comparable_awards") or []
    values = _extract_award_values(awards)

    if not values:
        return {
            "price_statistics": {
                "sample_size": 0,
                "note": "No comparable award values found for statistical analysis",
            },
            "messages": [HumanMessage(content="No award values available for statistics")],
        }

    values_sorted = sorted(values)
    n = len(values_sorted)

    stats = {
        "sample_size": n,
        "min": round(min(values), 2),
        "max": round(max(values), 2),
        "mean": round(statistics.mean(values), 2),
        "median": round(statistics.median(values), 2),
        "stdev": round(statistics.stdev(values), 2) if n > 1 else 0,
        "p25": round(values_sorted[max(0, n // 4 - 1)], 2),
        "p75": round(values_sorted[min(n - 1, 3 * n // 4)], 2),
        "iqr": round(
            values_sorted[min(n - 1, 3 * n // 4)] - values_sorted[max(0, n // 4 - 1)], 2
        ),
    }

    # Price range bands for competitive positioning
    stats["competitive_range"] = {
        "floor": round(stats["p25"], 2),
        "target": round(stats["median"], 2),
        "ceiling": round(stats["p75"], 2),
    }

    return {
        "price_statistics": stats,
        "messages": [HumanMessage(
            content=f"Price stats: median ${stats['median']:,.0f}, "
                    f"range ${stats['min']:,.0f} - ${stats['max']:,.0f} "
                    f"(n={n})"
        )],
    }


async def analyze_incumbents(state: PriceIntelligenceState) -> dict:
    """Identify incumbents and their pricing patterns from award data."""
    logger.info("PriceIntelligence: analyzing incumbents for deal %s", state["deal_id"])

    awards = state.get("comparable_awards") or []

    # Extract vendor information from awards
    vendor_awards: dict[str, list[dict]] = {}
    for a in awards:
        vendor = (
            a.get("incumbent_vendor")
            or a.get("awardee")
            or a.get("vendor_name")
            or a.get("company_name")
            or ""
        )
        if vendor and vendor != "Unknown":
            vendor_awards.setdefault(vendor, []).append(a)

    # Build incumbent profiles
    incumbents = []
    for vendor, v_awards in vendor_awards.items():
        values = _extract_award_values(v_awards)
        profile = {
            "vendor": vendor,
            "award_count": len(v_awards),
            "total_value": round(sum(values), 2) if values else 0,
            "avg_value": round(statistics.mean(values), 2) if values else 0,
        }
        incumbents.append(profile)

    # Sort by total value (most significant incumbent first)
    incumbents.sort(key=lambda x: x["total_value"], reverse=True)

    return {
        "incumbent_analysis": {
            "incumbents": incumbents[:10],
            "incumbent_count": len(incumbents),
            "market_concentration": "high" if len(incumbents) <= 3 else "moderate" if len(incumbents) <= 7 else "competitive",
        },
        "messages": [HumanMessage(content=f"Identified {len(incumbents)} incumbent vendors")],
    }


async def generate_benchmark_report(state: PriceIntelligenceState) -> dict:
    """Use LLM to synthesize all price intelligence into an actionable report."""
    logger.info("PriceIntelligence: generating benchmark report for deal %s", state["deal_id"])

    llm = get_chat_model(max_tokens=3000)

    deal = state.get("deal") or {}
    opp = state.get("opportunity") or {}
    stats = state.get("price_statistics") or {}
    incumbents = state.get("incumbent_analysis") or {}
    n_awards = len(state.get("comparable_awards") or [])

    system = SystemMessage(content=(
        "You are a senior price analyst for a U.S. government contracting firm. "
        "You specialize in Independent Government Cost Estimates (IGCE), price "
        "reasonableness determinations, and competitive pricing strategy. "
        "Use statistical data from historical awards to produce actionable "
        "pricing intelligence."
    ))

    human = HumanMessage(content=(
        f"DEAL: {deal.get('title', 'Unknown')}\n"
        f"AGENCY: {opp.get('agency', deal.get('agency', 'Unknown'))}\n"
        f"NAICS: {opp.get('naics_code', 'N/A')}\n"
        f"ESTIMATED VALUE: ${deal.get('contract_value', 'N/A')}\n\n"
        f"COMPARABLE AWARDS ({n_awards} total):\n"
        f"Statistical Summary:\n"
        f"  Sample Size: {stats.get('sample_size', 0)}\n"
        f"  Min: ${stats.get('min', 0):,.0f}\n"
        f"  25th Percentile: ${stats.get('p25', 0):,.0f}\n"
        f"  Median: ${stats.get('median', 0):,.0f}\n"
        f"  75th Percentile: ${stats.get('p75', 0):,.0f}\n"
        f"  Max: ${stats.get('max', 0):,.0f}\n"
        f"  Std Dev: ${stats.get('stdev', 0):,.0f}\n\n"
        f"INCUMBENT ANALYSIS:\n"
        f"  Market Concentration: {incumbents.get('market_concentration', 'unknown')}\n"
        f"  Top Incumbents: {incumbents.get('incumbents', [])[:5]}\n\n"
        "Produce a Price Intelligence Report with:\n"
        "1. MARKET PRICE BENCHMARK: What the government typically pays for this work\n"
        "2. COMPETITIVE RANGE: Floor/target/ceiling price bands with justification\n"
        "3. INCUMBENT THREAT ASSESSMENT: How incumbents affect pricing strategy\n"
        "4. PRICE-TO-WIN RECOMMENDATION: Recommended price position with confidence level\n"
        "5. PRICE REASONABLENESS NARRATIVE: Draft narrative suitable for a\n"
        "   price reasonableness determination (2-3 paragraphs)\n"
        "6. RISKS: Key pricing risks based on market data"
    ))

    try:
        response = await llm.ainvoke([system, human])
        report = response.content
    except Exception as exc:
        logger.error("LLM failed in generate_benchmark_report: %s", exc)
        report = "Price intelligence report unavailable due to API error."

    # Extract the price reasonableness section
    reasonableness = ""
    in_reasonableness = False
    for line in report.split("\n"):
        if "PRICE REASONABLENESS" in line.upper():
            in_reasonableness = True
            continue
        elif in_reasonableness and line.strip().startswith(("6.", "RISK")):
            break
        elif in_reasonableness:
            reasonableness += line + "\n"

    return {
        "benchmark_report": report,
        "price_reasonableness": reasonableness.strip() or "See benchmark report.",
        "messages": [HumanMessage(content="Price intelligence benchmark report generated.")],
    }


# ── Graph Builder ────────────────────────────────────────────────────────────

def build_price_intelligence_graph() -> StateGraph:
    wf = StateGraph(PriceIntelligenceState)

    wf.add_node("load_deal_context", load_deal_context)
    wf.add_node("fetch_comparable_awards", fetch_comparable_awards)
    wf.add_node("analyze_price_statistics", analyze_price_statistics)
    wf.add_node("analyze_incumbents", analyze_incumbents)
    wf.add_node("generate_benchmark_report", generate_benchmark_report)

    wf.set_entry_point("load_deal_context")
    wf.add_edge("load_deal_context", "fetch_comparable_awards")
    wf.add_edge("fetch_comparable_awards", "analyze_price_statistics")
    wf.add_edge("analyze_price_statistics", "analyze_incumbents")
    wf.add_edge("analyze_incumbents", "generate_benchmark_report")
    wf.add_edge("generate_benchmark_report", END)

    return wf.compile()


price_intelligence_graph = build_price_intelligence_graph()


# ── Agent Class ──────────────────────────────────────────────────────────────

class PriceIntelligenceAgent(BaseAgent):
    """
    FPDS-powered price intelligence agent.

    Fetches historical award data, runs statistical price analysis,
    identifies incumbents, and generates price benchmarks + price
    reasonableness narratives for the pricing pipeline.
    """

    agent_name = "price_intelligence_agent"

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        deal_id = input_data.get("deal_id", "")
        if not deal_id:
            return {"error": "deal_id is required"}

        initial: PriceIntelligenceState = {
            "deal_id": deal_id,
            "deal": {},
            "opportunity": {},
            "comparable_awards": [],
            "price_statistics": {},
            "incumbent_analysis": {},
            "benchmark_report": "",
            "price_reasonableness": "",
            "messages": [],
        }

        try:
            await self.emit_event(
                "thinking",
                {"message": f"Starting FPDS price intelligence analysis for deal {deal_id}"},
                execution_id=deal_id,
            )
            fs = await price_intelligence_graph.ainvoke(initial)
            await self.emit_event(
                "output",
                {
                    "comparable_awards_count": len(fs["comparable_awards"]),
                    "sample_size": fs["price_statistics"].get("sample_size", 0),
                    "median_price": fs["price_statistics"].get("median", 0),
                },
                execution_id=deal_id,
            )
            return {
                "deal_id": deal_id,
                "comparable_awards_count": len(fs["comparable_awards"]),
                "price_statistics": fs["price_statistics"],
                "incumbent_analysis": fs["incumbent_analysis"],
                "benchmark_report": fs["benchmark_report"],
                "price_reasonableness": fs["price_reasonableness"],
            }
        except Exception as exc:
            logger.exception("PriceIntelligenceAgent failed for deal %s", deal_id)
            await self.emit_event("error", {"error": str(exc)}, execution_id=deal_id)
            return {"error": str(exc), "deal_id": deal_id}
