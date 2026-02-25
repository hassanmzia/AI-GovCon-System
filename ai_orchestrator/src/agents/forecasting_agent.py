"""
Forecasting Agent — Predicts deal outcomes and generates revenue forecasts.

Uses historical deal data and pipeline analysis to predict win/loss outcomes,
forecast revenue by quarter with confidence intervals, and assess prediction
confidence based on data quality and historical accuracy.
"""

import logging
import os
from decimal import Decimal
from typing import Any

import httpx
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from typing_extensions import TypedDict

from src.agents.base import BaseAgent

logger = logging.getLogger("ai_orchestrator.agents.forecasting")

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


class ForecastingState(TypedDict):
    deal_id: str | None
    historical_deals: list[dict]
    pipeline_deals: list[dict]
    win_loss_analyses: list[dict]
    velocity_metrics: list[dict]
    pipeline_analysis: dict
    forecast: dict
    confidence_assessment: dict
    messages: list


async def load_historical_data(state: ForecastingState) -> dict:
    """Load historical deal data, win/loss analyses, and velocity metrics."""
    # Fetch closed deals for historical patterns
    closed_deals = await _get("/api/deals/?stage=closed_won", default={})
    lost_deals = await _get("/api/deals/?stage=closed_lost", default={})

    closed_results = (
        closed_deals.get("results", []) if isinstance(closed_deals, dict) else []
    )
    lost_results = (
        lost_deals.get("results", []) if isinstance(lost_deals, dict) else []
    )
    historical = closed_results + lost_results

    # Fetch active pipeline deals
    pipeline_data = await _get("/api/deals/?ordering=-estimated_value", default={})
    pipeline_deals = (
        pipeline_data.get("results", []) if isinstance(pipeline_data, dict) else []
    )

    # Fetch win/loss analysis records
    wl_data = await _get("/api/analytics/win-loss/", default={})
    wl_records = wl_data.get("results", []) if isinstance(wl_data, dict) else []

    # Fetch velocity metrics
    velocity_data = await _get("/api/analytics/velocity/avg-by-stage/", default=[])
    velocity = velocity_data if isinstance(velocity_data, list) else []

    return {
        "historical_deals": historical,
        "pipeline_deals": pipeline_deals,
        "win_loss_analyses": wl_records,
        "velocity_metrics": velocity,
        "messages": [
            HumanMessage(
                content=(
                    f"Loaded {len(historical)} historical deals, "
                    f"{len(pipeline_deals)} pipeline deals, "
                    f"{len(wl_records)} win/loss analyses"
                )
            )
        ],
    }


async def analyze_pipeline(state: ForecastingState) -> dict:
    """Analyze pipeline composition and identify patterns."""
    llm = _get_llm()

    historical = state.get("historical_deals", [])
    pipeline = state.get("pipeline_deals", [])
    wl = state.get("win_loss_analyses", [])
    velocity = state.get("velocity_metrics", [])

    # Compute basic statistics
    won_count = sum(1 for d in historical if d.get("stage") == "closed_won")
    lost_count = sum(1 for d in historical if d.get("stage") == "closed_lost")
    total_closed = won_count + lost_count
    historical_win_rate = (
        round((won_count / total_closed) * 100, 1) if total_closed > 0 else None
    )

    # Stage distribution of pipeline
    stage_dist: dict[str, int] = {}
    for d in pipeline:
        s = d.get("stage", "unknown")
        stage_dist[s] = stage_dist.get(s, 0) + 1

    # Top loss reasons
    loss_reasons: dict[str, int] = {}
    for w in wl:
        reason = w.get("primary_loss_reason", "")
        if reason:
            loss_reasons[reason] = loss_reasons.get(reason, 0) + 1

    pipeline_summary = (
        f"Pipeline: {len(pipeline)} deals across stages: {stage_dist}\n"
        f"Historical win rate: {historical_win_rate}% ({won_count}W / {lost_count}L)\n"
        f"Top loss reasons: {dict(sorted(loss_reasons.items(), key=lambda x: -x[1])[:5])}\n"
        f"Avg velocity by stage: {velocity[:6]}"
    )

    try:
        resp = await llm.ainvoke([
            SystemMessage(content=(
                "You are a GovCon business analyst specializing in pipeline analytics. "
                "Analyse the provided pipeline data and identify:\n"
                "1. Stage-specific win probabilities based on historical data\n"
                "2. Deals at risk (low probability, stalled, overdue)\n"
                "3. Pipeline health indicators\n"
                "4. Trends and patterns\n"
                "Return structured analysis with specific deal-level insights."
            )),
            HumanMessage(content=pipeline_summary),
        ])
        analysis_text = resp.content
    except Exception as exc:
        logger.error("Pipeline analysis LLM call failed: %s", exc)
        analysis_text = "Pipeline analysis unavailable."

    return {
        "pipeline_analysis": {
            "historical_win_rate": historical_win_rate,
            "stage_distribution": stage_dist,
            "top_loss_reasons": loss_reasons,
            "llm_analysis": analysis_text,
            "won_count": won_count,
            "lost_count": lost_count,
            "pipeline_count": len(pipeline),
        },
        "messages": [HumanMessage(content="Pipeline analysis complete")],
    }


