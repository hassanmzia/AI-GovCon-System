"""Quality Assurance AI Agent using LangGraph.

Reviews a complete proposal for consistency, clarity, win-theme integration,
and compliance with formatting and page-limit requirements.

Events: QA_COMPLETE, QA_ISSUES_FOUND.
"""
import logging
import os
from typing import Annotated, Any
import operator

import httpx
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from typing_extensions import TypedDict

from src.agents.base import BaseAgent

logger = logging.getLogger("ai_orchestrator.agents.qa")

DJANGO_API_URL = os.getenv("DJANGO_API_URL", "http://django-api:8001")
DJANGO_SERVICE_TOKEN = os.getenv("DJANGO_SERVICE_TOKEN", "")


# ── State ─────────────────────────────────────────────────────────────────────

class QAState(TypedDict):
    deal_id: str
    deal: dict
    drafted_sections: dict          # {title: text}
    revised_sections: dict          # Revisions from proposal writer
    win_themes: list[str]
    evaluation_criteria: list[dict]
    page_limits: dict               # From RFP
    consistency_issues: list[dict]  # {section, issue, severity}
    clarity_score: float            # 0.0–1.0
    win_theme_coverage: dict        # {theme: sections_where_found}
    formatting_issues: list[str]
    qa_summary: str                 # Overall QA pass/fail + action items
    messages: Annotated[list, operator.add]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _auth_headers() -> dict[str, str]:
    t = DJANGO_SERVICE_TOKEN
    return {"Authorization": f"Bearer {t}"} if t else {}


async def _get(path: str, default: Any = None) -> Any:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{DJANGO_API_URL}{path}", headers=_auth_headers())
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.warning("API GET %s failed: %s", path, exc)
        return default


async def _llm(system: str, human: str, max_tokens: int = 2500) -> str:
    try:
        llm = ChatAnthropic(
            model="claude-sonnet-4-6",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            max_tokens=max_tokens,
        )
        resp = await llm.ainvoke([SystemMessage(content=system), HumanMessage(content=human)])
        return resp.content
    except Exception as exc:
        logger.error("LLM failed: %s", exc)
        return ""


# ── Graph nodes ───────────────────────────────────────────────────────────────

async def load_qa_context(state: QAState) -> dict:
    logger.info("QAAgent: loading context for deal %s", state["deal_id"])
    deal = await _get(f"/api/deals/{state['deal_id']}/", default={})
    rfp_reqs = await _get(f"/api/rfp/requirements/?deal={state['deal_id']}&limit=20", default={})
    criteria = rfp_reqs.get("results", []) if isinstance(rfp_reqs, dict) else []
    return {
        "deal": deal,
        "evaluation_criteria": criteria,
        "messages": [HumanMessage(content=f"QA review for: {deal.get('title', state['deal_id'])}")],
    }


async def check_consistency(state: QAState) -> dict:
    """Find inconsistencies across proposal sections (numbers, claims, acronyms)."""
    logger.info("QAAgent: checking consistency for deal %s", state["deal_id"])

    all_sections = {**(state.get("drafted_sections") or {}), **(state.get("revised_sections") or {})}
    if not all_sections:
        return {
            "consistency_issues": [],
            "messages": [HumanMessage(content="No sections to review.")],
        }

    sections_text = "\n\n---\n\n".join(
        f"## {title}\n{text[:500]}" for title, text in all_sections.items()
    )

    content = await _llm(
        system=(
            "You are a meticulous proposal editor. Review all proposal sections for internal "
            "inconsistencies: conflicting numbers/statistics, inconsistent acronym usage, "
            "contradictory claims, mismatched personnel counts or timelines, or "
            "sections that contradict each other."
        ),
        human=(
            f"Proposal sections for review:\n{sections_text}\n\n"
            "Identify all consistency issues. For each issue output:\n"
            "SECTION: [section name] | ISSUE: [description] | SEVERITY: HIGH/MEDIUM/LOW\n\n"
            "If no issues found, output: NO_ISSUES_FOUND"
        ),
        max_tokens=2000,
    )

    issues = []
    if "NO_ISSUES_FOUND" not in content:
        for line in content.split("\n"):
            if "SECTION:" in line and "ISSUE:" in line:
                parts = line.split("|")
                if len(parts) >= 2:
                    section = parts[0].replace("SECTION:", "").strip()
                    issue_text = parts[1].replace("ISSUE:", "").strip()
                    severity = parts[2].replace("SEVERITY:", "").strip() if len(parts) > 2 else "MEDIUM"
                    issues.append({"section": section, "issue": issue_text, "severity": severity})

    return {
        "consistency_issues": issues,
        "messages": [HumanMessage(content=f"Consistency check: {len(issues)} issue(s) found.")],
    }


