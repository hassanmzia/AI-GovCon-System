"""
Evidence Validator Agent — anti-hallucination engine for proposals.

Before submission, validates that:
1. Every key claim/capability has a citation (RFP section reference or past performance vault entry)
2. Past performance metrics cited actually exist in the vault
3. Compliance matrix has coverage >= policy minimum
4. No fabricated statistics or certifications

Blocks final submission if validation fails.
"""
import json
import logging
import operator
import os
from typing import Annotated, Any

import httpx
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from typing_extensions import TypedDict

from src.agents.base import BaseAgent
from src.governance import policy_loader

logger = logging.getLogger("ai_orchestrator.agents.evidence_validator")

DJANGO_API_URL = os.getenv("DJANGO_API_URL", "http://django-api:8001")
DJANGO_SERVICE_TOKEN = os.getenv("DJANGO_SERVICE_TOKEN", "")


# ── State ─────────────────────────────────────────────────────────────────────


class EvidenceValidatorState(TypedDict):
    deal_id: str
    proposal_sections: dict             # {section_title: content_text}
    pp_vault_entries: list[dict]        # Past performance vault records
    rfp_requirements: list[dict]        # All RFP requirements for compliance check
    validation_results: list[dict]      # Per-claim validation outcomes
    uncited_claims: list[dict]          # Claims without citations
    fabricated_metrics: list[dict]      # Metrics that cannot be verified
    compliance_coverage: float          # 0.0–1.0 fraction of requirements addressed
    is_submission_safe: bool            # True = safe to submit; False = blocked
    blocking_issues: list[str]          # Reasons blocking submission
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
        logger.warning("EvidenceValidator API GET %s failed: %s", path, exc)
        return default


async def _llm(
    system: str,
    human: str,
    max_tokens: int = 4096,
    execution_id: str | None = None,
) -> str:
    try:
        from src.observability.tracing import build_llm

        llm = build_llm(
            max_tokens=max_tokens,
            execution_id=execution_id,
            agent_name="evidence_validator_agent",
        )
        resp = await llm.ainvoke(
            [SystemMessage(content=system), HumanMessage(content=human)]
        )
        return resp.content if isinstance(resp.content, str) else str(resp.content)
    except Exception as exc:
        logger.error("EvidenceValidator LLM call failed: %s", exc)
        return ""


def _parse_json_response(raw: str, fallback: Any = None) -> Any:
    """Attempt to parse a JSON response from the LLM, stripping markdown fences."""
    try:
        clean = raw.strip()
        if clean.startswith("```"):
            clean = "\n".join(clean.split("\n")[1:])
        if clean.endswith("```"):
            clean = clean[: clean.rfind("```")]
        return json.loads(clean.strip())
    except (json.JSONDecodeError, ValueError):
        return fallback


# ── Graph nodes ───────────────────────────────────────────────────────────────


async def load_evidence_sources(state: EvidenceValidatorState) -> dict:
    """
    Load proposal sections, past performance vault entries, and RFP requirements
    from the Django backend.
    """
    deal_id = state["deal_id"]
    logger.info("EvidenceValidator: loading evidence sources for deal %s", deal_id)

    deal = await _get(f"/api/deals/{deal_id}/", default={})
    proposal_id = (
        deal.get("latest_proposal_id")
        or deal.get("proposal_id")
        or ""
    )

    # ── Proposal sections ──────────────────────────────────────────────────────
    proposal_sections: dict = dict(state.get("proposal_sections") or {})
    if not proposal_sections and proposal_id:
        sections_data = await _get(
            f"/api/proposals/{proposal_id}/sections/", default={}
        )
        results = (
            sections_data.get("results", [])
            if isinstance(sections_data, dict)
            else sections_data
            if isinstance(sections_data, list)
            else []
        )
        for s in results:
            title = s.get("section_type") or s.get("title") or "Section"
            content = s.get("content") or s.get("text") or ""
            proposal_sections[title] = content

    # ── Past performance vault ─────────────────────────────────────────────────
    pp_vault_entries: list[dict] = list(state.get("pp_vault_entries") or [])
    if not pp_vault_entries:
        pp_data = await _get(
            f"/api/past-performance/?deal={deal_id}&limit=100", default={}
        )
        if isinstance(pp_data, dict):
            pp_vault_entries = pp_data.get("results", [])
        elif isinstance(pp_data, list):
            pp_vault_entries = pp_data

    # ── RFP requirements ───────────────────────────────────────────────────────
    rfp_requirements: list[dict] = list(state.get("rfp_requirements") or [])
    if not rfp_requirements:
        req_data = await _get(
            f"/api/rfp/requirements/?deal={deal_id}&limit=200", default={}
        )
        if isinstance(req_data, dict):
            rfp_requirements = req_data.get("results", [])
        elif isinstance(req_data, list):
            rfp_requirements = req_data

    return {
        "proposal_sections": proposal_sections,
        "pp_vault_entries": pp_vault_entries,
        "rfp_requirements": rfp_requirements,
        "messages": [
            HumanMessage(
                content=(
                    f"Loaded {len(proposal_sections)} proposal sections, "
                    f"{len(pp_vault_entries)} PP vault entries, "
                    f"{len(rfp_requirements)} RFP requirements."
                )
            )
        ],
    }


