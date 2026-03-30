"""CUI Handler AI Agent using LangGraph.

Detects and flags Controlled Unclassified Information (CUI) in proposal
content. Ensures CUI markings are applied per 32 CFR Part 2002 before
external distribution. Checks for proper handling of FOUO, ITAR, EAR,
and other CUI categories.

Events: CUI_SCAN_STARTED, CUI_DETECTED, CUI_MARKINGS_VERIFIED, CUI_REPORT_GENERATED.
"""
import logging
import os
from typing import Annotated, Any
import operator

import httpx
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from typing_extensions import TypedDict

from src.agents.base import BaseAgent
from src.llm_provider import get_chat_model

logger = logging.getLogger("ai_orchestrator.agents.cui_handler")

DJANGO_API_URL = os.getenv("DJANGO_API_URL", "http://django-api:8001")
DJANGO_SERVICE_TOKEN = os.getenv("DJANGO_SERVICE_TOKEN", "")


# ── CUI Categories (32 CFR Part 2002) ────────────────────────────────────────

CUI_CATEGORIES = [
    "CTI",          # Controlled Technical Information
    "ITAR",         # International Traffic in Arms Regulations
    "EAR",          # Export Administration Regulations
    "FOUO",         # For Official Use Only
    "SBU",          # Sensitive But Unclassified
    "PCII",         # Protected Critical Infrastructure Information
    "SSI",          # Sensitive Security Information
    "LES",          # Law Enforcement Sensitive
    "PII",          # Personally Identifiable Information
    "PHI",          # Protected Health Information
    "PROPIN",       # Proprietary Information
    "EXDIS",        # Exclusive Distribution
]

CUI_MARKING_PATTERNS = [
    "CUI//",
    "CONTROLLED//",
    "CUI//SP-",     # CUI Specified
    "CUI//BASIC",   # CUI Basic
    "DISTRIBUTION STATEMENT",
    "EXPORT CONTROLLED",
    "ITAR CONTROLLED",
]


# ── State ─────────────────────────────────────────────────────────────────────

class CUIHandlerState(TypedDict):
    deal_id: str
    deal: dict
    proposal_sections: list[dict]   # {title, content}
    cui_detections: list[dict]      # {section, category, excerpt, severity}
    marking_issues: list[dict]      # {section, issue, recommendation}
    distribution_statement: str
    handling_instructions: str
    cui_report: dict
    messages: Annotated[list, operator.add]


# ── Django API helpers ────────────────────────────────────────────────────────

def _auth_headers() -> dict[str, str]:
    token = DJANGO_SERVICE_TOKEN
    return {"Authorization": f"Bearer {token}"} if token else {}


async def _fetch_proposal_sections(deal_id: str) -> list[dict]:
    """Fetch proposal sections for CUI scanning."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{DJANGO_API_URL}/api/deals/deals/{deal_id}/artifacts/",
                headers=_auth_headers(),
            )
            if resp.status_code == 200:
                artifacts = resp.json()
                proposal = artifacts.get("proposal")
                if proposal and proposal.get("id"):
                    sec_resp = await client.get(
                        f"{DJANGO_API_URL}/api/proposals/proposals/{proposal['id']}/",
                        headers=_auth_headers(),
                    )
                    if sec_resp.status_code == 200:
                        data = sec_resp.json()
                        return data.get("sections", [])
        return []
    except Exception as exc:
        logger.warning("Failed to fetch proposal sections for deal %s: %s", deal_id, exc)
        return []


# ── Graph Nodes ───────────────────────────────────────────────────────────────

async def gather_content(state: CUIHandlerState) -> dict:
    """Gather proposal content for CUI scanning."""
    deal_id = state["deal_id"]
    sections = await _fetch_proposal_sections(deal_id)

    # Also fetch deal context
    deal = {}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{DJANGO_API_URL}/api/deals/deals/{deal_id}/",
                headers=_auth_headers(),
            )
            if resp.status_code == 200:
                deal = resp.json()
    except Exception:
        pass

    return {
        "deal": deal,
        "proposal_sections": sections,
        "messages": [{"role": "system", "content": f"Gathered {len(sections)} sections for CUI scan"}],
    }


async def scan_for_cui(state: CUIHandlerState) -> dict:
    """Scan proposal content for CUI indicators."""
    llm = get_chat_model(max_tokens=4000)
    sections = state.get("proposal_sections", [])
    deal = state.get("deal", {})

    if not sections:
        return {
            "cui_detections": [],
            "messages": [{"role": "assistant", "content": "No sections to scan"}],
        }

    # Build content summary for scanning
    content_for_scan = "\n\n".join(
        f"=== SECTION: {s.get('title', 'Untitled')} ===\n{s.get('content', '')[:3000]}"
        for s in sections[:20]
    )

    prompt = f"""You are a CUI (Controlled Unclassified Information) compliance specialist
for federal government contracts. Scan the following proposal content for potential CUI.

Contract: {deal.get('title', 'N/A')}

CUI categories to check: {', '.join(CUI_CATEGORIES)}

PROPOSAL CONTENT:
{content_for_scan[:12000]}

For each detection, provide a JSON array of objects with:
- "section": section title where found
- "category": CUI category (from list above)
- "excerpt": brief excerpt of the problematic text (max 100 chars)
- "severity": "high" | "medium" | "low"
- "recommendation": what action to take

