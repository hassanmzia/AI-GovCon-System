"""CO answer impact mapping – maps answers to compliance matrix and pricing changes."""
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


async def map_answer_impact(
    answer_id: str,
    answer_text: str,
    deal_id: str,
    compliance_matrix: list[dict[str, Any]] | None = None,
    pricing_assumptions: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Analyze how a CO answer impacts the proposal strategy.

    Args:
        answer_id: Answer UUID.
        answer_text: The CO's answer text.
        deal_id: Deal UUID.
        compliance_matrix: Current compliance matrix items.
        pricing_assumptions: Current pricing assumptions.

    Returns:
        Dict with compliance_matrix_changes, pricing_impacts, scope_changes, risk_changes.
    """
    answer_lower = answer_text.lower()

    # Detect answer category
    impact_category = _categorize_answer(answer_lower)

    # Map to compliance matrix changes
    matrix_changes = _map_to_compliance(answer_text, answer_lower, compliance_matrix or [])

    # Map to pricing impacts
    pricing_impacts = _map_to_pricing(answer_text, answer_lower, pricing_assumptions or [])

    # Detect scope changes
    scope_changes = _detect_scope_changes(answer_lower)

    # Detect risk changes
    risk_changes = _detect_risk_changes(answer_lower)

    # AI-enhanced analysis if API key available
    if os.getenv("ANTHROPIC_API_KEY") and (matrix_changes or pricing_impacts):
        enhanced = await _ai_impact_analysis(answer_text, matrix_changes, pricing_impacts)
        matrix_changes = enhanced.get("matrix_changes", matrix_changes)
        pricing_impacts = enhanced.get("pricing_impacts", pricing_impacts)

    impact_level = _compute_impact_level(matrix_changes, pricing_impacts, scope_changes, risk_changes)

    return {
        "answer_id": answer_id,
        "deal_id": deal_id,
        "impact_level": impact_level,
        "impact_category": impact_category,
        "compliance_matrix_changes": matrix_changes,
        "pricing_impacts": pricing_impacts,
        "scope_changes": scope_changes,
        "risk_changes": risk_changes,
        "action_required": impact_level in ("high", "critical"),
        "recommended_actions": _recommend_actions(impact_level, matrix_changes, pricing_impacts, scope_changes),
    }


async def bulk_map_impacts(
    answers: list[dict[str, Any]],
    deal_id: str,
) -> list[dict[str, Any]]:
    """Map impacts for a batch of CO answers.

    Returns:
        List of impact mapping results.
    """
    import asyncio

    tasks = [
        map_answer_impact(
            answer_id=a.get("id", ""),
            answer_text=a.get("answer_text", ""),
            deal_id=deal_id,
        )
        for a in answers
    ]
    return await asyncio.gather(*tasks)


# ── Internal helpers ──────────────────────────────────────────────────────────

def _categorize_answer(answer_lower: str) -> str:
    if any(kw in answer_lower for kw in ["scope", "deliverable", "requirement", "shall", "must"]):
        return "scope_clarification"
    if any(kw in answer_lower for kw in ["price", "cost", "rate", "fee", "hours", "budget"]):
        return "pricing_clarification"
    if any(kw in answer_lower for kw in ["evaluation", "criteria", "factor", "award"]):
        return "evaluation_clarification"
    if any(kw in answer_lower for kw in ["schedule", "deadline", "date", "period"]):
        return "schedule_clarification"
    if any(kw in answer_lower for kw in ["term", "condition", "clause", "contract"]):
        return "terms_clarification"
    return "general_clarification"


def _map_to_compliance(text: str, text_lower: str, matrix: list[dict]) -> list[dict]:
    changes = []
    if "no longer required" in text_lower or "is removed" in text_lower:
        changes.append(
            {
                "change_type": "requirement_removed",
                "description": "A requirement appears to have been removed or modified",
                "action": "Update compliance matrix and remove or flag affected items",
                "impact": "medium",
            }
        )
    if "clarify" in text_lower or "the intent is" in text_lower:
        changes.append(
            {
                "change_type": "requirement_clarified",
                "description": "A requirement has been clarified",
                "action": "Review affected compliance matrix items and update response",
                "impact": "medium",
            }
        )
    if "see amendment" in text_lower or "will be issued" in text_lower:
        changes.append(
            {
                "change_type": "amendment_forthcoming",
                "description": "An amendment will be issued with changes",
                "action": "Monitor for amendment and update compliance matrix upon receipt",
                "impact": "high",
            }
        )
    return changes


def _map_to_pricing(text: str, text_lower: str, assumptions: list[dict]) -> list[dict]:
    impacts = []
    if any(kw in text_lower for kw in ["hours", "fte", "staffing", "level of effort"]):
        impacts.append(
            {
                "impact_type": "loe_change",
                "description": "Answer may affect Level of Effort assumptions",
                "action": "Review and update LOE estimates in pricing model",
                "impact": "high",
            }
        )
    if any(kw in text_lower for kw in ["odcs", "travel", "materials", "equipment"]):
        impacts.append(
            {
                "impact_type": "odc_change",
                "description": "Other Direct Costs may be affected",
                "action": "Update ODC budget in pricing model",
                "impact": "medium",
            }
        )
    if any(kw in text_lower for kw in ["period", "option", "extension", "year"]):
        impacts.append(
            {
                "impact_type": "pop_change",
                "description": "Period of performance may have changed",
                "action": "Verify POP and adjust pricing accordingly",
                "impact": "high",
            }
        )
    return impacts


def _detect_scope_changes(text_lower: str) -> list[dict]:
    changes = []
    if "added" in text_lower or "additional" in text_lower:
        changes.append({"type": "scope_addition", "description": "Scope addition may have been made"})
    if "removed" in text_lower or "deleted" in text_lower or "no longer" in text_lower:
        changes.append({"type": "scope_reduction", "description": "Scope reduction may have occurred"})
    return changes


def _detect_risk_changes(text_lower: str) -> list[dict]:
    changes = []
    if any(kw in text_lower for kw in ["security clearance", "clearance required", "classified"]):
        changes.append({"type": "clearance_requirement", "description": "Security clearance requirements identified"})
    if any(kw in text_lower for kw in ["small business", "set-aside", "sb goals"]):
        changes.append({"type": "sb_requirement", "description": "Small business requirement may have changed"})
    return changes


def _compute_impact_level(matrix: list, pricing: list, scope: list, risk: list) -> str:
    total = len(matrix) + len(pricing) + len(scope) + len(risk)
    if total >= 4:
        return "critical"
    if total >= 2:
        return "high"
    if total >= 1:
        return "medium"
    return "low"


def _recommend_actions(level: str, matrix: list, pricing: list, scope: list) -> list[str]:
    actions = []
    if level in ("critical", "high"):
        actions.append("URGENT: Convene team to discuss answer impacts")
    for m in matrix[:2]:
        actions.append(m.get("action", "Update compliance matrix"))
    for p in pricing[:2]:
        actions.append(p.get("action", "Review pricing model"))
    for s in scope[:1]:
        actions.append(f"Review scope change: {s.get('description', '')}")
    return actions or ["No significant action required – file for reference"]


async def _ai_impact_analysis(
    answer_text: str,
    matrix_changes: list,
    pricing_impacts: list,
) -> dict:
    """Use AI for enhanced impact analysis."""
    try:
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        prompt = (
            f"CO Answer: {answer_text}\n\n"
            f"Analyze the impact of this answer on:\n"
            f"1. Compliance matrix items\n"
            f"2. Pricing assumptions\n\n"
            f"Return JSON with matrix_changes (list) and pricing_impacts (list)."
        )
        message = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        import json

        content = message.content[0].text
        try:
            return json.loads(content)
        except Exception:
            return {"matrix_changes": matrix_changes, "pricing_impacts": pricing_impacts}
    except Exception:
        return {"matrix_changes": matrix_changes, "pricing_impacts": pricing_impacts}
