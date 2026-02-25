"""Business Legal Agent using LangGraph (ReAct pattern)."""
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

logger = logging.getLogger("ai_orchestrator.agents.legal")

DJANGO_API_URL = os.getenv("DJANGO_API_URL", "http://django-api:8001")
DJANGO_SERVICE_TOKEN = os.getenv("DJANGO_SERVICE_TOKEN", "")


# ── State ─────────────────────────────────────────────────────────────────────

class LegalState(TypedDict):
    deal_id: str
    rfp_text: str
    contract_text: str
    review_type: str  # "rfp_review" | "contract_review" | "far_compliance" | "oci_assessment"
    risks_identified: list[dict]
    far_clauses: list[str]
    compliance_gaps: list[str]
    recommendations: list[str]
    overall_risk_level: str  # "low" | "medium" | "high" | "critical"
    oci_findings: str
    messages: Annotated[list, operator.add]


# ── LLM ───────────────────────────────────────────────────────────────────────

def _get_llm() -> ChatAnthropic:
    return ChatAnthropic(
        model="claude-sonnet-4-6",
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        max_tokens=3000,
    )


# ── Django API helper ─────────────────────────────────────────────────────────

def _auth_headers() -> dict[str, str]:
    token = DJANGO_SERVICE_TOKEN
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


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


# ── Graph nodes ───────────────────────────────────────────────────────────────

async def identify_legal_requirements(state: LegalState) -> dict:
    """Extract all legal requirements from RFP/contract text."""
    logger.info("Identifying legal requirements for deal %s", state["deal_id"])
    llm = _get_llm()

    document_text = state.get("rfp_text") or state.get("contract_text") or ""
    review_type = state.get("review_type", "rfp_review")

    if not document_text:
        return {
            "messages": [
                HumanMessage(content="No document text provided. Proceeding with general review.")
            ]
        }

    system = SystemMessage(
        content=(
            "You are a senior government contracts attorney with expertise in FAR/DFARS, "
            "federal acquisition regulations, and government contracting law. "
            "Identify all legal requirements, obligations, and constraints in the provided document."
        )
    )
    human = HumanMessage(
        content=(
            f"Review Type: {review_type}\n"
            f"Deal ID: {state['deal_id']}\n\n"
            f"Document Text:\n{document_text[:8000]}\n\n"
            "Identify all legal requirements including:\n"
            "1. Mandatory clauses and provisions\n"
            "2. Certification requirements\n"
            "3. Reporting obligations\n"
            "4. Performance standards\n"
            "5. Compliance requirements\n"
            "List each requirement clearly."
        )
    )

    try:
        response = await llm.ainvoke([system, human])
        content = response.content
    except Exception as exc:
        logger.error("LLM call failed in identify_legal_requirements: %s", exc)
        content = "Legal requirements identification unavailable due to API error."

    return {
        "messages": [HumanMessage(content=f"Legal requirements identified:\n{content}")],
    }


async def check_far_compliance(state: LegalState) -> dict:
    """Check against FAR/DFARS requirements."""
    logger.info("Checking FAR/DFARS compliance for deal %s", state["deal_id"])
    llm = _get_llm()

    document_text = state.get("rfp_text") or state.get("contract_text") or ""

    system = SystemMessage(
        content=(
            "You are a FAR/DFARS compliance expert. Analyze the document for compliance with "
            "Federal Acquisition Regulations. Identify applicable FAR/DFARS clauses, "
            "compliance gaps, and mandatory requirements."
        )
    )
    human = HumanMessage(
        content=(
            f"Review Type: {state['review_type']}\n\n"
            f"Document Text:\n{document_text[:6000] if document_text else 'No document provided.'}\n\n"
            "Provide FAR/DFARS compliance analysis:\n"
            "1. List applicable FAR/DFARS clause numbers (e.g., FAR 52.212-4, DFARS 252.204-7012)\n"
            "2. Identify any compliance gaps\n"
            "3. Flag missing mandatory clauses\n"
            "4. Note any unusual or onerous clauses\n\n"
            "Format FAR clauses as a comma-separated list on a line starting with 'FAR CLAUSES:'"
        )
    )

    try:
        response = await llm.ainvoke([system, human])
        content = response.content
    except Exception as exc:
        logger.error("LLM call failed in check_far_compliance: %s", exc)
        content = "FAR compliance check unavailable due to API error."

    # Parse FAR clauses from response
    far_clauses = []
    compliance_gaps = []
    for line in content.split("\n"):
        line = line.strip()
        if line.upper().startswith("FAR CLAUSES:"):
            clauses_raw = line.split(":", 1)[-1].strip()
            far_clauses = [c.strip() for c in clauses_raw.split(",") if c.strip()]
        elif "gap" in line.lower() or "missing" in line.lower() or "required" in line.lower():
            if line and not line.startswith("#"):
                compliance_gaps.append(line)

    return {
        "far_clauses": far_clauses,
        "compliance_gaps": compliance_gaps,
        "messages": [HumanMessage(content=f"FAR compliance check complete. Found {len(far_clauses)} clauses, {len(compliance_gaps)} gaps.")],
    }