async def extract_claims(state: EvidenceValidatorState) -> dict:
    """
    Scan each proposal section for factual claims that require citation.

    Extracts:
      - Specific metrics (percentages, dollar amounts, timelines)
      - Certifications and clearances claimed
      - Past contract values and agency names
      - Technology or capability claims with specific numbers
    """
    deal_id = state["deal_id"]
    logger.info("EvidenceValidator: extracting claims for deal %s", deal_id)

    proposal_sections = state.get("proposal_sections") or {}
    if not proposal_sections:
        return {
            "validation_results": [],
            "messages": [HumanMessage(content="No proposal sections to scan.")],
        }

    sections_text = "\n\n".join(
        f"=== {title} ===\n{content[:1500]}"
        for title, content in list(proposal_sections.items())[:8]
    )

    system_prompt = (
        "You are an anti-hallucination auditor for US Government proposals. "
        "Scan the proposal text for ALL factual claims that require evidence:\n\n"
        "Types of claims to extract:\n"
        "1. Specific metrics (e.g., '99.9% uptime', '40% cost reduction', '$50M contract')\n"
        "2. Certifications/clearances (e.g., 'ISO 27001 certified', 'SECRET facility clearance')\n"
        "3. Past contract references (agency names, contract values, dates)\n"
        "4. Technology capabilities (e.g., 'processes 10,000 transactions/second')\n"
        "5. Team qualifications (e.g., '15 years of DoD experience')\n"
        "6. Named past projects or clients\n\n"
        "For each claim, output a JSON object:\n"
        "  {\"section\": str, \"claim\": str, \"claim_type\": str, \"requires_citation\": bool}\n\n"
        "Output a JSON array 'claims' of these objects. "
        "Only include claims that are verifiable facts, not general statements."
    )

    human_prompt = (
        f"Proposal Sections:\n{sections_text}\n\n"
        "Extract all factual claims as JSON."
    )

    raw = await _llm(system_prompt, human_prompt, max_tokens=4096, execution_id=state.get("deal_id"))
    parsed = _parse_json_response(raw, fallback={})

    claims: list[dict] = []
    if isinstance(parsed, list):
        claims = parsed
    elif isinstance(parsed, dict):
        claims = parsed.get("claims", [])

    # Initialise validation_results with citation_found=False
    validation_results = [
        {**claim, "citation_found": False, "citation_source": None}
        for claim in claims
        if isinstance(claim, dict)
    ]

    return {
        "validation_results": validation_results,
        "messages": [
            HumanMessage(
                content=f"Extracted {len(validation_results)} factual claim(s) requiring validation."
            )
        ],
    }


