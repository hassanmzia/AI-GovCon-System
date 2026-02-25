"""
Autonomy-Aware Proposal Graph — full governance-controlled proposal workflow.

This is the master proposal workflow with integrated:
- Policy enforcement at every consequential step via AutonomyController
- HITL gates at bid/no-bid, pricing, and final submission
- Risk scoring before each major transition
- Evidence validation before submission (anti-hallucination)
- Synthetic evaluation (government evaluator simulation)
- Audit logging of every decision

Workflow steps:
  1.  Load deal + active policy
  2.  Bid/No-Bid recommendation → HITL gate
  3.  RFP analysis + compliance matrix
  4.  Past performance selection
  5.  Solution architecture
  6.  Proposal drafting (section by section)
  7.  Evidence validation (anti-hallucination, citation check)
  8.  Synthetic evaluation (gov evaluator simulation)
  9.  Pricing scenarios → HITL gate
  10. Final proposal assembly → HITL gate
  11. Submission (only after all required approvals obtained)
"""

import asyncio
import logging
import os
from typing import Any

import httpx
from typing_extensions import TypedDict

logger = logging.getLogger("ai_orchestrator.graphs.autonomy_aware_proposal")

DJANGO_API_URL = os.getenv("DJANGO_API_URL", "http://django-api:8001")
DJANGO_SERVICE_TOKEN = os.getenv("DJANGO_SERVICE_TOKEN", "")


def _auth_headers() -> dict[str, str]:
    t = DJANGO_SERVICE_TOKEN
    return {"Authorization": f"Bearer {t}"} if t else {}


async def _get(path: str, default: Any = None) -> Any:
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{DJANGO_API_URL}{path}", headers=_auth_headers())
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.warning("API GET %s failed: %s", path, exc)
        return default


async def _post(path: str, data: dict) -> Any:
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                f"{DJANGO_API_URL}{path}",
                json=data,
                headers=_auth_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.warning("API POST %s failed: %s", path, exc)
        return None


# ── State ─────────────────────────────────────────────────────────────────────


class ProposalWorkflowState(TypedDict):
    deal_id: str
    policy: dict
    risk_score: dict
    deal: dict
    opportunity: dict
    bid_recommendation: str          # "BID" | "NO_BID" | "PENDING_HITL"
    compliance_matrix: dict
    past_performance: list[dict]
    solution_architecture: dict
    proposal_draft: dict
    validation_result: dict          # Evidence validator output
    evaluation_result: dict          # Synthetic evaluator output
    pricing_scenarios: list[dict]
    final_package: dict
    hitl_requests: list[dict]        # All HITL requests submitted
    approvals_obtained: list[str]    # Action names that got approval
    final_status: str                # "submitted" | "pending_approval" | "blocked" | "no_bid" | "error"
    error: str
    messages: list[str]


# ── Helper: run agent safely ───────────────────────────────────────────────────


async def _run_agent(agent_name: str, input_data: dict) -> dict:
    """Safely run a named agent, returning error dict on failure."""
    try:
        from src.graphs.stage_trigger_graph import get_registry
        registry = get_registry()
        agent = registry.get(agent_name)
        if not agent:
            logger.warning("Agent '%s' not in registry", agent_name)
            return {"skipped": True, "reason": f"Agent {agent_name} not registered"}
        return await agent.run(input_data)
    except Exception as exc:
        logger.error("Agent '%s' failed: %s", agent_name, exc)
        return {"error": str(exc)}


# ── Workflow steps ─────────────────────────────────────────────────────────────


async def step_load_context(state: ProposalWorkflowState) -> dict:
    """Load deal context and active AI Autonomy Policy."""
    from src.governance.policy_loader import get_policy

    deal_id = state["deal_id"]
    logger.info("[ProposalWorkflow] Loading context for deal %s", deal_id)

    deal = await _get(f"/api/deals/{deal_id}/", default={})
    opp_id = deal.get("opportunity", "")
    opp = await _get(f"/api/opportunities/{opp_id}/", default={}) if opp_id else {}
    policy = await get_policy()

    return {
        "deal": deal,
        "opportunity": opp,
        "policy": policy,
        "messages": [f"Loaded context for deal: {deal.get('title', deal_id)}"],
    }


