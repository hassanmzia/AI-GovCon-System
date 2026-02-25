"""Communication AI Agent using LangGraph.

Handles all proposal-related communications: drafts clarification questions
for the CO, processes Q&A answers, maps answers to proposal impacts,
and generates professional correspondence.

Events: CLARIFICATIONS_DRAFTED, CLARIFICATION_ANSWERED, QA_IMPACT_MAPPED.
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

logger = logging.getLogger("ai_orchestrator.agents.communication")

DJANGO_API_URL = os.getenv("DJANGO_API_URL", "http://django-api:8001")
DJANGO_SERVICE_TOKEN = os.getenv("DJANGO_SERVICE_TOKEN", "")

# Proposal sections that Q&A answers commonly impact
_PROPOSAL_SECTIONS = [
    "Technical Approach",
    "Management Approach",
    "Past Performance",
    "Price/Cost",
    "Compliance/Certifications",
    "Key Personnel",
    "Teaming",
    "Security",
]


# ── State ─────────────────────────────────────────────────────────────────────

class CommunicationState(TypedDict):
    deal_id: str
    deal: dict
    opportunity: dict
    rfp_requirements: list[dict]      # From RFP analyst
    qa_pairs: list[dict]              # Existing Q&A: [{question, answer, source}]
    ambiguous_requirements: list[str] # Requirements needing clarification
    drafted_questions: list[dict]     # [{question_text, section_ref, priority, rationale}]
    answer_impacts: list[dict]        # [{question, answer, impacted_sections, action_required}]
    correspondence_drafts: list[dict] # [{type, subject, body, recipient}]
    communication_summary: str        # Summary of all pending comms actions
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

async def load_communication_context(state: CommunicationState) -> dict:
    logger.info("CommunicationAgent: loading context for deal %s", state["deal_id"])
    deal = await _get(f"/api/deals/{state['deal_id']}/", default={})
    opp_id = deal.get("opportunity", "")
    opportunity = await _get(f"/api/opportunities/{opp_id}/", default={}) if opp_id else {}
    rfp_reqs = await _get(f"/api/rfp/requirements/?deal={state['deal_id']}&limit=50", default={})
    requirements = rfp_reqs.get("results", []) if isinstance(rfp_reqs, dict) else []
    qa_data = await _get(f"/api/qa/?deal={state['deal_id']}&limit=50", default={})
    qa_pairs = qa_data.get("results", []) if isinstance(qa_data, dict) else []
    return {
        "deal": deal,
        "opportunity": opportunity,
        "rfp_requirements": requirements,
        "qa_pairs": qa_pairs,
        "messages": [HumanMessage(content=f"Communication management for: {deal.get('title', state['deal_id'])}")],
    }


async def draft_clarification_questions(state: CommunicationState) -> dict:
    """Draft high-value clarification questions for the Contracting Officer."""
    logger.info("CommunicationAgent: drafting clarification questions for deal %s", state["deal_id"])

    requirements = state.get("rfp_requirements") or []
    existing_qa = state.get("qa_pairs") or []
    ambiguous = state.get("ambiguous_requirements") or []

    # Build context from requirements
    req_sample = requirements[:30]
    req_list = "\n".join(
        f"[{r.get('requirement_id', f'REQ-{i}')}] {r.get('requirement_text', '')[:200]}"
        for i, r in enumerate(req_sample)
    )

    already_asked = set(q.get("question", "")[:50] for q in existing_qa)

    content = await _llm(
        system=(
            "You are a capture manager and proposal coordinator drafting vendor clarification "
            "questions for a U.S. government RFP. Questions must be specific, professionally "
            "worded, and strategically valuable for shaping the proposal."
        ),
        human=(
            f"Opportunity: {state['opportunity'].get('title', '')}\n"
            f"Agency: {state['opportunity'].get('agency', '')}\n\n"
            f"RFP Requirements (showing {len(req_sample)}):\n{req_list}\n\n"
            f"Previously asked questions: {len(already_asked)}\n\n"
            f"Specific ambiguous requirements flagged:\n"
            + "\n".join(f"- {r}" for r in ambiguous[:10])
            + "\n\n"
            "Draft 8–10 high-value clarification questions. For each:\n"
            "Q: [question text]\n"
            "SECTION: [RFP section reference, e.g. L.4.2]\n"
            "PRIORITY: HIGH/MEDIUM/LOW\n"
            "RATIONALE: [why this matters for the proposal]\n"
            "---\n\n"
            "Focus on: scope boundaries, evaluation criteria weights, "
            "key personnel requirements, page limits, and technical constraints."
        ),
        max_tokens=2500,
    )

    questions = []
    blocks = content.split("---")
    for block in blocks:
        if "Q:" in block:
            lines = {}
            for line in block.strip().split("\n"):
                if ":" in line:
                    key, _, val = line.partition(":")
                    lines[key.strip().upper()] = val.strip()
            if "Q" in lines:
                questions.append({
                    "question_text": lines.get("Q", ""),
                    "section_ref": lines.get("SECTION", ""),
                    "priority": lines.get("PRIORITY", "MEDIUM"),
                    "rationale": lines.get("RATIONALE", ""),
                })

    return {
        "drafted_questions": questions,
        "messages": [HumanMessage(content=f"Drafted {len(questions)} clarification question(s).")],
    }


async def map_qa_impacts(state: CommunicationState) -> dict:
    """Map each Q&A answer to the proposal sections it impacts."""
    logger.info("CommunicationAgent: mapping Q&A impacts for deal %s", state["deal_id"])

    qa_pairs = state.get("qa_pairs") or []
    answered = [q for q in qa_pairs if q.get("answer")]

    if not answered:
        return {
            "answer_impacts": [],
            "messages": [HumanMessage(content="No answered Q&A pairs to map.")],
        }

    qa_text = "\n\n".join(
        f"Q: {q.get('question', '')[:200]}\nA: {q.get('answer', '')[:200]}"
        for q in answered[:20]
    )

    content = await _llm(
        system=(
            "You are a proposal coordinator. For each Q&A pair, identify which proposal "
            "sections must be updated based on the government's answer, and what action is required."
        ),
        human=(
            f"Proposal sections: {_PROPOSAL_SECTIONS}\n\n"
            f"Q&A Pairs ({len(answered)} answered):\n{qa_text}\n\n"
            "For each Q&A pair, output:\n"
            "QA: [Q&A number, 1-based]\n"
            "IMPACTS: [comma-separated section names from the list above]\n"
            "ACTION: [specific action required, e.g. 'Update page 12 technical approach']\n"
            "URGENCY: HIGH/MEDIUM/LOW\n"
            "---"
        ),
        max_tokens=2000,
    )

    impacts = []
    blocks = content.split("---")
    for i, block in enumerate(blocks):
        if "QA:" in block or "IMPACTS:" in block:
            lines = {}
            for line in block.strip().split("\n"):
                if ":" in line:
                    key, _, val = line.partition(":")
                    lines[key.strip().upper()] = val.strip()

            # Match to original Q&A pair
            qa_idx = i if i < len(answered) else 0
            original_qa = answered[qa_idx] if answered else {}

            if lines.get("IMPACTS") or lines.get("ACTION"):
                impacted = [s.strip() for s in lines.get("IMPACTS", "").split(",") if s.strip()]
                impacts.append({
                    "question": original_qa.get("question", ""),
                    "answer": original_qa.get("answer", ""),
                    "impacted_sections": impacted,
                    "action_required": lines.get("ACTION", "Review and update as needed"),
                    "urgency": lines.get("URGENCY", "MEDIUM"),
                })

    return {
        "answer_impacts": impacts,
        "messages": [HumanMessage(content=f"Mapped {len(impacts)} Q&A impact(s).")],
    }


async def draft_correspondence(state: CommunicationState) -> dict:
    """Draft professional correspondence: question submissions, acknowledgments, follow-ups."""
    logger.info("CommunicationAgent: drafting correspondence for deal %s", state["deal_id"])

    questions = state.get("drafted_questions") or []
    high_priority_q = [q for q in questions if q.get("priority") == "HIGH"][:5]

    if not high_priority_q:
        return {
            "correspondence_drafts": [],
            "communication_summary": "No high-priority questions to submit.",
            "messages": [HumanMessage(content="No correspondence needed.")],
        }

    agency = state["opportunity"].get("agency", "the Government")
    opp_title = state["opportunity"].get("title", "the referenced procurement")
    solicitation_number = state["opportunity"].get("solicitation_number", "[SOLICITATION NUMBER]")

    content = await _llm(
        system=(
            "You are a proposal coordinator drafting a formal vendor questions letter "
            "to a U.S. government contracting officer. Use professional, concise government "
            "contracting language. Follow standard RFP question submission format."
        ),
        human=(
            f"Agency: {agency}\n"
            f"Opportunity: {opp_title}\n"
            f"Solicitation: {solicitation_number}\n\n"
            "Draft a formal vendor questions submission letter including:\n"
            "1. Professional salutation and reference to the solicitation\n"
            "2. Each of the following questions numbered and formatted:\n\n"
            + "\n".join(
                f"{i+1}. [Section {q.get('section_ref', 'General')}] {q.get('question_text', '')}"
                for i, q in enumerate(high_priority_q)
            )
            + "\n\n3. Professional closing requesting responses by the Q&A deadline\n\n"
            "Keep the letter under 400 words. Use formal business letter format."
        ),
        max_tokens=1500,
    )

    drafts = [{
        "type": "vendor_questions_letter",
        "subject": f"Vendor Questions - {opp_title} - {solicitation_number}",
        "body": content,
        "recipient": f"Contracting Officer, {agency}",
    }]

    summary = (
        f"Communications summary for deal {state['deal_id']}:\n"
        f"- {len(questions)} clarification questions drafted ({len(high_priority_q)} HIGH priority)\n"
        f"- {len(state.get('answer_impacts') or [])} Q&A impacts mapped\n"
        f"- {len(drafts)} correspondence draft(s) ready\n"
        f"- Action required: Submit questions before Q&A deadline"
    )

    return {
        "correspondence_drafts": drafts,
        "communication_summary": summary,
        "messages": [HumanMessage(content=f"Drafted {len(drafts)} correspondence item(s).")],
    }


# ── Graph ─────────────────────────────────────────────────────────────────────

def build_communication_graph() -> StateGraph:
    wf = StateGraph(CommunicationState)
    wf.add_node("load_communication_context", load_communication_context)
    wf.add_node("draft_clarification_questions", draft_clarification_questions)
    wf.add_node("map_qa_impacts", map_qa_impacts)
    wf.add_node("draft_correspondence", draft_correspondence)
    wf.set_entry_point("load_communication_context")
    wf.add_edge("load_communication_context", "draft_clarification_questions")
    wf.add_edge("draft_clarification_questions", "map_qa_impacts")
    wf.add_edge("map_qa_impacts", "draft_correspondence")
    wf.add_edge("draft_correspondence", END)
    return wf.compile()


communication_graph = build_communication_graph()


# ── Agent ─────────────────────────────────────────────────────────────────────

class CommunicationAgent(BaseAgent):
    """AI agent that manages proposal Q&A, clarifications, and correspondence."""

    agent_name = "communication_agent"

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        deal_id = input_data.get("deal_id", "")
        if not deal_id:
            return {"error": "deal_id is required"}

        initial: CommunicationState = {
            "deal_id": deal_id,
            "deal": {},
            "opportunity": {},
            "rfp_requirements": input_data.get("rfp_requirements", []),
            "qa_pairs": input_data.get("qa_pairs", []),
            "ambiguous_requirements": input_data.get("ambiguous_requirements", []),
            "drafted_questions": [],
            "answer_impacts": [],
            "correspondence_drafts": [],
            "communication_summary": "",
            "messages": [],
        }
        try:
            await self.emit_event(
                "thinking",
                {"message": f"Managing communications for deal {deal_id}"},
                execution_id=deal_id,
            )
            fs = await communication_graph.ainvoke(initial)
            await self.emit_event(
                "output",
                {
                    "questions_drafted": len(fs["drafted_questions"]),
                    "impacts_mapped": len(fs["answer_impacts"]),
                },
                execution_id=deal_id,
            )
            return {
                "deal_id": fs["deal_id"],
                "drafted_questions": fs["drafted_questions"],
                "answer_impacts": fs["answer_impacts"],
                "correspondence_drafts": fs["correspondence_drafts"],
                "communication_summary": fs["communication_summary"],
            }
        except Exception as exc:
            logger.exception("CommunicationAgent.run failed for deal %s", deal_id)
            await self.emit_event("error", {"error": str(exc)}, execution_id=deal_id)
            return {"error": str(exc), "deal_id": deal_id}
