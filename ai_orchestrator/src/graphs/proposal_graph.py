"""Proposal generation orchestration graph.

Coordinates the full proposal authoring pipeline:
1. Load deal context and RFP requirements
2. Retrieve technical solution and capture strategy
3. Match relevant past performance
4. Generate all proposal sections in parallel
5. Run AI review (pink team)
6. Human review gate
7. Generate final DOCX output
"""
import logging
import os
from typing import Annotated, Any
import operator

import httpx
from langchain_core.messages import HumanMessage
from langgraph.graph import END, StateGraph
from typing_extensions import TypedDict

logger = logging.getLogger("ai_orchestrator.graphs.proposal")

DJANGO_API_URL = os.getenv("DJANGO_API_URL", "http://django-api:8001")
DJANGO_SERVICE_TOKEN = os.getenv("DJANGO_SERVICE_TOKEN", "")


def _headers() -> dict:
    return {"Authorization": f"Bearer {DJANGO_SERVICE_TOKEN}"} if DJANGO_SERVICE_TOKEN else {}


# ── State ─────────────────────────────────────────────────────────────────────

class ProposalState(TypedDict):
    deal_id: str
    proposal_id: str
    deal: dict
    opportunity: dict
    rfp_requirements: list
    compliance_matrix: list
    technical_solution: dict
    capture_strategy: dict
    past_performance: list
    win_themes: list[str]
    sections_to_generate: list[str]
    generated_sections: dict  # section_type → content
    review_results: dict
    final_docx_url: str
    status: str
    human_approved: bool
    messages: Annotated[list, operator.add]


# ── Nodes ─────────────────────────────────────────────────────────────────────

async def load_deal_context(state: ProposalState) -> dict:
    """Load deal, opportunity, RFP requirements, and compliance matrix."""
    deal_id = state["deal_id"]
    logger.info("Loading deal context for proposal: %s", deal_id)

    async with httpx.AsyncClient(timeout=15.0) as client:
        results = {}
        for endpoint, key in [
            (f"/api/deals/{deal_id}/", "deal"),
            (f"/api/rfp/requirements/?deal_id={deal_id}", "rfp_requirements"),
            (f"/api/rfp/compliance-matrix/?deal_id={deal_id}", "compliance_matrix"),
        ]:
            try:
                resp = await client.get(f"{DJANGO_API_URL}{endpoint}", headers=_headers())
                if resp.status_code == 200:
                    results[key] = resp.json()
            except Exception as exc:
                logger.warning("Failed to load %s: %s", key, exc)
                results[key] = {} if key == "deal" else []

    deal = results.get("deal", {})
    opportunity = deal.get("opportunity", {})

    return {
        "deal": deal,
        "opportunity": opportunity,
        "rfp_requirements": results.get("rfp_requirements", []),
        "compliance_matrix": results.get("compliance_matrix", []),
        "messages": [HumanMessage(content=f"Starting proposal generation for deal {deal_id}")],
    }


async def load_proposal_inputs(state: ProposalState) -> dict:
    """Load technical solution, capture strategy, and win themes."""
    deal_id = state["deal_id"]

    async with httpx.AsyncClient(timeout=15.0) as client:
        tech_solution = {}
        capture = {}
        try:
            resp = await client.get(
                f"{DJANGO_API_URL}/api/proposals/{state.get('proposal_id', '')}/solution/",
                headers=_headers(),
            )
            if resp.status_code == 200:
                tech_solution = resp.json()
        except Exception:
            pass

        try:
            resp = await client.get(
                f"{DJANGO_API_URL}/api/marketing/capture-strategy/{deal_id}/",
                headers=_headers(),
            )
            if resp.status_code == 200:
                capture = resp.json()
        except Exception:
            pass

    win_themes = capture.get("win_themes", []) or [
        "Deep domain expertise and proven past performance",
        "Innovative technical approach with measurable outcomes",
        "Strong program management and quality assurance",
    ]

    return {
        "technical_solution": tech_solution,
        "capture_strategy": capture,
        "win_themes": win_themes,
    }


async def match_past_performance(state: ProposalState) -> dict:
    """Find and match relevant past performance projects."""
    deal_id = state["deal_id"]
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{DJANGO_API_URL}/api/past-performance/matches/?deal_id={deal_id}",
                headers=_headers(),
            )
            if resp.status_code == 200:
                return {"past_performance": resp.json()}
    except Exception as exc:
        logger.warning("Past performance match failed: %s", exc)

    return {"past_performance": []}


async def plan_sections(state: ProposalState) -> dict:
    """Determine which sections to generate based on RFP structure."""
    # Standard 5-volume proposal structure
    sections = [
        "executive_summary",
        "technical_approach",
        "management_approach",
        "past_performance",
        "staffing_plan",
        "transition_plan",
        "quality_plan",
        "risk_management",
    ]

    # Add security section if required
    opp = state.get("opportunity", {})
    if opp.get("security_requirements") or "security" in str(opp.get("description", "")).lower():
        sections.append("security_approach")

    return {"sections_to_generate": sections}


