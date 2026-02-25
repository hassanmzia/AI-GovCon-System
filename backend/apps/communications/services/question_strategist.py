"""Vendor question strategist – AI-powered prioritization of clarification questions."""
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


async def generate_question_strategy(
    deal_id: str,
    rfp_text: str,
    max_questions: int = 20,
    focus_areas: list[str] | None = None,
) -> dict[str, Any]:
    """Generate a prioritized list of clarification questions using AI.

    Questions are ranked by information value – the higher the value,
    the more the answer will impact bid strategy.

    Args:
        deal_id: Deal UUID.
        rfp_text: Full RFP text.
        max_questions: Maximum questions to generate.
        focus_areas: Areas to focus on (e.g. ["technical", "pricing", "terms"]).

    Returns:
        Dict with questions (ranked list), strategy_notes, categories.
    """
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")

    if anthropic_key:
        questions = await _generate_with_ai(rfp_text, max_questions, focus_areas, anthropic_key)
    else:
        questions = _generate_rule_based(rfp_text, max_questions)

    # Rank by information value
    questions.sort(key=lambda q: q.get("priority", 5), reverse=True)

    return {
        "deal_id": deal_id,
        "questions": questions[:max_questions],
        "total_generated": len(questions),
        "categories": _count_by_category(questions),
        "strategy_notes": _build_strategy_notes(questions),
        "submission_tips": _get_submission_tips(),
    }


