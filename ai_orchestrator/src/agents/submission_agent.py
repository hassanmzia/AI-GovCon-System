"""Submission Package AI Agent using LangGraph.

Assembles the final proposal submission package, verifies all required files
are present, generates a submission checklist, and validates against RFP
requirements before final delivery.

Events: SUBMISSION_PACKAGED, SUBMISSION_CHECKLIST_READY.
"""
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

logger = logging.getLogger("ai_orchestrator.agents.submission")

DJANGO_API_URL = os.getenv("DJANGO_API_URL", "http://django-api:8001")
DJANGO_SERVICE_TOKEN = os.getenv("DJANGO_SERVICE_TOKEN", "")

# Standard proposal volumes and required contents
_REQUIRED_VOLUMES = [
    "Volume I - Technical Approach",
    "Volume II - Management Approach",
    "Volume III - Past Performance",
    "Volume IV - Price/Cost",
]

_STANDARD_ATTACHMENTS = [
    "Cover Letter / Transmittal",
    "Table of Contents",
    "Executive Summary",
    "Representations and Certifications",
    "Small Business Subcontracting Plan",
    "Resumes / Key Personnel",
    "Teaming Agreements",
    "Price Breakdown / Cost Detail",
]


# ── State ─────────────────────────────────────────────────────────────────────

class SubmissionState(TypedDict):
    deal_id: str
    deal: dict
    opportunity: dict
    proposal_sections: dict          # {title: text} — final approved sections
    compliance_matrix: list[dict]    # From compliance agent
    qa_summary: str                  # From QA agent
    key_dates: dict                  # From RFP analyst
    page_limits: dict                # From RFP analyst
    checklist: list[dict]            # [{item, status, notes}]
    missing_items: list[str]         # Items not yet complete
    submission_package_summary: str  # Final summary of what is ready
    submission_risks: list[str]      # Risks to address before submission
    messages: Annotated[list, operator.add]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _auth_headers() -> dict[str, str]:
    t = DJANGO_SERVICE_TOKEN
    return {"Authorization": f"Bearer {t}"} if t else {}


async def _get(path: str, default: Any = None) -> Any:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{DJANGO_API_URL}{path}", headers=_auth_headers())
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.warning("API GET %s failed: %s", path, exc)
        return default


async def _llm(system: str, human: str, max_tokens: int = 2500) -> str:
    try:
        llm = ChatAnthropic(
            model="claude-sonnet-4-6",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            max_tokens=max_tokens,
        )
        resp = await llm.ainvoke([SystemMessage(content=system), HumanMessage(content=human)])
        return resp.content
    except Exception as exc:
        logger.error("LLM failed: %s", exc)
        return ""


# ── Graph nodes ───────────────────────────────────────────────────────────────

async def load_submission_context(state: SubmissionState) -> dict:
    logger.info("SubmissionAgent: loading context for deal %s", state["deal_id"])
    deal = await _get(f"/api/deals/{state['deal_id']}/", default={})
    opp_id = deal.get("opportunity", "")
    opportunity = await _get(f"/api/opportunities/{opp_id}/", default={}) if opp_id else {}
    rfp_reqs = await _get(f"/api/rfp/requirements/?deal={state['deal_id']}&limit=5", default={})
    key_dates = rfp_reqs.get("key_dates", {}) if isinstance(rfp_reqs, dict) else {}
    page_limits = rfp_reqs.get("page_limits", {}) if isinstance(rfp_reqs, dict) else {}
    return {
        "deal": deal,
        "opportunity": opportunity,
        "key_dates": key_dates,
        "page_limits": page_limits,
        "messages": [HumanMessage(content=f"Building submission package for: {deal.get('title', state['deal_id'])}")],
    }


async def build_submission_checklist(state: SubmissionState) -> dict:
    """Generate a comprehensive submission checklist."""
    logger.info("SubmissionAgent: building checklist for deal %s", state["deal_id"])

    proposal_sections = state.get("proposal_sections") or {}
    present_sections = set(proposal_sections.keys())

    checklist = []
    missing = []

    # Check required volumes
    for vol in _REQUIRED_VOLUMES:
        found = any(vol.lower() in s.lower() or s.lower() in vol.lower() for s in present_sections)
        status = "COMPLETE" if found else "MISSING"
        checklist.append({"item": vol, "status": status, "notes": ""})
        if not found:
            missing.append(vol)

    # Check standard attachments
    for attach in _STANDARD_ATTACHMENTS:
        found = any(attach.lower() in s.lower() for s in present_sections)
        status = "COMPLETE" if found else "PENDING"
        checklist.append({"item": attach, "status": status, "notes": "Verify with contracting team"})
        if not found:
            missing.append(attach)

    # Check compliance matrix
    if state.get("compliance_matrix"):
        checklist.append({"item": "Compliance Matrix", "status": "COMPLETE", "notes": f"{len(state['compliance_matrix'])} requirements mapped"})
    else:
        checklist.append({"item": "Compliance Matrix", "status": "MISSING", "notes": "Run compliance agent first"})
        missing.append("Compliance Matrix")

    # Check QA
    qa_done = bool(state.get("qa_summary"))
    checklist.append({
        "item": "QA Review",
        "status": "COMPLETE" if qa_done else "PENDING",
        "notes": "PASS" if "PASS" in (state.get("qa_summary") or "") else "Review pending"
    })
    if not qa_done:
        missing.append("QA Review")

    return {
        "checklist": checklist,
        "missing_items": missing,
        "messages": [HumanMessage(content=f"Checklist built: {len(checklist)} items, {len(missing)} missing.")],
    }


