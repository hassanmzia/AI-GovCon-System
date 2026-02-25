"""Proposal section generation service using AI and knowledge vault."""
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


async def generate_section(
    section_type: str,
    deal_id: str,
    rfp_requirements: list[dict[str, Any]] | None = None,
    compliance_matrix: list[dict[str, Any]] | None = None,
    technical_solution: dict[str, Any] | None = None,
    capture_strategy: dict[str, Any] | None = None,
    past_performance: list[dict[str, Any]] | None = None,
    win_themes: list[str] | None = None,
    instructions: str = "",
) -> dict[str, Any]:
    """Generate a proposal section using AI.

    Args:
        section_type: Section to generate:
            "executive_summary", "technical_approach", "management_approach",
            "past_performance", "staffing_plan", "transition_plan",
            "quality_plan", "risk_management", "security_approach", "pricing_narrative".
        deal_id: Deal UUID.
        rfp_requirements: Relevant RFP requirements.
        compliance_matrix: Compliance matrix items.
        technical_solution: Solution architect output.
        capture_strategy: Marketing/capture strategy.
        past_performance: Relevant past performance.
        win_themes: Win themes to weave in.
        instructions: Additional instructions for the AI.

    Returns:
        Dict with content (markdown), compliance_trace, win_themes_used, word_count.
    """
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    context = _build_context(
        section_type, rfp_requirements, compliance_matrix,
        technical_solution, capture_strategy, past_performance, win_themes
    )

    system_prompt = _get_system_prompt(section_type)
    user_prompt = _build_user_prompt(section_type, context, instructions)

    content = ""
    if anthropic_key:
        content = await _generate_with_anthropic(system_prompt, user_prompt, anthropic_key)
    elif openai_key:
        content = await _generate_with_openai(system_prompt, user_prompt, openai_key)
    else:
        content = _generate_template(section_type, context)

    # Trace compliance coverage
    compliance_trace = _trace_compliance(content, compliance_matrix or [])

    return {
        "section_type": section_type,
        "deal_id": deal_id,
        "content": content,
        "compliance_trace": compliance_trace,
        "win_themes_used": [t for t in (win_themes or []) if t.lower()[:10] in content.lower()],
        "word_count": len(content.split()),
        "requires_human_review": True,
        "status": "draft",
    }


async def generate_executive_summary(
    deal: dict[str, Any],
    win_themes: list[str],
    value_proposition: str,
    technical_approach_summary: str,
    pricing_summary: str = "",
) -> dict[str, Any]:
    """Generate a Shipley-method executive summary.

    Returns:
        Dict with content, key_messages, word_count.
    """
    return await generate_section(
        section_type="executive_summary",
        deal_id=deal.get("id", ""),
        win_themes=win_themes,
        instructions=(
            f"Value proposition: {value_proposition}\n"
            f"Technical approach summary: {technical_approach_summary}\n"
            f"Pricing summary: {pricing_summary}"
        ),
    )


# ── Internal helpers ──────────────────────────────────────────────────────────

def _build_context(
    section_type: str,
    rfp_reqs: list | None,
    matrix: list | None,
    solution: dict | None,
    capture: dict | None,
    past_perf: list | None,
    win_themes: list | None,
) -> dict:
    return {
        "section_type": section_type,
        "rfp_requirements": (rfp_reqs or [])[:10],
        "compliance_items": (matrix or [])[:10],
        "win_themes": win_themes or [],
        "value_proposition": (capture or {}).get("value_proposition", ""),
        "technical_summary": (solution or {}).get("solution_overview", ""),
        "past_performance_count": len(past_perf or []),
    }


def _get_system_prompt(section_type: str) -> str:
    prompts = {
        "executive_summary": (
            "You are an expert proposal writer specializing in government contract proposals. "
            "Write a compelling executive summary using the Shipley method that addresses the "
            "customer's needs, differentiates the offeror, and clearly articulates value. "
            "Use active voice, specific claims, and weave in win themes naturally."
        ),
        "technical_approach": (
            "You are a senior systems architect and proposal writer. Write a detailed technical "
            "approach section that demonstrates thorough understanding of requirements, presents "
            "a sound technical solution, and highlights discriminators. Include methodology, "
            "tools, techniques, and risk mitigations."
        ),
        "management_approach": (
            "You are an expert proposal writer for management volumes. Write a professional "
            "management approach section covering PM methodology, organizational structure, "
            "communication plan, quality management, and risk management."
        ),
        "past_performance": (
            "You are a proposal writer creating a past performance volume. Write concise, "
            "impactful past performance narratives that demonstrate relevance to the current "
            "requirement. Focus on scope, results, and lessons applied."
        ),
    }
    return prompts.get(
        section_type,
        "You are an expert government proposal writer. Write a professional, compliant, "
        "and compelling proposal section. Use active voice, specific claims backed by evidence, "
        "and ensure all government requirements are addressed.",
    )


def _build_user_prompt(section_type: str, context: dict, instructions: str) -> str:
    parts = [
        f"Write the '{section_type.replace('_', ' ').title()}' section of a government proposal.",
        "",
    ]
    if context.get("win_themes"):
        parts.append("Win themes to incorporate: " + "; ".join(context["win_themes"][:3]))
    if context.get("value_proposition"):
        parts.append(f"Value proposition: {context['value_proposition']}")
    if context.get("rfp_requirements"):
        parts.append("Key requirements to address:")
        for req in context["rfp_requirements"][:5]:
            parts.append(f"  - {req.get('text', str(req))[:200]}")
    if instructions:
        parts.append(f"\nAdditional context: {instructions}")
    parts.append("\nWrite a professional, government proposal section in markdown format.")
    return "\n".join(parts)


async def _generate_with_anthropic(system: str, user: str, api_key: str) -> str:
    try:
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=api_key)
        message = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return message.content[0].text
    except Exception as exc:
        logger.error("Anthropic generation failed: %s", exc)
        return ""


async def _generate_with_openai(system: str, user: str, api_key: str) -> str:
    try:
        import openai  # type: ignore

        client = openai.AsyncOpenAI(api_key=api_key)
        resp = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=4096,
        )
        return resp.choices[0].message.content or ""
    except Exception as exc:
        logger.error("OpenAI generation failed: %s", exc)
        return ""


def _generate_template(section_type: str, context: dict) -> str:
    return (
        f"## {section_type.replace('_', ' ').title()}\n\n"
        f"[AI-generated content placeholder for {section_type}]\n\n"
        f"Win themes: {', '.join(context.get('win_themes', [])[:3])}\n\n"
        f"Requirements addressed: {len(context.get('rfp_requirements', []))}\n"
    )


def _trace_compliance(content: str, matrix: list[dict]) -> list[dict]:
    """Trace which compliance matrix items are addressed in the content."""
    traced = []
    content_lower = content.lower()
    for item in matrix:
        req_text = (item.get("requirement_text") or item.get("text") or "").lower()
        if req_text and any(word in content_lower for word in req_text.split()[:5]):
            traced.append(
                {
                    "requirement_id": item.get("id", ""),
                    "requirement_text": req_text[:100],
                    "addressed": True,
                }
            )
    return traced
