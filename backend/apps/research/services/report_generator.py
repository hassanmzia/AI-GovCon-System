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
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
    openai_key = os.getenv("OPENAI_API_KEY", "")

    if anthropic_key:
        try:
            import anthropic  # type: ignore

            client = anthropic.AsyncAnthropic(api_key=anthropic_key)
            msg = await client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = msg.content[0].text
            return _parse_json_response(raw)
        except Exception as exc:
            logger.warning("Anthropic research report generation failed: %s", exc)

    if openai_key:
        try:
            import openai  # type: ignore

            client = openai.AsyncOpenAI(api_key=openai_key)
            resp = await client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                max_tokens=2000,
            )
            import json

            return json.loads(resp.choices[0].message.content or "{}")
        except Exception as exc:
            logger.warning("OpenAI research report generation failed: %s", exc)

    # Rule-based fallback
    return {
        "summary": "Research synthesis unavailable – AI provider not configured.",
        "findings": ["Multiple sources retrieved but synthesis requires AI configuration."],
        "key_facts": [],
        "recommendations": ["Configure ANTHROPIC_API_KEY or OPENAI_API_KEY for AI synthesis."],
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
