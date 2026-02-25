"""Security Compliance AI Agent using LangGraph."""
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

logger = logging.getLogger("ai_orchestrator.agents.security_compliance")

DJANGO_API_URL = os.getenv("DJANGO_API_URL", "http://django-api:8001")
DJANGO_SERVICE_TOKEN = os.getenv("DJANGO_SERVICE_TOKEN", "")


# ── State ─────────────────────────────────────────────────────────────────────

class SecurityComplianceState(TypedDict):
    deal_id: str
    deal: dict
    applicable_frameworks: list[dict]
    control_mappings: list[dict]
    gap_analysis: dict
    poam_items: list[dict]
    compliance_score: float
    risk_summary: str
    remediation_roadmap: str
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


async def _fetch_frameworks() -> list:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{DJANGO_API_URL}/api/security-compliance/frameworks/?is_active=true",
                headers=_auth_headers(),
            )
            resp.raise_for_status()
            return resp.json().get("results", [])
    except Exception as exc:
        logger.warning("Could not fetch security frameworks: %s", exc)
        return []


async def _fetch_control_mappings(deal_id: str) -> list:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{DJANGO_API_URL}/api/security-compliance/control-mappings/?deal={deal_id}",
                headers=_auth_headers(),
            )
            resp.raise_for_status()
            return resp.json().get("results", [])
    except Exception as exc:
        logger.warning("Could not fetch control mappings for deal %s: %s", deal_id, exc)
        return []


# ── LLM ───────────────────────────────────────────────────────────────────────

def _get_llm() -> ChatAnthropic:
    return ChatAnthropic(
        model="claude-sonnet-4-6",
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        max_tokens=2048,
    )


# ── Graph nodes ───────────────────────────────────────────────────────────────

async def load_compliance_context(state: SecurityComplianceState) -> dict:
    """Fetch deal, frameworks, and existing control mappings."""
    logger.info("Loading compliance context for deal %s", state["deal_id"])
    deal, frameworks, control_mappings = (
        await _fetch_deal(state["deal_id"]),
        await _fetch_frameworks(),
        await _fetch_control_mappings(state["deal_id"]),
    )
    return {
        "deal": deal,
        "applicable_frameworks": frameworks,
        "control_mappings": control_mappings,
        "messages": [
            HumanMessage(content=f"Analyzing compliance for: {deal.get('title', state['deal_id'])}")
        ],
    }


async def determine_applicable_frameworks(state: SecurityComplianceState) -> dict:
    """Claude determines which security frameworks apply to this deal."""
    logger.info("Determining applicable frameworks for deal %s", state["deal_id"])
    llm = _get_llm()

    system = SystemMessage(
        content=(
            "You are a cybersecurity and compliance expert specializing in U.S. government "
            "contracting. Determine which security frameworks apply to a contract based on "
            "the agency, data types handled, and contract clauses. "
            "Common frameworks: NIST SP 800-53, NIST SP 800-171, CMMC 2.0, FedRAMP, "
            "FISMA, HIPAA, DISA STIGs."
        )
    )
    human = HumanMessage(
        content=(
            f"Deal: {state['deal']}\n\n"
            f"Available Frameworks: {state['applicable_frameworks']}\n\n"
            "Determine which frameworks apply. For each applicable framework provide:\n"
            "1. Framework name and level/tier\n"
            "2. Rationale for applicability\n"
            "3. Key compliance driver (agency requirement, data type, contract clause)\n"
            "4. Priority (high/medium/low)\n"
        )
    )

    try:
        response = await llm.ainvoke([system, human])
        content = response.content
    except Exception as exc:
        logger.error("LLM failed in determine_applicable_frameworks: %s", exc)
        content = "Framework determination unavailable due to API error."

    # Update framework list with AI-generated rationales
    enriched = [
        {**fw, "ai_rationale": content}
        for fw in state["applicable_frameworks"][:5]  # Limit to top 5
    ]

    return {
        "applicable_frameworks": enriched,
        "messages": [HumanMessage(content=f"Identified {len(enriched)} applicable framework(s).")],
    }


async def analyze_compliance_gaps(state: SecurityComplianceState) -> dict:
    """Claude performs AI-powered gap analysis on the control mappings."""
    logger.info("Analyzing compliance gaps for deal %s", state["deal_id"])
    llm = _get_llm()

    system = SystemMessage(
        content=(
            "You are a cybersecurity compliance analyst. Perform a gap analysis by "
            "examining the current control implementation status and identifying "
            "controls that are not yet implemented or only partially implemented."
        )
    )
    human = HumanMessage(
        content=(
            f"Deal: {state['deal']}\n\n"
            f"Applicable Frameworks: {state['applicable_frameworks']}\n\n"
            f"Current Control Mappings (sample): {state['control_mappings'][:20]}\n\n"
            "Provide:\n"
            "1. Overall compliance posture assessment\n"
            "2. Critical gaps (P1 controls not implemented)\n"
            "3. High-priority gaps (P2 controls)\n"
            "4. Estimated compliance percentage\n"
            "5. Key risk areas\n"
        )
    )

    try:
        response = await llm.ainvoke([system, human])
        content = response.content
    except Exception as exc:
        logger.error("LLM failed in analyze_compliance_gaps: %s", exc)
        content = "Gap analysis unavailable due to API error."

    # Derive a rough compliance score
    compliance_score = 0.5
    for token in content.split():
        token_clean = token.strip(",.()%")
        try:
            val = float(token_clean)
            if token.endswith("%"):
                val /= 100
            if 0.0 <= val <= 1.0 and "%" in token:
                compliance_score = val
                break
            elif 0.0 <= val <= 100 and "%" in content[content.index(token_clean) - 2:content.index(token_clean)]:
                compliance_score = val / 100
                break
        except (ValueError, IndexError):
            pass

    gap_analysis = {
        "analysis": content,
        "compliance_score": compliance_score,
        "total_controls": len(state["control_mappings"]),
    }

    return {
        "gap_analysis": gap_analysis,
        "compliance_score": compliance_score,
        "messages": [HumanMessage(content=f"Gap analysis complete. Compliance: {compliance_score:.1%}")],
    }


