"""Compliance Matrix AI Agent using LangGraph.

Builds a detailed compliance matrix from proposal sections, cross-referencing
each RFP requirement against drafted content to identify gaps and risks.

Events: COMPLIANCE_MATRIX_READY, COMPLIANCE_GAPS_FOUND.
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

logger = logging.getLogger("ai_orchestrator.agents.compliance")

DJANGO_API_URL = os.getenv("DJANGO_API_URL", "http://django-api:8001")
DJANGO_SERVICE_TOKEN = os.getenv("DJANGO_SERVICE_TOKEN", "")


# ── State ─────────────────────────────────────────────────────────────────────

class ComplianceState(TypedDict):
    deal_id: str
    deal: dict
    requirements: list[dict]          # From RFP analyst
    drafted_sections: dict            # From proposal writer: {title: text}
    compliance_matrix: list[dict]     # {req_id, req_text, section, status, gap_note}
    gaps: list[dict]                  # Requirements not addressed
    compliance_score: float           # 0.0–1.0
    gap_remediation: str              # Recommendations to fix gaps
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


async def _llm(system: str, human: str, max_tokens: int = 3000) -> str:
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

async def load_compliance_context(state: ComplianceState) -> dict:
    logger.info("ComplianceAgent: loading context for deal %s", state["deal_id"])
    deal = await _get(f"/api/deals/{state['deal_id']}/", default={})
    rfp_reqs = await _get(f"/api/rfp/requirements/?deal={state['deal_id']}&limit=100", default={})
    requirements = rfp_reqs.get("results", []) if isinstance(rfp_reqs, dict) else []
    return {
        "deal": deal,
        "requirements": requirements,
        "messages": [HumanMessage(content=f"Checking compliance for: {deal.get('title', state['deal_id'])}")],
    }


async def cross_reference_requirements(state: ComplianceState) -> dict:
    """Map each requirement to drafted proposal sections."""
    logger.info("ComplianceAgent: cross-referencing requirements for deal %s", state["deal_id"])

    requirements = state.get("requirements") or []
    drafted = state.get("drafted_sections") or {}

    if not requirements:
        return {
            "compliance_matrix": [],
            "gaps": [],
            "compliance_score": 0.0,
            "messages": [HumanMessage(content="No requirements found — matrix empty.")],
        }

    sections_summary = "\n".join(
        f"- {title}: {text[:300]}..." for title, text in drafted.items()
    )

    req_list = "\n".join(
        f"[{r.get('requirement_id', f'REQ-{i}')}] {r.get('requirement_text', '')[:200]}"
        for i, r in enumerate(requirements[:50])
    )

    content = await _llm(
        system=(
            "You are a proposal compliance manager. Map each RFP requirement to the proposal "
            "section that addresses it. Mark each as ADDRESSED, PARTIAL, or NOT_ADDRESSED. "
            "Be precise and specific."
        ),
        human=(
            f"Deal: {state['deal'].get('title', '')}\\n\\n"
            f"Proposal Sections:\\n{sections_summary}\\n\\n"
            f"RFP Requirements ({len(requirements)} total, showing up to 50):\\n{req_list}\\n\\n"
            "For each requirement output a compliance matrix row:\\n"
            "REQ-ID | Requirement Summary (20 words max) | Addressing Section | Status | Gap Note\\n"
            "Status options: ADDRESSED / PARTIAL / NOT_ADDRESSED\\n"
            "Gap Note: blank if ADDRESSED, brief description if PARTIAL or NOT_ADDRESSED."
        ),
        max_tokens=3000,
    )

    matrix = []
    gaps = []
    for line in content.split("\n"):
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 3 and (parts[0].startswith("REQ") or parts[0].startswith("L-") or parts[0].startswith("M-")):
            status = parts[3].strip().upper() if len(parts) > 3 else "ADDRESSED"
            row = {
                "req_id": parts[0],
                "requirement_summary": parts[1] if len(parts) > 1 else "",
                "addressing_section": parts[2] if len(parts) > 2 else "",
                "status": status,
                "gap_note": parts[4] if len(parts) > 4 else "",
            }
            matrix.append(row)
            if status in ("PARTIAL", "NOT_ADDRESSED"):
                gaps.append(row)

    if not matrix:
        matrix = [{"raw_analysis": content}]

    addressed = sum(1 for r in matrix if r.get("status") == "ADDRESSED")
    score = addressed / len(matrix) if matrix else 0.0

    return {
        "compliance_matrix": matrix,
        "gaps": gaps,
        "compliance_score": round(score, 3),
        "messages": [HumanMessage(content=f"Compliance matrix: {len(matrix)} rows, {len(gaps)} gaps, score={score:.1%}.")],
    }


async def generate_gap_remediation(state: ComplianceState) -> dict:
    """Generate specific remediation instructions for each compliance gap."""
    logger.info("ComplianceAgent: generating gap remediation for deal %s", state["deal_id"])

    gaps = state.get("gaps") or []
    if not gaps:
        return {
            "gap_remediation": "No compliance gaps identified. Proposal appears fully compliant.",
            "messages": [HumanMessage(content="No gaps — no remediation needed.")],
        }

    gap_list = "\n".join(
        f"- [{g['req_id']}] {g.get('requirement_summary', '')} — {g.get('gap_note', 'Not addressed')}"
        for g in gaps[:20]
    )

    content = await _llm(
        system=(
            "You are a proposal compliance specialist. For each compliance gap, provide specific "
            "actionable instructions to add or strengthen the proposal content to achieve full compliance."
        ),
        human=(
            f"Opportunity: {state['deal'].get('title', '')}\\n\\n"
            f"Compliance Gaps ({len(gaps)} total):\\n{gap_list}\\n\\n"
            "For each gap provide:\\n"
            "1. Which proposal section to update\\n"
            "2. Specific content to add (2-3 sentences)\\n"
            "3. Priority: HIGH / MEDIUM / LOW\\n\\n"
            "Also provide an overall compliance improvement plan."
        ),
        max_tokens=2000,
    )

    return {
        "gap_remediation": content,
        "messages": [HumanMessage(content=f"Gap remediation generated for {len(gaps)} gap(s).")],
    }


# ── Graph ─────────────────────────────────────────────────────────────────────

def build_compliance_graph() -> StateGraph:
    wf = StateGraph(ComplianceState)
    wf.add_node("load_compliance_context", load_compliance_context)
    wf.add_node("cross_reference_requirements", cross_reference_requirements)
    wf.add_node("generate_gap_remediation", generate_gap_remediation)
    wf.set_entry_point("load_compliance_context")
    wf.add_edge("load_compliance_context", "cross_reference_requirements")
    wf.add_edge("cross_reference_requirements", "generate_gap_remediation")
    wf.add_edge("generate_gap_remediation", END)
    return wf.compile()


compliance_graph = build_compliance_graph()


# ── Agent ─────────────────────────────────────────────────────────────────────

class ComplianceAgent(BaseAgent):
    """AI agent that builds compliance matrices and identifies proposal gaps."""

    agent_name = "compliance_agent"

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        deal_id = input_data.get("deal_id", "")
        if not deal_id:
            return {"error": "deal_id is required"}

        initial: ComplianceState = {
            "deal_id": deal_id,
            "deal": {},
            "requirements": input_data.get("requirements", []),
            "drafted_sections": input_data.get("drafted_sections", {}),
            "compliance_matrix": [],
            "gaps": [],
            "compliance_score": 0.0,
            "gap_remediation": "",
            "messages": [],
        }
        try:
            await self.emit_event(
                "thinking",
                {"message": f"Building compliance matrix for deal {deal_id}"},
                execution_id=deal_id,
            )
            fs = await compliance_graph.ainvoke(initial)
            await self.emit_event(
                "output",
                {
                    "compliance_score": fs["compliance_score"],
                    "gaps_count": len(fs["gaps"]),
                },
                execution_id=deal_id,
            )
            return {
                "deal_id": fs["deal_id"],
                "compliance_matrix": fs["compliance_matrix"],
                "gaps": fs["gaps"],
                "compliance_score": fs["compliance_score"],
                "gap_remediation": fs["gap_remediation"],
            }
        except Exception as exc:
            logger.exception("ComplianceAgent.run failed for deal %s", deal_id)
            await self.emit_event("error", {"error": str(exc)}, execution_id=deal_id)
            return {"error": str(exc), "deal_id": deal_id}