async def generate_forecast(state: ForecastingState) -> dict:
    """Generate quarterly revenue forecast with deal-level predictions."""
    llm = _get_llm()

    pipeline = state.get("pipeline_deals", [])
    analysis = state.get("pipeline_analysis", {})

    # Group deals by expected quarter (based on due_date or award_date)
    quarterly_buckets: dict[str, list[dict]] = {}
    for d in pipeline:
        due = d.get("due_date") or d.get("award_date") or ""
        if due:
            # Extract quarter from date string
            date_str = due[:10] if isinstance(due, str) else str(due)[:10]
            try:
                year = int(date_str[:4])
                month = int(date_str[5:7])
                q = (month - 1) // 3 + 1
                q_label = f"{year}-Q{q}"
            except (ValueError, IndexError):
                q_label = "Unscheduled"
        else:
            q_label = "Unscheduled"

        quarterly_buckets.setdefault(q_label, []).append(d)

    # Compute per-quarter forecasts
    quarterly_forecasts = []
    for quarter, deals in sorted(quarterly_buckets.items()):
        pipeline_value = sum(
            float(d.get("estimated_value", 0) or 0) for d in deals
        )
        weighted_value = sum(
            float(d.get("estimated_value", 0) or 0) * float(d.get("win_probability", 0) or 0)
            for d in deals
        )

        # Simple confidence interval: +/- 30% on weighted value
        confidence_low = weighted_value * 0.7
        confidence_high = weighted_value * 1.3

        deal_details = [
            {
                "id": d.get("id", ""),
                "title": d.get("title", ""),
                "stage": d.get("stage", ""),
                "value": d.get("estimated_value"),
                "probability": d.get("win_probability"),
                "weighted": float(d.get("estimated_value", 0) or 0) * float(d.get("win_probability", 0) or 0),
            }
            for d in deals
        ]

        quarterly_forecasts.append({
            "quarter": quarter,
            "deal_count": len(deals),
            "pipeline_value": round(pipeline_value, 2),
            "weighted_value": round(weighted_value, 2),
            "confidence_low": round(confidence_low, 2),
            "confidence_high": round(confidence_high, 2),
            "deal_details": deal_details,
        })

    # LLM-enhanced narrative forecast
    try:
        resp = await llm.ainvoke([
            SystemMessage(content=(
                "You are a GovCon revenue forecasting analyst. Based on the pipeline "
                "data and analysis, provide a concise executive narrative forecast. "
                "Include: overall revenue outlook, key risks to forecast, and "
                "recommended actions to improve forecast accuracy."
            )),
            HumanMessage(content=(
                f"Pipeline analysis:\n{analysis.get('llm_analysis', 'N/A')}\n\n"
                f"Quarterly forecasts: {quarterly_forecasts}"
            )),
        ])
        narrative = resp.content
    except Exception as exc:
        logger.error("Forecast narrative generation failed: %s", exc)
        narrative = "Narrative forecast unavailable."

    return {
        "forecast": {
            "quarterly": quarterly_forecasts,
            "narrative": narrative,
            "total_pipeline": sum(q["pipeline_value"] for q in quarterly_forecasts),
            "total_weighted": sum(q["weighted_value"] for q in quarterly_forecasts),
        },
        "messages": [HumanMessage(content="Revenue forecast generated")],
    }


