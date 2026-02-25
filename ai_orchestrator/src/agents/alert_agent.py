"""
Alert Agent — Monitors opportunities for changes, amendments, and deadline shifts.

Part of the decomposed Opportunity Intelligence domain.
Watches tracked opportunities and emits events when material changes occur.
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

logger = logging.getLogger("ai_orchestrator.agents.alert")

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


class AlertState(TypedDict):
    tracked_opportunities: list[dict]
    amendments_found: list[dict]
    deadline_changes: list[dict]
    scope_changes: list[dict]
    alerts: list[dict]
    messages: list


async def load_tracked_opportunities(state: AlertState) -> dict:
    """Load all opportunities that are tied to active deals."""
    deals_data = await _get(
        "/api/deals/?stage__in=qualify,bid_no_bid,capture_plan,proposal_dev&limit=100",
        default={},
    )
    deals = deals_data.get("results", []) if isinstance(deals_data, dict) else []

    tracked = []
    for deal in deals:
        opp_id = deal.get("opportunity", "")
        if opp_id:
            opp = await _get(f"/api/opportunities/{opp_id}/", default={})
            if opp:
                opp["deal_id"] = deal.get("id", "")
                opp["deal_stage"] = deal.get("stage", "")
                tracked.append(opp)

    return {
        "tracked_opportunities": tracked,
        "messages": [HumanMessage(content=f"Tracking {len(tracked)} active opportunities")],
    }


async def check_amendments(state: AlertState) -> dict:
    """Check SAM.gov for amendments on tracked opportunities."""
    amendments = []

    for opp in state.get("tracked_opportunities", []):
        notice_id = opp.get("notice_id", "")
        if not notice_id:
            continue

        try:
            from src.mcp_servers.samgov_tools import get_amendments
            amends = await get_amendments(notice_id=notice_id)
            if amends:
                amendments.append({
                    "opportunity_id": opp.get("id", ""),
                    "notice_id": notice_id,
                    "deal_id": opp.get("deal_id", ""),
                    "title": opp.get("title", ""),
                    "amendments": amends if isinstance(amends, list) else [amends],
                })
        except Exception as exc:
            logger.debug("Amendment check failed for %s: %s", notice_id, exc)

    return {
        "amendments_found": amendments,
        "messages": [HumanMessage(content=f"Found {len(amendments)} opportunities with amendments")],
    }


async def detect_changes(state: AlertState) -> dict:
    """Detect material changes: deadline shifts, scope changes, etc."""
    deadline_changes = []
    scope_changes = []

    for opp in state.get("tracked_opportunities", []):
        # Check if stored deadline differs from current SAM.gov data
        stored_deadline = opp.get("response_deadline", "")
        notice_id = opp.get("notice_id", "")

        try:
            from src.mcp_servers.samgov_tools import get_opportunity_detail
            current = await get_opportunity_detail(notice_id=notice_id)
            if not current:
                continue

            current_deadline = current.get("responseDeadLine", current.get("response_deadline", ""))
            if stored_deadline and current_deadline and stored_deadline != current_deadline:
                deadline_changes.append({
                    "opportunity_id": opp.get("id", ""),
                    "notice_id": notice_id,
                    "deal_id": opp.get("deal_id", ""),
                    "title": opp.get("title", ""),
                    "old_deadline": stored_deadline,
                    "new_deadline": current_deadline,
                    "change_type": "deadline_extended" if current_deadline > stored_deadline else "deadline_shortened",
                })

            # Check for significant description/scope changes
            current_desc = current.get("description", "")[:500]
            stored_desc = opp.get("description", "")[:500]
            if current_desc and stored_desc and current_desc != stored_desc:
                scope_changes.append({
                    "opportunity_id": opp.get("id", ""),
                    "notice_id": notice_id,
                    "deal_id": opp.get("deal_id", ""),
                    "title": opp.get("title", ""),
                    "change_type": "scope_modified",
                })

        except Exception as exc:
            logger.debug("Change detection failed for %s: %s", notice_id, exc)

    return {
        "deadline_changes": deadline_changes,
        "scope_changes": scope_changes,
        "messages": [HumanMessage(content=f"Detected {len(deadline_changes)} deadline changes, {len(scope_changes)} scope changes")],
    }


async def generate_alerts(state: AlertState) -> dict:
    """Compile all detected changes into prioritized alerts."""
    alerts = []

    for amend in state.get("amendments_found", []):
        alerts.append({
            "type": "amendment",
            "severity": "high",
            "title": f"Amendment detected: {amend['title']}",
            "deal_id": amend.get("deal_id", ""),
            "opportunity_id": amend.get("opportunity_id", ""),
            "details": amend,
        })

    for change in state.get("deadline_changes", []):
        severity = "high" if change.get("change_type") == "deadline_shortened" else "medium"
        alerts.append({
            "type": "deadline_change",
            "severity": severity,
            "title": f"Deadline {change['change_type']}: {change['title']}",
            "deal_id": change.get("deal_id", ""),
            "opportunity_id": change.get("opportunity_id", ""),
            "details": change,
        })

    for change in state.get("scope_changes", []):
        alerts.append({
            "type": "scope_change",
            "severity": "high",
            "title": f"Scope modified: {change['title']}",
            "deal_id": change.get("deal_id", ""),
            "opportunity_id": change.get("opportunity_id", ""),
            "details": change,
        })

    # Sort by severity
    severity_order = {"high": 0, "medium": 1, "low": 2}
    alerts.sort(key=lambda a: severity_order.get(a.get("severity", "low"), 3))

    return {
        "alerts": alerts,
        "messages": [HumanMessage(content=f"Generated {len(alerts)} alerts")],
    }


def build_alert_graph() -> StateGraph:
    wf = StateGraph(AlertState)
    wf.add_node("load_tracked_opportunities", load_tracked_opportunities)
    wf.add_node("check_amendments", check_amendments)
    wf.add_node("detect_changes", detect_changes)
    wf.add_node("generate_alerts", generate_alerts)
    wf.set_entry_point("load_tracked_opportunities")
    wf.add_edge("load_tracked_opportunities", "check_amendments")
    wf.add_edge("check_amendments", "detect_changes")
    wf.add_edge("detect_changes", "generate_alerts")
    wf.add_edge("generate_alerts", END)
    return wf.compile()


alert_graph = build_alert_graph()


class AlertAgent(BaseAgent):
    """AI agent that monitors opportunities for changes and amendments."""

    agent_name = "alert_agent"

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        initial: AlertState = {
            "tracked_opportunities": [],
            "amendments_found": [],
            "deadline_changes": [],
            "scope_changes": [],
            "alerts": [],
            "messages": [],
        }
        try:
            await self.emit_event("thinking", {"message": "Checking for opportunity changes"})
            result = await alert_graph.ainvoke(initial)
            await self.emit_event("output", {
                "alert_count": len(result["alerts"]),
            })
            return {
                "alerts": result["alerts"],
                "amendments_found": len(result["amendments_found"]),
                "deadline_changes": len(result["deadline_changes"]),
                "scope_changes": len(result["scope_changes"]),
            }
        except Exception as exc:
            logger.exception("AlertAgent.run failed")
            await self.emit_event("error", {"error": str(exc)})
            return {"error": str(exc)}
