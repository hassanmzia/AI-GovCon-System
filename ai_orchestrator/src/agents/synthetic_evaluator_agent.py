"""
Synthetic Evaluator Agent — simulates a US Government source selection evaluator.

Scores a proposal draft against the evaluation criteria exactly as a government
evaluator would, providing section-by-section scoring, weaknesses, and fix suggestions.
This dramatically improves win probability before submission.
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

logger = logging.getLogger("ai_orchestrator.agents.synthetic_evaluator")

DJANGO_API_URL = os.getenv("DJANGO_API_URL", "http://django-api:8001")
DJANGO_SERVICE_TOKEN = os.getenv("DJANGO_SERVICE_TOKEN", "")


# ── State ─────────────────────────────────────────────────────────────────────


class SyntheticEvaluatorState(TypedDict):
    deal_id: str
    proposal_draft: dict                # {section_title: content_text}
    rfp_evaluation_criteria: list[dict] # [{factor, subfactor, weight, description}]
    section_scores: list[dict]          # Per-section rating results
    overall_score: float                # Normalised 0-100 win-probability-weighted score
    weaknesses: list[dict]              # [{section, weakness, severity, fix_hint}]
    strengths: list[str]                # Notable strengths for proposal marketing
    recommendations: list[str]          # Actionable improvements
    evaluator_persona: str              # Description of the simulated evaluator
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
        logger.warning("SyntheticEvaluator API GET %s failed: %s", path, exc)
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
            agent_name="synthetic_evaluator_agent",
        )
        resp = await llm.ainvoke(
            [SystemMessage(content=system), HumanMessage(content=human)]
        )
        return resp.content if isinstance(resp.content, str) else str(resp.content)
    except Exception as exc:
        logger.error("SyntheticEvaluator LLM call failed: %s", exc)
        return ""


# ── Graph nodes ───────────────────────────────────────────────────────────────


async def load_proposal_and_criteria(state: SyntheticEvaluatorState) -> dict:
    """
    Fetch the proposal draft and RFP evaluation criteria from the Django backend.

    Loads:
      - Deal record for context
      - Proposal sections (latest draft)
      - RFP requirements/evaluation criteria (Section M)
    """
    deal_id = state["deal_id"]
    logger.info("SyntheticEvaluator: loading proposal + criteria for deal %s", deal_id)

    deal = await _get(f"/api/deals/{deal_id}/", default={})
    proposal_id = deal.get("latest_proposal_id") or deal.get("proposal_id") or ""

    # Fetch proposal sections
    proposal_draft: dict = {}
    if proposal_id:
        sections_data = await _get(
            f"/api/proposals/{proposal_id}/sections/", default={}
        )
        if isinstance(sections_data, dict):
            results = sections_data.get("results", [])
        elif isinstance(sections_data, list):
            results = sections_data
        else:
            results = []
        for section in results:
            title = section.get("section_type") or section.get("title") or "Unnamed Section"
            content = section.get("content") or section.get("text") or ""
            proposal_draft[title] = content

    # Merge with any sections already in state
    if state.get("proposal_draft"):
        proposal_draft = {**state["proposal_draft"], **proposal_draft}

    # Fetch evaluation criteria (Section M / evaluation factors)
    criteria_data = await _get(
        f"/api/rfp/requirements/?deal={deal_id}&type=evaluation_criterion&limit=50",
        default={},
    )
    rfp_evaluation_criteria: list[dict] = []
    if isinstance(criteria_data, dict):
        rfp_evaluation_criteria = criteria_data.get("results", [])
    elif isinstance(criteria_data, list):
        rfp_evaluation_criteria = criteria_data

    # Merge with state-provided criteria
    if state.get("rfp_evaluation_criteria"):
        rfp_evaluation_criteria = state["rfp_evaluation_criteria"] or rfp_evaluation_criteria

    # Build a persona description for the evaluator
    agency = deal.get("agency_name") or deal.get("agency") or "US Federal Agency"
    evaluator_persona = (
        f"Senior Source Selection Authority (SSA) representative at {agency}, "
        "with 15+ years of federal acquisition experience. Applies FAR Part 15 "
        "source selection procedures strictly."
    )

    return {
        "proposal_draft": proposal_draft,
        "rfp_evaluation_criteria": rfp_evaluation_criteria,
        "evaluator_persona": evaluator_persona,
        "messages": [
            HumanMessage(
                content=(
                    f"Loaded proposal ({len(proposal_draft)} sections) and "
                    f"{len(rfp_evaluation_criteria)} evaluation criteria for deal {deal_id}."
                )
            )
        ],
    }


async def simulate_government_evaluation(state: SyntheticEvaluatorState) -> dict:
    """
    Simulate a US Government source selection board evaluation.

    Uses FAR Part 15 evaluation methodology with Outstanding / Good / Acceptable /
    Marginal / Unacceptable ratings. Produces section-by-section scores, identified
    weaknesses/deficiencies, and notable strengths.
    """
    deal_id = state["deal_id"]
    logger.info(
        "SyntheticEvaluator: simulating government evaluation for deal %s", deal_id
    )

    proposal_draft = state.get("proposal_draft") or {}
    criteria = state.get("rfp_evaluation_criteria") or []
    persona = state.get("evaluator_persona") or "US Government Source Selection Evaluator"

    # Build the evaluation input text
    sections_text = "\n\n".join(
        f"=== SECTION: {title} ===\n{content[:2000]}"
        for title, content in list(proposal_draft.items())[:10]
    )
    criteria_text = "\n".join(
        f"- {c.get('requirement_text') or c.get('factor') or str(c)[:200]}"
        for c in criteria[:15]
    )

    system_prompt = (
        "You are a US Government source selection evaluation board member. "
        "Score this proposal against the stated evaluation criteria using the "
        "FAR Part 15 evaluation methodology. Use Outstanding / Good / Acceptable / "
        "Marginal / Unacceptable ratings.\n\n"
        f"Your evaluator persona: {persona}\n\n"
        "For each proposal section, provide:\n"
        "1. FAR rating (Outstanding/Good/Acceptable/Marginal/Unacceptable)\n"
        "2. Specific strengths (features that exceed requirements)\n"
        "3. Specific weaknesses (significant flaws that increase risk)\n"
        "4. Deficiencies (material failures to meet requirements)\n"
        "5. Risks to the Government\n\n"
        "Output a JSON array named 'section_scores' with objects having keys: "
        "section, rating, rating_numeric (5=Outstanding,4=Good,3=Acceptable,"
        "2=Marginal,1=Unacceptable), strengths (list), weaknesses (list), "
        "deficiencies (list), risk_assessment (str).\n\n"
        "Also output a 'strengths' key (top 5 overall strengths as list of strings) "
        "and a 'weaknesses' key (all weaknesses as list of {section,weakness,severity,fix_hint})."
    )

    human_prompt = (
        f"Evaluation Criteria (Section M):\n{criteria_text or 'Not provided — evaluate on general merit.'}\n\n"
        f"Proposal Sections:\n{sections_text or 'No proposal sections available.'}\n\n"
        "Produce your evaluation now in JSON format with keys: "
        "section_scores, strengths, weaknesses."
    )

    raw = await _llm(system_prompt, human_prompt, max_tokens=4096, execution_id=state.get("deal_id"))

    # Parse JSON out of the LLM response
    section_scores: list[dict] = []
    strengths: list[str] = []
    weaknesses: list[dict] = []

    try:
        # Strip markdown code blocks if present
        clean = raw.strip()
        if clean.startswith("```"):
            clean = "\n".join(clean.split("\n")[1:])
        if clean.endswith("```"):
            clean = clean[: clean.rfind("```")]
        parsed = json.loads(clean)
        section_scores = parsed.get("section_scores", [])
        strengths = parsed.get("strengths", [])
        weaknesses = parsed.get("weaknesses", [])
    except (json.JSONDecodeError, ValueError) as exc:
        logger.warning(
            "SyntheticEvaluator: failed to parse evaluation JSON (%s) — storing raw", exc
        )
        section_scores = [{"raw_evaluation": raw[:3000]}]
        strengths = []
        weaknesses = []

    return {
        "section_scores": section_scores,
        "strengths": strengths if isinstance(strengths, list) else [],
        "weaknesses": weaknesses if isinstance(weaknesses, list) else [],
        "messages": [
            HumanMessage(
                content=(
                    f"Government evaluation complete: {len(section_scores)} sections scored, "
                    f"{len(weaknesses)} weakness(es) identified."
                )
            )
        ],
    }


async def generate_improvement_recommendations(
    state: SyntheticEvaluatorState,
) -> dict:
    """
    Generate specific, actionable improvements for every identified weakness.

    For each weakness, provides a targeted fix that would upgrade the rating
    from Marginal → Acceptable → Good → Outstanding.
    """
    deal_id = state["deal_id"]
    logger.info(
        "SyntheticEvaluator: generating improvement recommendations for deal %s", deal_id
    )

    weaknesses = state.get("weaknesses") or []
    section_scores = state.get("section_scores") or []

    if not weaknesses and not section_scores:
        return {
            "recommendations": [
                "No weaknesses identified — proposal appears strong across all evaluated sections."
            ],
            "messages": [HumanMessage(content="No weaknesses to address.")],
        }

    weakness_text = "\n".join(
        f"- Section: {w.get('section','?')} | Weakness: {w.get('weakness','?')} "
        f"| Severity: {w.get('severity','?')}"
        for w in weaknesses[:20]
    )

    low_scores = [
        s for s in section_scores
        if isinstance(s.get("rating_numeric"), (int, float)) and s["rating_numeric"] < 4
    ]
    low_score_text = "\n".join(
        f"- {s.get('section','?')}: {s.get('rating','?')} — {s.get('risk_assessment','')[:200]}"
        for s in low_scores[:10]
    )

    system_prompt = (
        "You are a senior proposal manager and government contracting expert. "
        "Based on the government evaluator's feedback, provide specific, actionable "
        "improvements for each weakness. Your goal is to upgrade every rating:\n"
        "  Marginal → Acceptable → Good → Outstanding\n\n"
        "For each improvement:\n"
        "1. Be extremely specific (what exact text/data/evidence to add)\n"
        "2. Reference which proposal section and paragraph to modify\n"
        "3. Suggest concrete language or metrics to include\n"
        "4. Explain why this change will satisfy the evaluator\n\n"
        "Output a JSON array 'recommendations' of strings, each a complete improvement instruction."
    )

    human_prompt = (
        f"Identified Weaknesses:\n{weakness_text or 'None listed.'}\n\n"
        f"Low-Scoring Sections:\n{low_score_text or 'None listed.'}\n\n"
        "Produce the recommendations JSON now."
    )

    raw = await _llm(system_prompt, human_prompt, max_tokens=3000, execution_id=state.get("deal_id"))

    recommendations: list[str] = []
    try:
        clean = raw.strip()
        if clean.startswith("```"):
            clean = "\n".join(clean.split("\n")[1:])
        if clean.endswith("```"):
            clean = clean[: clean.rfind("```")]
        parsed = json.loads(clean)
        if isinstance(parsed, list):
            recommendations = parsed
        elif isinstance(parsed, dict):
            recommendations = parsed.get("recommendations", [])
    except (json.JSONDecodeError, ValueError):
        # Fall back to splitting raw text into lines as individual recommendations
        recommendations = [
            line.strip().lstrip("-•* ")
            for line in raw.split("\n")
            if line.strip() and len(line.strip()) > 20
        ][:25]

    return {
        "recommendations": recommendations,
        "messages": [
            HumanMessage(
                content=f"Generated {len(recommendations)} improvement recommendation(s)."
            )
        ],
    }


async def compute_win_probability(state: SyntheticEvaluatorState) -> dict:
    """
    Estimate a realistic win probability from the section-level evaluation scores.

    Uses a weighted-average of rating_numeric values mapped to probability ranges:
      Outstanding (5) → ~85-95%
      Good        (4) → ~65-80%
      Acceptable  (3) → ~40-60%
      Marginal    (2) → ~15-35%
      Unacceptable(1) → ~0-15%

    The final estimate is stored as overall_score (0-100).
    """
    deal_id = state["deal_id"]
    logger.info("SyntheticEvaluator: computing win probability for deal %s", deal_id)

    section_scores = state.get("section_scores") or []

    # Rating → probability midpoint mapping
    rating_to_prob = {5: 90.0, 4: 72.5, 3: 50.0, 2: 25.0, 1: 7.5}

    numeric_scores = [
        s.get("rating_numeric")
        for s in section_scores
        if isinstance(s.get("rating_numeric"), (int, float))
    ]

    if not numeric_scores:
        overall_score = 50.0  # Default to 50% when no scores available
    else:
        avg_numeric = sum(numeric_scores) / len(numeric_scores)
        # Interpolate between rating probability midpoints
        lower = int(avg_numeric)
        upper = lower + 1
        frac = avg_numeric - lower
        prob_lower = rating_to_prob.get(max(lower, 1), 7.5)
        prob_upper = rating_to_prob.get(min(upper, 5), 90.0)
        overall_score = round(prob_lower + frac * (prob_upper - prob_lower), 1)

    # Penalise for each Unacceptable or Marginal section
    unacceptable_count = sum(
        1 for s in section_scores
        if str(s.get("rating", "")).lower() in ("unacceptable", "marginal")
    )
    overall_score = max(0.0, overall_score - unacceptable_count * 5.0)

    logger.info(
        "SyntheticEvaluator: win probability estimate = %.1f%% for deal %s",
        overall_score, deal_id,
    )

    return {
        "overall_score": overall_score,
        "messages": [
            HumanMessage(
                content=(
                    f"Win probability estimate: {overall_score:.1f}% "
                    f"(based on {len(numeric_scores)} scored section(s))."
                )
            )
        ],
    }


# ── Graph ─────────────────────────────────────────────────────────────────────


def build_synthetic_evaluator_graph():
    wf = StateGraph(SyntheticEvaluatorState)
    wf.add_node("load_proposal_and_criteria", load_proposal_and_criteria)
    wf.add_node("simulate_government_evaluation", simulate_government_evaluation)
    wf.add_node("generate_improvement_recommendations", generate_improvement_recommendations)
    wf.add_node("compute_win_probability", compute_win_probability)

    wf.set_entry_point("load_proposal_and_criteria")
    wf.add_edge("load_proposal_and_criteria", "simulate_government_evaluation")
    wf.add_edge("simulate_government_evaluation", "generate_improvement_recommendations")
    wf.add_edge("generate_improvement_recommendations", "compute_win_probability")
    wf.add_edge("compute_win_probability", END)
    return wf.compile()


synthetic_evaluator_graph = build_synthetic_evaluator_graph()


# ── Agent ─────────────────────────────────────────────────────────────────────


class SyntheticEvaluatorAgent(BaseAgent):
    """
    AI agent that simulates a US Government source selection evaluator.

    Scores a proposal draft section-by-section using FAR Part 15 methodology,
    identifies weaknesses/deficiencies, generates improvement recommendations,
    and estimates a win probability.
    """

    agent_name = "synthetic_evaluator_agent"

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        deal_id = input_data.get("deal_id", "")
        if not deal_id:
            return {"error": "deal_id is required"}

        initial: SyntheticEvaluatorState = {
            "deal_id": deal_id,
            "proposal_draft": input_data.get("proposal_draft", {}),
            "rfp_evaluation_criteria": input_data.get("rfp_evaluation_criteria", []),
            "section_scores": [],
            "overall_score": 0.0,
            "weaknesses": [],
            "strengths": [],
            "recommendations": [],
            "evaluator_persona": "",
            "messages": [],
        }

        try:
            await self.emit_event(
                "thinking",
                {"message": f"Simulating government evaluation for deal {deal_id}"},
                execution_id=deal_id,
            )
            fs = await synthetic_evaluator_graph.ainvoke(initial)
            await self.emit_event(
                "output",
                {
                    "overall_score": fs["overall_score"],
                    "sections_scored": len(fs["section_scores"]),
                    "weaknesses_count": len(fs["weaknesses"]),
                    "recommendations_count": len(fs["recommendations"]),
                },
                execution_id=deal_id,
            )
            return {
                "deal_id": fs["deal_id"],
                "overall_score": fs["overall_score"],
                "section_scores": fs["section_scores"],
                "weaknesses": fs["weaknesses"],
                "strengths": fs["strengths"],
                "recommendations": fs["recommendations"],
                "evaluator_persona": fs["evaluator_persona"],
            }
        except Exception as exc:
            logger.exception(
                "SyntheticEvaluatorAgent.run failed for deal %s", deal_id
            )
            await self.emit_event(
                "error", {"error": str(exc)}, execution_id=deal_id
            )
            return {"error": str(exc), "deal_id": deal_id}