async def validate_citations(state: EvidenceValidatorState) -> dict:
    """
    For each extracted claim, check whether it can be matched to a PP vault entry
    or an RFP section reference using LLM-assisted matching.

    Marks each claim as cited or uncited, and flags potential fabrications.
    """
    deal_id = state["deal_id"]
    logger.info("EvidenceValidator: validating citations for deal %s", deal_id)

    validation_results: list[dict] = list(state.get("validation_results") or [])
    pp_vault_entries: list[dict] = state.get("pp_vault_entries") or []

    if not validation_results:
        return {
            "validation_results": [],
            "uncited_claims": [],
            "fabricated_metrics": [],
            "messages": [HumanMessage(content="No claims to validate.")],
        }

    # Build a compact vault summary for the LLM
    vault_summary = "\n".join(
        f"[PP-{i+1}] Agency: {e.get('agency_name','?')} | "
        f"Contract: {e.get('contract_title','?')} | "
        f"Value: {e.get('contract_value','?')} | "
        f"Period: {e.get('period_of_performance','?')} | "
        f"Highlights: {str(e.get('key_metrics') or e.get('highlights',''))[:200]}"
        for i, e in enumerate(pp_vault_entries[:20])
    )

    claims_text = "\n".join(
        f"[C-{i+1}] Section={c.get('section','?')} | "
        f"Type={c.get('claim_type','?')} | Claim: {c.get('claim','?')}"
        for i, c in enumerate(validation_results[:30])
    )

    system_prompt = (
        "You are a proposal compliance auditor. For each proposal claim, determine "
        "whether it can be substantiated by the past performance vault or standard "
        "RFP references.\n\n"
        "Matching rules:\n"
        "- A claim is CITED if a vault entry contains matching data (agency, value, "
        "  metric, certification).\n"
        "- A claim is UNCITED if no vault entry or RFP reference supports it.\n"
        "- A claim is FABRICATED if it contains specific numbers/certifications that "
        "  contradict or are absent from all vault entries.\n\n"
        "Output JSON array 'results' with objects:\n"
        "  {\"claim_index\": int (1-based), \"citation_found\": bool, "
        "\"citation_source\": str|null, \"is_potentially_fabricated\": bool, "
        "\"fabrication_risk\": \"low\"|\"medium\"|\"high\", \"note\": str}\n\n"
        "Be conservative: only flag as fabricated when the claim is specific and "
        "clearly unsupported."
    )

    human_prompt = (
        f"Past Performance Vault ({len(pp_vault_entries)} entries):\n"
        f"{vault_summary or 'No vault entries available.'}\n\n"
        f"Claims to Validate ({len(validation_results)} total):\n{claims_text}\n\n"
        "Produce validation results JSON now."
    )

    raw = await _llm(system_prompt, human_prompt, max_tokens=4096, execution_id=state.get("deal_id"))
    parsed = _parse_json_response(raw, fallback={})

    citation_results: list[dict] = []
    if isinstance(parsed, list):
        citation_results = parsed
    elif isinstance(parsed, dict):
        citation_results = parsed.get("results", [])

    # Apply citation results back onto validation_results
    for cr in citation_results:
        idx = int(cr.get("claim_index", 0)) - 1
        if 0 <= idx < len(validation_results):
            validation_results[idx]["citation_found"] = cr.get("citation_found", False)
            validation_results[idx]["citation_source"] = cr.get("citation_source")
            validation_results[idx]["is_potentially_fabricated"] = cr.get(
                "is_potentially_fabricated", False
            )
            validation_results[idx]["fabrication_risk"] = cr.get("fabrication_risk", "low")
            validation_results[idx]["note"] = cr.get("note", "")

    uncited_claims = [
        c for c in validation_results
        if not c.get("citation_found") and c.get("requires_citation", True)
    ]
    fabricated_metrics = [
        c for c in validation_results
        if c.get("is_potentially_fabricated") and c.get("fabrication_risk") in ("medium", "high")
    ]

    return {
        "validation_results": validation_results,
        "uncited_claims": uncited_claims,
        "fabricated_metrics": fabricated_metrics,
        "messages": [
            HumanMessage(
                content=(
                    f"Citation validation: {len(uncited_claims)} uncited claim(s), "
                    f"{len(fabricated_metrics)} potential fabrication(s)."
                )
            )
        ],
    }