async def assess_confidence(state: ForecastingState) -> dict:
    """Assess confidence level of the forecast based on data quality."""
    historical = state.get("historical_deals", [])
    pipeline = state.get("pipeline_deals", [])
    forecast = state.get("forecast", {})

    # Data quality factors
    factors = []
    score = 100.0

    # Historical data volume
    if len(historical) < 10:
        factors.append("Insufficient historical data (< 10 closed deals)")
        score -= 25
    elif len(historical) < 50:
        factors.append("Limited historical data (< 50 closed deals)")
        score -= 10

    # Pipeline data completeness
    missing_values = sum(
        1 for d in pipeline
        if not d.get("estimated_value") or not d.get("win_probability")
    )
    if missing_values > 0:
        pct = round((missing_values / max(len(pipeline), 1)) * 100, 1)
        factors.append(f"{pct}% of pipeline deals missing value or probability data")
        score -= min(pct * 0.3, 20)

    # Deals without due dates
    missing_dates = sum(1 for d in pipeline if not d.get("due_date"))
    if missing_dates > 0:
        pct = round((missing_dates / max(len(pipeline), 1)) * 100, 1)
        factors.append(f"{pct}% of pipeline deals have no due date")
        score -= min(pct * 0.2, 15)

    # Win probability spread
    probs = [float(d.get("win_probability", 0) or 0) for d in pipeline]
    if probs:
        avg_prob = sum(probs) / len(probs)
        if avg_prob > 0.8:
            factors.append("Pipeline win probabilities may be overly optimistic")
            score -= 10
        elif avg_prob < 0.2:
            factors.append("Pipeline win probabilities are very conservative")
            score -= 5

    score = max(0, min(100, score))

    if score >= 80:
        level = "high"
    elif score >= 50:
        level = "medium"
    else:
        level = "low"

    return {
        "confidence_assessment": {
            "score": round(score, 1),
            "level": level,
            "factors": factors,
            "historical_deal_count": len(historical),
            "pipeline_deal_count": len(pipeline),
        },
        "messages": [HumanMessage(content=f"Confidence assessment: {level} ({score:.0f}/100)")],
    }


def build_forecasting_graph() -> StateGraph:
    wf = StateGraph(ForecastingState)
    wf.add_node("load_historical_data", load_historical_data)
    wf.add_node("analyze_pipeline", analyze_pipeline)
    wf.add_node("generate_forecast", generate_forecast)
    wf.add_node("assess_confidence", assess_confidence)
    wf.set_entry_point("load_historical_data")
    wf.add_edge("load_historical_data", "analyze_pipeline")
    wf.add_edge("analyze_pipeline", "generate_forecast")
    wf.add_edge("generate_forecast", "assess_confidence")
    wf.add_edge("assess_confidence", END)
    return wf.compile()


forecasting_graph = build_forecasting_graph()


class ForecastingAgent(BaseAgent):
    """AI agent that predicts deal outcomes and forecasts revenue."""

    agent_name = "forecasting_agent"

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        deal_id = input_data.get("deal_id")

        initial: ForecastingState = {
            "deal_id": deal_id,
            "historical_deals": [],
            "pipeline_deals": [],
            "win_loss_analyses": [],
            "velocity_metrics": [],
            "pipeline_analysis": {},
            "forecast": {},
            "confidence_assessment": {},
            "messages": [],
        }
        try:
            await self.emit_event("thinking", {"message": "Generating revenue forecast and deal predictions"})
            result = await forecasting_graph.ainvoke(initial)
            await self.emit_event("output", {
                "status": "forecast_generated",
                "confidence": result.get("confidence_assessment", {}).get("level", "unknown"),
            })
            return {
                "pipeline_analysis": result.get("pipeline_analysis", {}),
                "forecast": result.get("forecast", {}),
                "confidence_assessment": result.get("confidence_assessment", {}),
                "status": "generated",
            }
        except Exception as exc:
            logger.exception("ForecastingAgent.run failed")
            await self.emit_event("error", {"error": str(exc)})
            return {"error": str(exc)}
