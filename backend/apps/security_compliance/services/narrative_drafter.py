"""Security narrative drafter: generates SSP narratives and security approach sections."""
import logging
import os
from typing import Any

logger = logging.getLogger("ai_deal_manager.security.narrative")


async def draft_control_narrative(
    control_id: str,
    system_description: str = "",
    existing_implementation: str = "",
    organization_name: str = "",
) -> dict[str, Any]:
    """Draft an SSP narrative for a specific security control.

    Args:
        control_id: NIST 800-53 control ID (e.g., "AC-2").
        system_description: Brief description of the system.
        existing_implementation: Any known existing implementation details.
        organization_name: Organization name for personalization.

    Returns:
        Dict with: control_id, narrative, implementation_status, gaps.
    """
    from backend.apps.security_compliance.services.control_mapper import (
        get_control_details,
    )

    ctrl = get_control_details(control_id)
    if "error" in ctrl:
        return {"control_id": control_id, "error": ctrl["error"]}

    prompt = _build_narrative_prompt(
        ctrl, system_description, existing_implementation, organization_name
    )
    narrative = await _call_ai(prompt, max_tokens=600)

    return {
        "control_id": control_id,
        "control_title": ctrl.get("title", ""),
        "control_family": ctrl.get("family", ""),
        "narrative": narrative,
        "implementation_status": _assess_implementation_status(existing_implementation),
        "word_count": len(narrative.split()),
    }


async def draft_security_approach_section(
    rfp_security_requirements: list[str],
    framework: str = "NIST_800_53",
    clearance_required: str | None = None,
    fedramp_level: str | None = None,
    cmmc_level: int | None = None,
    organization_name: str = "",
) -> dict[str, Any]:
    """Draft a complete security approach proposal section.

    Returns:
        Dict with: content, word_count, controls_addressed, frameworks_cited.
    """
    requirements_text = "\n".join(f"- {r}" for r in rfp_security_requirements[:10])
    frameworks_text = _build_frameworks_text(framework, fedramp_level, cmmc_level)
    clearance_text = f"\nRequired clearance level: {clearance_required}" if clearance_required else ""

    prompt = f"""You are a cybersecurity proposal writer for a government contractor.
Draft a comprehensive Security Approach section for a proposal.

Organization: {organization_name or "Our organization"}
Compliance frameworks required: {frameworks_text}
{clearance_text}

Security requirements from RFP:
{requirements_text or "General security requirements apply."}

Write a professional, detailed security approach section (600-800 words) covering:
1. Security architecture and principles (zero trust, defense in depth)
2. Identity and access management approach
3. Data protection (encryption at rest and in transit)
4. Continuous monitoring and incident response
5. Compliance posture ({frameworks_text})
6. Supply chain security

Use specific, measurable commitments. Reference relevant NIST controls where appropriate."""

    content = await _call_ai(prompt, max_tokens=1200)

    return {
        "section_type": "security_approach",
        "content": content,
        "word_count": len(content.split()),
        "frameworks_cited": [framework],
        "fedramp_level": fedramp_level,
        "cmmc_level": cmmc_level,
    }


async def draft_security_narrative_for_controls(
    control_ids: list[str],
    system_description: str = "",
    organization_name: str = "",
) -> list[dict[str, Any]]:
    """Draft narratives for multiple controls in parallel."""
    import asyncio

    tasks = [
        draft_control_narrative(cid, system_description, "", organization_name)
        for cid in control_ids
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    output = []
    for cid, result in zip(control_ids, results):
        if isinstance(result, Exception):
            logger.warning("Narrative draft failed for %s: %s", cid, result)
            output.append({"control_id": cid, "error": str(result)})
        else:
            output.append(result)
    return output


# ── Internal helpers ──────────────────────────────────────────────────────────

def _build_narrative_prompt(
    ctrl: dict,
    system_description: str,
    existing_implementation: str,
    org_name: str,
) -> str:
    system_ctx = f" for {system_description}" if system_description else ""
    existing_ctx = f"\n\nExisting implementation: {existing_implementation}" if existing_implementation else ""
    return (
        f"Write a professional SSP (System Security Plan) narrative for control "
        f"{ctrl['control_id']} - {ctrl.get('title', '')}{system_ctx}.\n\n"
        f"Organization: {org_name or 'The organization'}\n"
        f"Control family: {ctrl.get('family', '')}"
        f"{existing_ctx}\n\n"
        f"The narrative should:\n"
        f"- Describe HOW the control is implemented (not just what it requires)\n"
        f"- Be specific about tools, processes, and responsible roles\n"
        f"- Be 150-250 words\n"
        f"- Use past/present tense (implemented, maintains, reviews)\n"
        f"- Reference specific policies and procedures"
    )


def _assess_implementation_status(existing_implementation: str) -> str:
    if not existing_implementation or len(existing_implementation) < 20:
        return "not_implemented"
    keywords_implemented = ["implemented", "deployed", "configured", "in place", "currently"]
    keywords_partial = ["partial", "in progress", "planned", "developing"]
    text_lower = existing_implementation.lower()
    if any(k in text_lower for k in keywords_implemented):
        return "implemented"
    if any(k in text_lower for k in keywords_partial):
        return "partially_implemented"
    return "planned"


def _build_frameworks_text(framework: str, fedramp_level: str | None, cmmc_level: int | None) -> str:
    parts = [framework.replace("_", " ")]
    if fedramp_level:
        parts.append(f"FedRAMP {fedramp_level.capitalize()}")
    if cmmc_level:
        parts.append(f"CMMC Level {cmmc_level}")
    return ", ".join(parts)


async def _call_ai(prompt: str, max_tokens: int = 600) -> str:
    """Call AI to generate security narrative."""
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
    if anthropic_key:
        try:
            import anthropic  # type: ignore

            client = anthropic.AsyncAnthropic(api_key=anthropic_key)
            msg = await client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            return msg.content[0].text
        except Exception as exc:
            logger.warning("AI narrative generation failed: %s", exc)

    openai_key = os.getenv("OPENAI_API_KEY", "")
    if openai_key:
        try:
            import openai  # type: ignore

            client = openai.AsyncOpenAI(api_key=openai_key)
            resp = await client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
            )
            return resp.choices[0].message.content or ""
        except Exception as exc:
            logger.warning("OpenAI narrative generation failed: %s", exc)

    return f"[AI narrative generation requires ANTHROPIC_API_KEY or OPENAI_API_KEY configuration]"