async def validate_submission_readiness(state: SubmissionState) -> dict:
    """Use Claude to perform a final submission readiness assessment."""
    logger.info("SubmissionAgent: validating readiness for deal %s", state["deal_id"])

    checklist = state.get("checklist") or []
    missing = state.get("missing_items") or []
    key_dates = state.get("key_dates") or {}

    complete_count = sum(1 for item in checklist if item.get("status") == "COMPLETE")
    total_count = len(checklist)

    content = await _llm(
        system=(
            "You are a proposal submission manager. Assess whether a proposal submission package "
            "is ready for delivery. Identify risks and required actions."
        ),
        human=(
            f"Opportunity: {state['opportunity'].get('title', state['deal_id'])}\n"
            f"Key Dates: {key_dates}\n\n"
            f"Submission Checklist: {complete_count}/{total_count} items complete\n\n"
            f"Missing Items:\n" + "\n".join(f"- {item}" for item in missing[:10])
            + f"\n\nQA Status: {(state.get('qa_summary') or 'Not run')[:200]}\n\n"
            "Provide:\n"
            "1. SUBMISSION_READY: YES or NO\n"
            "2. Top 5 risks if submitted as-is\n"
            "3. Critical action items (must be done before submission)\n"
            "4. Nice-to-have improvements (can wait)\n"
            "5. Estimated submission readiness percentage"
        ),
        max_tokens=1500,
    )

    # Extract risks from content
    risks = []
    in_risks = False
    for line in content.split("\n"):
        stripped = line.strip()
        if "risk" in stripped.lower() and ("top" in stripped.lower() or "5" in stripped):
            in_risks = True
            continue
        if in_risks and stripped.startswith(("-", "•", "*", "1.", "2.", "3.", "4.", "5.")):
            risk_text = stripped.lstrip("-•*0123456789. ").strip()
            if risk_text:
                risks.append(risk_text)
            if len(risks) >= 5:
                in_risks = False

    return {
        "submission_risks": risks,
        "submission_package_summary": content,
        "messages": [HumanMessage(content=f"Readiness validated: {complete_count}/{total_count} complete.")],
    }


# ── Graph ─────────────────────────────────────────────────────────────────────

def build_submission_graph() -> StateGraph:
    wf = StateGraph(SubmissionState)
    wf.add_node("load_submission_context", load_submission_context)
    wf.add_node("build_submission_checklist", build_submission_checklist)
    wf.add_node("validate_submission_readiness", validate_submission_readiness)
    wf.set_entry_point("load_submission_context")
    wf.add_edge("load_submission_context", "build_submission_checklist")
    wf.add_edge("build_submission_checklist", "validate_submission_readiness")
    wf.add_edge("validate_submission_readiness", END)
    return wf.compile()


submission_graph = build_submission_graph()


# ── Agent ─────────────────────────────────────────────────────────────────────

class SubmissionAgent(BaseAgent):
    """AI agent that assembles and validates the proposal submission package."""

    agent_name = "submission_agent"

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        deal_id = input_data.get("deal_id", "")
        if not deal_id:
            return {"error": "deal_id is required"}

        initial: SubmissionState = {
            "deal_id": deal_id,
            "deal": {},
            "opportunity": {},
            "proposal_sections": input_data.get("proposal_sections", {}),
            "compliance_matrix": input_data.get("compliance_matrix", []),
            "qa_summary": input_data.get("qa_summary", ""),
            "key_dates": input_data.get("key_dates", {}),
            "page_limits": input_data.get("page_limits", {}),
            "checklist": [],
            "missing_items": [],
            "submission_package_summary": "",
            "submission_risks": [],
            "messages": [],
        }
        try:
            await self.emit_event(
                "thinking",
                {"message": f"Assembling submission package for deal {deal_id}"},
                execution_id=deal_id,
            )
            fs = await submission_graph.ainvoke(initial)
            await self.emit_event(
                "output",
                {
                    "checklist_count": len(fs["checklist"]),
                    "missing_count": len(fs["missing_items"]),
                },
                execution_id=deal_id,
            )
            return {
                "deal_id": fs["deal_id"],
                "checklist": fs["checklist"],
                "missing_items": fs["missing_items"],
                "submission_package_summary": fs["submission_package_summary"],
                "submission_risks": fs["submission_risks"],
            }
        except Exception as exc:
            logger.exception("SubmissionAgent.run failed for deal %s", deal_id)
            await self.emit_event("error", {"error": str(exc)}, execution_id=deal_id)
            return {"error": str(exc), "deal_id": deal_id}