async def score_clarity_and_win_themes(state: QAState) -> dict:
    """Score proposal clarity and measure win-theme coverage across sections."""
    logger.info("QAAgent: scoring clarity and win themes for deal %s", state["deal_id"])

    all_sections = {**(state.get("drafted_sections") or {}), **(state.get("revised_sections") or {})}
    win_themes = state.get("win_themes") or []

    if not all_sections:
        return {
            "clarity_score": 0.0,
            "win_theme_coverage": {},
            "messages": [HumanMessage(content="No sections to score.")],
        }

    sections_text = "\n\n---\n\n".join(
        f"## {title}\n{text[:600]}" for title, text in all_sections.items()
    )

    content = await _llm(
        system=(
            "You are a proposal scoring evaluator. Score proposal sections for clarity, "
            "conciseness, and evaluator-friendliness. Also track win-theme integration."
        ),
        human=(
            f"Win Themes: {win_themes[:5]}\n\n"
            f"Proposal Sections:\n{sections_text}\n\n"
            "Provide:\n"
            "1. CLARITY_SCORE: [0.0-1.0] with brief justification\n"
            "2. For each win theme, list which sections mention it:\n"
            "   THEME: [theme text] | FOUND_IN: [comma-separated section names]\n"
            "3. Top 3 clarity improvement recommendations"
        ),
        max_tokens=1500,
    )

    # Parse clarity score
    clarity_score = 0.75  # Default
    for line in content.split("\n"):
        if "CLARITY_SCORE:" in line:
            try:
                score_str = line.split("CLARITY_SCORE:")[1].strip().split()[0]
                clarity_score = float(score_str)
            except (ValueError, IndexError):
                pass

    # Parse win theme coverage
    win_theme_coverage: dict = {}
    for line in content.split("\n"):
        if "THEME:" in line and "FOUND_IN:" in line:
            parts = line.split("|")
            if len(parts) >= 2:
                theme = parts[0].replace("THEME:", "").strip()
                found = [s.strip() for s in parts[1].replace("FOUND_IN:", "").split(",")]
                win_theme_coverage[theme] = found

    return {
        "clarity_score": round(clarity_score, 3),
        "win_theme_coverage": win_theme_coverage,
        "messages": [HumanMessage(content=f"Clarity score: {clarity_score:.1%}, {len(win_theme_coverage)} themes tracked.")],
    }


async def check_formatting(state: QAState) -> dict:
    """Verify formatting compliance against RFP page limits and format requirements."""
    logger.info("QAAgent: checking formatting for deal %s", state["deal_id"])

    all_sections = {**(state.get("drafted_sections") or {}), **(state.get("revised_sections") or {})}
    page_limits = state.get("page_limits") or {}

    issues = []

    # Rough word/page count estimates (250 words ≈ 1 page)
    for section_title, text in all_sections.items():
        word_count = len(text.split())
        page_estimate = word_count / 250

        # Check against page limits if specified
        for limit_key, limit_val in page_limits.items():
            if any(keyword in section_title.lower() for keyword in limit_key.lower().split()):
                try:
                    limit_pages = float(str(limit_val).split()[0])
                    if page_estimate > limit_pages * 1.1:  # 10% tolerance
                        issues.append(
                            f"'{section_title}': estimated {page_estimate:.1f} pages "
                            f"exceeds limit of {limit_pages} pages"
                        )
                except (ValueError, TypeError):
                    pass

    # Check for common formatting problems
    for section_title, text in all_sections.items():
        if len(text) > 100:
            if text.count("\n\n") < 2 and len(text) > 500:
                issues.append(f"'{section_title}': lacks paragraph breaks — may be hard to read")
            if not any(c in text for c in [".", "!", "?"]):
                issues.append(f"'{section_title}': no sentence-ending punctuation detected")

    return {
        "formatting_issues": issues,
        "messages": [HumanMessage(content=f"Formatting check: {len(issues)} issue(s).")],
    }


