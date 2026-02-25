"""Deal Pipeline AI Agent using LangGraph.

Manages deal stage transitions, task assignments, and approval gates.
Acts as the orchestrating agent that coordinates the other specialist agents
at each deal stage.

Events: DEAL_CREATED, DEAL_STAGE_CHANGED, DEAL_TASK_ASSIGNED,
        DEAL_APPROVAL_REQUIRED, DEAL_APPROVAL_GRANTED, DEAL_WON, DEAL_LOST.
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

logger = logging.getLogger("ai_orchestrator.agents.deal_pipeline")

DJANGO_API_URL = os.getenv("DJANGO_API_URL", "http://django-api:8001")
DJANGO_SERVICE_TOKEN = os.getenv("DJANGO_SERVICE_TOKEN", "")

# Stage progression order
_STAGE_ORDER = [
    "identified",
    "qualification",
    "capture",
    "rfp_analysis",
    "proposal",
    "review",
    "submitted",
    "awarded",
    "lost",
]

# Stage-specific tasks to create when entering a stage
_STAGE_TASKS: dict[str, list[str]] = {
    "qualification":  [
        "Run Opportunity Intelligence analysis",
        "Conduct bid/no-bid decision meeting",
        "Assess resource availability",
    ],
    "capture":        [
        "Run Strategy Agent analysis",
        "Identify teaming partners",
        "Schedule customer meeting",
        "Research incumbent and competitors",
    ],
    "rfp_analysis":   [
        "Upload and parse RFP document",
        "Build compliance matrix",
        "Identify all requirements",
        "Assign proposal sections to authors",
    ],
    "proposal":       [
        "Run Solution Architect Agent",
        "Match relevant past performance",
        "Run Pricing Agent",
        "Draft executive summary",
        "Complete Technical Volume I",
        "Complete Management Volume II",
        "Complete Past Performance Volume III",
        "Build price/cost volume",
    ],
    "review":         [
        "Conduct pink team review",
        "Conduct red team review",
        "Address all review comments",
        "Final compliance check",
        "Pricing approval gate",
    ],
    "submitted":      [
        "Confirm submission receipt",
        "Prepare for oral presentations (if required)",
        "Monitor for RFP amendments",
    ],
}


# ── State ─────────────────────────────────────────────────────────────────────

class DealPipelineState(TypedDict):
    deal_id: str
    deal: dict
    current_stage: str
    target_stage: str              # Stage to transition to
    stage_assessment: str          # AI assessment of readiness
    readiness_score: float         # 0.0–1.0 stage completion
    blockers: list[str]            # Issues blocking stage progression
    recommended_tasks: list[str]   # Tasks to create for next stage
    approval_required: bool
    approval_context: str
    next_agent_recommendations: list[str]  # Which agents to run next
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


async def _llm(system: str, human: str) -> str:
    try:
        llm = ChatAnthropic(
            model="claude-sonnet-4-6",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            max_tokens=2048,
        )
        resp = await llm.ainvoke([SystemMessage(content=system), HumanMessage(content=human)])
        return resp.content
    except Exception as exc:
        logger.error("LLM failed: %s", exc)
        return ""


# ── Graph nodes ───────────────────────────────────────────────────────────────

async def load_deal(state: DealPipelineState) -> dict:
    logger.info("DealPipeline: loading deal %s", state["deal_id"])
    deal = await _get(f"/api/deals/{state['deal_id']}/", default={})
    current_stage = deal.get("stage") or deal.get("status") or "identified"
    return {
        "deal": deal,
        "current_stage": current_stage,
        "messages": [HumanMessage(content=f"Pipeline analysis for: {deal.get('title', state['deal_id'])}")],
    }


async def assess_stage_readiness(state: DealPipelineState) -> dict:
    """Assess whether the deal is ready to advance to the next stage."""
    logger.info(
        "DealPipeline: assessing readiness for deal %s (stage=%s)",
        state["deal_id"],
        state["current_stage"],
    )
    deal = state["deal"]
    current = state["current_stage"]
    target = state.get("target_stage") or _next_stage(current)

    content = await _llm(
        system=(
            "You are a capture manager and business development director assessing "
            "whether a deal is ready to advance to the next stage of the pipeline. "
            "Be rigorous — incomplete stages lead to failed proposals."
        ),
        human=(
            f"Deal: {deal}\n\n"
            f"Current Stage: {current}\n"
            f"Target Stage: {target}\n\n"
            f"Stage entry criteria for '{target}':\n"
            + _stage_entry_criteria(target)
            + "\n\nAssess:\n"
            "1. Readiness score (0.0–1.0) — state as 'READINESS_SCORE: X.XX'\n"
            "2. Completed criteria\n"
            "3. Blockers preventing stage advancement\n"
            "4. Recommended actions to unblock\n"
            "5. Whether management approval is required before advancing\n"
        ),
    )

    score = 0.5
    for line in content.split("\n"):
        if line.strip().startswith("READINESS_SCORE:"):
            try:
                score = float(line.split(":", 1)[1].strip())
                score = max(0.0, min(1.0, score))
            except ValueError:
                pass
            break

    blockers = [
        ln.strip("- •*").strip()
        for ln in content.split("\n")
        if any(kw in ln.lower() for kw in ("block", "missing", "required", "not complete", "incomplete"))
        and ln.strip()
    ][:8]

    approval_required = "approval" in content.lower() and score < 0.9

    return {
        "stage_assessment": content,
        "readiness_score": score,
        "blockers": blockers,
        "approval_required": approval_required,
        "approval_context": content[:400] if approval_required else "",
        "messages": [HumanMessage(content=f"Readiness: {score:.0%} for stage '{target}'.")],
    }


async def generate_pipeline_actions(state: DealPipelineState) -> dict:
    """Generate recommended tasks and next agent runs for the target stage."""
    logger.info("DealPipeline: generating actions for deal %s", state["deal_id"])
    target = state.get("target_stage") or _next_stage(state["current_stage"])

    # Standard tasks for the target stage
    stage_tasks = _STAGE_TASKS.get(target, [])

    # AI-driven additional recommendations
    content = await _llm(
        system=(
            "You are a capture manager. Recommend specific AI agents and tasks "
            "to run at the next deal stage."
        ),
        human=(
            f"Deal: {state['deal'].get('title', '')}\n"
            f"Stage: {target}\n"
            f"Readiness Score: {state['readiness_score']:.0%}\n"
            f"Blockers: {state['blockers']}\n\n"
            "Recommend:\n"
            "1. Which AI agents to run (Strategy, Research, RFP Analyst, SA, Pricing, "
            "Teaming, Past Performance, Proposal Writer, Security Compliance)\n"
            "2. Priority order (list numbered 1-5)\n"
            "3. Any deal-specific tasks beyond the standard checklist\n"
        ),
    )

    # Parse agent recommendations
    agent_names = [
        "Strategy", "Research", "RFP Analyst", "Solution Architect",
        "Pricing", "Teaming", "Past Performance", "Proposal Writer",
        "Security Compliance", "Opportunity Intelligence",
    ]
    agent_recs = [a for a in agent_names if a.lower() in content.lower()]

    return {
        "recommended_tasks": stage_tasks,
        "next_agent_recommendations": agent_recs,
        "messages": [HumanMessage(content=f"Generated {len(stage_tasks)} task(s) for stage '{target}'.")],
    }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _next_stage(current: str) -> str:
    try:
        idx = _STAGE_ORDER.index(current)
        return _STAGE_ORDER[idx + 1] if idx + 1 < len(_STAGE_ORDER) else current
    except ValueError:
        return "qualification"


def _stage_entry_criteria(stage: str) -> str:
    criteria: dict[str, str] = {
        "qualification":  "- Opportunity identified and basic details captured\n- Initial business case documented",
        "capture":        "- Bid/no-bid decision made (BID)\n- Capture manager assigned\n- Opportunity scored ≥ 0.6",
        "rfp_analysis":   "- RFP/solicitation released\n- Capture plan complete\n- Proposal team assembled",
        "proposal":       "- RFP fully parsed and compliance matrix complete\n- Win themes finalized\n- Solution architecture drafted",
        "review":         "- All proposal volumes drafted\n- Pricing model approved\n- Compliance self-check complete",
        "submitted":      "- All review comments addressed\n- Final pricing approval obtained\n- Proposal submitted to agency",
        "awarded":        "- Award notification received\n- Contract negotiations complete",
        "lost":           "- Loss notification received\n- Debrief requested",
    }
    return criteria.get(stage, "- Stage entry criteria not defined")


# ── Graph ─────────────────────────────────────────────────────────────────────

def build_deal_pipeline_graph() -> StateGraph:
    wf = StateGraph(DealPipelineState)
    wf.add_node("load_deal", load_deal)
    wf.add_node("assess_stage_readiness", assess_stage_readiness)
    wf.add_node("generate_pipeline_actions", generate_pipeline_actions)
    wf.set_entry_point("load_deal")
    wf.add_edge("load_deal", "assess_stage_readiness")
    wf.add_edge("assess_stage_readiness", "generate_pipeline_actions")
    wf.add_edge("generate_pipeline_actions", END)
    return wf.compile()


deal_pipeline_graph = build_deal_pipeline_graph()


# ── Agent ─────────────────────────────────────────────────────────────────────

class DealPipelineAgent(BaseAgent):
    """AI agent that manages deal stage progression, tasks, and approvals."""

    agent_name = "deal_pipeline_agent"

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        deal_id = input_data.get("deal_id", "")
        if not deal_id:
            return {"error": "deal_id is required"}

        initial: DealPipelineState = {
            "deal_id": deal_id,
            "deal": {},
            "current_stage": input_data.get("current_stage", ""),
            "target_stage": input_data.get("target_stage", ""),
            "stage_assessment": "",
            "readiness_score": 0.0,
            "blockers": [],
            "recommended_tasks": [],
            "approval_required": False,
            "approval_context": "",
            "next_agent_recommendations": [],
            "messages": [],
        }
        try:
            await self.emit_event(
                "thinking",
                {"message": f"Analyzing pipeline for deal {deal_id}"},
                execution_id=deal_id,
            )
            fs = await deal_pipeline_graph.ainvoke(initial)
            await self.emit_event(
                "output",
                {
                    "readiness_score": fs["readiness_score"],
                    "approval_required": fs["approval_required"],
                },
                execution_id=deal_id,
            )
            return {
                "deal_id": fs["deal_id"],
                "current_stage": fs["current_stage"],
                "readiness_score": fs["readiness_score"],
                "stage_assessment": fs["stage_assessment"],
                "blockers": fs["blockers"],
                "recommended_tasks": fs["recommended_tasks"],
                "approval_required": fs["approval_required"],
                "approval_context": fs["approval_context"],
                "next_agent_recommendations": fs["next_agent_recommendations"],
            }
        except Exception as exc:
            logger.exception("DealPipelineAgent.run failed for deal %s", deal_id)
            await self.emit_event("error", {"error": str(exc)}, execution_id=deal_id)
            return {"error": str(exc), "deal_id": deal_id}
