"""Research report generator: synthesizes sources into structured findings."""
import logging
import os
from typing import Any

logger = logging.getLogger("ai_deal_manager.research.report")


async def generate_research_report(
    topic: str,
    research_type: str,
    sources: list[dict[str, Any]],
    deal_id: str | None = None,
) -> dict[str, Any]:
    """Synthesize research sources into a structured report.

    Uses Claude (or GPT-4o fallback) to extract key findings and create a summary.

    Returns:
        Dict with: summary, findings, key_facts, citations, recommendations.
    """
    if not sources:
        return {
            "summary": f"No sources found for research on: {topic}",
            "findings": [],
            "key_facts": [],
            "citations": [],
            "recommendations": [],
        }

    # Build context from sources
    source_texts = []
    citations = []
    for i, src in enumerate(sources[:15]):  # cap at 15 sources
        title = src.get("title", f"Source {i + 1}")
        content = src.get("content", src.get("snippet", src.get("description", "")))
        url = src.get("url", src.get("link", ""))
        if content:
            source_texts.append(f"[{i + 1}] {title}\n{content[:500]}")
            citations.append({"index": i + 1, "title": title, "url": url})

    sources_block = "\n\n".join(source_texts)

    prompt = f"""You are a research analyst for a government contracting firm.
Analyze the following sources and produce a structured research report on: {topic}

Research type: {research_type}
{"Deal context: " + deal_id if deal_id else ""}

SOURCES:
{sources_block}

Provide a JSON response with these keys:
- summary: 2-3 paragraph executive summary
- findings: list of 5-10 key findings (strings)
- key_facts: list of specific facts, numbers, dates (strings)
- recommendations: list of 3-5 actionable recommendations

Format as valid JSON only, no markdown."""

    report = await _call_ai(prompt)

    # Merge with citations collected from sources
    report["citations"] = citations
    return report


async def _call_ai(prompt: str) -> dict[str, Any]:
    """Call AI provider to generate the report. Falls back to rule-based extraction."""
    try:
        from apps.core.llm_provider import chat_completion

        raw = await chat_completion(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
        )
        return _parse_json_response(raw)
    except Exception as exc:
        logger.warning("AI research report generation failed: %s", exc)

    # Rule-based fallback
    return {
        "summary": "Research synthesis unavailable – LLM provider not configured.",
        "findings": ["Multiple sources retrieved but synthesis requires LLM configuration."],
        "key_facts": [],
        "recommendations": ["Configure LLM_PROVIDER and the required API key for AI synthesis."],
    }


def _parse_json_response(text: str) -> dict[str, Any]:
    """Parse JSON from AI response, stripping markdown fences if present."""
    import json
    import re

    text = text.strip()
    # Strip markdown code fences
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {
            "summary": text[:500] if text else "Unable to parse report.",
            "findings": [],
            "key_facts": [],
            "recommendations": [],
        }