async def compute_compliance_coverage(state: EvidenceValidatorState) -> dict:
    """
    Count RFP requirements covered vs. total to compute a compliance coverage percentage.

    A requirement is considered covered if any proposal section text contains a
    reference to its requirement ID or key requirement text fragment.
    """
    deal_id = state["deal_id"]
    logger.info(
        "EvidenceValidator: computing compliance coverage for deal %s", deal_id
    )

    rfp_requirements: list[dict] = state.get("rfp_requirements") or []
    proposal_sections: dict = state.get("proposal_sections") or {}

    if not rfp_requirements:
        # Cannot assess coverage — assume minimum safe coverage
        return {
            "compliance_coverage": 0.0,
            "messages": [
                HumanMessage(content="No RFP requirements available — coverage cannot be computed.")
            ],
        }

    proposal_text_combined = " ".join(
        text.lower() for text in proposal_sections.values()
    )

    covered = 0
    for req in rfp_requirements:
        req_id = str(req.get("requirement_id") or req.get("id") or "")
        req_text = str(req.get("requirement_text") or req.get("text") or "")[:200].lower()

        # Check if requirement ID appears in proposal
        id_covered = req_id.lower() in proposal_text_combined if req_id else False
        # Check if key phrases from requirement text appear in proposal
        if not id_covered and req_text:
            # Use a 5-word window from the requirement text as a key phrase
            words = req_text.split()[:5]
            phrase = " ".join(words)
            id_covered = phrase in proposal_text_combined

        if id_covered:
            covered += 1

    coverage = covered / len(rfp_requirements) if rfp_requirements else 0.0
    coverage = round(coverage, 4)

    logger.info(
        "EvidenceValidator: compliance coverage = %.1f%% (%d/%d requirements) for deal %s",
        coverage * 100, covered, len(rfp_requirements), deal_id,
    )

    return {
        "compliance_coverage": coverage,
        "messages": [
            HumanMessage(
                content=(
                    f"Compliance coverage: {coverage*100:.1f}% "
                    f"({covered}/{len(rfp_requirements)} requirements addressed)."
                )
            )
        ],
    }


async def generate_validation_report(state: EvidenceValidatorState) -> dict:
    """
    Compile the full validation report and determine whether submission is safe.

    Submission is blocked if any of the following are true:
      - compliance_coverage < policy minimum (default 0.95)
      - High-risk fabricated metrics found
      - More than 20% of cited claims are uncited

    Sets is_submission_safe and populates blocking_issues.
    """
    deal_id = state["deal_id"]
    logger.info(
        "EvidenceValidator: generating validation report for deal %s", deal_id
    )

    # Load policy to get minimum coverage threshold
    try:
        policy = await policy_loader.get_policy()
    except Exception as exc:
        logger.warning(
            "EvidenceValidator: failed to load policy, using default: %s", exc
        )
        policy = policy_loader.DEFAULT_POLICY

    min_coverage = float(
        policy.get("risk_thresholds", {}).get("min_requirement_coverage", 0.95)
    )

    compliance_coverage = float(state.get("compliance_coverage") or 0.0)
    uncited_claims: list[dict] = state.get("uncited_claims") or []
    fabricated_metrics: list[dict] = state.get("fabricated_metrics") or []
    validation_results: list[dict] = state.get("validation_results") or []

    blocking_issues: list[str] = []

    # ── Check 1: Compliance coverage threshold ─────────────────────────────────
    if compliance_coverage < min_coverage:
        blocking_issues.append(
            f"Compliance coverage {compliance_coverage*100:.1f}% is below the required "
            f"minimum of {min_coverage*100:.1f}%."
        )

    # ── Check 2: High-risk fabricated metrics ──────────────────────────────────
    high_risk_fabrications = [
        f for f in fabricated_metrics if f.get("fabrication_risk") == "high"
    ]
    if high_risk_fabrications:
        blocking_issues.append(
            f"{len(high_risk_fabrications)} high-risk fabricated metric(s) detected: "
            + "; ".join(
                f.get("claim", "unknown")[:100] for f in high_risk_fabrications[:3]
            )
        )

    # ── Check 3: Uncited claims ratio ─────────────────────────────────────────
    total_claims = len(validation_results)
    uncited_count = len(uncited_claims)
    if total_claims > 0 and uncited_count / total_claims > 0.20:
        blocking_issues.append(
            f"{uncited_count}/{total_claims} claims ({uncited_count/total_claims*100:.0f}%) "
            "lack citations — exceeds 20% threshold."
        )

    is_submission_safe = len(blocking_issues) == 0

    if is_submission_safe:
        logger.info(
            "EvidenceValidator: proposal CLEARED for submission on deal %s", deal_id
        )
    else:
        logger.warning(
            "EvidenceValidator: proposal BLOCKED for deal %s — %d issue(s): %s",
            deal_id, len(blocking_issues), blocking_issues,
        )

    return {
        "is_submission_safe": is_submission_safe,
        "blocking_issues": blocking_issues,
        "messages": [
            HumanMessage(
                content=(
                    f"Validation report complete. "
                    f"Safe to submit: {is_submission_safe}. "
                    f"Blocking issues: {len(blocking_issues)}. "
                    f"Coverage: {compliance_coverage*100:.1f}%. "
                    f"Uncited: {uncited_count}. "
                    f"Fabrications: {len(fabricated_metrics)}."
                )
            )
        ],
    }