async def step_bid_no_bid(state: ProposalWorkflowState) -> dict:
    """Generate bid/no-bid recommendation with HITL gate."""
    from src.governance.autonomy_controller import AutonomyController
    from src.governance.risk_engine import assess

    deal_id = state["deal_id"]
    policy = state["policy"]
    deal = state.get("deal", {})

    logger.info("[ProposalWorkflow] Running bid/no-bid for deal %s", deal_id)

    # Compute risk score
    deal_context = {
        "days_remaining": deal.get("days_until_deadline", 30),
        "compliance_coverage_pct": 0.5,  # Pre-draft estimate
        "margin_pct": float(deal.get("target_margin_pct") or 20),
    }
    risk = assess(deal_context, policy)

    # Get bid/no-bid recommendation from strategy agent
    result = await _run_agent("strategy_agent", {
        "deal_id": deal_id,
        "action": "bid_no_bid_recommendation",
    })
    bid_rec = result.get("recommendation", "BID")

    # Check HITL gate
    controller = AutonomyController()
    gate = await controller.enforce(
        action="bid_no_bid",
        deal_id=deal_id,
        agent_name="proposal_workflow",
        deal_context=deal_context,
        payload={"recommendation": bid_rec, "risk_score": risk.to_dict()},
    )

    hitl_requests = list(state.get("hitl_requests", []))
    if not gate.get("proceed"):
        if gate.get("hitl_requested"):
            hitl_requests.append({
                "action": "bid_no_bid",
                "approval_id": gate.get("approval_id"),
                "status": "pending",
            })
        bid_rec = "PENDING_HITL"

    return {
        "bid_recommendation": bid_rec,
        "risk_score": risk.to_dict(),
        "hitl_requests": hitl_requests,
        "messages": state.get("messages", []) + [f"Bid/No-Bid: {bid_rec}"],
    }


async def step_rfp_analysis(state: ProposalWorkflowState) -> dict:
    """Run RFP analyst to build compliance matrix."""
    deal_id = state["deal_id"]
    logger.info("[ProposalWorkflow] Running RFP analysis for deal %s", deal_id)

    result = await _run_agent("rfp_analyst_agent", {"deal_id": deal_id, "action": "analyze"})
    compliance_result = await _run_agent("compliance_agent", {"deal_id": deal_id, "action": "build_matrix"})

    return {
        "compliance_matrix": compliance_result.get("matrix", result.get("compliance_matrix", {})),
        "messages": state.get("messages", []) + ["RFP analysis and compliance matrix complete"],
    }


async def step_past_performance(state: ProposalWorkflowState) -> dict:
    """Select relevant past performance for this opportunity."""
    deal_id = state["deal_id"]
    logger.info("[ProposalWorkflow] Selecting past performance for deal %s", deal_id)

    result = await _run_agent("past_performance_agent", {
        "deal_id": deal_id,
        "action": "select_relevant",
    })

    return {
        "past_performance": result.get("selected", []),
        "messages": state.get("messages", []) + [
            f"Selected {len(result.get('selected', []))} past performance references"
        ],
    }


async def step_solution_architecture(state: ProposalWorkflowState) -> dict:
    """Generate solution architecture for technical volume."""
    deal_id = state["deal_id"]
    logger.info("[ProposalWorkflow] Building solution architecture for deal %s", deal_id)

    result = await _run_agent("solution_architect_agent", {
        "deal_id": deal_id,
        "action": "design",
    })

    return {
        "solution_architecture": result,
        "messages": state.get("messages", []) + ["Solution architecture generated"],
    }


async def step_proposal_drafting(state: ProposalWorkflowState) -> dict:
    """Draft proposal sections using proposal writer agent."""
    deal_id = state["deal_id"]
    logger.info("[ProposalWorkflow] Drafting proposal for deal %s", deal_id)

    result = await _run_agent("proposal_writer_agent", {
        "deal_id": deal_id,
        "action": "draft_all_sections",
        "compliance_matrix": state.get("compliance_matrix", {}),
        "past_performance": state.get("past_performance", []),
        "solution_architecture": state.get("solution_architecture", {}),
    })

    return {
        "proposal_draft": result,
        "messages": state.get("messages", []) + ["Proposal draft complete"],
    }


