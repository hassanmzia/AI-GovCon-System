"""Submission Package AI Agent using LangGraph.

Assembles the final proposal submission package through a 5-node pipeline:
  1. load_submission_context — fetch deal, proposal, RFP, and pricing data
  2. verify_completeness — check all sections complete, compliance 100%, pricing approved
  3. validate_formatting — enforce page limits, required volumes, attachment presence
  4. generate_checklist — build per-item submission checklist with status
  5. package_submission — produce final readiness summary and risk assessment

Events: SUBMISSION_PACKAGED, SUBMISSION_CHECKLIST_READY.
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

logger = logging.getLogger("ai_orchestrator.agents.submission")

DJANGO_API_URL = os.getenv("DJANGO_API_URL", "http://django-api:8001")
DJANGO_SERVICE_TOKEN = os.getenv("DJANGO_SERVICE_TOKEN", "")

# Standard proposal volumes and required contents
_REQUIRED_VOLUMES = [
    "Volume I - Technical Approach",
    "Volume II - Management Approach",
    "Volume III - Past Performance",
    "Volume IV - Price/Cost",
]

_STANDARD_ATTACHMENTS = [
    "Cover Letter / Transmittal",
    "Table of Contents",
    "Executive Summary",
    "Representations and Certifications",
    "Small Business Subcontracting Plan",
    "Resumes / Key Personnel",
    "Teaming Agreements",
    "Price Breakdown / Cost Detail",
]


# ── State ─────────────────────────────────────────────────────────────────────

class SubmissionState(TypedDict):
    deal_id: str
    deal: dict
    opportunity: dict
    proposal: dict                   # Full proposal record from Django
    proposal_sections: dict          # {title: text} — final approved sections
    compliance_matrix: list[dict]    # From compliance agent
    pricing_volume: dict             # Pricing volume status
    qa_summary: str                  # From QA agent
    key_dates: dict                  # From RFP analyst
    page_limits: dict                # From RFP analyst
    # Verification results
    completeness_issues: list[str]   # Issues found during completeness check
    formatting_issues: list[str]     # Issues found during formatting check
    all_sections_complete: bool
    compliance_at_100: bool
    pricing_approved: bool
    page_limits_met: bool
    # Outputs
    checklist: list[dict]            # [{item, status, notes, category}]
    missing_items: list[str]         # Items not yet complete
    submission_package_summary: str  # Final summary of what is ready
    submission_risks: list[str]      # Risks to address before submission
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
        llm = get_chat_model(max_tokens=max_tokens)
        resp = await llm.ainvoke([SystemMessage(content=system), HumanMessage(content=human)])
        return resp.content
    except Exception as exc:
        logger.error("LLM failed: %s", exc)
        return ""


# ── Node 1: Load Submission Context ──────────────────────────────────────────

async def load_submission_context(state: SubmissionState) -> dict:
    """Fetch deal, proposal, RFP, pricing, and compliance data from Django."""
    logger.info("SubmissionAgent [1/5]: loading context for deal %s", state["deal_id"])
    deal_id = state["deal_id"]

    deal = await _get(f"/api/deals/{deal_id}/", default={})
    opp_id = deal.get("opportunity", "")
    opportunity = await _get(f"/api/opportunities/{opp_id}/", default={}) if opp_id else {}

    # Fetch proposal (latest version)
    proposals = await _get(f"/api/proposals/?deal={deal_id}&ordering=-version&limit=1", default=[])
    proposal = proposals[0] if isinstance(proposals, list) and proposals else {}
    proposal_id = proposal.get("id", "")

    # Fetch proposal sections
    sections_data = await _get(
        f"/api/proposals/{proposal_id}/sections/", default=[]
    ) if proposal_id else []
    proposal_sections = {}
    if isinstance(sections_data, list):
        for sec in sections_data:
            title = sec.get("title", "")
            content = sec.get("final_content") or sec.get("human_content") or sec.get("ai_draft", "")
            if title:
                proposal_sections[title] = content

    # Fetch RFP requirements for key dates and page limits
    rfp_data = await _get(f"/api/rfp/documents/?deal={deal_id}&limit=1", default=[])
    rfp_doc = rfp_data[0] if isinstance(rfp_data, list) and rfp_data else {}
    key_dates = rfp_doc.get("extracted_dates", {}) if isinstance(rfp_doc, dict) else {}
    page_limits = rfp_doc.get("extracted_page_limits", {}) if isinstance(rfp_doc, dict) else {}

    # Fetch compliance matrix
    compliance_matrix = await _get(
        f"/api/rfp/compliance/?deal={deal_id}", default=[]
    )
    if isinstance(compliance_matrix, dict):
        compliance_matrix = compliance_matrix.get("results", [])

    # Fetch pricing volume status
    pricing_data = await _get(f"/api/pricing/volumes/?deal={deal_id}&limit=1", default=[])
    pricing_volume = pricing_data[0] if isinstance(pricing_data, list) and pricing_data else {}

    return {
        "deal": deal,
        "opportunity": opportunity,
        "proposal": proposal,
        "proposal_sections": proposal_sections,
        "compliance_matrix": compliance_matrix if isinstance(compliance_matrix, list) else [],
        "pricing_volume": pricing_volume,
        "key_dates": key_dates,
        "page_limits": page_limits,
        "messages": [HumanMessage(content=f"Context loaded for: {deal.get('title', deal_id)}")],
    }


# ── Node 2: Verify Completeness ─────────────────────────────────────────────

async def verify_completeness(state: SubmissionState) -> dict:
    """Check that all sections are complete, compliance is 100%, and pricing is approved."""
    logger.info("SubmissionAgent [2/5]: verifying completeness for deal %s", state["deal_id"])

    issues: list[str] = []
    proposal = state.get("proposal") or {}
    proposal_sections = state.get("proposal_sections") or {}
    compliance_matrix = state.get("compliance_matrix") or []
    pricing_volume = state.get("pricing_volume") or {}

    # ── Check: All sections complete ─────────────────────────────────
    all_complete = True
    if not proposal_sections:
        issues.append("No proposal sections found — proposal content is empty")
        all_complete = False
    else:
        empty_sections = [
            title for title, content in proposal_sections.items()
            if not content or not content.strip()
        ]
        if empty_sections:
            all_complete = False
            for sec in empty_sections[:5]:
                issues.append(f"Section '{sec}' has no content")
            if len(empty_sections) > 5:
                issues.append(f"... and {len(empty_sections) - 5} more empty sections")

    # Check section approval status from proposal data
    sections_list = proposal.get("sections", [])
    if isinstance(sections_list, list):
        unapproved = [
            s.get("title", "Unknown")
            for s in sections_list
            if s.get("status") not in ("approved", "revised")
        ]
        if unapproved:
            for sec in unapproved[:3]:
                issues.append(f"Section '{sec}' is not yet approved")
            if len(unapproved) > 3:
                issues.append(f"... and {len(unapproved) - 3} more unapproved sections")

    # ── Check: Compliance matrix at 100% ─────────────────────────────
    compliance_100 = False
    if not compliance_matrix:
        issues.append("No compliance matrix items found")
    else:
        total = len(compliance_matrix)
        compliant = sum(
            1 for item in compliance_matrix
            if item.get("compliance_status") == "compliant"
        )
        pct = (compliant / total * 100) if total > 0 else 0
        if pct < 100:
            issues.append(
                f"Compliance matrix at {pct:.0f}% ({compliant}/{total} compliant) — must be 100%"
            )
        else:
            compliance_100 = True

    # ── Check: Pricing approved ──────────────────────────────────────
    pricing_approved = False
    pricing_status = pricing_volume.get("status", "")
    if pricing_status in ("approved", "final"):
        pricing_approved = True
    elif pricing_status == "draft":
        issues.append("Pricing volume is still in draft — requires approval")
    else:
        issues.append("No pricing volume found — pricing data is missing")

    return {
        "completeness_issues": issues,
        "all_sections_complete": all_complete,
        "compliance_at_100": compliance_100,
        "pricing_approved": pricing_approved,
        "messages": [HumanMessage(content=f"Completeness check: {len(issues)} issues found")],
    }


# ── Node 3: Validate Formatting ─────────────────────────────────────────────

async def validate_formatting(state: SubmissionState) -> dict:
    """Enforce page limits, required volume presence, and attachment presence."""
    logger.info("SubmissionAgent [3/5]: validating formatting for deal %s", state["deal_id"])

    issues: list[str] = []
    proposal_sections = state.get("proposal_sections") or {}
    page_limits = state.get("page_limits") or {}
    present_sections = set(proposal_sections.keys())

    # ── Check: Required volumes present ──────────────────────────────
    for vol in _REQUIRED_VOLUMES:
        found = any(
            vol.lower() in s.lower() or s.lower() in vol.lower()
            for s in present_sections
        )
        if not found:
            issues.append(f"Required volume missing: {vol}")

    # ── Check: Page limits met ───────────────────────────────────────
    page_limits_met = True
    for section_name, content in proposal_sections.items():
        if not content:
            continue
        # Approximate page count: ~300 words per page
        word_count = len(content.split())
        approx_pages = word_count / 300.0

        # Check against page limits from RFP
        for limit_key, limit_value in page_limits.items():
            if not isinstance(limit_value, (int, float)):
                continue
            if limit_key.lower().replace("_", " ") in section_name.lower():
                if approx_pages > limit_value:
                    issues.append(
                        f"Section '{section_name}' exceeds page limit: "
                        f"~{approx_pages:.0f} pages vs {limit_value} allowed"
                    )
                    page_limits_met = False

    # ── Check: Standard attachments ──────────────────────────────────
    for attach in _STANDARD_ATTACHMENTS:
        found = any(attach.lower() in s.lower() for s in present_sections)
        if not found:
            issues.append(f"Standard attachment not found: {attach}")

    return {
        "formatting_issues": issues,
        "page_limits_met": page_limits_met,
        "messages": [HumanMessage(content=f"Formatting validation: {len(issues)} issues found")],
    }


# ── Node 4: Generate Checklist ───────────────────────────────────────────────

async def generate_checklist(state: SubmissionState) -> dict:
    """Build a comprehensive submission checklist with per-item status and category."""
    logger.info("SubmissionAgent [4/5]: generating checklist for deal %s", state["deal_id"])

    proposal_sections = state.get("proposal_sections") or {}
    present_sections = set(proposal_sections.keys())

    checklist: list[dict] = []
    missing: list[str] = []

    # ── Content items ────────────────────────────────────────────────
    for vol in _REQUIRED_VOLUMES:
        found = any(
            vol.lower() in s.lower() or s.lower() in vol.lower()
            for s in present_sections
        )
        status = "COMPLETE" if found else "MISSING"
        checklist.append({
            "item": vol,
            "status": status,
            "notes": "",
            "category": "content",
        })
        if not found:
            missing.append(vol)

    # ── Administrative items ─────────────────────────────────────────
    for attach in _STANDARD_ATTACHMENTS:
        found = any(attach.lower() in s.lower() for s in present_sections)
        status = "COMPLETE" if found else "PENDING"
        checklist.append({
            "item": attach,
            "status": status,
            "notes": "Verify with contracting team" if not found else "",
            "category": "administrative",
        })
        if not found:
            missing.append(attach)

    # ── Compliance items ─────────────────────────────────────────────
    if state.get("compliance_at_100"):
        matrix = state.get("compliance_matrix") or []
        checklist.append({
            "item": "Compliance Matrix",
            "status": "COMPLETE",
            "notes": f"{len(matrix)} requirements — 100% compliant",
            "category": "compliance",
        })
    else:
        checklist.append({
            "item": "Compliance Matrix",
            "status": "INCOMPLETE",
            "notes": "Compliance matrix is not at 100%",
            "category": "compliance",
        })
        missing.append("Compliance Matrix (100%)")

    # ── Pricing items ────────────────────────────────────────────────
    if state.get("pricing_approved"):
        pricing_vol = state.get("pricing_volume") or {}
        total = pricing_vol.get("total_price", "N/A")
        checklist.append({
            "item": "Pricing Volume Approved",
            "status": "COMPLETE",
            "notes": f"Total price: ${total}",
            "category": "content",
        })
    else:
        checklist.append({
            "item": "Pricing Volume Approved",
            "status": "MISSING",
            "notes": "Pricing requires approval before submission",
            "category": "content",
        })
        missing.append("Pricing Volume Approval")

    # ── Formatting items ─────────────────────────────────────────────
    if state.get("page_limits_met"):
        checklist.append({
            "item": "Page Limits Compliance",
            "status": "COMPLETE",
            "notes": "All sections within page limits",
            "category": "formatting",
        })
    else:
        checklist.append({
            "item": "Page Limits Compliance",
            "status": "FAILED",
            "notes": "One or more sections exceed page limits",
            "category": "formatting",
        })
        missing.append("Page Limit Compliance")

    # ── Section completeness ─────────────────────────────────────────
    if state.get("all_sections_complete"):
        checklist.append({
            "item": "All Sections Drafted & Reviewed",
            "status": "COMPLETE",
            "notes": f"{len(proposal_sections)} sections finalized",
            "category": "content",
        })
    else:
        checklist.append({
            "item": "All Sections Drafted & Reviewed",
            "status": "INCOMPLETE",
            "notes": "Some sections are empty or unapproved",
            "category": "content",
        })
        missing.append("Section Completion")

    # ── QA Review ────────────────────────────────────────────────────
    qa_done = bool(state.get("qa_summary"))
    qa_passed = "PASS" in (state.get("qa_summary") or "").upper()
    checklist.append({
        "item": "QA Review",
        "status": "COMPLETE" if qa_done and qa_passed else "PENDING",
        "notes": "PASS" if qa_passed else ("Review pending" if not qa_done else "Review completed with issues"),
        "category": "compliance",
    })
    if not qa_done:
        missing.append("QA Review")

    return {
        "checklist": checklist,
        "missing_items": missing,
        "messages": [HumanMessage(
            content=f"Checklist generated: {len(checklist)} items, {len(missing)} missing/incomplete"
        )],
    }


# ── Node 5: Package Submission ───────────────────────────────────────────────

async def package_submission(state: SubmissionState) -> dict:
    """Produce final readiness summary and risk assessment using LLM."""
    logger.info("SubmissionAgent [5/5]: packaging submission for deal %s", state["deal_id"])

    checklist = state.get("checklist") or []
    missing = state.get("missing_items") or []
    completeness_issues = state.get("completeness_issues") or []
    formatting_issues = state.get("formatting_issues") or []
    key_dates = state.get("key_dates") or {}

    complete_count = sum(1 for item in checklist if item.get("status") == "COMPLETE")
    total_count = len(checklist)

    all_issues = completeness_issues + formatting_issues

    content = await _llm(
        system=(
            "You are a proposal submission manager for government contracts. "
            "Assess whether a proposal submission package is ready for delivery. "
            "Identify risks and required actions. Be specific and actionable."
        ),
        human=(
            f"Opportunity: {state['opportunity'].get('title', state['deal_id'])}\n"
            f"Agency: {state['opportunity'].get('agency', 'Unknown')}\n"
            f"Key Dates: {key_dates}\n\n"
            f"Submission Checklist: {complete_count}/{total_count} items complete\n\n"
            f"Missing/Incomplete Items:\n"
            + "\n".join(f"- {item}" for item in missing[:10])
            + f"\n\nVerification Issues ({len(all_issues)}):\n"
            + "\n".join(f"- {issue}" for issue in all_issues[:10])
            + f"\n\nPricing Approved: {'Yes' if state.get('pricing_approved') else 'No'}"
            + f"\nCompliance at 100%: {'Yes' if state.get('compliance_at_100') else 'No'}"
            + f"\nAll Sections Complete: {'Yes' if state.get('all_sections_complete') else 'No'}"
            + f"\nPage Limits Met: {'Yes' if state.get('page_limits_met') else 'No'}"
            + f"\n\nQA Status: {(state.get('qa_summary') or 'Not run')[:200]}\n\n"
            "Provide:\n"
            "1. SUBMISSION_READY: YES or NO\n"
            "2. Readiness percentage (0-100%)\n"
            "3. Top 5 risks if submitted as-is\n"
            "4. Critical action items (must be done before submission)\n"
            "5. Nice-to-have improvements\n"
            "6. Recommended submission timeline"
        ),
        max_tokens=2000,
    )

    # Extract risks from LLM output
    risks: list[str] = []
    in_risks = False
    for line in content.split("\n"):
        stripped = line.strip()
        if "risk" in stripped.lower() and ("top" in stripped.lower() or "5" in stripped):
            in_risks = True
            continue
        if in_risks and stripped.startswith(("-", "*", "1.", "2.", "3.", "4.", "5.")):
            risk_text = stripped.lstrip("-*0123456789. ").strip()
            if risk_text:
                risks.append(risk_text)
            if len(risks) >= 5:
                in_risks = False

    # Add programmatically detected risks
    if not state.get("pricing_approved"):
        risks.append("Pricing volume has not been approved")
    if not state.get("compliance_at_100"):
        risks.append("Compliance matrix is not at 100%")
    if not state.get("all_sections_complete"):
        risks.append("Not all proposal sections are complete or approved")
    if not state.get("page_limits_met"):
        risks.append("One or more sections exceed RFP page limits")

    # Deduplicate risks
    seen = set()
    unique_risks = []
    for risk in risks:
        key = risk.lower()[:50]
        if key not in seen:
            seen.add(key)
            unique_risks.append(risk)

    return {
        "submission_risks": unique_risks,
        "submission_package_summary": content,
        "messages": [HumanMessage(
            content=f"Submission packaged: {complete_count}/{total_count} complete, {len(unique_risks)} risks identified."
        )],
    }


# ── Graph ─────────────────────────────────────────────────────────────────────

def build_submission_graph() -> StateGraph:
    wf = StateGraph(SubmissionState)

    # 5-node pipeline
    wf.add_node("load_submission_context", load_submission_context)
    wf.add_node("verify_completeness", verify_completeness)
    wf.add_node("validate_formatting", validate_formatting)
    wf.add_node("generate_checklist", generate_checklist)
    wf.add_node("package_submission", package_submission)

    # Linear pipeline: 1 -> 2 -> 3 -> 4 -> 5 -> END
    wf.set_entry_point("load_submission_context")
    wf.add_edge("load_submission_context", "verify_completeness")
    wf.add_edge("verify_completeness", "validate_formatting")
    wf.add_edge("validate_formatting", "generate_checklist")
    wf.add_edge("generate_checklist", "package_submission")
    wf.add_edge("package_submission", END)

    return wf.compile()


submission_graph = build_submission_graph()


# ── Agent ─────────────────────────────────────────────────────────────────────

class SubmissionAgent(BaseAgent):
    """AI agent that assembles and validates the proposal submission package.

    Runs a 5-node LangGraph pipeline:
      1. load_submission_context
      2. verify_completeness
      3. validate_formatting
      4. generate_checklist
      5. package_submission
    """

    agent_name = "submission_agent"

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        deal_id = input_data.get("deal_id", "")
        if not deal_id:
            return {"error": "deal_id is required"}

        initial: SubmissionState = {
            "deal_id": deal_id,
            "deal": {},
            "opportunity": {},
            "proposal": {},
            "proposal_sections": input_data.get("proposal_sections", {}),
            "compliance_matrix": input_data.get("compliance_matrix", []),
            "pricing_volume": input_data.get("pricing_volume", {}),
            "qa_summary": input_data.get("qa_summary", ""),
            "key_dates": input_data.get("key_dates", {}),
            "page_limits": input_data.get("page_limits", {}),
            # Verification results (populated by nodes)
            "completeness_issues": [],
            "formatting_issues": [],
            "all_sections_complete": False,
            "compliance_at_100": False,
            "pricing_approved": False,
            "page_limits_met": False,
            # Outputs
            "checklist": [],
            "missing_items": [],
            "submission_package_summary": "",
            "submission_risks": [],
            "messages": [],
        }

        try:
            await self.emit_event(
                "thinking",
                {"message": f"Assembling submission package for deal {deal_id}"},
                execution_id=deal_id,
            )

            fs = await submission_graph.ainvoke(initial)

            await self.emit_event(
                "output",
                {
                    "checklist_count": len(fs["checklist"]),
                    "missing_count": len(fs["missing_items"]),
                    "risks_count": len(fs["submission_risks"]),
                    "all_sections_complete": fs["all_sections_complete"],
                    "compliance_at_100": fs["compliance_at_100"],
                    "pricing_approved": fs["pricing_approved"],
                    "page_limits_met": fs["page_limits_met"],
                },
                execution_id=deal_id,
            )

            return {
                "deal_id": fs["deal_id"],
                "checklist": fs["checklist"],
                "missing_items": fs["missing_items"],
                "submission_package_summary": fs["submission_package_summary"],
                "submission_risks": fs["submission_risks"],
                "verification": {
                    "all_sections_complete": fs["all_sections_complete"],
                    "compliance_at_100": fs["compliance_at_100"],
                    "pricing_approved": fs["pricing_approved"],
                    "page_limits_met": fs["page_limits_met"],
                    "completeness_issues": fs["completeness_issues"],
                    "formatting_issues": fs["formatting_issues"],
                },
            }
        except Exception as exc:
            logger.exception("SubmissionAgent.run failed for deal %s", deal_id)
            await self.emit_event("error", {"error": str(exc)}, execution_id=deal_id)
            return {"error": str(exc), "deal_id": deal_id}
