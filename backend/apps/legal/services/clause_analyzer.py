"""Clause analyzer – clause-by-clause risk analysis for contracts and RFPs."""
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# Known high-risk clause patterns
_HIGH_RISK_PATTERNS = [
    (r"52\.227-14", "Rights in Data – General", "IP/Data rights – restricts your ability to use deliverables"),
    (r"252\.204-7012", "DFARS 252.204-7012", "CMMC/NIST 800-171 compliance required"),
    (r"52\.215-2", "Audit and Records", "Government audit rights – ensure cost records are maintained"),
    (r"52\.232-7", "Payments under Time-and-Materials", "T&M payment terms – document all labor hours"),
    (r"termination for convenience", "Termination for Convenience", "Government may terminate without cause – limit startup costs"),
    (r"liquidated damages", "Liquidated Damages", "Financial penalties for late delivery – assess feasibility"),
    (r"key personnel", "Key Personnel", "Key personnel cannot leave without CO approval"),
    (r"organizational conflict", "OCI Clause", "OCI restrictions may limit future business"),
    (r"unlimited rights", "Unlimited Rights", "Government gets unlimited use of all deliverables"),
    (r"buy american", "Buy American Act", "Domestic sourcing requirements may impact supply chain"),
    (r"section 889", "Section 889", "Prohibited telecommunications equipment must be removed"),
]

_MEDIUM_RISK_PATTERNS = [
    (r"indemnif", "Indemnification", "Review scope of indemnification obligations"),
    (r"hold harmless", "Hold Harmless", "Broad hold harmless may exceed insurance coverage"),
    (r"consequential damages", "Consequential Damages", "Unlimited consequential damages exposure"),
    (r"change order", "Change Order", "Ensure change order process preserves pricing rights"),
    (r"warranty", "Warranty", "Warranty period and scope – evaluate cost impact"),
]


async def analyze_contract_clauses(
    contract_text: str,
    contract_type: str = "prime",
) -> dict[str, Any]:
    """Perform clause-by-clause risk analysis on contract text.

    Args:
        contract_text: Full contract text.
        contract_type: Type ("prime", "subcontract", "teaming", "nda").

    Returns:
        Dict with clauses_found, risk_summary, red_flags, recommendations.
    """
    text_lower = contract_text.lower()

    high_risk = []
    medium_risk = []
    low_risk = []

    for pattern, clause_name, risk_explanation in _HIGH_RISK_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            # Extract surrounding context
            match = re.search(pattern, contract_text, re.IGNORECASE)
            context = ""
            if match:
                start = max(0, match.start() - 100)
                end = min(len(contract_text), match.end() + 200)
                context = contract_text[start:end].strip()

            high_risk.append(
                {
                    "clause_name": clause_name,
                    "risk_level": "high",
                    "explanation": risk_explanation,
                    "context_excerpt": context[:300],
                    "action_required": True,
                }
            )

    for pattern, clause_name, risk_explanation in _MEDIUM_RISK_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            medium_risk.append(
                {
                    "clause_name": clause_name,
                    "risk_level": "medium",
                    "explanation": risk_explanation,
                    "action_required": False,
                }
            )

    # Identify missing clauses (protective clauses)
    missing_protective = []
    if "limitation of liability" not in text_lower:
        missing_protective.append("Limitation of Liability clause is absent – consider negotiating a cap")
    if "force majeure" not in text_lower:
        missing_protective.append("Force Majeure clause absent – no protection for unforeseen events")
    if "dispute resolution" not in text_lower and "disputes" not in text_lower:
        missing_protective.append("Dispute resolution mechanism unclear")

    overall_risk = "high" if len(high_risk) > 2 else "medium" if high_risk else "low"

    return {
        "contract_type": contract_type,
        "clauses_analyzed": len(high_risk) + len(medium_risk),
        "high_risk_clauses": high_risk,
        "medium_risk_clauses": medium_risk,
        "low_risk_clauses": low_risk,
        "missing_protective_clauses": missing_protective,
        "overall_risk": overall_risk,
        "risk_summary": _build_risk_summary(high_risk, medium_risk),
        "recommendations": _build_recommendations(high_risk, medium_risk, missing_protective),
        "far_dfars_clauses_found": _extract_far_references(contract_text),
    }


async def extract_far_clauses(rfp_or_contract_text: str) -> list[dict[str, Any]]:
    """Extract all FAR/DFARS clause references from a document.

    Args:
        rfp_or_contract_text: Document text.

    Returns:
        List of clause references with number, title, and risk level.
    """
    return _extract_far_references(rfp_or_contract_text)


async def check_flow_down_requirements(
    prime_contract_clauses: list[str],
) -> list[dict[str, Any]]:
    """Identify which clauses from the prime contract must flow down to subcontractors.

    Args:
        prime_contract_clauses: List of FAR/DFARS clause numbers.

    Returns:
        List of flow-down required clauses with guidance.
    """
    from apps.legal.services.legal_rag import search_far_clause

    flow_downs = []
    for clause_ref in prime_contract_clauses:
        clause_info = await search_far_clause(clause_ref)
        if clause_info and clause_info.get("flow_down_required"):
            flow_downs.append(
                {
                    "clause_number": clause_ref,
                    "title": clause_info.get("title", ""),
                    "flow_down_required": True,
                    "negotiation_guidance": clause_info.get("negotiation_guidance", ""),
                }
            )
    return flow_downs


# ── Internal helpers ──────────────────────────────────────────────────────────

def _extract_far_references(text: str) -> list[dict]:
    """Extract FAR (52.xxx-xxx) and DFARS (252.xxx-xxxx) references."""
    far_pattern = r"(52\.\d{3}-\d+)"
    dfars_pattern = r"(252\.\d{3}-\d+)"

    far_matches = set(re.findall(far_pattern, text, re.IGNORECASE))
    dfars_matches = set(re.findall(dfars_pattern, text, re.IGNORECASE))

    results = []
    for ref in sorted(far_matches):
        results.append(
            {"clause_number": ref, "source": "FAR", "risk_level": _assess_clause_risk(ref)}
        )
    for ref in sorted(dfars_matches):
        results.append(
            {"clause_number": ref, "source": "DFARS", "risk_level": _assess_clause_risk(ref)}
        )

    return results


def _assess_clause_risk(clause_number: str) -> str:
    high_risk_clauses = {
        "52.227-14", "52.233-1", "52.215-2", "52.232-7",
        "252.204-7012", "252.227-7013", "252.227-7014",
    }
    medium_risk_clauses = {
        "52.212-4", "52.215-14", "52.232-22", "52.247-34",
    }
    if clause_number in high_risk_clauses:
        return "high"
    if clause_number in medium_risk_clauses:
        return "medium"
    return "low"


def _build_risk_summary(high: list, medium: list) -> str:
    if not high and not medium:
        return "No significant risk clauses identified."
    parts = []
    if high:
        parts.append(f"{len(high)} high-risk clause(s): " + ", ".join(c["clause_name"] for c in high[:3]))
    if medium:
        parts.append(f"{len(medium)} medium-risk clause(s): " + ", ".join(c["clause_name"] for c in medium[:3]))
    return ". ".join(parts) + "."


def _build_recommendations(high: list, medium: list, missing: list) -> list[str]:
    recs = []
    for h in high[:3]:
        recs.append(f"Review and negotiate '{h['clause_name']}': {h['explanation']}")
    if missing:
        recs.extend(missing[:2])
    if not recs:
        recs.append("Contract appears low-risk; proceed with standard review")
    return recs