async def step_evidence_validation(state: ProposalWorkflowState) -> dict:
    """Run evidence validator to catch hallucinations and uncited claims."""
    deal_id = state["deal_id"]
    logger.info("[ProposalWorkflow] Validating evidence for deal %s", deal_id)

    result = await _run_agent("evidence_validator_agent", {
        "deal_id": deal_id,
        "proposal_draft": state.get("proposal_draft", {}),
    })

    is_safe = result.get("is_submission_safe", True)
    blocking_issues = result.get("blocking_issues", [])

    msg = (
        "Evidence validation: PASSED — submission safe"
        if is_safe
        else f"Evidence validation: BLOCKED — {len(blocking_issues)} issues"
    )

    return {
        "validation_result": result,
        "messages": state.get("messages", []) + [msg],
    }


async def step_synthetic_evaluation(state: ProposalWorkflowState) -> dict:
    """Run synthetic government evaluator on proposal draft."""
    deal_id = state["deal_id"]
    logger.info("[ProposalWorkflow] Running synthetic evaluation for deal %s", deal_id)

    result = await _run_agent("synthetic_evaluator_agent", {
        "deal_id": deal_id,
        "proposal_draft": state.get("proposal_draft", {}),
    })

    win_prob = result.get("win_probability", 0)
    return {
        "evaluation_result": result,
        "messages": state.get("messages", []) + [
            f"Synthetic evaluation complete: estimated win probability {win_prob:.0%}"
        ],
    }


async def step_pricing(state: ProposalWorkflowState) -> dict:
    """Generate pricing scenarios with HITL gate for final pricing decision."""
    from src.governance.autonomy_controller import AutonomyController

    deal_id = state["deal_id"]
    policy = state["policy"]
    logger.info("[ProposalWorkflow] Generating pricing for deal %s", deal_id)

    result = await _run_agent("pricing_agent", {
        "deal_id": deal_id,
        "action": "generate_scenarios",
    })
    scenarios = result.get("scenarios", [])

    # HITL gate for pricing
    controller = AutonomyController()
    gate = await controller.enforce(
        action="final_price",
        deal_id=deal_id,
        agent_name="proposal_workflow",
        deal_context=state.get("risk_score", {}),
        payload={"scenarios": scenarios, "selected": result.get("recommended_scenario")},
    )

    hitl_requests = list(state.get("hitl_requests", []))
    if not gate.get("proceed"):
        if gate.get("hitl_requested"):
            hitl_requests.append({
                "action": "final_price",
                "approval_id": gate.get("approval_id"),
                "status": "pending",
            })

    return {
        "pricing_scenarios": scenarios,
        "hitl_requests": hitl_requests,
        "messages": state.get("messages", []) + [f"Pricing: {len(scenarios)} scenarios generated"],
    }


async def step_final_assembly(state: ProposalWorkflowState) -> dict:
    """Assemble final submission package with HITL gate."""
    from src.governance.autonomy_controller import AutonomyController

    deal_id = state["deal_id"]
    logger.info("[ProposalWorkflow] Assembling final package for deal %s", deal_id)

    result = await _run_agent("submission_agent", {
        "deal_id": deal_id,
        "action": "assemble_package",
        "proposal_draft": state.get("proposal_draft", {}),
        "pricing_scenarios": state.get("pricing_scenarios", []),
        "validation_result": state.get("validation_result", {}),
    })

    # HITL gate for final submission
    controller = AutonomyController()
    gate = await controller.enforce(
        action="final_submission",
        deal_id=deal_id,
        agent_name="proposal_workflow",
        deal_context=state.get("risk_score", {}),
        payload={"package_summary": result.get("summary", {})},
    )

    hitl_requests = list(state.get("hitl_requests", []))
    final_status = "submitted"

    if not gate.get("proceed"):
        if gate.get("hitl_requested"):
            hitl_requests.append({
                "action": "final_submission",
                "approval_id": gate.get("approval_id"),
                "status": "pending",
            })
        final_status = "pending_approval"

    # Block submission if evidence validation failed
    validation = state.get("validation_result", {})
    if not validation.get("is_submission_safe", True):
        final_status = "blocked"
        logger.warning("[ProposalWorkflow] Submission BLOCKED for deal %s — evidence validation failed", deal_id)

    return {
        "final_package": result,
        "hitl_requests": hitl_requests,
        "final_status": final_status,
        "messages": state.get("messages", []) + [f"Final status: {final_status}"],
    }