async def generate_sections(state: ProposalState) -> dict:
    """Generate all proposal sections (can be parallelized per section type)."""
    import asyncio

    from backend.apps.proposals.services.generator import generate_section

    sections_to_gen = state.get("sections_to_generate", ["technical_approach", "management_approach"])

    async def gen_one(section_type: str) -> tuple[str, dict]:
        result = await generate_section(
            section_type=section_type,
            deal_id=state["deal_id"],
            rfp_requirements=state.get("rfp_requirements", []),
            compliance_matrix=state.get("compliance_matrix", []),
            technical_solution=state.get("technical_solution", {}),
            capture_strategy=state.get("capture_strategy", {}),
            past_performance=state.get("past_performance", []),
            win_themes=state.get("win_themes", []),
        )
        return section_type, result

    tasks = [gen_one(s) for s in sections_to_gen]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    generated = {}
    for result in results:
        if isinstance(result, tuple):
            section_type, section_content = result
            generated[section_type] = section_content
        elif isinstance(result, Exception):
            logger.error("Section generation failed: %s", result)

    logger.info("Generated %d proposal sections", len(generated))
    return {"generated_sections": generated}


async def run_ai_review(state: ProposalState) -> dict:
    """Run automated pink team review."""
    from backend.apps.proposals.services.reviewer import run_ai_review as do_review

    sections_list = [
        {"title": k.replace("_", " ").title(), "content": v.get("content", "")}
        for k, v in state.get("generated_sections", {}).items()
    ]

    review = await do_review(
        proposal_id=state.get("proposal_id", state["deal_id"]),
        review_type="pink",
        sections=sections_list,
        rfp_requirements=state.get("rfp_requirements", []),
        win_themes=state.get("win_themes", []),
    )
    logger.info(
        "AI review complete: score=%s, issues=%d",
        review.get("overall_score"),
        review.get("issue_count", 0),
    )
    return {"review_results": review}


async def human_review_gate(state: ProposalState) -> dict:
    """HITL gate – proposal requires human approval before finalization."""
    # Create approval request
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            review = state.get("review_results", {})
            resp = await client.post(
                f"{DJANGO_API_URL}/api/deals/{state['deal_id']}/approvals/",
                json={
                    "approval_type": "proposal_review",
                    "ai_recommendation": "approve" if review.get("ready_to_submit") else "review_needed",
                    "ai_rationale": (
                        f"AI review score: {review.get('overall_score', 0)}/10. "
                        f"Issues: {review.get('issue_count', 0)}. "
                        f"{'Ready to submit.' if review.get('ready_to_submit') else 'Review issues before submitting.'}"
                    ),
                    "ai_confidence": min(1.0, (review.get("overall_score", 5) or 5) / 10),
                },
                headers=_headers(),
            )
    except Exception as exc:
        logger.warning("Approval creation failed: %s", exc)

    return {"status": "pending_human_review", "human_approved": False}


def should_continue_after_review(state: ProposalState) -> str:
    """Route after human review gate."""
    if state.get("human_approved"):
        return "generate_docx"
    return "await_approval"  # Stay in waiting state


async def generate_docx_output(state: ProposalState) -> dict:
    """Generate final DOCX proposal document."""
    from src.mcp_servers.template_render import render_full_proposal_docx

    sections_list = [
        {
            "title": k.replace("_", " ").title(),
            "content": v.get("content", "") if isinstance(v, dict) else str(v),
            "level": 1,
            "diagrams": [],
        }
        for k, v in state.get("generated_sections", {}).items()
    ]

    result = await render_full_proposal_docx(
        proposal_id=state.get("proposal_id", state["deal_id"]),
        sections=sections_list,
        cover_page={
            "opportunity_name": state.get("opportunity", {}).get("title", "Proposal"),
            "company_name": "",
            "date": "",
        },
    )

    docx_url = result.get("url", "")
    logger.info("Proposal DOCX generated: %s", docx_url)

    # Update proposal status
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.patch(
                f"{DJANGO_API_URL}/api/proposals/{state.get('proposal_id', '')}/",
                json={"status": "final", "docx_url": docx_url},
                headers=_headers(),
            )
    except Exception:
        pass

    return {"final_docx_url": docx_url, "status": "complete"}


async def await_approval(state: ProposalState) -> dict:
    """Placeholder node for awaiting human approval (interrupt point)."""
    logger.info("Proposal awaiting human approval for deal %s", state["deal_id"])
    return {"status": "awaiting_approval"}


# ── Graph construction ─────────────────────────────────────────────────────────

def build_proposal_graph():
    """Build and compile the proposal generation graph."""
    workflow = StateGraph(ProposalState)

    workflow.add_node("load_deal_context", load_deal_context)
    workflow.add_node("load_proposal_inputs", load_proposal_inputs)
    workflow.add_node("match_past_performance", match_past_performance)
    workflow.add_node("plan_sections", plan_sections)
    workflow.add_node("generate_sections", generate_sections)
    workflow.add_node("run_ai_review", run_ai_review)
    workflow.add_node("human_review_gate", human_review_gate)
    workflow.add_node("generate_docx_output", generate_docx_output)
    workflow.add_node("await_approval", await_approval)

    workflow.set_entry_point("load_deal_context")
    workflow.add_edge("load_deal_context", "load_proposal_inputs")
    workflow.add_edge("load_proposal_inputs", "match_past_performance")
    workflow.add_edge("match_past_performance", "plan_sections")
    workflow.add_edge("plan_sections", "generate_sections")
    workflow.add_edge("generate_sections", "run_ai_review")
    workflow.add_edge("run_ai_review", "human_review_gate")

    workflow.add_conditional_edges(
        "human_review_gate",
        should_continue_after_review,
        {
            "generate_docx": "generate_docx_output",
            "await_approval": "await_approval",
        },
    )

    workflow.add_edge("generate_docx_output", END)
    workflow.add_edge("await_approval", END)

    return workflow.compile()


# Module-level compiled graph
proposal_graph = build_proposal_graph()
