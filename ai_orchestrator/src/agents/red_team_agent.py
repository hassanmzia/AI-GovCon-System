"""
Red Team Agent — Adversarial proposal evaluator.

Evaluates proposals against RFP evaluation criteria as if scoring
for the government. Identifies weaknesses, missing requirements,
and non-responsive sections. Generates improvement recommendations.
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

logger = logging.getLogger("ai_orchestrator.agents.red_team")

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


class RedTeamState(TypedDict):
    deal_id: str
    proposal: dict
    rfp_requirements: list[dict]
    evaluation_criteria: list[dict]
    sections: list[dict]
    findings: list[dict]
    section_scores: dict
    overall_score: float
    strengths: list[str]
    weaknesses: list[str]
    recommendations: list[dict]
    messages: list


async def load_proposal_context(state: RedTeamState) -> dict:
    """Load proposal, RFP requirements, and evaluation criteria."""
    deal_id = state["deal_id"]

    deal = await _get(f"/api/deals/{deal_id}/", default={})
    proposals = await _get(f"/api/proposals/?deal={deal_id}", default={})
    proposal = {}
    sections = []
    if isinstance(proposals, dict) and proposals.get("results"):
        proposal = proposals["results"][0]
        prop_id = proposal.get("id", "")
        sections_data = await _get(f"/api/proposals/{prop_id}/sections/", default={})
        sections = sections_data.get("results", []) if isinstance(sections_data, dict) else []

    rfp_data = await _get(f"/api/rfp/?deal={deal_id}", default={})
    rfp_reqs = []
    eval_criteria = []
    if isinstance(rfp_data, dict) and rfp_data.get("results"):
        rfp = rfp_data["results"][0]
        rfp_id = rfp.get("id", "")
        req_data = await _get(f"/api/rfp/{rfp_id}/requirements/", default={})
        rfp_reqs = req_data.get("results", []) if isinstance(req_data, dict) else []
        eval_criteria = rfp.get("evaluation_criteria", [])

    return {
        "proposal": proposal,
        "sections": sections,
        "rfp_requirements": rfp_reqs,
        "evaluation_criteria": eval_criteria,
        "messages": [HumanMessage(content=f"Loaded {len(sections)} proposal sections and {len(rfp_reqs)} requirements")],
    }


async def evaluate_compliance(state: RedTeamState) -> dict:
    """Check each RFP requirement against proposal sections."""
    llm = _get_llm()
    findings = []

    sections_text = "\n\n".join([
        f"## {s.get('title', 'Untitled')}\n{s.get('content', s.get('ai_draft', ''))[:1000]}"
        for s in state.get("sections", [])
    ])

    requirements = state.get("rfp_requirements", [])[:30]

    if not sections_text or not requirements:
        return {
            "findings": [{"type": "warning", "message": "Insufficient data for compliance evaluation"}],
            "messages": [HumanMessage(content="Skipped compliance evaluation — insufficient data")],
        }

    try:
        resp = await llm.ainvoke([
            SystemMessage(content=(
                "You are a government proposal evaluator performing a red team review. "
                "Check each requirement against the proposal sections. For each requirement, "
                "determine if it is: FULLY_ADDRESSED, PARTIALLY_ADDRESSED, or NOT_ADDRESSED.\n"
                "For each finding, provide:\n"
                "- requirement_id\n"
                "- status (FULLY_ADDRESSED / PARTIALLY_ADDRESSED / NOT_ADDRESSED)\n"
                "- section (which proposal section addresses it)\n"
                "- gap (what's missing if not fully addressed)\n"
                "- severity (HIGH / MEDIUM / LOW)\n"
                "Format as one finding per line: REQ_ID | STATUS | SECTION | GAP | SEVERITY"
            )),
            HumanMessage(content=(
                f"Requirements:\n{_format_requirements(requirements)}\n\n"
                f"Proposal Sections:\n{sections_text[:6000]}"
            )),
        ])

        for line in resp.content.strip().split("\n"):
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 5:
                findings.append({
                    "requirement_id": parts[0],
                    "status": parts[1],
                    "section": parts[2],
                    "gap": parts[3],
                    "severity": parts[4],
                })

    except Exception as exc:
        logger.error("Red team compliance evaluation failed: %s", exc)
        findings.append({"type": "error", "message": str(exc)})

    return {
        "findings": findings,
        "messages": [HumanMessage(content=f"Found {len(findings)} compliance findings")],
    }


async def evaluate_quality(state: RedTeamState) -> dict:
    """Evaluate proposal quality, scoring, strengths, and weaknesses."""
    llm = _get_llm()

    sections_text = "\n\n".join([
        f"## {s.get('title', 'Untitled')}\n{s.get('content', s.get('ai_draft', ''))[:1500]}"
        for s in state.get("sections", [])
    ])

    eval_criteria = state.get("evaluation_criteria", [])

    try:
        resp = await llm.ainvoke([
            SystemMessage(content=(
                "You are a senior government evaluator scoring a proposal. "
                "Evaluate the proposal against the evaluation criteria.\n"
                "Provide:\n"
                "1. SECTION_SCORES: Score each section 1-5 (format: section_title: score)\n"
                "2. OVERALL_SCORE: Single score 1-5\n"
                "3. STRENGTHS: 3-5 specific strengths\n"
                "4. WEAKNESSES: 3-5 specific weaknesses with remediation suggestions\n"
                "5. RECOMMENDATIONS: Prioritized list of improvements\n\n"
                "Be harsh and specific. This is a red team review."
            )),
            HumanMessage(content=(
                f"Evaluation Criteria: {eval_criteria}\n\n"
                f"Proposal Sections:\n{sections_text[:8000]}"
            )),
        ])

        content = resp.content
        parsed = _parse_quality_review(content)
    except Exception as exc:
        logger.error("Red team quality evaluation failed: %s", exc)
        parsed = {
            "section_scores": {},
            "overall_score": 0.0,
            "strengths": [],
            "weaknesses": [],
            "recommendations": [],
        }

    return {
        "section_scores": parsed["section_scores"],
        "overall_score": parsed["overall_score"],
        "strengths": parsed["strengths"],
        "weaknesses": parsed["weaknesses"],
        "recommendations": parsed["recommendations"],
        "messages": [HumanMessage(content=f"Quality score: {parsed['overall_score']}/5.0")],
    }


def _format_requirements(reqs: list) -> str:
    lines = []
    for i, r in enumerate(reqs, 1):
        lines.append(f"REQ-{i}: {r.get('text', r.get('requirement_text', 'N/A'))[:200]}")
    return "\n".join(lines)


def _parse_quality_review(content: str) -> dict:
    result = {
        "section_scores": {},
        "overall_score": 0.0,
        "strengths": [],
        "weaknesses": [],
        "recommendations": [],
    }

    for line in content.split("\n"):
        line = line.strip()
        if "OVERALL_SCORE" in line.upper():
            try:
                score_part = line.split(":")[-1].strip()
                result["overall_score"] = float(score_part.split("/")[0].strip())
            except (ValueError, IndexError):
                pass

    # Extract lists
    current_section = None
    for line in content.split("\n"):
        stripped = line.strip()
        upper = stripped.upper()

        if "STRENGTH" in upper:
            current_section = "strengths"
            continue
        elif "WEAKNESS" in upper:
            current_section = "weaknesses"
            continue
        elif "RECOMMENDATION" in upper:
            current_section = "recommendations"
            continue

        if current_section and stripped.startswith(("-", "•", "*", "1", "2", "3", "4", "5")):
            item = stripped.lstrip("-•*0123456789. ").strip()
            if item and current_section in ("strengths", "weaknesses"):
                result[current_section].append(item)
            elif item and current_section == "recommendations":
                result["recommendations"].append({"text": item, "priority": "medium"})

    return result


def build_red_team_graph() -> StateGraph:
    wf = StateGraph(RedTeamState)
    wf.add_node("load_proposal_context", load_proposal_context)
    wf.add_node("evaluate_compliance", evaluate_compliance)
    wf.add_node("evaluate_quality", evaluate_quality)
    wf.set_entry_point("load_proposal_context")
    wf.add_edge("load_proposal_context", "evaluate_compliance")
    wf.add_edge("evaluate_compliance", "evaluate_quality")
    wf.add_edge("evaluate_quality", END)
    return wf.compile()


red_team_graph = build_red_team_graph()


class RedTeamAgent(BaseAgent):
    """AI agent that performs adversarial red team review of proposals."""

    agent_name = "red_team_agent"

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        deal_id = input_data.get("deal_id", "")
        if not deal_id:
            return {"error": "deal_id is required"}

        initial: RedTeamState = {
            "deal_id": deal_id,
            "proposal": {},
            "rfp_requirements": [],
            "evaluation_criteria": [],
            "sections": [],
            "findings": [],
            "section_scores": {},
            "overall_score": 0.0,
            "strengths": [],
            "weaknesses": [],
            "recommendations": [],
            "messages": [],
        }
        try:
            await self.emit_event("thinking", {"message": f"Red team review for deal {deal_id}"})
            result = await red_team_graph.ainvoke(initial)
            await self.emit_event("output", {
                "overall_score": result["overall_score"],
                "findings_count": len(result["findings"]),
            })
            return {
                "deal_id": deal_id,
                "findings": result["findings"],
                "section_scores": result["section_scores"],
                "overall_score": result["overall_score"],
                "strengths": result["strengths"],
                "weaknesses": result["weaknesses"],
                "recommendations": result["recommendations"],
            }
        except Exception as exc:
            logger.exception("RedTeamAgent.run failed for deal %s", deal_id)
            await self.emit_event("error", {"error": str(exc)})
            return {"error": str(exc), "deal_id": deal_id}
