"""
Amendment Diff Agent — detects and analyzes changes when a solicitation amendment drops.

Compares current solicitation against a previous version, identifies:
- Changed paragraphs/sections (diff)
- Impact on proposal sections (what needs updating)
- New/removed requirements
- Changed evaluation criteria
- Deadline changes
- Triggers re-approval gates if substantive changes found
"""
import difflib
import logging
import operator
import os
from typing import Annotated, Any

import httpx
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from typing_extensions import TypedDict

from src.agents.base import BaseAgent

logger = logging.getLogger("ai_orchestrator.agents.amendment_diff")

DJANGO_API_URL = os.getenv("DJANGO_API_URL", "http://django-api:8001")
DJANGO_SERVICE_TOKEN = os.getenv("DJANGO_SERVICE_TOKEN", "")


# ── State ─────────────────────────────────────────────────────────────────────


class AmendmentDiffState(TypedDict):
    deal_id: str
    amendment_id: str
    original_text: str                    # Text of the original solicitation
    amended_text: str                     # Text of the amended solicitation
    diff_sections: list[dict]             # [{type: added|removed|changed, content: str}]
    impact_analysis: str                  # LLM narrative of the impact
    affected_proposal_sections: list[str] # Proposal sections that need updates
    requires_reapproval: bool             # True if substantive changes require re-approval
    change_summary: str                   # Executive-level summary of all changes
    messages: Annotated[list, operator.add]


# ── Helpers ───────────────────────────────────────────────────────────────────


def _auth_headers() -> dict[str, str]:
    t = DJANGO_SERVICE_TOKEN
    return {"Authorization": f"Bearer {t}"} if t else {}


async def _get(path: str, default: Any = None) -> Any:
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{DJANGO_API_URL}{path}", headers=_auth_headers()
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.warning("AmendmentDiff API GET %s failed: %s", path, exc)
        return default


async def _post(path: str, body: dict) -> dict:
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{DJANGO_API_URL}{path}",
                json=body,
                headers=_auth_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.warning("AmendmentDiff API POST %s failed: %s", path, exc)
        return {"error": str(exc)}


async def _llm(system: str, human: str, max_tokens: int = 3000) -> str:
    try:
        llm = ChatAnthropic(
            model="claude-sonnet-4-6",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            max_tokens=max_tokens,
        )
        resp = await llm.ainvoke(
            [SystemMessage(content=system), HumanMessage(content=human)]
        )
        return resp.content if isinstance(resp.content, str) else str(resp.content)
    except Exception as exc:
        logger.error("AmendmentDiff LLM call failed: %s", exc)
        return ""


# ── Graph nodes ───────────────────────────────────────────────────────────────


async def load_amendment(state: AmendmentDiffState) -> dict:
    """
    Fetch the original and amended solicitation text from the Django backend.

    Loads the amendment record to get the amendment_id, then fetches the
    original solicitation text and the amended text for comparison.
    """
    deal_id = state["deal_id"]
    amendment_id = state.get("amendment_id") or ""
    logger.info(
        "AmendmentDiff: loading amendment %s for deal %s", amendment_id, deal_id
    )

    # Fetch deal for context
    deal = await _get(f"/api/deals/{deal_id}/", default={})

    # Fetch amendment record
    amendment: dict = {}
    if amendment_id:
        amendment = await _get(
            f"/api/rfp/amendments/{amendment_id}/", default={}
        ) or {}

    # Try to get the solicitation texts from the amendment record
    original_text: str = (
        state.get("original_text")
        or amendment.get("original_text")
        or amendment.get("base_solicitation_text")
        or ""
    )
    amended_text: str = (
        state.get("amended_text")
        or amendment.get("amended_text")
        or amendment.get("amendment_text")
        or amendment.get("full_text")
        or ""
    )

    # Fallback: fetch from deal's solicitation documents
    if not original_text or not amended_text:
        rfp_docs = await _get(
            f"/api/rfp/documents/?deal={deal_id}&ordering=-created_at", default={}
        )
        docs = rfp_docs.get("results", []) if isinstance(rfp_docs, dict) else []
        if len(docs) >= 2:
            amended_text = amended_text or docs[0].get("full_text") or ""
            original_text = original_text or docs[1].get("full_text") or ""
        elif len(docs) == 1:
            amended_text = amended_text or docs[0].get("full_text") or ""

    return {
        "original_text": original_text,
        "amended_text": amended_text,
        "messages": [
            HumanMessage(
                content=(
                    f"Loaded amendment for deal {deal_id}. "
                    f"Original: {len(original_text)} chars, "
                    f"Amended: {len(amended_text)} chars."
                )
            )
        ],
    }


