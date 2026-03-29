"""
Continuous ATO (Authority to Operate) Monitoring Agent.

Monitors active contracts for ongoing compliance with security frameworks.
Detects drift, collects evidence, manages POAMs, and tracks ATO renewal timelines.
"""

import logging
import os
from typing import Any

import httpx
from src.llm_provider import get_chat_model
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from typing_extensions import TypedDict

from src.agents.base import BaseAgent

logger = logging.getLogger("ai_orchestrator.agents.ato")

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


def _get_llm():
    return get_chat_model(max_tokens=4096)


class ATOState(TypedDict):
    contract_id: str
    contract: dict
    compliance_reports: list[dict]
    drift_findings: list[dict]
    evidence_collected: list[dict]
    poam_items: list[dict]
    remediation_plan: dict
    overall_health: dict
    messages: list


async def load_compliance_context(state: ATOState) -> dict:
    """Load contract and compliance data."""
    contract_id = state.get("contract_id", "")

    contract = await _get(f"/api/contracts/{contract_id}/", default={})
    reports = await _get(
        f"/api/security-compliance/reports/?contract={contract_id}",
        default={},
    )

    return {
        "contract": contract,
        "compliance_reports": reports.get("results", []) if isinstance(reports, dict) else [],
        "messages": [HumanMessage(content=f"Loaded compliance context for contract {contract_id}")],
    }


async def detect_drift(state: ATOState) -> dict:
    """Run drift detection on the contract."""
    findings = []

    contract = state.get("contract", {})
    reports = state.get("compliance_reports", [])

    # Check assessment freshness
    if reports:
        latest = reports[0]
        from datetime import datetime
        created = latest.get("created_at", "")
        if created:
            try:
                dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                days_old = (datetime.now(dt.tzinfo) - dt).days
                if days_old > 90:
                    findings.append({
                        "type": "stale_assessment",
                        "severity": "medium" if days_old < 180 else "high",
                        "description": f"Last assessment is {days_old} days old",
                        "remediation": "Schedule reassessment",
                    })
            except Exception:
                pass
    else:
        findings.append({
            "type": "no_assessment",
            "severity": "high",
            "description": "No compliance assessment found",
            "remediation": "Perform initial assessment",
        })

    return {
        "drift_findings": findings,
        "messages": [HumanMessage(content=f"Found {len(findings)} drift issues")],
    }


async def collect_evidence(state: ATOState) -> dict:
    """Attempt to collect automated evidence."""
    evidence = []
    contract_id = state.get("contract_id", "")

    # Check audit trail
    audit_data = await _get(
        f"/api/core/audit-logs/?entity_id={contract_id}&limit=5",
        default={},
    )
    audit_count = audit_data.get("count", 0) if isinstance(audit_data, dict) else 0
    evidence.append({
        "type": "audit_trail",
        "control_family": "AU",
        "status": "collected" if audit_count > 0 else "gap",
        "detail": f"{audit_count} audit events found",
    })

    return {
        "evidence_collected": evidence,
        "messages": [HumanMessage(content=f"Collected {len(evidence)} evidence items")],
    }


async def generate_remediation(state: ATOState) -> dict:
    """Generate remediation plan for drift findings."""
    findings = state.get("drift_findings", [])
    if not findings:
        return {
            "remediation_plan": {"status": "clean", "items": []},
            "poam_items": [],
            "overall_health": {"score": 100, "risk_level": "low"},
            "messages": [HumanMessage(content="No remediation needed")],
        }

    llm = _get_llm()
    try:
        resp = await llm.ainvoke([
            SystemMessage(content=(
                "You are a cybersecurity compliance officer. Generate a remediation plan "
                "for the compliance drift findings. For each finding, provide:\n"
                "1. POAM item with milestone dates\n"
                "2. Responsible party (role, not person)\n"
                "3. Priority (1=immediate, 2=30 days, 3=90 days)\n"
                "4. Resources needed\n"
                "Be specific and actionable."
            )),
            HumanMessage(content=(
                f"Contract: {state.get('contract', {}).get('title', 'N/A')}\n\n"
                f"Drift Findings:\n{findings}\n\n"
                f"Evidence Status:\n{state.get('evidence_collected', [])}\n\n"
                "Generate remediation plan."
            )),
        ])
        plan_text = resp.content
    except Exception as exc:
        logger.error("Remediation plan generation failed: %s", exc)
        plan_text = "Manual remediation plan required."

    # Compute health score
    score = 100
    for f in findings:
        sev = f.get("severity", "low")
        if sev == "critical":
            score -= 25
        elif sev == "high":
            score -= 15
        elif sev == "medium":
            score -= 8
    score = max(0, score)

    risk = "low"
    if score < 50:
        risk = "critical"
    elif score < 70:
        risk = "high"
    elif score < 85:
        risk = "medium"

    poam_items = [
        {
            "finding": f.get("description", ""),
            "severity": f.get("severity", "medium"),
            "remediation": f.get("remediation", ""),
            "status": "open",
        }
        for f in findings
    ]

    return {
        "remediation_plan": {"text": plan_text, "items": poam_items},
        "poam_items": poam_items,
        "overall_health": {"score": score, "risk_level": risk},
        "messages": [HumanMessage(content=f"Health score: {score} ({risk})")],
    }


def build_ato_graph() -> StateGraph:
    wf = StateGraph(ATOState)
    wf.add_node("load_compliance_context", load_compliance_context)
    wf.add_node("detect_drift", detect_drift)
    wf.add_node("collect_evidence", collect_evidence)
    wf.add_node("generate_remediation", generate_remediation)
    wf.set_entry_point("load_compliance_context")
    wf.add_edge("load_compliance_context", "detect_drift")
    wf.add_edge("detect_drift", "collect_evidence")
    wf.add_edge("collect_evidence", "generate_remediation")
    wf.add_edge("generate_remediation", END)
    return wf.compile()


ato_graph = build_ato_graph()


class ATOAgent(BaseAgent):
    """AI agent for continuous ATO monitoring."""

    agent_name = "ato_agent"

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        contract_id = input_data.get("contract_id", input_data.get("deal_id", ""))
        if not contract_id:
            return {"error": "contract_id or deal_id is required"}

        initial: ATOState = {
            "contract_id": contract_id,
            "contract": {},
            "compliance_reports": [],
            "drift_findings": [],
            "evidence_collected": [],
            "poam_items": [],
            "remediation_plan": {},
            "overall_health": {},
            "messages": [],
        }
        try:
            await self.emit_event("thinking", {"message": f"ATO monitoring for {contract_id}"})
            result = await ato_graph.ainvoke(initial)
            await self.emit_event("output", {
                "health": result.get("overall_health", {}),
                "findings": len(result.get("drift_findings", [])),
            })
            return {
                "contract_id": contract_id,
                "drift_findings": result.get("drift_findings", []),
                "evidence_collected": result.get("evidence_collected", []),
                "poam_items": result.get("poam_items", []),
                "remediation_plan": result.get("remediation_plan", {}),
                "overall_health": result.get("overall_health", {}),
            }
        except Exception as exc:
            logger.exception("ATOAgent.run failed")
            await self.emit_event("error", {"error": str(exc)})
            return {"error": str(exc)}