async def assess_risks(state: LegalState) -> dict:
    """Identify legal risks and classify severity."""
    logger.info("Assessing legal risks for deal %s", state["deal_id"])
    llm = _get_llm()

    document_text = state.get("rfp_text") or state.get("contract_text") or ""
    compliance_gaps_text = "\n".join(state.get("compliance_gaps", []))
    far_clauses_text = ", ".join(state.get("far_clauses", []))

    system = SystemMessage(
        content=(
            "You are a risk management attorney specializing in government contracts. "
            "Identify, categorize, and assess legal risks in government contract documents. "
            "Classify each risk by severity: low, medium, high, or critical."
        )
    )
    human = HumanMessage(
        content=(
            f"Deal ID: {state['deal_id']}\n"
            f"Review Type: {state['review_type']}\n"
            f"FAR Clauses Found: {far_clauses_text or 'None identified'}\n"
            f"Compliance Gaps: {compliance_gaps_text or 'None identified'}\n\n"
            f"Document Text:\n{document_text[:5000] if document_text else 'No document provided.'}\n\n"
            "Identify all legal risks. For each risk provide:\n"
            "- risk_name: Short descriptive name\n"
            "- severity: low|medium|high|critical\n"
            "- description: What the risk is\n"
            "- impact: Potential business impact\n\n"
            "Also provide OVERALL_RISK_LEVEL: low|medium|high|critical on its own line."
        )
    )

    try:
        response = await llm.ainvoke([system, human])
        content = response.content
    except Exception as exc:
        logger.error("LLM call failed in assess_risks: %s", exc)
        content = "OVERALL_RISK_LEVEL: medium\nRisk assessment unavailable due to API error."

    # Parse overall risk level
    overall_risk = "medium"
    risks_identified = []
    current_risk: dict[str, str] = {}

    for line in content.split("\n"):
        line = line.strip()
        if not line:
            if current_risk:
                risks_identified.append(current_risk)
                current_risk = {}
            continue
        if "overall_risk_level:" in line.lower():
            risk_val = line.split(":", 1)[-1].strip().lower()
            if risk_val in ("low", "medium", "high", "critical"):
                overall_risk = risk_val
        for field in ("risk_name", "severity", "description", "impact"):
            if line.lower().startswith(f"{field}:"):
                current_risk[field] = line.split(":", 1)[-1].strip()
                break

    if current_risk:
        risks_identified.append(current_risk)

    # Fallback
    if not risks_identified and content:
        risks_identified = [{"risk_name": "General Risk", "severity": overall_risk, "description": content[:500], "impact": "Review required"}]

    return {
        "risks_identified": risks_identified,
        "overall_risk_level": overall_risk,
        "messages": [HumanMessage(content=f"Risk assessment complete. Overall risk: {overall_risk}. Risks found: {len(risks_identified)}")],
    }


async def generate_recommendations(state: LegalState) -> dict:
    """Generate mitigation recommendations."""
    logger.info("Generating legal recommendations for deal %s", state["deal_id"])
    llm = _get_llm()

    risks_text = "\n".join(
        f"- {r.get('risk_name', 'Unknown')} ({r.get('severity', 'unknown')}): {r.get('description', '')}"
        for r in state.get("risks_identified", [])
    )

    system = SystemMessage(
        content=(
            "You are a senior government contracts attorney providing strategic legal advice. "
            "Generate specific, actionable recommendations to mitigate identified risks "
            "and ensure compliance."
        )
    )
    human = HumanMessage(
        content=(
            f"Deal ID: {state['deal_id']}\n"
            f"Review Type: {state['review_type']}\n"
            f"Overall Risk Level: {state['overall_risk_level']}\n\n"
            f"Identified Risks:\n{risks_text or 'No specific risks identified.'}\n\n"
            f"Compliance Gaps:\n{chr(10).join(state.get('compliance_gaps', ['None']))}\n\n"
            "Provide 5-8 specific, actionable recommendations to:\n"
            "1. Mitigate the identified risks\n"
            "2. Close compliance gaps\n"
            "3. Protect company interests\n\n"
            "Format as a numbered list. Each recommendation should be specific and actionable."
        )
    )

    try:
        response = await llm.ainvoke([system, human])
        content = response.content
    except Exception as exc:
        logger.error("LLM call failed in generate_recommendations: %s", exc)
        content = "1. Engage legal counsel to review all identified risks prior to bid submission."

    # Parse numbered list
    recommendations = []
    for line in content.split("\n"):
        line = line.strip()
        if line and line[0].isdigit() and "." in line:
            rec = line.split(".", 1)[-1].strip()
            if rec:
                recommendations.append(rec)

    if not recommendations:
        recommendations = [content.strip()]

    return {
        "recommendations": recommendations,
        "messages": [HumanMessage(content=f"Generated {len(recommendations)} recommendations.")],
    }