async def compute_text_diff(state: AmendmentDiffState) -> dict:
    """
    Compute a structured diff between the original and amended solicitation texts.

    Splits both documents into paragraphs (double-newline delimited), runs a
    unified diff, and tags each changed block as 'added', 'removed', or 'changed'.
    """
    logger.info(
        "AmendmentDiff: computing text diff for deal %s", state["deal_id"]
    )

    original = state.get("original_text") or ""
    amended = state.get("amended_text") or ""

    if not original and not amended:
        return {
            "diff_sections": [],
            "messages": [HumanMessage(content="No text available for diff computation.")],
        }

    # Split into paragraphs for meaningful diff granularity
    original_paragraphs = [
        p.strip() for p in original.split("\n\n") if p.strip()
    ]
    amended_paragraphs = [
        p.strip() for p in amended.split("\n\n") if p.strip()
    ]

    # Generate unified diff
    diff_lines = list(
        difflib.unified_diff(
            original_paragraphs,
            amended_paragraphs,
            lineterm="",
            n=0,
        )
    )

    diff_sections: list[dict] = []
    current_block: dict | None = None

    for line in diff_lines:
        if line.startswith("---") or line.startswith("+++") or line.startswith("@@"):
            # Flush current block
            if current_block:
                diff_sections.append(current_block)
                current_block = None
            continue

        if line.startswith("-"):
            content = line[1:].strip()
            if content:
                if current_block and current_block["type"] == "removed":
                    current_block["content"] += "\n" + content
                else:
                    if current_block:
                        diff_sections.append(current_block)
                    current_block = {"type": "removed", "content": content}

        elif line.startswith("+"):
            content = line[1:].strip()
            if content:
                if current_block and current_block["type"] == "added":
                    current_block["content"] += "\n" + content
                elif current_block and current_block["type"] == "removed":
                    # Treat remove+add pair as "changed"
                    current_block["type"] = "changed"
                    current_block["new_content"] = content
                else:
                    if current_block:
                        diff_sections.append(current_block)
                    current_block = {"type": "added", "content": content}
        else:
            if current_block:
                diff_sections.append(current_block)
                current_block = None

    if current_block:
        diff_sections.append(current_block)

    # Limit to most significant changes for context window management
    diff_sections = diff_sections[:50]

    logger.info(
        "AmendmentDiff: found %d changed section(s) for deal %s",
        len(diff_sections), state["deal_id"],
    )

    return {
        "diff_sections": diff_sections,
        "messages": [
            HumanMessage(
                content=f"Diff computed: {len(diff_sections)} changed section(s) detected."
            )
        ],
    }