async def generate_qa_summary(state: QAState) -> dict:
    """Generate final QA report with pass/fail determination and action items."""
    logger.info("QAAgent: generating QA summary for deal %s", state["deal_id"])

    consistency_issues = state.get("consistency_issues") or []
    formatting_issues = state.get("formatting_issues") or []
    clarity_score = state.get("clarity_score", 0.0)
    win_theme_coverage = state.get("win_theme_coverage") or {}

    high_severity = [i for i in consistency_issues if i.get("severity") == "HIGH"]
    qa_pass = len(high_severity) == 0 and clarity_score >= 0.6

    content = await _llm(
        system="You are a proposal QA manager creating a final review report.",
        human=(
            f"QA Results for: {state['deal'].get('title', state['deal_id'])}\n\n"
            f"Clarity Score: {clarity_score:.1%}\n"
            f"Consistency Issues: {len(consistency_issues)} ({len(high_severity)} HIGH severity)\n"
            f"Formatting Issues: {len(formatting_issues)}\n"
            f"Win Theme Coverage: {len(win_theme_coverage)} themes tracked\n\n"
            f"High Severity Issues:\n"
            + "\n".join(f"- {i['section']}: {i['issue']}" for i in high_severity[:5])
            + "\n\nFormatting Issues:\n"
            + "\n".join(f"- {i}" for i in formatting_issues[:5])
            + "\n\n"
            "Provide:\n"
            "1. QA VERDICT: PASS or FAIL with brief justification\n"
            "2. Top 5 action items before submission (prioritized)\n"
            "3. Risk assessment for submission as-is\n"
            "4. Overall proposal quality assessment (1-10)"
        ),
        max_tokens=1500,
    )

    return {
        "qa_summary": f"QA {'PASS' if qa_pass else 'FAIL'}\n\n{content}",
        "messages": [HumanMessage(content=f"QA complete: {'PASS' if qa_pass else 'FAIL'}, score={clarity_score:.1%}.")],
    }


# ── Graph ─────────────────────────────────────────────────────────────────────

def build_qa_graph() -> StateGraph:
    wf = StateGraph(QAState)
    wf.add_node("load_qa_context", load_qa_context)
    wf.add_node("check_consistency", check_consistency)
    wf.add_node("score_clarity_and_win_themes", score_clarity_and_win_themes)
    wf.add_node("check_formatting", check_formatting)
    wf.add_node("generate_qa_summary", generate_qa_summary)
    wf.set_entry_point("load_qa_context")
    wf.add_edge("load_qa_context", "check_consistency")
    wf.add_edge("check_consistency", "score_clarity_and_win_themes")
    wf.add_edge("score_clarity_and_win_themes", "check_formatting")
    wf.add_edge("check_formatting", "generate_qa_summary")
    wf.add_edge("generate_qa_summary", END)
    return wf.compile()


qa_graph = build_qa_graph()


# ── Agent ─────────────────────────────────────────────────────────────────────

class QAAgent(BaseAgent):
    """AI agent that performs quality assurance review of proposal sections."""

    agent_name = "qa_agent"

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        deal_id = input_data.get("deal_id", "")
        if not deal_id:
            return {"error": "deal_id is required"}

        initial: QAState = {
            "deal_id": deal_id,
            "deal": {},
            "drafted_sections": input_data.get("drafted_sections", {}),
            "revised_sections": input_data.get("revised_sections", {}),
            "win_themes": input_data.get("win_themes", []),
            "evaluation_criteria": [],
            "page_limits": input_data.get("page_limits", {}),
            "consistency_issues": [],
            "clarity_score": 0.0,
            "win_theme_coverage": {},
            "formatting_issues": [],
            "qa_summary": "",
            "messages": [],
        }
        try:
            await self.emit_event(
                "thinking",
                {"message": f"Running QA review for deal {deal_id}"},
                execution_id=deal_id,
            )
            fs = await qa_graph.ainvoke(initial)
            await self.emit_event(
                "output",
                {
                    "clarity_score": fs["clarity_score"],
                    "issues_count": len(fs["consistency_issues"]) + len(fs["formatting_issues"]),
                },
                execution_id=deal_id,
            )
            return {
                "deal_id": fs["deal_id"],
                "consistency_issues": fs["consistency_issues"],
                "clarity_score": fs["clarity_score"],
                "win_theme_coverage": fs["win_theme_coverage"],
                "formatting_issues": fs["formatting_issues"],
                "qa_summary": fs["qa_summary"],
            }
        except Exception as exc:
            logger.exception("QAAgent.run failed for deal %s", deal_id)
            await self.emit_event("error", {"error": str(exc)}, execution_id=deal_id)
            return {"error": str(exc), "deal_id": deal_id}