async def prioritize_questions(
    questions: list[dict[str, Any]],
    rfp_context: str = "",
    deal_context: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Re-prioritize an existing list of questions.

    Args:
        questions: List of question dicts.
        rfp_context: RFP text for context.
        deal_context: Deal dict for context.

    Returns:
        Re-prioritized list of questions.
    """
    for question in questions:
        # Score information value
        info_value = _score_information_value(
            question.get("question_text", ""),
            question.get("category", "general"),
            rfp_context,
        )
        question["priority"] = info_value
        question["information_value_score"] = info_value

    questions.sort(key=lambda q: q["priority"], reverse=True)
    return questions


# ── Internal helpers ──────────────────────────────────────────────────────────

async def _generate_with_ai(
    rfp_text: str,
    max_questions: int,
    focus_areas: list[str] | None,
    api_key: str,
) -> list[dict]:
    try:
        import anthropic
        import json

        client = anthropic.AsyncAnthropic(api_key=api_key)
        focus = f"\nFocus areas: {', '.join(focus_areas)}" if focus_areas else ""
        rfp_excerpt = rfp_text[:4000]  # Limit to fit in context

        prompt = f"""You are a government proposal expert. Analyze this RFP and generate the most valuable
clarification questions to ask the Contracting Officer.{focus}

RFP Excerpt:
{rfp_excerpt}

Generate up to {max_questions} questions as JSON array. Each question:
{{
  "question_text": "The actual question",
  "category": "technical|pricing|terms|scope|evaluation|logistics",
  "priority": 1-10,
  "rfp_section_ref": "Section X.X" or null,
  "information_value": "Why this answer matters",
  "impact_if_not_asked": "Risk of not asking"
}}

Focus on questions that:
1. Reveal evaluation criteria weight or methodology
2. Clarify scope ambiguities that affect LOE
3. Identify incumbent advantages
4. Expose unstated requirements
5. Clarify terms that create performance risk

Return only the JSON array."""

        message = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=3000,
            messages=[{"role": "user", "content": prompt}],
        )

        content = message.content[0].text
        # Extract JSON array
        import re

        json_match = re.search(r"\[.*\]", content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return json.loads(content)

    except Exception as exc:
        logger.error("AI question generation failed: %s", exc)
        return _generate_rule_based(rfp_text, max_questions)


def _generate_rule_based(rfp_text: str, max_questions: int) -> list[dict]:
    """Generate questions using rule-based patterns when AI is unavailable."""
    questions = []
    rfp_lower = rfp_text.lower()

    # Evaluation criteria questions
    if "evaluation" in rfp_lower or "criteria" in rfp_lower:
        questions.append(
            {
                "question_text": "What is the relative weighting of Technical, Management, Past Performance, and Price/Cost evaluation factors?",
                "category": "evaluation",
                "priority": 10,
                "rfp_section_ref": "Section M",
                "information_value": "Determines how to allocate proposal writing effort",
                "impact_if_not_asked": "May over-invest in lower-weighted areas",
            }
        )

    # Incumbent questions
    questions.append(
        {
            "question_text": "Is there an incumbent contractor currently performing these services? If so, can you provide their contract number?",
            "category": "scope",
            "priority": 9,
            "rfp_section_ref": None,
            "information_value": "Identifies competitive landscape and transition challenges",
            "impact_if_not_asked": "May miss transition requirements",
        }
    )

    # Staffing questions
    if "personnel" in rfp_lower or "staffing" in rfp_lower or "key personnel" in rfp_lower:
        questions.append(
            {
                "question_text": "Will key personnel proposed in the offeror's proposal be evaluated beyond the minimum qualifications listed in the PWS?",
                "category": "evaluation",
                "priority": 8,
                "rfp_section_ref": "Section L",
                "information_value": "Determines seniority level to propose for key personnel",
            }
        )

    # Security questions
    if "clearance" in rfp_lower or "secret" in rfp_lower or "classified" in rfp_lower:
        questions.append(
            {
                "question_text": "Please confirm the security clearance level required for all proposed personnel and whether interim clearances are acceptable at start of contract.",
                "category": "technical",
                "priority": 9,
                "rfp_section_ref": "Section H",
                "information_value": "Affects staffing plan and transition timeline",
            }
        )

    # Pricing questions
    questions.extend(
        [
            {
                "question_text": "Does the Government have an Independent Government Cost Estimate (IGCE)? If so, what is the ceiling?",
                "category": "pricing",
                "priority": 8,
                "rfp_section_ref": "Section B",
                "information_value": "Validates our price-to-win estimate",
            },
            {
                "question_text": "Are travel costs included in the ceiling price or in addition to it?",
                "category": "pricing",
                "priority": 7,
                "rfp_section_ref": "Section B/J",
                "information_value": "Affects cost model",
            },
        ]
    )

    # Schedule questions
    questions.append(
        {
            "question_text": "What is the anticipated award date and transition period?",
            "category": "logistics",
            "priority": 6,
            "rfp_section_ref": "Section F",
            "information_value": "Affects staffing timeline and transition cost estimates",
        }
    )

    return questions[:max_questions]


def _score_information_value(question_text: str, category: str, rfp_context: str) -> int:
    """Score a question's information value 1-10."""
    base_scores = {
        "evaluation": 9,
        "pricing": 8,
        "scope": 7,
        "technical": 7,
        "terms": 6,
        "logistics": 5,
        "general": 4,
    }
    score = base_scores.get(category, 5)

    # Boost for high-impact keywords
    high_impact = ["evaluation", "criteria", "weight", "incumbent", "clearance", "price", "ceiling"]
    q_lower = question_text.lower()
    boost = sum(1 for kw in high_impact if kw in q_lower)
    return min(10, score + boost)


def _count_by_category(questions: list[dict]) -> dict:
    counts: dict[str, int] = {}
    for q in questions:
        cat = q.get("category", "general")
        counts[cat] = counts.get(cat, 0) + 1
    return counts


def _build_strategy_notes(questions: list[dict]) -> str:
    total = len(questions)
    high_priority = sum(1 for q in questions if q.get("priority", 0) >= 8)
    categories = _count_by_category(questions)
    top_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:3]

    return (
        f"Generated {total} questions ({high_priority} high priority). "
        f"Top areas: {', '.join(f'{cat}({count})' for cat, count in top_cats)}. "
        f"Submit all questions before the Q&A deadline to maximize information."
    )


def _get_submission_tips() -> list[str]:
    return [
        "Submit questions early – first submission window often gets more detailed answers",
        "Group related questions under the same RFP section reference",
        "Ask one clear question per submission to get a clear answer",
        "Review all Q&A answers for cumulative impact on bid strategy",
        "Monitor for amendments that may result from aggregated questions",
    ]