async def analyze_impact(state: AmendmentDiffState) -> dict:
    """
    Use the LLM to analyze the impact of the detected changes on the proposal.

    Identifies which proposal sections need updating, whether evaluation criteria
    changed, whether requirements were added/removed/modified, and whether
    re-approval is warranted.
    """
    deal_id = state["deal_id"]
    logger.info("AmendmentDiff: analyzing impact for deal %s", deal_id)

    diff_sections = state.get("diff_sections") or []
    if not diff_sections:
        return {
            "impact_analysis": "No changes detected — amendment appears identical to original.",
            "affected_proposal_sections": [],
            "change_summary": "No substantive changes found in this amendment.",
            "messages": [HumanMessage(content="No diff sections to analyze.")],
        }

    diff_text = "\n\n".join(
        f"[{s['type'].upper()}] {s.get('content', '')[:400]}"
        + (f"\n→ NEW: {s.get('new_content', '')[:400]}" if s.get("new_content") else "")
        for s in diff_sections[:20]
    )

    system_prompt = (
        "You are a proposal manager with deep US government contracting expertise. "
        "Given these changed RFP sections from a solicitation amendment, identify:\n\n"
        "1. Which proposal sections need updating (be specific: Technical Approach, "
        "   Management Plan, Past Performance, Price Volume, etc.)\n"
        "2. Whether evaluation criteria (Section M) changed — specify what changed\n"
        "3. Whether any requirements were added, removed, or modified\n"
        "4. Whether this amendment requires proposal re-approval (Yes/No and why)\n"
        "5. New submission deadlines or Q&A dates introduced\n"
        "6. Any new compliance forms or certifications required\n\n"
        "Be specific and actionable. Format your response with clear section headers."
    )

    human_prompt = (
        f"Changed RFP Sections ({len(diff_sections)} total):\n{diff_text}\n\n"
        "Provide your complete impact analysis."
    )

    impact_analysis = await _llm(system_prompt, human_prompt, max_tokens=3000)

    # Extract affected sections from the analysis text (heuristic)
    proposal_section_keywords = [
        "Technical Approach", "Management Plan", "Management Approach",
        "Past Performance", "Price Volume", "Staffing Plan", "Transition Plan",
        "Quality Plan", "Risk Management", "Security Approach",
        "Executive Summary", "Compliance Matrix",
    ]
    affected_proposal_sections = [
        kw for kw in proposal_section_keywords if kw.lower() in impact_analysis.lower()
    ]

    # Build a concise change summary
    change_summary_prompt = (
        "Summarize the following amendment impact analysis in 2-3 sentences suitable "
        "for a management briefing. Include the number of sections affected and the "
        "most critical change.\n\n" + impact_analysis[:2000]
    )
    change_summary = await _llm(
        "You are a technical writer producing executive briefing summaries.",
        change_summary_prompt,
        max_tokens=300,
    )

    return {
        "impact_analysis": impact_analysis,
        "affected_proposal_sections": affected_proposal_sections,
        "change_summary": change_summary,
        "messages": [
            HumanMessage(
                content=(
                    f"Impact analysis complete. "
                    f"{len(affected_proposal_sections)} proposal section(s) need updates."
                )
            )
        ],
    }


async def determine_reapproval(state: AmendmentDiffState) -> dict:
    """
    Determine whether this amendment requires proposal re-approval.

    Sets requires_reapproval=True if:
      - Evaluation criteria changed
      - Requirements were added
      - Proposal sections with HITL gates are affected (e.g. pricing, final submission)
    """
    deal_id = state["deal_id"]
    logger.info("AmendmentDiff: determining re-approval need for deal %s", deal_id)

    impact_analysis = state.get("impact_analysis") or ""
    affected_sections = state.get("affected_proposal_sections") or []
    diff_sections = state.get("diff_sections") or []

    # Trigger re-approval if evaluation criteria changed
    criteria_changed = any(
        keyword in impact_analysis.lower()
        for keyword in [
            "evaluation criteria", "section m", "evaluation factor",
            "evaluation weight", "criteria changed", "criteria modified",
        ]
    )

    # Trigger re-approval if new requirements were added
    requirements_added = any(
        keyword in impact_analysis.lower()
        for keyword in [
            "requirement added", "new requirement", "shall now", "must now",
            "additional requirement", "added requirement",
        ]
    )

    # Trigger re-approval if substantive sections were affected
    high_impact_sections = {
        "Price Volume", "Compliance Matrix", "Technical Approach", "Past Performance"
    }
    substantive_section_affected = bool(
        high_impact_sections.intersection(set(affected_sections))
    )

    # Trigger re-approval if there are a significant number of changes
    large_change_volume = len(diff_sections) >= 10

    requires_reapproval = (
        criteria_changed
        or requirements_added
        or substantive_section_affected
        or large_change_volume
    )

    reasons = []
    if criteria_changed:
        reasons.append("evaluation criteria changed")
    if requirements_added:
        reasons.append("new requirements added")
    if substantive_section_affected:
        reasons.append(f"substantive sections affected: {affected_sections}")
    if large_change_volume:
        reasons.append(f"large change volume ({len(diff_sections)} sections)")

    reason_str = "; ".join(reasons) if reasons else "no substantive changes detected"
    logger.info(
        "AmendmentDiff: requires_reapproval=%s (%s) for deal %s",
        requires_reapproval, reason_str, deal_id,
    )

    return {
        "requires_reapproval": requires_reapproval,
        "messages": [
            HumanMessage(
                content=(
                    f"Re-approval required: {requires_reapproval}. Reason: {reason_str}."
                )
            )
        ],
    }


