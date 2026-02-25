"""Proposal Writer AI Agent using LangGraph.

Drafts proposal sections from solution architecture, past performance,
win themes, and compliance matrix. Manages pink/red/gold team review flow.

Events: PROPOSAL_SECTION_DRAFTED, PROPOSAL_REVIEW_REQUESTED,
        PROPOSAL_REVIEW_COMPLETED, PROPOSAL_SECTION_APPROVED, PROPOSAL_ASSEMBLED.
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

logger = logging.getLogger("ai_orchestrator.agents.proposal_writer")

DJANGO_API_URL = os.getenv("DJANGO_API_URL", "http://django-api:8001")
DJANGO_SERVICE_TOKEN = os.getenv("DJANGO_SERVICE_TOKEN", "")


# ── State ─────────────────────────────────────────────────────────────────────

class ProposalWriterState(TypedDict):
    deal_id: str
    proposal_id: str               # Existing Proposal record to populate
    deal: dict
    opportunity: dict
    win_themes: list[str]
    evaluation_criteria: list[dict]
    compliance_matrix: list[dict]
    technical_solution_summary: str
    past_performance_summaries: list[str]
    drafted_sections: dict         # {section_title: drafted_text}
    review_feedback: str           # From pink/red team review
    revised_sections: dict         # Sections revised after review
    assembly_summary: str          # Final assembled proposal summary
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

async def load_proposal_context(state: ProposalWriterState) -> dict:
    logger.info("ProposalWriter: loading context for deal %s", state["deal_id"])
    deal = await _get(f"/api/deals/{state['deal_id']}/", default={})
    opp_id = deal.get("opportunity", "")
    opportunity = await _get(f"/api/opportunities/{opp_id}/", default={}) if opp_id else {}

    # Pull win themes from strategy if deal has them
    strategy_data = await _get("/api/strategy/current/", default={})
    win_themes = deal.get("win_themes") or strategy_data.get("win_themes", [])

    # RFP evaluation criteria
    rfp_reqs = await _get(f"/api/rfp/requirements/?deal={state['deal_id']}&limit=50", default={})
    compliance_matrix = rfp_reqs.get("results", []) if isinstance(rfp_reqs, dict) else []

    return {
        "deal": deal,
        "opportunity": opportunity,
        "win_themes": win_themes if isinstance(win_themes, list) else [],
        "compliance_matrix": compliance_matrix,
        "messages": [HumanMessage(content=f"Writing proposal for: {deal.get('title', state['deal_id'])}")],
    }


async def draft_executive_summary(state: ProposalWriterState) -> dict:
    """Draft the Executive Summary — the most important proposal section."""
    logger.info("ProposalWriter: drafting executive summary for deal %s", state["deal_id"])

    content = await _llm(
        system=(
            "You are a master proposal writer for U.S. government contracts. "
            "Write a compelling executive summary that immediately captures the evaluator's "
            "attention and communicates the company's unique value proposition. "
            "Every sentence must be customer-focused and evaluation-criteria-aligned."
        ),
        human=(
            f"Opportunity: {state['opportunity']}\n\n"
            f"Win Themes:\n{chr(10).join(f'- {t}' for t in state['win_themes'][:5])}\n\n"
            f"Technical Solution Summary:\n{state['technical_solution_summary'][:800]}\n\n"
            f"Past Performance (sample):\n{state['past_performance_summaries'][:3]}\n\n"
            "Write a 400–500 word Executive Summary that:\n"
            "1. Opens with a compelling hook addressing the agency's mission\n"
            "2. Clearly states our solution and its primary benefit\n"
            "3. Integrates the top 3 win themes naturally\n"
            "4. References relevant past performance\n"
            "5. Closes with a confident statement of our unique qualifications\n"
            "6. Uses the agency's language and priorities\n\n"
            "Do NOT use generic boilerplate. Make it specific to this opportunity."
        ),
        max_tokens=2000,
    )

    sections = dict(state.get("drafted_sections") or {})
    sections["Executive Summary"] = content
    return {
        "drafted_sections": sections,
        "messages": [HumanMessage(content="Executive summary drafted.")],
    }


async def draft_technical_approach(state: ProposalWriterState) -> dict:
    """Draft the Technical Approach section."""
    logger.info("ProposalWriter: drafting technical approach for deal %s", state["deal_id"])

    content = await _llm(
        system=(
            "You are a senior proposal writer and solutions architect. Write a technical "
            "approach section that is both technically rigorous and evaluator-friendly. "
            "Every paragraph should address specific evaluation criteria."
        ),
        human=(
            f"Opportunity: {state['opportunity']}\n\n"
            f"Technical Solution:\n{state['technical_solution_summary'][:1500]}\n\n"
            f"Evaluation Criteria:\n{state['evaluation_criteria'][:10]}\n\n"
            f"Win Themes:\n{state['win_themes'][:5]}\n\n"
            "Write a Technical Approach section (600–800 words) covering:\n"
            "1. Solution overview and guiding principles\n"
            "2. How the approach meets each key technical requirement\n"
            "3. Key differentiating technology choices with justification\n"
            "4. Implementation methodology (phasing, milestones)\n"
            "5. Risk mitigation strategy\n"
            "6. Innovation highlights\n\n"
            "Use clear headings, be specific, and avoid vague claims."
        ),
        max_tokens=2500,
    )

    sections = dict(state.get("drafted_sections") or {})
    sections["Technical Approach"] = content
    return {
        "drafted_sections": sections,
        "messages": [HumanMessage(content="Technical approach drafted.")],
    }


async def draft_management_approach(state: ProposalWriterState) -> dict:
    """Draft the Management Approach section."""
    logger.info("ProposalWriter: drafting management approach for deal %s", state["deal_id"])

    content = await _llm(
        system=(
            "You are a program manager and proposal writer. Write a management approach "
            "that demonstrates strong governance, quality assurance, and delivery credibility."
        ),
        human=(
            f"Opportunity: {state['opportunity']}\n\n"
            f"Win Themes:\n{state['win_themes'][:5]}\n\n"
            "Write a Management Approach section (500–600 words) covering:\n"
            "1. Program management structure (PM, DPM, CORs, key personnel)\n"
            "2. Governance model (status reporting, escalation, change control)\n"
            "3. Quality assurance process\n"
            "4. Communications plan (internal + client)\n"
            "5. Key personnel qualifications and retention strategy\n"
            "6. Transition-in/transition-out approach\n"
        ),
        max_tokens=2000,
    )

    sections = dict(state.get("drafted_sections") or {})
    sections["Management Approach"] = content
    return {
        "drafted_sections": sections,
        "messages": [HumanMessage(content="Management approach drafted.")],
    }


async def conduct_ai_review(state: ProposalWriterState) -> dict:
    """AI 'pink team' review — critique all drafted sections."""
    logger.info("ProposalWriter: AI pink-team review for deal %s", state["deal_id"])

    sections_text = "\n\n---\n\n".join(
        f"## {title}\n{text[:600]}"
        for title, text in (state.get("drafted_sections") or {}).items()
    )

    content = await _llm(
        system=(
            "You are a gold-team reviewer for a U.S. government proposal. "
            "Critically evaluate all sections for: evaluation-criteria alignment, "
            "customer focus, specificity, win-theme integration, and compliance. "
            "Provide actionable improvement instructions per section."
        ),
        human=(
            f"Opportunity: {state['opportunity']}\n\n"
            f"Evaluation Criteria:\n{state['evaluation_criteria'][:8]}\n\n"
            f"Draft Sections:\n{sections_text}\n\n"
            "Review each section and provide:\n"
            "1. Score (1-10) for evaluation-criteria alignment\n"
            "2. Top 3 weaknesses\n"
            "3. Specific improvement instructions\n"
            "4. Win-theme integration assessment\n"
            "5. Overall proposal readiness score (1-10)"
        ),
        max_tokens=2000,
    )

    return {
        "review_feedback": content,
        "messages": [HumanMessage(content="AI pink-team review complete.")],
    }


async def revise_from_feedback(state: ProposalWriterState) -> dict:
    """Apply review feedback to revise the weakest sections."""
    logger.info("ProposalWriter: revising sections from feedback for deal %s", state["deal_id"])

    # Revise the executive summary based on feedback as the highest-value section
    exec_summary = (state.get("drafted_sections") or {}).get("Executive Summary", "")
    if not exec_summary:
        return {
            "revised_sections": {},
            "messages": [HumanMessage(content="Nothing to revise.")],
        }

    revised_exec = await _llm(
        system=(
            "You are a senior proposal writer revising a draft based on review feedback. "
            "Address every criticism precisely. Maintain the word count target."
        ),
        human=(
            f"Original Executive Summary:\n{exec_summary}\n\n"
            f"Review Feedback:\n{state['review_feedback'][:1000]}\n\n"
            "Revise the Executive Summary to address all issues. "
            "Mark key improvements with [IMPROVED]."
        ),
        max_tokens=1500,
    )

    revised = {"Executive Summary": revised_exec}
    return {
        "revised_sections": revised,
        "messages": [HumanMessage(content=f"Revised {len(revised)} section(s) from feedback.")],
    }


async def assemble_proposal(state: ProposalWriterState) -> dict:
    """Assemble final proposal summary and volume structure."""
    logger.info("ProposalWriter: assembling proposal for deal %s", state["deal_id"])

    all_sections = {**(state.get("drafted_sections") or {}), **(state.get("revised_sections") or {})}
    section_count = len(all_sections)

    content = await _llm(
        system="You are a proposal manager creating a final assembly summary.",
        human=(
            f"Proposal for: {state['opportunity'].get('title', '')}\n\n"
            f"Sections drafted: {list(all_sections.keys())}\n\n"
            f"Win themes: {state['win_themes'][:5]}\n\n"
            "Provide:\n"
            "1. Proposal assembly checklist (what's done, what's missing)\n"
            "2. Final compliance verification summary\n"
            "3. Volume structure recommendation (I: Technical, II: Management, III: Past Perf, IV: Price)\n"
            "4. Page count estimates per volume\n"
            "5. Top 3 submission risks to address before final submission"
        ),
        max_tokens=1500,
    )

    return {
        "assembly_summary": content,
        "messages": [HumanMessage(content=f"Proposal assembled with {section_count} section(s).")],
    }


# ── Graph ─────────────────────────────────────────────────────────────────────

def build_proposal_writer_graph() -> StateGraph:
    wf = StateGraph(ProposalWriterState)
    wf.add_node("load_proposal_context", load_proposal_context)
    wf.add_node("draft_executive_summary", draft_executive_summary)
    wf.add_node("draft_technical_approach", draft_technical_approach)
    wf.add_node("draft_management_approach", draft_management_approach)
    wf.add_node("conduct_ai_review", conduct_ai_review)
    wf.add_node("revise_from_feedback", revise_from_feedback)
    wf.add_node("assemble_proposal", assemble_proposal)

    wf.set_entry_point("load_proposal_context")
    wf.add_edge("load_proposal_context", "draft_executive_summary")
    wf.add_edge("draft_executive_summary", "draft_technical_approach")
    wf.add_edge("draft_technical_approach", "draft_management_approach")
    wf.add_edge("draft_management_approach", "conduct_ai_review")
    wf.add_edge("conduct_ai_review", "revise_from_feedback")
    wf.add_edge("revise_from_feedback", "assemble_proposal")
    wf.add_edge("assemble_proposal", END)
    return wf.compile()


proposal_writer_graph = build_proposal_writer_graph()


# ── Agent ─────────────────────────────────────────────────────────────────────

class ProposalWriterAgent(BaseAgent):
    """AI agent that drafts, reviews, and assembles proposal sections."""

    agent_name = "proposal_writer_agent"

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        deal_id = input_data.get("deal_id", "")
        if not deal_id:
            return {"error": "deal_id is required"}

        initial: ProposalWriterState = {
            "deal_id": deal_id,
            "proposal_id": input_data.get("proposal_id", ""),
            "deal": {},
            "opportunity": {},
            "win_themes": input_data.get("win_themes", []),
            "evaluation_criteria": input_data.get("evaluation_criteria", []),
            "compliance_matrix": [],
            "technical_solution_summary": input_data.get("technical_solution_summary", ""),
            "past_performance_summaries": input_data.get("past_performance_summaries", []),
            "drafted_sections": {},
            "review_feedback": "",
            "revised_sections": {},
            "assembly_summary": "",
            "messages": [],
        }
        try:
            await self.emit_event(
                "thinking",
                {"message": f"Writing proposal for deal {deal_id}"},
                execution_id=deal_id,
            )
            fs = await proposal_writer_graph.ainvoke(initial)
            await self.emit_event(
                "output",
                {"sections_drafted": len(fs["drafted_sections"])},
                execution_id=deal_id,
            )
            return {
                "deal_id": fs["deal_id"],
                "drafted_sections": fs["drafted_sections"],
                "review_feedback": fs["review_feedback"],
                "revised_sections": fs["revised_sections"],
                "assembly_summary": fs["assembly_summary"],
            }
        except Exception as exc:
            logger.exception("ProposalWriterAgent.run failed for deal %s", deal_id)
            await self.emit_event("error", {"error": str(exc)}, execution_id=deal_id)
            return {"error": str(exc), "deal_id": deal_id}