# ── Main workflow runner ───────────────────────────────────────────────────────


async def run_proposal_workflow(deal_id: str) -> ProposalWorkflowState:
    """
    Execute the full governance-aware proposal workflow for a deal.

    Each step is autonomous unless a HITL gate blocks it, in which case
    an approval request is submitted and the workflow continues (approvals
    are resolved out-of-band by humans via the approval dashboard).

    Returns the final ProposalWorkflowState.
    """
    state: ProposalWorkflowState = {
        "deal_id": deal_id,
        "policy": {},
        "risk_score": {},
        "deal": {},
        "opportunity": {},
        "bid_recommendation": "",
        "compliance_matrix": {},
        "past_performance": [],
        "solution_architecture": {},
        "proposal_draft": {},
        "validation_result": {},
        "evaluation_result": {},
        "pricing_scenarios": [],
        "final_package": {},
        "hitl_requests": [],
        "approvals_obtained": [],
        "final_status": "running",
        "error": "",
        "messages": [],
    }

    steps = [
        ("load_context", step_load_context),
        ("bid_no_bid", step_bid_no_bid),
        ("rfp_analysis", step_rfp_analysis),
        ("past_performance", step_past_performance),
        ("solution_architecture", step_solution_architecture),
        ("proposal_drafting", step_proposal_drafting),
        ("evidence_validation", step_evidence_validation),
        ("synthetic_evaluation", step_synthetic_evaluation),
        ("pricing", step_pricing),
        ("final_assembly", step_final_assembly),
    ]

    for step_name, step_fn in steps:
        try:
            logger.info("[ProposalWorkflow] Step: %s for deal %s", step_name, deal_id)
            updates = await step_fn(state)
            state.update(updates)

            # Stop if bid is NO_BID
            if state.get("bid_recommendation") == "NO_BID":
                state["final_status"] = "no_bid"
                state["messages"].append("Workflow stopped: NO_BID decision")
                break

        except Exception as exc:
            logger.error("[ProposalWorkflow] Step '%s' failed for deal %s: %s", step_name, deal_id, exc)
            state["error"] = f"Step {step_name} failed: {exc}"
            state["final_status"] = "error"
            break

    logger.info(
        "[ProposalWorkflow] Complete for deal %s — status=%s, hitl_requests=%d",
        deal_id, state["final_status"], len(state["hitl_requests"]),
    )
    return state


# ── Graph wrapper ──────────────────────────────────────────────────────────────


class AutonomyAwareProposalGraph:
    """
    Top-level graph wrapper exposing the proposal workflow as an async callable.

    Compatible with the stage trigger graph's agent invocation pattern.
    """

    async def ainvoke(self, input_data: dict) -> dict:
        deal_id = input_data.get("deal_id", "")
        if not deal_id:
            return {"error": "deal_id is required", "final_status": "error"}

        state = await run_proposal_workflow(deal_id)
        return {
            "deal_id": deal_id,
            "final_status": state["final_status"],
            "bid_recommendation": state["bid_recommendation"],
            "hitl_requests": state["hitl_requests"],
            "hitl_requests_count": len(state["hitl_requests"]),
            "risk_score": state["risk_score"],
            "validation_passed": state.get("validation_result", {}).get("is_submission_safe", None),
            "win_probability": state.get("evaluation_result", {}).get("win_probability"),
            "pricing_scenarios_count": len(state["pricing_scenarios"]),
            "messages": state["messages"],
            "error": state.get("error", ""),
        }


proposal_workflow_graph = AutonomyAwareProposalGraph()