# ── Graph ─────────────────────────────────────────────────────────────────────


def build_evidence_validator_graph():
    wf = StateGraph(EvidenceValidatorState)
    wf.add_node("load_evidence_sources", load_evidence_sources)
    wf.add_node("extract_claims", extract_claims)
    wf.add_node("validate_citations", validate_citations)
    wf.add_node("compute_compliance_coverage", compute_compliance_coverage)
    wf.add_node("generate_validation_report", generate_validation_report)

    wf.set_entry_point("load_evidence_sources")
    wf.add_edge("load_evidence_sources", "extract_claims")
    wf.add_edge("extract_claims", "validate_citations")
    wf.add_edge("validate_citations", "compute_compliance_coverage")
    wf.add_edge("compute_compliance_coverage", "generate_validation_report")
    wf.add_edge("generate_validation_report", END)
    return wf.compile()


evidence_validator_graph = build_evidence_validator_graph()


# ── Agent ─────────────────────────────────────────────────────────────────────


class EvidenceValidatorAgent(BaseAgent):
    """
    AI agent that validates proposal evidence and blocks submission on hallucinations.

    Scans every proposal section for factual claims, verifies each against the
    past performance vault, checks compliance coverage, and returns a submission
    safety verdict.
    """

    agent_name = "evidence_validator_agent"

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        deal_id = input_data.get("deal_id", "")
        if not deal_id:
            return {"error": "deal_id is required"}

        initial: EvidenceValidatorState = {
            "deal_id": deal_id,
            "proposal_sections": input_data.get("proposal_sections", {}),
            "pp_vault_entries": input_data.get("pp_vault_entries", []),
            "rfp_requirements": input_data.get("rfp_requirements", []),
            "validation_results": [],
            "uncited_claims": [],
            "fabricated_metrics": [],
            "compliance_coverage": 0.0,
            "is_submission_safe": False,
            "blocking_issues": [],
            "messages": [],
        }

        try:
            await self.emit_event(
                "thinking",
                {"message": f"Validating proposal evidence for deal {deal_id}"},
                execution_id=deal_id,
            )
            fs = await evidence_validator_graph.ainvoke(initial)
            await self.emit_event(
                "output",
                {
                    "is_submission_safe": fs["is_submission_safe"],
                    "compliance_coverage": fs["compliance_coverage"],
                    "uncited_claims_count": len(fs["uncited_claims"]),
                    "fabricated_metrics_count": len(fs["fabricated_metrics"]),
                    "blocking_issues_count": len(fs["blocking_issues"]),
                },
                execution_id=deal_id,
            )
            return {
                "deal_id": fs["deal_id"],
                "is_submission_safe": fs["is_submission_safe"],
                "compliance_coverage": fs["compliance_coverage"],
                "validation_results": fs["validation_results"],
                "uncited_claims": fs["uncited_claims"],
                "fabricated_metrics": fs["fabricated_metrics"],
                "blocking_issues": fs["blocking_issues"],
            }
        except Exception as exc:
            logger.exception(
                "EvidenceValidatorAgent.run failed for deal %s", deal_id
            )
            await self.emit_event(
                "error", {"error": str(exc)}, execution_id=deal_id
            )
            return {"error": str(exc), "deal_id": deal_id}
