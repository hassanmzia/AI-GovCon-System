"""Regulatory Classifier Agent — Early FAR/DFARS Clause Detection.

Runs at intake/qualify to auto-classify which FAR/DFARS clauses and
regulatory requirements apply to a deal based on:
  - Dollar threshold (SAT, TINA thresholds)
  - Contract type (FFP, T&M, CPFF, IDIQ, etc.)
  - Set-aside status (8(a), HUBZone, SDVOSB, WOSB)
  - Agency (DoD vs civilian → DFARS applicability)
  - NAICS/PSC codes
  - Security requirements (CUI, clearance levels)

This early classification surfaces compliance cost and risk upfront,
instead of waiting for the legal_agent at final_review. Catches issues
like CAS-covered contracts, DFARS 252.204-7012 cyber requirements,
and TINA thresholds before proposal work begins.
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

logger = logging.getLogger("ai_orchestrator.agents.regulatory_classifier")

DJANGO_API_URL = os.getenv("DJANGO_API_URL", "http://django-api:8001")
DJANGO_SERVICE_TOKEN = os.getenv("DJANGO_SERVICE_TOKEN", "")

# ── Threshold Constants (FAR-based) ─────────────────────────────────────────

MICRO_PURCHASE_THRESHOLD = 10_000
SIMPLIFIED_ACQUISITION_THRESHOLD = 250_000
TINA_THRESHOLD = 2_000_000  # Truth in Negotiations Act
CAS_THRESHOLD = 2_000_000  # Cost Accounting Standards
CAS_FULL_THRESHOLD = 50_000_000  # Full CAS coverage

# DoD-specific agency keywords
DOD_AGENCIES = {
    "department of defense", "dod", "army", "navy", "air force",
    "marine corps", "space force", "defense logistics agency", "dla",
    "disa", "darpa", "missile defense agency", "socom",
    "defense health agency", "dha", "defense information systems",
}


# ── State ────────────────────────────────────────────────────────────────────

class RegulatoryClassifierState(TypedDict):
    deal_id: str
    deal: dict
    opportunity: dict
    # Classification outputs
    contract_characteristics: dict
    threshold_analysis: dict
    mandatory_clauses: list[dict]
    conditional_clauses: list[dict]
    compliance_flags: list[dict]
    risk_summary: dict
    classification_report: str
    messages: Annotated[list, operator.add]


# ── Helpers ──────────────────────────────────────────────────────────────────

def _auth_headers() -> dict[str, str]:
    t = DJANGO_SERVICE_TOKEN
    return {"Authorization": f"Bearer {t}"} if t else {}


async def _get(path: str, default: Any = None) -> Any:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{DJANGO_API_URL}{path}", headers=_auth_headers()
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.warning("API GET %s failed: %s", path, exc)
        return default


def _is_dod(agency: str) -> bool:
    """Check if agency is DoD (triggers DFARS applicability)."""
    agency_lower = agency.lower()
    return any(kw in agency_lower for kw in DOD_AGENCIES)


def _estimate_value(deal: dict, opp: dict) -> float:
    """Extract estimated contract value from deal or opportunity."""
    for field in ("contract_value", "estimated_value", "award_amount"):
        for source in (deal, opp):
            raw = source.get(field)
            if raw is not None:
                try:
                    return float(str(raw).replace(",", "").replace("$", ""))
                except (ValueError, TypeError):
                    continue
    return 0.0


# ── Graph Nodes ──────────────────────────────────────────────────────────────

async def load_context(state: RegulatoryClassifierState) -> dict:
    """Fetch deal and opportunity context."""
    logger.info("RegulatoryClassifier: loading context for deal %s", state["deal_id"])

    deal = await _get(f"/api/deals/deals/{state['deal_id']}/", default={})
    opp_id = deal.get("opportunity") or deal.get("opportunity_id") or ""
    opportunity = {}
    if opp_id:
        opportunity = await _get(f"/api/opportunities/opportunities/{opp_id}/", default={})

    return {
        "deal": deal,
        "opportunity": opportunity,
        "messages": [HumanMessage(content=f"Loaded deal: {deal.get('title', state['deal_id'])}")],
    }


async def classify_contract_characteristics(state: RegulatoryClassifierState) -> dict:
    """Deterministic classification of contract characteristics from metadata."""
    logger.info("RegulatoryClassifier: classifying characteristics for deal %s", state["deal_id"])

    deal = state.get("deal") or {}
    opp = state.get("opportunity") or {}

    agency = opp.get("agency") or deal.get("agency") or ""
    est_value = _estimate_value(deal, opp)
    contract_type = opp.get("contract_type") or deal.get("contract_type") or ""
    set_aside = opp.get("set_aside") or opp.get("setAside") or ""
    naics = opp.get("naics_code") or ""
    notice_type = opp.get("notice_type") or ""
    is_dod = _is_dod(agency)

    chars = {
        "agency": agency,
        "is_dod": is_dod,
        "dfars_applicable": is_dod,
        "estimated_value": est_value,
        "contract_type": contract_type,
        "set_aside": set_aside,
        "naics_code": naics,
        "notice_type": notice_type,
        # Threshold classifications
        "above_sat": est_value > SIMPLIFIED_ACQUISITION_THRESHOLD,
        "above_tina": est_value > TINA_THRESHOLD,
        "cas_applicable": est_value > CAS_THRESHOLD and contract_type not in ("FFP", "ffp"),
        "cas_full_coverage": est_value > CAS_FULL_THRESHOLD,
        "micro_purchase": est_value <= MICRO_PURCHASE_THRESHOLD,
    }

    return {
        "contract_characteristics": chars,
        "messages": [HumanMessage(content=(
            f"Contract: {'DoD' if is_dod else 'Civilian'}, "
            f"${est_value:,.0f}, {contract_type or 'type TBD'}, "
            f"{'above' if chars['above_sat'] else 'below'} SAT"
        ))],
    }


async def determine_threshold_requirements(state: RegulatoryClassifierState) -> dict:
    """Map dollar thresholds to mandatory regulatory requirements."""
    logger.info("RegulatoryClassifier: analyzing thresholds for deal %s", state["deal_id"])

    chars = state.get("contract_characteristics") or {}
    est_value = chars.get("estimated_value", 0)

    analysis = {
        "estimated_value": est_value,
        "thresholds_triggered": [],
        "procurement_method": "micro_purchase",
    }

    if est_value > MICRO_PURCHASE_THRESHOLD:
        analysis["procurement_method"] = "simplified_acquisition"

    if chars.get("above_sat"):
        analysis["procurement_method"] = "full_and_open"
        analysis["thresholds_triggered"].append({
            "threshold": "Simplified Acquisition Threshold ($250K)",
            "impact": "Full and open competition required. Full FAR Part 15 procedures apply.",
            "far_reference": "FAR Part 13/15",
        })

    if chars.get("above_tina"):
        analysis["thresholds_triggered"].append({
            "threshold": "TINA Threshold ($2M)",
            "impact": "Truth in Negotiations Act applies. Certified cost or pricing data required unless exemption applies.",
            "far_reference": "FAR 15.403-4",
        })

    if chars.get("cas_applicable"):
        coverage = "Full CAS" if chars.get("cas_full_coverage") else "Modified CAS"
        analysis["thresholds_triggered"].append({
            "threshold": f"CAS Threshold ($2M) — {coverage}",
            "impact": f"{coverage} coverage required. Cost Accounting Standards Disclosure Statement may be needed.",
            "far_reference": "FAR 30.201-4",
        })

    return {
        "threshold_analysis": analysis,
        "messages": [HumanMessage(content=f"Thresholds triggered: {len(analysis['thresholds_triggered'])}")],
    }


async def classify_mandatory_clauses(state: RegulatoryClassifierState) -> dict:
    """Use LLM to classify mandatory and conditional FAR/DFARS clauses."""
    logger.info("RegulatoryClassifier: classifying clauses for deal %s", state["deal_id"])

    chars = state.get("contract_characteristics") or {}
    thresholds = state.get("threshold_analysis") or {}
    llm = get_chat_model(max_tokens=3000)

    system = SystemMessage(content=(
        "You are a FAR/DFARS regulatory specialist with deep expertise in "
        "government contract clause prescription. Given contract characteristics, "
        "identify ALL mandatory and conditionally-required clauses.\n\n"
        "For each clause, provide:\n"
        "- clause_number (e.g., FAR 52.212-4 or DFARS 252.204-7012)\n"
        "- title\n"
        "- prescription (why it's required)\n"
        "- category: MANDATORY or CONDITIONAL\n"
        "- compliance_cost: LOW / MEDIUM / HIGH (effort to comply)\n"
        "Format each clause on one line: CLAUSE|number|title|prescription|category|cost"
    ))

    human = HumanMessage(content=(
        f"CONTRACT CHARACTERISTICS:\n"
        f"  Agency: {chars.get('agency', 'Unknown')}\n"
        f"  DoD: {'Yes → DFARS applies' if chars.get('is_dod') else 'No → FAR only'}\n"
        f"  Estimated Value: ${chars.get('estimated_value', 0):,.0f}\n"
        f"  Contract Type: {chars.get('contract_type', 'TBD')}\n"
        f"  Set-Aside: {chars.get('set_aside', 'None')}\n"
        f"  NAICS: {chars.get('naics_code', 'N/A')}\n"
        f"  Above SAT: {chars.get('above_sat', False)}\n"
        f"  Above TINA: {chars.get('above_tina', False)}\n"
        f"  CAS Applicable: {chars.get('cas_applicable', False)}\n\n"
        f"THRESHOLDS:\n"
        + "\n".join(
            f"  - {t['threshold']}: {t['impact']}"
            for t in thresholds.get("thresholds_triggered", [])
        )
        + "\n\nList all applicable FAR/DFARS clauses using the CLAUSE| format."
    ))

    try:
        response = await llm.ainvoke([system, human])
        content = response.content
    except Exception as exc:
        logger.error("LLM failed in classify_mandatory_clauses: %s", exc)
        content = ""

    mandatory = []
    conditional = []

    for line in content.split("\n"):
        line = line.strip()
        if line.startswith("CLAUSE|"):
            parts = line.split("|")
            if len(parts) >= 6:
                clause = {
                    "clause_number": parts[1].strip(),
                    "title": parts[2].strip(),
                    "prescription": parts[3].strip(),
                    "compliance_cost": parts[5].strip().upper(),
                }
                if parts[4].strip().upper() == "MANDATORY":
                    mandatory.append(clause)
                else:
                    conditional.append(clause)

    return {
        "mandatory_clauses": mandatory,
        "conditional_clauses": conditional,
        "messages": [HumanMessage(content=(
            f"Classified {len(mandatory)} mandatory + {len(conditional)} conditional clauses"
        ))],
    }


async def assess_compliance_risk(state: RegulatoryClassifierState) -> dict:
    """Generate compliance flags and risk summary."""
    logger.info("RegulatoryClassifier: assessing compliance risk for deal %s", state["deal_id"])

    chars = state.get("contract_characteristics") or {}
    mandatory = state.get("mandatory_clauses") or []
    conditional = state.get("conditional_clauses") or []

    flags = []

    # High-impact flags based on deterministic rules
    if chars.get("is_dod"):
        flags.append({
            "flag": "DFARS CYBERSECURITY (252.204-7012)",
            "severity": "HIGH",
            "description": "DoD contract requires NIST SP 800-171 compliance. CMMC certification may be required.",
            "action": "Verify CMMC readiness level and SSP completeness",
        })

    if chars.get("above_tina"):
        flags.append({
            "flag": "TINA COST DATA REQUIRED",
            "severity": "HIGH",
            "description": "Contract value exceeds $2M. Certified cost or pricing data required unless commercial item or adequate price competition exemption.",
            "action": "Prepare certified cost or pricing data package or document exemption",
        })

    if chars.get("cas_applicable"):
        flags.append({
            "flag": "COST ACCOUNTING STANDARDS",
            "severity": "HIGH",
            "description": f"{'Full' if chars.get('cas_full_coverage') else 'Modified'} CAS coverage triggered.",
            "action": "Ensure CAS Disclosure Statement is current and cost accounting practices are compliant",
        })

    high_cost_clauses = [c for c in mandatory if c.get("compliance_cost") == "HIGH"]
    if high_cost_clauses:
        flags.append({
            "flag": "HIGH-COST COMPLIANCE CLAUSES",
            "severity": "MEDIUM",
            "description": f"{len(high_cost_clauses)} clause(s) with high compliance cost identified",
            "action": "Factor compliance costs into pricing and schedule",
        })

    set_aside = chars.get("set_aside", "")
    if set_aside and set_aside.lower() not in ("none", ""):
        flags.append({
            "flag": f"SET-ASIDE: {set_aside}",
            "severity": "MEDIUM",
            "description": f"Set-aside competition. Verify eligibility for {set_aside}.",
            "action": "Confirm SBA certification status and eligibility",
        })

    # Risk level
    high_flags = sum(1 for f in flags if f["severity"] == "HIGH")
    if high_flags >= 3:
        risk_level = "HIGH"
    elif high_flags >= 1:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    risk_summary = {
        "overall_risk": risk_level,
        "total_mandatory_clauses": len(mandatory),
        "total_conditional_clauses": len(conditional),
        "high_severity_flags": high_flags,
        "total_flags": len(flags),
        "estimated_compliance_effort": (
            "Significant — multiple high-cost clauses and regulatory triggers"
            if high_flags >= 2
            else "Moderate — standard compliance requirements"
            if mandatory
            else "Low — minimal regulatory burden"
        ),
    }

    # Build a concise classification report
    report_lines = [
        f"REGULATORY CLASSIFICATION — Deal: {state['deal'].get('title', state['deal_id'])}",
        f"Agency: {chars.get('agency', 'Unknown')} ({'DoD — DFARS applies' if chars.get('is_dod') else 'Civilian — FAR only'})",
        f"Estimated Value: ${chars.get('estimated_value', 0):,.0f}",
        f"Risk Level: {risk_level}",
        "",
        f"Mandatory Clauses: {len(mandatory)}",
        f"Conditional Clauses: {len(conditional)}",
        f"Compliance Flags: {len(flags)}",
        "",
        "KEY FLAGS:",
    ]
    for f in flags:
        report_lines.append(f"  [{f['severity']}] {f['flag']}: {f['description']}")

    return {
        "compliance_flags": flags,
        "risk_summary": risk_summary,
        "classification_report": "\n".join(report_lines),
        "messages": [HumanMessage(content=f"Compliance risk: {risk_level} ({len(flags)} flags)")],
    }


# ── Graph Builder ────────────────────────────────────────────────────────────

def build_regulatory_classifier_graph() -> StateGraph:
    wf = StateGraph(RegulatoryClassifierState)

    wf.add_node("load_context", load_context)
    wf.add_node("classify_contract_characteristics", classify_contract_characteristics)
    wf.add_node("determine_threshold_requirements", determine_threshold_requirements)
    wf.add_node("classify_mandatory_clauses", classify_mandatory_clauses)
    wf.add_node("assess_compliance_risk", assess_compliance_risk)

    wf.set_entry_point("load_context")
    wf.add_edge("load_context", "classify_contract_characteristics")
    wf.add_edge("classify_contract_characteristics", "determine_threshold_requirements")
    wf.add_edge("determine_threshold_requirements", "classify_mandatory_clauses")
    wf.add_edge("classify_mandatory_clauses", "assess_compliance_risk")
    wf.add_edge("assess_compliance_risk", END)

    return wf.compile()


regulatory_classifier_graph = build_regulatory_classifier_graph()


# ── Agent Class ──────────────────────────────────────────────────────────────

class RegulatoryClassifierAgent(BaseAgent):
    """
    Early-stage FAR/DFARS regulatory classifier.

    Runs at intake/qualify to identify mandatory clauses, threshold
    triggers, and compliance flags before proposal work begins.
    """

    agent_name = "regulatory_classifier_agent"

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        deal_id = input_data.get("deal_id", "")
        if not deal_id:
            return {"error": "deal_id is required"}

        initial: RegulatoryClassifierState = {
            "deal_id": deal_id,
            "deal": {},
            "opportunity": {},
            "contract_characteristics": {},
            "threshold_analysis": {},
            "mandatory_clauses": [],
            "conditional_clauses": [],
            "compliance_flags": [],
            "risk_summary": {},
            "classification_report": "",
            "messages": [],
        }

        try:
            await self.emit_event(
                "thinking",
                {"message": f"Classifying regulatory requirements for deal {deal_id}"},
                execution_id=deal_id,
            )
            fs = await regulatory_classifier_graph.ainvoke(initial)
            await self.emit_event(
                "output",
                {
                    "risk_level": fs["risk_summary"].get("overall_risk", "unknown"),
                    "mandatory_clauses": len(fs["mandatory_clauses"]),
                    "flags": len(fs["compliance_flags"]),
                },
                execution_id=deal_id,
            )
            return {
                "deal_id": deal_id,
                "contract_characteristics": fs["contract_characteristics"],
                "threshold_analysis": fs["threshold_analysis"],
                "mandatory_clauses": fs["mandatory_clauses"],
                "conditional_clauses": fs["conditional_clauses"],
                "compliance_flags": fs["compliance_flags"],
                "risk_summary": fs["risk_summary"],
                "classification_report": fs["classification_report"],
            }
        except Exception as exc:
            logger.exception("RegulatoryClassifierAgent failed for deal %s", deal_id)
            await self.emit_event("error", {"error": str(exc)}, execution_id=deal_id)
            return {"error": str(exc), "deal_id": deal_id}