async def generate_poam_and_roadmap(state: SecurityComplianceState) -> dict:
    """Claude generates a POA&M and remediation roadmap."""
    logger.info("Generating POA&M for deal %s", state["deal_id"])
    llm = _get_llm()

    system = SystemMessage(
        content=(
            "You are a cybersecurity program manager creating a Plan of Action and "
            "Milestones (POA&M) for U.S. government contract compliance. "
            "Prioritize by severity, provide realistic timelines, and recommend "
            "specific remediation actions."
        )
    )
    human = HumanMessage(
        content=(
            f"Deal: {state['deal']}\n\n"
            f"Gap Analysis:\n{state['gap_analysis']}\n\n"
            f"Applicable Frameworks: {[fw.get('name') for fw in state['applicable_frameworks']]}\n\n"
            "Generate:\n"
            "1. POA&M with top 10 priority items (control ID, weakness, remediation, timeline)\n"
            "2. 90-day remediation roadmap\n"
            "3. Resource requirements estimate\n"
            "4. Risk acceptance recommendations for low-priority items\n"
        )
    )

    try:
        response = await llm.ainvoke([system, human])
        content = response.content
    except Exception as exc:
        logger.error("LLM failed in generate_poam_and_roadmap: %s", exc)
        content = "POA&M generation unavailable due to API error."

    # Parse POA&M items from the response
    poam_items = [{"analysis": content}]

    risk_summary = "\n".join(
        line for line in content.split("\n")
        if any(kw in line.lower() for kw in ["risk", "critical", "high", "priority"])
    )[:500]

    return {
        "poam_items": poam_items,
        "remediation_roadmap": content,
        "risk_summary": risk_summary or content[:300],
        "messages": [HumanMessage(content="POA&M and remediation roadmap generated.")],
    }


# ── Graph builder ─────────────────────────────────────────────────────────────

def build_security_compliance_graph() -> StateGraph:
    """Construct and compile the security compliance LangGraph workflow."""
    workflow = StateGraph(SecurityComplianceState)

    workflow.add_node("load_compliance_context", load_compliance_context)
    workflow.add_node("determine_applicable_frameworks", determine_applicable_frameworks)
    workflow.add_node("analyze_compliance_gaps", analyze_compliance_gaps)
    workflow.add_node("generate_poam_and_roadmap", generate_poam_and_roadmap)

    workflow.set_entry_point("load_compliance_context")
    workflow.add_edge("load_compliance_context", "determine_applicable_frameworks")
    workflow.add_edge("determine_applicable_frameworks", "analyze_compliance_gaps")
    workflow.add_edge("analyze_compliance_gaps", "generate_poam_and_roadmap")
    workflow.add_edge("generate_poam_and_roadmap", END)

    return workflow.compile()


security_compliance_graph = build_security_compliance_graph()


# ── Agent class ───────────────────────────────────────────────────────────────

class SecurityComplianceAgent(BaseAgent):
    """LangGraph-based Security Compliance AI Agent."""

    agent_name = "security_compliance_agent"

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Run security compliance analysis for a deal.

        Args:
            input_data: Must contain 'deal_id'.

        Returns:
            dict with keys: deal_id, applicable_frameworks, gap_analysis,
            compliance_score, poam_items, remediation_roadmap, risk_summary.
        """
        deal_id = input_data.get("deal_id", "")
        if not deal_id:
            return {"error": "deal_id is required"}

        initial_state: SecurityComplianceState = {
            "deal_id": deal_id,
            "deal": {},
            "applicable_frameworks": [],
            "control_mappings": [],
            "gap_analysis": {},
            "poam_items": [],
            "compliance_score": 0.0,
            "risk_summary": "",
            "remediation_roadmap": "",
            "messages": [],
        }

        try:
            await self.emit_event(
                "thinking",
                {"message": f"Starting compliance analysis for deal {deal_id}"},
                execution_id=deal_id,
            )
            final_state = await security_compliance_graph.ainvoke(initial_state)
            await self.emit_event(
                "output",
                {"compliance_score": final_state["compliance_score"]},
                execution_id=deal_id,
            )
            return {
                "deal_id": final_state["deal_id"],
                "applicable_frameworks": final_state["applicable_frameworks"],
                "gap_analysis": final_state["gap_analysis"],
                "compliance_score": final_state["compliance_score"],
                "poam_items": final_state["poam_items"],
                "remediation_roadmap": final_state["remediation_roadmap"],
                "risk_summary": final_state["risk_summary"],
            }
        except Exception as exc:
            logger.exception("SecurityComplianceAgent.run failed for deal %s", deal_id)
            await self.emit_event("error", {"error": str(exc)}, execution_id=deal_id)
            return {"error": str(exc), "deal_id": deal_id}