async def assess_oci(state: LegalState) -> dict:
    """Organizational Conflict of Interest (OCI) check."""
    logger.info("Performing OCI assessment for deal %s", state["deal_id"])
    llm = _get_llm()

    document_text = state.get("rfp_text") or state.get("contract_text") or ""

    system = SystemMessage(
        content=(
            "You are a government contracting OCI (Organizational Conflict of Interest) specialist. "
            "Assess whether the contractor may have an OCI under FAR Subpart 9.5. "
            "Identify biased ground rules OCI, unequal access to information OCI, "
            "and impaired objectivity OCI."
        )
    )
    human = HumanMessage(
        content=(
            f"Deal ID: {state['deal_id']}\n"
            f"Review Type: {state['review_type']}\n\n"
            f"Document Text:\n{document_text[:4000] if document_text else 'No document provided.'}\n\n"
            "Perform OCI assessment:\n"
            "1. Identify potential OCI scenarios (biased ground rules, unequal access, impaired objectivity)\n"
            "2. Assess likelihood and severity of each\n"
            "3. Recommend mitigation measures\n"
            "4. Determine if OCI mitigation plan is required\n"
        )
    )

    try:
        response = await llm.ainvoke([system, human])
        oci_findings = response.content
    except Exception as exc:
        logger.error("LLM call failed in assess_oci: %s", exc)
        oci_findings = f"OCI assessment unavailable due to API error: {exc}"

    return {
        "oci_findings": oci_findings,
        "messages": [HumanMessage(content="OCI assessment complete.")],
    }


# ── Graph builder ─────────────────────────────────────────────────────────────

def build_legal_graph() -> StateGraph:
    """Construct and compile the legal review LangGraph workflow."""
    workflow = StateGraph(LegalState)

    workflow.add_node("identify_legal_requirements", identify_legal_requirements)
    workflow.add_node("check_far_compliance", check_far_compliance)
    workflow.add_node("assess_risks", assess_risks)
    workflow.add_node("generate_recommendations", generate_recommendations)
    workflow.add_node("assess_oci", assess_oci)

    workflow.set_entry_point("identify_legal_requirements")
    workflow.add_edge("identify_legal_requirements", "check_far_compliance")
    workflow.add_edge("check_far_compliance", "assess_risks")
    workflow.add_edge("assess_risks", "generate_recommendations")
    workflow.add_edge("generate_recommendations", "assess_oci")
    workflow.add_edge("assess_oci", END)

    return workflow.compile()


# Compiled graph instance
legal_graph = build_legal_graph()


# ── Agent class ───────────────────────────────────────────────────────────────

class LegalAgent(BaseAgent):
    """LangGraph-based Business Legal Review Agent."""

    agent_name = "legal_agent"

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Run legal review for a deal/contract.

        Args:
            input_data: Must contain 'deal_id'. Optional: 'rfp_text', 'contract_text', 'review_type'.

        Returns:
            dict with keys: deal_id, review_type, risks_identified, far_clauses,
            compliance_gaps, recommendations, overall_risk_level, oci_findings.
        """
        deal_id = input_data.get("deal_id", "")
        if not deal_id:
            return {"error": "deal_id is required"}

        initial_state: LegalState = {
            "deal_id": deal_id,
            "rfp_text": input_data.get("rfp_text", ""),
            "contract_text": input_data.get("contract_text", ""),
            "review_type": input_data.get("review_type", "rfp_review"),
            "risks_identified": [],
            "far_clauses": [],
            "compliance_gaps": [],
            "recommendations": [],
            "overall_risk_level": "medium",
            "oci_findings": "",
            "messages": [],
        }

        try:
            await self.emit_event(
                "thinking",
                {"message": f"Starting legal review for deal {deal_id}"},
                execution_id=deal_id,
            )
            final_state = await legal_graph.ainvoke(initial_state)
            await self.emit_event(
                "output",
                {"overall_risk_level": final_state["overall_risk_level"]},
                execution_id=deal_id,
            )
            return {
                "deal_id": final_state["deal_id"],
                "review_type": final_state["review_type"],
                "risks_identified": final_state["risks_identified"],
                "far_clauses": final_state["far_clauses"],
                "compliance_gaps": final_state["compliance_gaps"],
                "recommendations": final_state["recommendations"],
                "overall_risk_level": final_state["overall_risk_level"],
                "oci_findings": final_state["oci_findings"],
            }
        except Exception as exc:
            logger.exception("LegalAgent.run failed for deal %s", deal_id)
            await self.emit_event("error", {"error": str(exc)}, execution_id=deal_id)
            return {"error": str(exc), "deal_id": deal_id}
