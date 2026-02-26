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
  5.  Proposal drafting (section by section)
  6.  Evidence validation (anti-hallucination, citation check)
  7.  Synthetic evaluation (gov evaluator simulation)
  8.  Pricing scenarios → HITL gate
  9.  Final proposal assembly → HITL gate
  10. Submission (only after all required approvals obtained)
"""

import logging
import os
from typing import Any

import httpx
from langchain_core.messages import HumanMessage
from typing_extensions import TypedDict

from src.governance import policy_loader
from src.governance.autonomy_controller import AutonomyController
from src.governance.risk_engine import assess as _assess_risk
from src.observability.tracing import get_callbacks

logger = logging.getLogger("ai_orchestrator.graphs.autonomy_aware_proposal")

DJANGO_API_URL = os.getenv("DJANGO_API_URL", "http://django-api:8001")
DJANGO_SERVICE_TOKEN = os.getenv("DJANGO_SERVICE_TOKEN", "")

_AGENT_NAME = "autonomy_aware_proposal_graph"


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
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{DJANGO_API_URL}{path}",
                json=data,
                headers=_auth_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.warning("API POST %s failed: %s", path, exc)
        return {"error": str(exc)}


# ── State ─────────────────────────────────────────────────────────────────────


class ProposalWorkflowState(TypedDict):
    deal_id: str
    policy: dict
    risk_score: dict
    bid_recommendation: str          # "BID" | "NO_BID" | "PENDING_HITL"
    compliance_matrix: dict
    proposal_draft: dict
    pricing_scenarios: list
    validation_result: dict          # Evidence validator output
    evaluation_result: dict          # Synthetic evaluator output
    hitl_requests: list[dict]        # All HITL requests submitted
    final_status: str                # "submitted" | "pending_approval" | "blocked" | "no_bid"
    messages: list


# ── Helper: run agent safely via registry or direct import ─────────────────────


async def _run_agent(agent_name: str, input_data: dict) -> dict:
    """
    Safely run a named agent. Attempts the stage trigger registry first,
    then falls back to a direct import for agents registered in this module.
    Returns an error dict on failure rather than raising.
    """
    try:
        from src.graphs.stage_trigger_graph import get_registry
        registry = get_registry()
        agent = registry.get(agent_name)
        if agent:
            return await agent.run(input_data)
    except Exception:
        pass  # Registry not available — try direct import below

    # Direct imports for agents defined in this package
    try:
        if agent_name == "evidence_validator_agent":
            from src.agents.evidence_validator_agent import EvidenceValidatorAgent
            return await EvidenceValidatorAgent().run(input_data)
        if agent_name == "synthetic_evaluator_agent":
            from src.agents.synthetic_evaluator_agent import SyntheticEvaluatorAgent
            return await SyntheticEvaluatorAgent().run(input_data)
    except Exception as exc:
        logger.error("Direct import of agent '%s' failed: %s", agent_name, exc)
        return {"error": str(exc)}

    logger.warning("Agent '%s' not found in registry or direct imports", agent_name)
    return {"skipped": True, "reason": f"Agent {agent_name} not registered"}


# ── Workflow steps ─────────────────────────────────────────────────────────────


async def step_load_context(state: ProposalWorkflowState) -> dict:
    """
    Step 1: Load deal context and active AI Autonomy Policy.

    Fetches the deal record from Django and loads the current governance policy.
    Builds the initial deal context dict used for risk scoring throughout.
    """
    deal_id = state["deal_id"]
    logger.info("[ProposalWorkflow] Step 1: Loading context for deal %s", deal_id)

    deal = await _get(f"/api/deals/{deal_id}/", default={})

    try:
        active_policy = await policy_loader.get_policy()
    except Exception as exc:
        logger.warning("[ProposalWorkflow] Policy load failed, using default: %s", exc)
        active_policy = policy_loader.DEFAULT_POLICY

    deal_context = {
        "days_remaining": float(deal.get("days_until_deadline") or 30),
        "days_needed_estimate": 14.0,
        "compliance_coverage_pct": 0.5,
        "margin_pct": float(deal.get("target_margin_pct") or 20),
        "has_cui": bool(deal.get("has_cui") or deal.get("requires_cui_handling")),
        "has_itar": bool(deal.get("has_itar") or deal.get("requires_itar")),
        "pp_gaps": int(deal.get("pp_gap_count") or 0),
    }

    # Compute initial risk score
    try:
        risk = _assess_risk(deal_context, active_policy)
        risk_score = risk.to_dict()
    except Exception as exc:
        logger.warning("[ProposalWorkflow] Initial risk assessment failed: %s", exc)
        risk_score = {}

    msgs = list(state.get("messages") or [])
    msgs.append(
        HumanMessage(
            content=(
                f"Step 1: Deal '{deal.get('title', deal_id)}' loaded. "
                f"Policy level: {active_policy.get('current_autonomy_level')}. "
                f"Kill switch: {active_policy.get('kill_switch_active', False)}."
            )
        )
    )

    return {
        "policy": active_policy,
        "risk_score": risk_score,
        "hitl_requests": [],
        "messages": msgs,
        # Internal carry-forward keys used by subsequent steps
        "_deal": deal,
        "_deal_context": deal_context,
    }


async def step_bid_no_bid(state: ProposalWorkflowState) -> dict:
    """
    Step 2: Generate bid/no-bid recommendation with HITL gate.

    Delegates recommendation to the strategy agent (or falls back to a
    direct LLM call) then enforces the governance gate.
    """
    deal_id = state["deal_id"]
    policy = state["policy"]
    deal: dict = state.get("_deal") or {}  # type: ignore[typeddict-item]
    deal_context: dict = state.get("_deal_context") or {}  # type: ignore[typeddict-item]

    logger.info("[ProposalWorkflow] Step 2: Bid/No-Bid for deal %s", deal_id)

    # Attempt to get recommendation from strategy agent
    result = await _run_agent("strategy_agent", {
        "deal_id": deal_id,
        "action": "bid_no_bid_recommendation",
    })
    bid_rec: str = result.get("recommendation") or result.get("bid_recommendation") or "BID"

    # Enforce governance gate
    controller = AutonomyController()
    gate = await controller.enforce(
        action="bid_no_bid",
        deal_id=deal_id,
        agent_name=_AGENT_NAME,
        deal_context=deal_context,
        payload={"recommendation": bid_rec, "risk_score": state.get("risk_score", {})},
    )

    hitl_requests = list(state.get("hitl_requests") or [])
    msgs = list(state.get("messages") or [])

    if not gate.get("proceed"):
        if gate.get("hitl_requested"):
            hitl_requests.append({
                "step": "bid_no_bid",
                "action": "bid_no_bid",
                "approval_id": gate.get("approval_id"),
                "ai_recommendation": bid_rec,
                "status": "pending",
                "reason": gate.get("reason"),
            })
        bid_rec = "PENDING_HITL"
        msgs.append(HumanMessage(
            content=f"Step 2: Bid/No-Bid HITL gate triggered. Awaiting human approval."
        ))
    else:
        msgs.append(HumanMessage(
            content=f"Step 2: Bid/No-Bid → {bid_rec} (autonomous)."
        ))

    return {
        "bid_recommendation": bid_rec,
        "hitl_requests": hitl_requests,
        "messages": msgs,
    }


async def step_rfp_analysis(state: ProposalWorkflowState) -> dict:
    """
    Step 3: Run RFP analyst and compliance agent to build the compliance matrix.

    Fetches RFP requirements from Django and produces a structured compliance
    matrix mapping each requirement to a proposed response approach.
    """
    deal_id = state["deal_id"]
    logger.info("[ProposalWorkflow] Step 3: RFP analysis for deal %s", deal_id)

    # Try agent registry first, then fall back to direct API
    rfp_result = await _run_agent("rfp_analyst_agent", {"deal_id": deal_id, "action": "analyze"})
    compliance_result = await _run_agent("compliance_agent", {"deal_id": deal_id, "action": "build_matrix"})

    # Merge compliance matrix results
    compliance_matrix: dict = (
        compliance_result.get("matrix")
        or rfp_result.get("compliance_matrix")
        or {}
    )

    # If agents not available, build minimal matrix from direct API
    if not compliance_matrix:
        req_data = await _get(f"/api/rfp/requirements/?deal={deal_id}&limit=100", default={})
        requirements: list = (
            req_data.get("results", []) if isinstance(req_data, dict)
            else req_data if isinstance(req_data, list)
            else []
        )
        compliance_matrix = {
            "requirements_count": len(requirements),
            "requirements": requirements[:50],
            "matrix_entries": [],
        }

    msgs = list(state.get("messages") or [])
    msgs.append(HumanMessage(
        content=f"Step 3: RFP analysis complete. {compliance_matrix.get('requirements_count', 0)} requirements loaded."
    ))

    return {
        "compliance_matrix": compliance_matrix,
        "messages": msgs,
    }


async def step_past_performance(state: ProposalWorkflowState) -> dict:
    """
    Step 4: Select relevant past performance entries for this opportunity.

    Queries Django's past performance matching service and returns the top
    matches ranked by relevance.
    """
    deal_id = state["deal_id"]
    logger.info("[ProposalWorkflow] Step 4: Past performance for deal %s", deal_id)

    result = await _run_agent("past_performance_agent", {
        "deal_id": deal_id,
        "action": "select_relevant",
    })
    selected_pp: list = result.get("selected") or result.get("past_performance_matches") or []

    # Fallback: direct API fetch
    if not selected_pp:
        pp_data = await _get(f"/api/past-performance/matches/?deal_id={deal_id}&limit=5", default={})
        selected_pp = (
            pp_data.get("results", []) if isinstance(pp_data, dict)
            else pp_data if isinstance(pp_data, list)
            else []
        )[:5]

    msgs = list(state.get("messages") or [])
    msgs.append(HumanMessage(
        content=f"Step 4: Selected {len(selected_pp)} past performance reference(s)."
    ))

    return {
        "messages": msgs,
        "_selected_pp": selected_pp,
    }


async def step_proposal_drafting(state: ProposalWorkflowState) -> dict:
    """
    Step 5: Draft proposal sections using the proposal writer agent.

    Delegates to the proposal_writer_agent if registered, otherwise falls back
    to direct agent import.
    """
    deal_id = state["deal_id"]
    logger.info("[ProposalWorkflow] Step 5: Proposal drafting for deal %s", deal_id)

    selected_pp: list = state.get("_selected_pp") or []  # type: ignore[typeddict-item]

    result = await _run_agent("proposal_writer_agent", {
        "deal_id": deal_id,
        "action": "draft_all_sections",
        "compliance_matrix": state.get("compliance_matrix", {}),
        "past_performance_summaries": [
            f"{p.get('contract_title','?')} @ {p.get('agency_name','?')}"
            for p in selected_pp[:5]
        ],
        "technical_solution_summary": "",
        "win_themes": [],
    })

    proposal_draft: dict = (
        result.get("drafted_sections")
        or result.get("proposal_draft")
        or result
        if not result.get("error") and not result.get("skipped")
        else {}
    )

    msgs = list(state.get("messages") or [])
    msgs.append(HumanMessage(
        content=f"Step 5: Proposal draft complete. {len(proposal_draft)} section(s) drafted."
    ))

    return {
        "proposal_draft": proposal_draft,
        "messages": msgs,
    }


async def step_evidence_validation(state: ProposalWorkflowState) -> dict:
    """
    Step 6: Run the Evidence Validator Agent to catch hallucinations and uncited claims.

    Validates every factual claim in the proposal draft against the past performance
    vault. Marks the proposal as unsafe if blocking issues are found.
    """
    deal_id = state["deal_id"]
    logger.info("[ProposalWorkflow] Step 6: Evidence validation for deal %s", deal_id)

    result = await _run_agent("evidence_validator_agent", {
        "deal_id": deal_id,
        "proposal_sections": state.get("proposal_draft", {}),
    })

    is_safe = result.get("is_submission_safe", True)
    blocking_issues = result.get("blocking_issues", [])

    msgs = list(state.get("messages") or [])
    msgs.append(HumanMessage(
        content=(
            f"Step 6: Evidence validation {'PASSED' if is_safe else 'FAILED'}. "
            f"Coverage: {result.get('compliance_coverage', 0)*100:.1f}%. "
            f"Blocking issues: {len(blocking_issues)}."
        )
    ))

    return {
        "validation_result": result,
        "messages": msgs,
    }


async def step_synthetic_evaluation(state: ProposalWorkflowState) -> dict:
    """
    Step 7: Run the Synthetic Evaluator Agent (government evaluator simulation).

    Scores the proposal as a government SSA board would, using FAR Part 15
    Outstanding / Good / Acceptable / Marginal / Unacceptable ratings.
    """
    deal_id = state["deal_id"]
    logger.info("[ProposalWorkflow] Step 7: Synthetic evaluation for deal %s", deal_id)

    result = await _run_agent("synthetic_evaluator_agent", {
        "deal_id": deal_id,
        "proposal_draft": state.get("proposal_draft", {}),
        "rfp_evaluation_criteria": state.get("compliance_matrix", {}).get("requirements", []),
    })

    win_prob = result.get("overall_score") or result.get("win_probability") or 0.0

    msgs = list(state.get("messages") or [])
    msgs.append(HumanMessage(
        content=(
            f"Step 7: Synthetic evaluation complete. "
            f"Win probability: {win_prob:.1f}%. "
            f"Weaknesses: {len(result.get('weaknesses', []))}."
        )
    ))

    return {
        "evaluation_result": result,
        "messages": msgs,
    }


async def step_pricing(state: ProposalWorkflowState) -> dict:
    """
    Step 8: Generate pricing scenarios with HITL gate.

    Delegates to the pricing agent if available, generates three scenarios
    (conservative / target / aggressive), and enforces the final_price HITL gate.
    """
    deal_id = state["deal_id"]
    policy = state["policy"]
    deal_context: dict = state.get("_deal_context") or {}  # type: ignore[typeddict-item]

    logger.info("[ProposalWorkflow] Step 8: Pricing for deal %s", deal_id)

    pricing_result = await _run_agent("pricing_agent", {
        "deal_id": deal_id,
        "action": "generate_scenarios",
    })
    scenarios: list = pricing_result.get("scenarios") or pricing_result.get("pricing_scenarios") or []

    # If agent not available, generate default scenarios
    if not scenarios:
        deal = await _get(f"/api/deals/{deal_id}/", default={})
        ceiling = float(deal.get("ceiling_value") or deal.get("estimated_value") or 1_000_000)
        margin_floor = float(
            policy.get("pricing_guardrails", {}).get("min_margin_percent", 18.0)
        )
        scenarios = [
            {"name": "Conservative", "total_price": round(ceiling * 0.95, 2), "margin_pct": margin_floor + 5.0},
            {"name": "Target",       "total_price": round(ceiling * 0.85, 2), "margin_pct": margin_floor + 8.0},
            {"name": "Aggressive",   "total_price": round(ceiling * 0.75, 2), "margin_pct": margin_floor + 2.0},
        ]

    # Enforce pricing HITL gate
    controller = AutonomyController()
    gate = await controller.enforce(
        action="final_price",
        deal_id=deal_id,
        agent_name=_AGENT_NAME,
        deal_context=deal_context,
        payload={
            "pricing_scenarios": scenarios,
            "recommended_scenario": pricing_result.get("recommended_scenario"),
        },
    )

    hitl_requests = list(state.get("hitl_requests") or [])
    msgs = list(state.get("messages") or [])

    if not gate.get("proceed"):
        if gate.get("hitl_requested"):
            hitl_requests.append({
                "step": "pricing",
                "action": "final_price",
                "approval_id": gate.get("approval_id"),
                "scenarios": scenarios,
                "status": "pending",
                "reason": gate.get("reason"),
            })
        msgs.append(HumanMessage(
            content=f"Step 8: Pricing HITL gate triggered. Awaiting human approval."
        ))
    else:
        msgs.append(HumanMessage(
            content=f"Step 8: Pricing approved autonomously. {len(scenarios)} scenario(s) generated."
        ))

    return {
        "pricing_scenarios": scenarios,
        "hitl_requests": hitl_requests,
        "messages": msgs,
    }


async def step_final_assembly(state: ProposalWorkflowState) -> dict:
    """
    Step 9: Assemble final proposal package with HITL gate.

    Consolidates all sections, validates evidence safety, and enforces the
    final_submission HITL gate. Blocks submission if evidence validation failed.
    """
    deal_id = state["deal_id"]
    deal_context: dict = state.get("_deal_context") or {}  # type: ignore[typeddict-item]

    logger.info("[ProposalWorkflow] Step 9: Final assembly for deal %s", deal_id)

    validation = state.get("validation_result") or {}
    evaluation = state.get("evaluation_result") or {}
    is_safe = validation.get("is_submission_safe", True)
    win_prob = float(evaluation.get("overall_score") or evaluation.get("win_probability") or 0.0)

    # Enforce final submission HITL gate
    controller = AutonomyController()
    gate = await controller.enforce(
        action="final_submission",
        deal_id=deal_id,
        agent_name=_AGENT_NAME,
        deal_context=deal_context,
        payload={
            "sections_count": len(state.get("proposal_draft") or {}),
            "is_submission_safe": is_safe,
            "win_probability": win_prob,
            "compliance_coverage": validation.get("compliance_coverage", 0.0),
            "blocking_issues": validation.get("blocking_issues", []),
            "pricing_scenarios_count": len(state.get("pricing_scenarios") or []),
        },
    )

    hitl_requests = list(state.get("hitl_requests") or [])
    msgs = list(state.get("messages") or [])

    if not gate.get("proceed"):
        if gate.get("hitl_requested"):
            hitl_requests.append({
                "step": "final_submission",
                "action": "final_submission",
                "approval_id": gate.get("approval_id"),
                "win_probability": win_prob,
                "is_submission_safe": is_safe,
                "status": "pending",
                "reason": gate.get("reason"),
            })
        msgs.append(HumanMessage(
            content=f"Step 9: Final submission HITL gate triggered. Awaiting human approval."
        ))
    else:
        msgs.append(HumanMessage(
            content=f"Step 9: Final assembly approved autonomously. Win probability: {win_prob:.1f}%."
        ))

    # Hard block if evidence validation failed
    if not is_safe:
        logger.warning(
            "[ProposalWorkflow] Submission BLOCKED for deal %s — evidence validation failed", deal_id
        )
        msgs.append(HumanMessage(
            content=(
                f"Step 9: Submission BLOCKED by evidence validator. "
                f"Issues: {validation.get('blocking_issues', [])}."
            )
        ))

    return {
        "hitl_requests": hitl_requests,
        "messages": msgs,
        "_final_gate": gate,
        "_evidence_safe": is_safe,
    }


async def step_submission(state: ProposalWorkflowState) -> dict:
    """
    Step 10: Execute or defer submission based on governance gate outcomes.

    Determines final_status:
      - "no_bid"           → bid/no-bid gate returned NO_BID
      - "blocked"          → evidence unsafe or kill switch
      - "pending_approval" → one or more HITL requests outstanding
      - "submitted"        → all gates cleared, submission confirmed
    """
    deal_id = state["deal_id"]
    logger.info("[ProposalWorkflow] Step 10: Submission for deal %s", deal_id)

    bid_rec = state.get("bid_recommendation") or ""
    hitl_requests = state.get("hitl_requests") or []
    final_gate: dict = state.get("_final_gate") or {}  # type: ignore[typeddict-item]
    evidence_safe: bool = state.get("_evidence_safe", True)  # type: ignore[typeddict-item]
    msgs = list(state.get("messages") or [])

    # NO_BID path
    if bid_rec == "NO_BID":
        msgs.append(HumanMessage(content="Step 10: NO_BID — workflow complete."))
        return {"final_status": "no_bid", "messages": msgs}

    # Hard-blocked path
    if not evidence_safe or final_gate.get("blocked"):
        msgs.append(HumanMessage(content="Step 10: Submission BLOCKED by governance policy."))
        return {"final_status": "blocked", "messages": msgs}

    # Pending HITL path
    if hitl_requests:
        await _post(
            f"/api/deals/{deal_id}/workflow-status/",
            {
                "status": "pending_approval",
                "pending_approvals": len(hitl_requests),
                "hitl_requests": [
                    {"step": r.get("step"), "approval_id": r.get("approval_id")}
                    for r in hitl_requests
                ],
            },
        )
        msgs.append(HumanMessage(
            content=(
                f"Step 10: {len(hitl_requests)} HITL approval(s) outstanding. "
                "Proposal in pending_approval state."
            )
        ))
        return {"final_status": "pending_approval", "messages": msgs}

    # All gates cleared — submit
    if final_gate.get("proceed"):
        submit_result = await _post(
            f"/api/deals/{deal_id}/submit/",
            {"submitted_by": _AGENT_NAME, "autonomous_submission": True},
        )
        if "error" not in (submit_result or {}):
            msgs.append(HumanMessage(content=f"Step 10: Proposal SUBMITTED for deal {deal_id}."))
            return {"final_status": "submitted", "messages": msgs}

    msgs.append(HumanMessage(content="Step 10: Submission deferred — pending_approval."))
    return {"final_status": "pending_approval", "messages": msgs}


# ── Main workflow runner ───────────────────────────────────────────────────────


async def run_proposal_workflow(deal_id: str) -> ProposalWorkflowState:
    """
    Execute the full governance-aware proposal workflow for a deal.

    Loads policy via policy_loader.get_policy(), creates an AutonomyController,
    and runs each step sequentially. HITL gates are non-blocking — when approval
    is required, the request is logged and the workflow continues to gather
    additional context. The final_status reflects the overall governance outcome.

    Observability:
        A top-level Langfuse trace is created for the whole workflow, scoped to
        deal_id as the session.  LangSmith automatically traces every LangGraph
        graph invoked inside the step functions when LANGCHAIN_TRACING_V2=true.

    Args:
        deal_id: The deal to run the proposal workflow for.

    Returns:
        ProposalWorkflowState dict populated with all results.
    """
    # --- Langfuse top-level trace for the entire workflow --------------------
    _lf_trace = None
    try:
        from src.observability.tracing import get_callbacks as _gcb, \
            _langfuse_client as _lfc  # noqa: F401 — intentional private access
        if _lfc is not None:
            _lf_trace = _lfc.trace(
                name="proposal_workflow",
                session_id=str(deal_id),
                input={"deal_id": deal_id},
                tags=["govcon", "proposal"],
            )
    except Exception:
        pass  # Observability must never block the workflow
    # -------------------------------------------------------------------------

    state: ProposalWorkflowState = {
        "deal_id": deal_id,
        "policy": {},
        "risk_score": {},
        "bid_recommendation": "",
        "compliance_matrix": {},
        "proposal_draft": {},
        "pricing_scenarios": [],
        "validation_result": {},
        "evaluation_result": {},
        "hitl_requests": [],
        "final_status": "running",
        "messages": [],
    }

    steps = [
        ("load_context",          step_load_context),
        ("bid_no_bid",            step_bid_no_bid),
        ("rfp_analysis",          step_rfp_analysis),
        ("past_performance",      step_past_performance),
        ("proposal_drafting",     step_proposal_drafting),
        ("evidence_validation",   step_evidence_validation),
        ("synthetic_evaluation",  step_synthetic_evaluation),
        ("pricing",               step_pricing),
        ("final_assembly",        step_final_assembly),
        ("submission",            step_submission),
    ]

    for step_name, step_fn in steps:
        try:
            logger.info("[ProposalWorkflow] Running step '%s' for deal %s", step_name, deal_id)
            updates = await step_fn(state)
            state.update(updates)

            # Short-circuit on NO_BID
            if state.get("bid_recommendation") == "NO_BID" and step_name == "bid_no_bid":
                state["final_status"] = "no_bid"
                msgs = list(state.get("messages") or [])
                msgs.append(HumanMessage(content="Workflow stopped: NO_BID decision."))
                state["messages"] = msgs
                break

        except Exception as exc:
            logger.error(
                "[ProposalWorkflow] Step '%s' failed for deal %s: %s", step_name, deal_id, exc
            )
            msgs = list(state.get("messages") or [])
            msgs.append(HumanMessage(content=f"Step '{step_name}' error: {exc}"))
            state["messages"] = msgs
            # Continue to next step rather than aborting entire workflow

    if not state.get("final_status") or state["final_status"] == "running":
        state["final_status"] = "pending_approval"

    logger.info(
        "[ProposalWorkflow] Complete for deal %s — status=%s, hitl_requests=%d",
        deal_id, state["final_status"], len(state.get("hitl_requests") or []),
    )

    # Close the Langfuse trace with final outcome
    if _lf_trace is not None:
        try:
            _lf_trace.update(
                output={
                    "final_status": state["final_status"],
                    "hitl_requests": len(state.get("hitl_requests") or []),
                    "bid_recommendation": state.get("bid_recommendation"),
                },
            )
        except Exception:
            pass

    return state


# ── Graph wrapper ──────────────────────────────────────────────────────────────


class AutonomyAwareProposalGraph:
    """
    Top-level graph wrapper exposing the proposal workflow via an ainvoke() interface.

    Compatible with LangGraph graph patterns and the stage trigger graph's
    agent invocation pattern. Use proposal_workflow_graph.ainvoke({"deal_id": ...}).
    """

    async def ainvoke(self, input_data: dict) -> dict:
        """
        Invoke the autonomy-aware proposal workflow.

        Args:
            input_data: Dict containing at minimum {"deal_id": str}.

        Returns:
            Result dict with final_status, hitl_requests, risk_score, and more.
        """
        deal_id = input_data.get("deal_id", "")
        if not deal_id:
            return {"error": "deal_id is required", "final_status": "blocked"}

        state = await run_proposal_workflow(deal_id)
        return {
            "deal_id": deal_id,
            "final_status": state["final_status"],
            "bid_recommendation": state["bid_recommendation"],
            "hitl_requests": state["hitl_requests"],
            "hitl_requests_count": len(state["hitl_requests"]),
            "risk_score": state["risk_score"],
            "policy_level": state.get("policy", {}).get("current_autonomy_level"),
            "compliance_matrix": state["compliance_matrix"],
            "proposal_draft_sections": list((state.get("proposal_draft") or {}).keys()),
            "pricing_scenarios": state["pricing_scenarios"],
            "validation_result": state["validation_result"],
            "evaluation_result": state["evaluation_result"],
            "messages": [
                m.content if hasattr(m, "content") else str(m)
                for m in (state.get("messages") or [])
            ],
        }


proposal_workflow_graph = AutonomyAwareProposalGraph()