async def notify_team(state: AmendmentDiffState) -> dict:
    """
    POST the amendment impact report to the Django amendment impact endpoint.

    Creates an amendment impact record in the backend so the proposal team
    is notified and the workflow can be re-triggered if needed.
    """
    deal_id = state["deal_id"]
    amendment_id = state.get("amendment_id") or ""
    logger.info("AmendmentDiff: notifying team for deal %s", deal_id)

    payload = {
        "deal_id": deal_id,
        "amendment_id": amendment_id,
        "change_summary": state.get("change_summary") or "",
        "impact_analysis": (state.get("impact_analysis") or "")[:5000],
        "affected_proposal_sections": state.get("affected_proposal_sections") or [],
        "requires_reapproval": state.get("requires_reapproval") or False,
        "diff_section_count": len(state.get("diff_sections") or []),
    }

    result = await _post(
        f"/api/rfp/amendments/{amendment_id}/impact/" if amendment_id
        else f"/api/deals/{deal_id}/amendment-impact/",
        payload,
    )

    if "error" in result:
        logger.warning(
            "AmendmentDiff: failed to post impact notification for deal %s: %s",
            deal_id, result["error"],
        )
    else:
        logger.info(
            "AmendmentDiff: impact notification posted for deal %s (id=%s)",
            deal_id, result.get("id"),
        )

    return {
        "messages": [
            HumanMessage(
                content=(
                    f"Team notified of amendment impact. "
                    f"Re-approval required: {state.get('requires_reapproval')}."
                )
            )
        ]
    }


# ── Graph ─────────────────────────────────────────────────────────────────────


def build_amendment_diff_graph():
    wf = StateGraph(AmendmentDiffState)
    wf.add_node("load_amendment", load_amendment)
    wf.add_node("compute_text_diff", compute_text_diff)
    wf.add_node("analyze_impact", analyze_impact)
    wf.add_node("determine_reapproval", determine_reapproval)
    wf.add_node("notify_team", notify_team)

    wf.set_entry_point("load_amendment")
    wf.add_edge("load_amendment", "compute_text_diff")
    wf.add_edge("compute_text_diff", "analyze_impact")
    wf.add_edge("analyze_impact", "determine_reapproval")
    wf.add_edge("determine_reapproval", "notify_team")
    wf.add_edge("notify_team", END)
    return wf.compile()


amendment_diff_graph = build_amendment_diff_graph()


# ── Agent ─────────────────────────────────────────────────────────────────────


class AmendmentDiffAgent(BaseAgent):
    """
    AI agent that detects and analyzes changes when a solicitation amendment drops.

    Compares original vs. amended solicitation texts, identifies changed sections,
    assesses proposal impact, and triggers re-approval gates when substantive
    changes are found.
    """

    agent_name = "amendment_diff_agent"

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        deal_id = input_data.get("deal_id", "")
        if not deal_id:
            return {"error": "deal_id is required"}

        initial: AmendmentDiffState = {
            "deal_id": deal_id,
            "amendment_id": input_data.get("amendment_id", ""),
            "original_text": input_data.get("original_text", ""),
            "amended_text": input_data.get("amended_text", ""),
            "diff_sections": [],
            "impact_analysis": "",
            "affected_proposal_sections": [],
            "requires_reapproval": False,
            "change_summary": "",
            "messages": [],
        }

        try:
            await self.emit_event(
                "thinking",
                {
                    "message": (
                        f"Analyzing amendment {initial['amendment_id']} for deal {deal_id}"
                    )
                },
                execution_id=deal_id,
            )
            fs = await amendment_diff_graph.ainvoke(initial)
            await self.emit_event(
                "output",
                {
                    "diff_sections_count": len(fs["diff_sections"]),
                    "affected_proposal_sections": fs["affected_proposal_sections"],
                    "requires_reapproval": fs["requires_reapproval"],
                },
                execution_id=deal_id,
            )
            return {
                "deal_id": fs["deal_id"],
                "amendment_id": fs["amendment_id"],
                "diff_sections": fs["diff_sections"],
                "impact_analysis": fs["impact_analysis"],
                "affected_proposal_sections": fs["affected_proposal_sections"],
                "requires_reapproval": fs["requires_reapproval"],
                "change_summary": fs["change_summary"],
            }
        except Exception as exc:
            logger.exception(
                "AmendmentDiffAgent.run failed for deal %s", deal_id
            )
            await self.emit_event(
                "error", {"error": str(exc)}, execution_id=deal_id
            )
            return {"error": str(exc), "deal_id": deal_id}