If no CUI is detected, return an empty array [].
Return ONLY the JSON array, no other text."""

    resp = await llm.ainvoke([
        SystemMessage(content="You are a CUI compliance expert for federal proposals. Be thorough but avoid false positives."),
        HumanMessage(content=prompt),
    ])

    # Parse detections
    detections = []
    try:
        import json
        text = resp.content.strip()
        if text.startswith("["):
            detections = json.loads(text)
    except Exception:
        logger.warning("Failed to parse CUI detections, treating as text response")
        if "no cui" not in resp.content.lower() and "empty" not in resp.content.lower():
            detections = [{"section": "General", "category": "REVIEW_NEEDED", "excerpt": resp.content[:200], "severity": "medium", "recommendation": "Manual review recommended"}]

    return {
        "cui_detections": detections,
        "messages": [{"role": "assistant", "content": f"Found {len(detections)} potential CUI items"}],
    }


async def verify_markings(state: CUIHandlerState) -> dict:
    """Verify CUI markings are properly applied."""
    llm = get_chat_model(max_tokens=2000)
    sections = state.get("proposal_sections", [])
    detections = state.get("cui_detections", [])

    # Check for proper CUI markings in content
    marking_issues = []

    if detections:
        prompt = f"""Based on {len(detections)} CUI detections in this proposal, verify that
proper CUI markings are in place per 32 CFR Part 2002.

Detections: {detections[:10]}

Check for:
1. Banner markings on each page ("CUI" or "CONTROLLED")
2. Portion markings on paragraphs containing CUI
3. Distribution/dissemination statements
4. Proper CUI category designations
5. Destruction/handling instructions

Provide a JSON array of marking issues found, each with:
- "section": affected section
- "issue": description of the marking problem
- "recommendation": how to fix it

Return ONLY the JSON array."""

        resp = await llm.ainvoke([
            SystemMessage(content="You are a CUI marking compliance expert."),
            HumanMessage(content=prompt),
        ])

        try:
            import json
            text = resp.content.strip()
            if text.startswith("["):
                marking_issues = json.loads(text)
        except Exception:
            marking_issues = [{"section": "General", "issue": "Could not verify markings automatically", "recommendation": "Manual review of CUI markings required"}]

    # Determine distribution statement
    distribution = "DISTRIBUTION STATEMENT D: Distribution authorized to DoD and U.S. Government agencies only."
    if not detections:
        distribution = "No CUI detected — standard distribution applies."

    return {
        "marking_issues": marking_issues,
        "distribution_statement": distribution,
        "handling_instructions": "Handle per 32 CFR Part 2002. Destroy when no longer needed." if detections else "",
        "messages": [{"role": "assistant", "content": f"Found {len(marking_issues)} marking issues"}],
    }


async def generate_report(state: CUIHandlerState) -> dict:
    """Generate final CUI compliance report."""
    detections = state.get("cui_detections", [])
    marking_issues = state.get("marking_issues", [])
    deal = state.get("deal", {})

    high_severity = sum(1 for d in detections if d.get("severity") == "high")
    medium_severity = sum(1 for d in detections if d.get("severity") == "medium")

    report = {
        "deal_id": state["deal_id"],
        "deal_title": deal.get("title", "N/A"),
        "total_detections": len(detections),
        "high_severity": high_severity,
        "medium_severity": medium_severity,
        "low_severity": len(detections) - high_severity - medium_severity,
        "marking_issues": len(marking_issues),
        "distribution_statement": state.get("distribution_statement", ""),
        "handling_instructions": state.get("handling_instructions", ""),
        "detections": detections,
        "marking_issues_detail": marking_issues,
        "compliant": len(detections) == 0 or (high_severity == 0 and len(marking_issues) == 0),
        "recommendation": (
            "CUI compliance verified — no issues found."
            if not detections
            else f"Review required: {high_severity} high, {medium_severity} medium severity CUI items detected."
        ),
    }

    return {
        "cui_report": report,
        "messages": [{"role": "assistant", "content": f"CUI report: {report['recommendation']}"}],
    }


# ── Graph ─────────────────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    g = StateGraph(CUIHandlerState)
    g.add_node("gather_content", gather_content)
    g.add_node("scan_for_cui", scan_for_cui)
    g.add_node("verify_markings", verify_markings)
    g.add_node("generate_report", generate_report)

    g.set_entry_point("gather_content")
    g.add_edge("gather_content", "scan_for_cui")
    g.add_edge("scan_for_cui", "verify_markings")
    g.add_edge("verify_markings", "generate_report")
    g.add_edge("generate_report", END)
    return g


_graph = build_graph().compile()


# ── Agent ─────────────────────────────────────────────────────────────────────

class CUIHandlerAgent(BaseAgent):
    agent_name = "cui_handler_agent"

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        deal_id = input_data.get("deal_id", "")
        await self.emit_event("thinking", {"message": "Scanning for Controlled Unclassified Information..."}, deal_id)

        initial_state: CUIHandlerState = {
            "deal_id": deal_id,
            "deal": {},
            "proposal_sections": [],
            "cui_detections": [],
            "marking_issues": [],
            "distribution_statement": "",
            "handling_instructions": "",
            "cui_report": {},
            "messages": [],
        }

        result = await _graph.ainvoke(initial_state)

        report = result.get("cui_report", {})
        await self.emit_event("output", {
            "message": report.get("recommendation", "CUI scan complete"),
            "total_detections": report.get("total_detections", 0),
            "compliant": report.get("compliant", True),
        }, deal_id)

        return report
