"""RFP Analyst AI Agent using LangGraph.

Parses RFP documents, extracts structured requirements, builds a compliance
matrix, and detects/diffs amendments.

Events: RFP_PARSED, RFP_REQUIREMENTS_EXTRACTED, RFP_COMPLIANCE_MATRIX_READY,
        RFP_AMENDMENT_DETECTED, RFP_AMENDMENT_DIFFED.
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

logger = logging.getLogger("ai_orchestrator.agents.rfp_analyst")

DJANGO_API_URL = os.getenv("DJANGO_API_URL", "http://django-api:8001")
DJANGO_SERVICE_TOKEN = os.getenv("DJANGO_SERVICE_TOKEN", "")


# ── State ─────────────────────────────────────────────────────────────────────

class RFPAnalystState(TypedDict):
    deal_id: str
    rfp_document_text: str          # Full RFP text
    deal: dict
    parsed_sections: dict           # {section_letter: content}
    requirements: list[dict]        # Extracted shall/must/will statements
    evaluation_criteria: list[dict] # Section M criteria with weights
    key_dates: dict                 # Submission deadlines, Q&A dates, etc.
    page_limits: dict               # Page/format limits from Section L
    compliance_matrix: list[dict]   # Requirements mapped to response strategies
    amendment_summary: str          # If processing an amendment
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


def _get_llm() -> ChatAnthropic:
    return ChatAnthropic(
        model="claude-sonnet-4-6",
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        max_tokens=4096,
    )


async def _llm(system: str, human: str, max_tokens: int = 2048) -> str:
    try:
        llm = ChatAnthropic(
            model="claude-sonnet-4-6",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            max_tokens=max_tokens,
        )
        resp = await llm.ainvoke([
            SystemMessage(content=system), HumanMessage(content=human)
        ])
        return resp.content
    except Exception as exc:
        logger.error("LLM failed: %s", exc)
        return ""


# ── Graph nodes ───────────────────────────────────────────────────────────────

async def load_rfp_context(state: RFPAnalystState) -> dict:
    logger.info("RFPAnalyst: loading context for deal %s", state["deal_id"])
    deal = await _get(f"/api/deals/{state['deal_id']}/", default={})
    return {
        "deal": deal,
        "messages": [HumanMessage(content=f"Analyzing RFP for: {deal.get('title', state['deal_id'])}")],
    }


async def parse_rfp_sections(state: RFPAnalystState) -> dict:
    """Parse the RFP text into standard sections (A through M)."""
    logger.info("RFPAnalyst: parsing sections for deal %s", state["deal_id"])
    import re

    doc = state["rfp_document_text"]
    if not doc:
        return {
            "parsed_sections": {},
            "messages": [HumanMessage(content="No RFP document text provided.")],
        }

    # Extract lettered sections (A-M are standard FAR uniform contract format)
    sections: dict[str, str] = {}
    section_re = re.compile(
        r'(?:^|\n)(?:SECTION|Section)\s+([A-M])\s*[\-–:]\s*([^\n]+)\n(.*?)(?=(?:^|\n)(?:SECTION|Section)\s+[A-M]\s*[\-–:]|\Z)',
        re.DOTALL | re.MULTILINE,
    )
    for m in section_re.finditer(doc):
        letter, title, body = m.group(1), m.group(2).strip(), m.group(3).strip()
        sections[letter] = body[:5000]  # Cap per section to prevent context explosion

    # If structured parsing failed, treat entire doc as raw
    if not sections:
        sections["RAW"] = doc[:8000]

    return {
        "parsed_sections": sections,
        "messages": [HumanMessage(content=f"Parsed {len(sections)} RFP section(s).")],
    }


async def extract_requirements(state: RFPAnalystState) -> dict:
    """Extract shall/must/will requirements using the RFP parser service."""
    logger.info("RFPAnalyst: extracting requirements for deal %s", state["deal_id"])
    from apps.rfp.services.parser import RFPParser  # type: ignore

    doc = state["rfp_document_text"]
    if not doc:
        return {"requirements": [], "key_dates": {}, "page_limits": {}, "evaluation_criteria": [],
                "messages": [HumanMessage(content="No document text — skipping extraction.")]}

    import asyncio
    parser = RFPParser()
    try:
        loop = asyncio.get_event_loop()
        reqs, dates, limits, criteria = await asyncio.gather(
            parser.extract_requirements(doc),
            parser.extract_dates(doc),
            parser.extract_page_limits(doc),
            parser.extract_evaluation_criteria(doc),
        )
    except Exception as exc:
        logger.error("RFP parser failed: %s", exc)
        reqs, dates, limits, criteria = [], {}, {}, []

    return {
        "requirements": reqs,
        "key_dates": dates,
        "page_limits": limits,
        "evaluation_criteria": criteria,
        "messages": [HumanMessage(content=f"Extracted {len(reqs)} requirements, {len(criteria)} evaluation criteria.")],
    }


async def build_compliance_matrix(state: RFPAnalystState) -> dict:
    """Claude builds a compliance matrix mapping each requirement to a response strategy."""
    logger.info("RFPAnalyst: building compliance matrix for deal %s", state["deal_id"])

    if not state["requirements"]:
        return {
            "compliance_matrix": [],
            "messages": [HumanMessage(content="No requirements to map — compliance matrix empty.")],
        }

    req_sample = state["requirements"][:30]  # Use first 30 for context window

    content = await _llm(
        system=(
            "You are a proposal compliance manager for a U.S. government contracting firm. "
            "Build a compliance matrix mapping each requirement to a response approach. "
            "Be concise — one row per requirement."
        ),
        human=(
            f"Opportunity: {state['deal'].get('title', '')}\n\n"
            f"Requirements ({len(state['requirements'])} total, showing {len(req_sample)}):\n"
            + "\n".join(
                f"[{r.get('requirement_id', 'REQ')}] {r.get('requirement_text', '')[:200]}"
                for r in req_sample
            )
            + "\n\n"
            "For each requirement provide a compliance matrix row:\n"
            "REQ-ID | Requirement Summary | Compliance Approach | Section Reference | Status\n"
            "Use status: COMPLIANT / PARTIAL / NON-COMPLIANT / CONDITIONAL"
        ),
        max_tokens=3000,
    )

    # Parse table rows into dicts
    matrix = []
    for line in content.split("\n"):
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 4 and parts[0].startswith("REQ"):
            matrix.append({
                "req_id": parts[0],
                "requirement_summary": parts[1] if len(parts) > 1 else "",
                "compliance_approach": parts[2] if len(parts) > 2 else "",
                "section_reference": parts[3] if len(parts) > 3 else "",
                "status": parts[4] if len(parts) > 4 else "COMPLIANT",
            })

    if not matrix:
        matrix = [{"raw_analysis": content}]

    return {
        "compliance_matrix": matrix,
        "messages": [HumanMessage(content=f"Compliance matrix built: {len(matrix)} entries.")],
    }


async def detect_amendments(state: RFPAnalystState) -> dict:
    """Detect and summarise any amendments present in the document."""
    logger.info("RFPAnalyst: detecting amendments for deal %s", state["deal_id"])

    doc = state["rfp_document_text"]
    if not doc:
        return {"amendment_summary": "", "messages": [HumanMessage(content="No document provided.")]}

    import re
    amendment_markers = re.findall(
        r'(?:amendment|modification|errata|change\s+\d+)[^\n]{0,100}',
        doc,
        re.IGNORECASE,
    )

    if not amendment_markers:
        return {
            "amendment_summary": "No amendments detected in document.",
            "messages": [HumanMessage(content="No amendments detected.")],
        }

    content = await _llm(
        system="You are an RFP amendment analyst. Summarise all changes, clarifications, and modifications found.",
        human=(
            f"Amendment markers found:\n{chr(10).join(amendment_markers[:20])}\n\n"
            f"Full document excerpt (first 3000 chars):\n{doc[:3000]}\n\n"
            "Summarise:\n"
            "1. Number of amendments/modifications\n"
            "2. Key changes to requirements\n"
            "3. Date/deadline changes\n"
            "4. Page limit or format changes\n"
            "5. New or deleted requirements"
        ),
    )

    return {
        "amendment_summary": content,
        "messages": [HumanMessage(content=f"Detected {len(amendment_markers)} amendment marker(s).")],
    }


# ── Graph ─────────────────────────────────────────────────────────────────────

def build_rfp_analyst_graph() -> StateGraph:
    wf = StateGraph(RFPAnalystState)
    wf.add_node("load_rfp_context", load_rfp_context)
    wf.add_node("parse_rfp_sections", parse_rfp_sections)
    wf.add_node("extract_requirements", extract_requirements)
    wf.add_node("build_compliance_matrix", build_compliance_matrix)
    wf.add_node("detect_amendments", detect_amendments)
    wf.set_entry_point("load_rfp_context")
    wf.add_edge("load_rfp_context", "parse_rfp_sections")
    wf.add_edge("parse_rfp_sections", "extract_requirements")
    wf.add_edge("extract_requirements", "build_compliance_matrix")
    wf.add_edge("build_compliance_matrix", "detect_amendments")
    wf.add_edge("detect_amendments", END)
    return wf.compile()


rfp_analyst_graph = build_rfp_analyst_graph()


# ── Agent ─────────────────────────────────────────────────────────────────────

class RFPAnalystAgent(BaseAgent):
    """AI agent that parses RFPs, extracts requirements, and builds compliance matrices."""

    agent_name = "rfp_analyst_agent"

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        deal_id = input_data.get("deal_id", "")
        if not deal_id:
            return {"error": "deal_id is required"}

        initial: RFPAnalystState = {
            "deal_id": deal_id,
            "rfp_document_text": input_data.get("rfp_document_text", ""),
            "deal": {},
            "parsed_sections": {},
            "requirements": [],
            "evaluation_criteria": [],
            "key_dates": {},
            "page_limits": {},
            "compliance_matrix": [],
            "amendment_summary": "",
            "messages": [],
        }
        try:
            await self.emit_event(
                "thinking",
                {"message": f"Parsing RFP for deal {deal_id}"},
                execution_id=deal_id,
            )
            fs = await rfp_analyst_graph.ainvoke(initial)
            await self.emit_event(
                "output",
                {
                    "requirements_count": len(fs["requirements"]),
                    "compliance_matrix_count": len(fs["compliance_matrix"]),
                },
                execution_id=deal_id,
            )
            return {
                "deal_id": fs["deal_id"],
                "parsed_sections": list(fs["parsed_sections"].keys()),
                "requirements": fs["requirements"],
                "evaluation_criteria": fs["evaluation_criteria"],
                "key_dates": fs["key_dates"],
                "page_limits": fs["page_limits"],
                "compliance_matrix": fs["compliance_matrix"],
                "amendment_summary": fs["amendment_summary"],
            }
        except Exception as exc:
            logger.exception("RFPAnalystAgent.run failed for deal %s", deal_id)
            await self.emit_event("error", {"error": str(exc)}, execution_id=deal_id)
            return {"error": str(exc), "deal_id": deal_id}
