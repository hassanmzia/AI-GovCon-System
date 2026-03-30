"""
Stage Trigger Graph — Master orchestration graph that listens for deal
stage-change events from Redis and dispatches the appropriate agent chain.

This is the AI-side counterpart to the Django WorkflowEngine. When a deal
transitions stages, the Django backend publishes an event to Redis. This
graph picks it up and runs the configured agent chain.
"""

import asyncio
import json
import logging
import os
import time
import uuid
from typing import Any

logger = logging.getLogger("ai_orchestrator.graphs.stage_trigger")

DJANGO_API_URL = os.getenv("DJANGO_API_URL", "http://django-api:8001")
DJANGO_SERVICE_TOKEN = os.getenv("DJANGO_SERVICE_TOKEN", "")

# Stages that require HITL (Human-in-the-Loop) approval before submission.
# When the agent chain for these stages completes, we create an Approval record
# in Django so a human must approve before the deal can advance further.
HITL_GATE_STAGES: dict[str, str] = {
    "bid_no_bid": "bid_no_bid",
    "final_review": "proposal_final",
    "submit": "submission",
    "contract_setup": "contract_terms",
}


def _auth_headers() -> dict[str, str]:
    t = DJANGO_SERVICE_TOKEN
    return {"Authorization": f"Bearer {t}"} if t else {}


# Agent registry — maps agent names to their graph/agent callables
def _get_agent_registry() -> dict:
    """Lazy-load the agent registry to avoid circular imports."""
    from src.agents.opportunity_agent import OpportunityAgent
    from src.agents.strategy_agent import StrategyAgent
    from src.agents.rfp_analyst_agent import RFPAnalystAgent
    from src.agents.past_performance_agent import PastPerformanceAgent
    from src.agents.solution_architect_agent import SolutionArchitectAgent
    from src.agents.proposal_writer_agent import ProposalWriterAgent
    from src.agents.pricing_agent import PricingAgent
    from src.agents.compliance_agent import ComplianceAgent
    from src.agents.contract_agent import ContractAgent
    from src.agents.qa_agent import QAAgent
    from src.agents.legal_agent import LegalAgent
    from src.agents.marketing_agent import MarketingAgent
    from src.agents.research_agent import ResearchAgent
    from src.agents.teaming_agent import TeamingAgent
    from src.agents.submission_agent import SubmissionAgent
    from src.agents.communication_agent import CommunicationAgent
    from src.agents.security_compliance_agent import SecurityComplianceAgent
    from src.agents.learning_agent import LearningAgent

    # Import new specialized sub-agents
    from src.agents.scout_agent import ScoutAgent
    from src.agents.fit_agent import FitAgent
    from src.agents.capture_agent import CaptureAgent
    from src.agents.red_team_agent import RedTeamAgent
    from src.agents.alert_agent import AlertAgent
    from src.agents.workforce_agent import WorkforceAgent
    from src.agents.ato_agent import ATOAgent
    from src.agents.forecasting_agent import ForecastingAgent
    from src.agents.competitor_sim_agent import CompetitorSimAgent
    from src.agents.ranking_agent import RankingAgent

    # Governance & safety agents (imported with try/except — created by governance framework)
    try:
        from src.agents.synthetic_evaluator_agent import SyntheticEvaluatorAgent
        from src.agents.amendment_diff_agent import AmendmentDiffAgent
        from src.agents.evidence_validator_agent import EvidenceValidatorAgent
        _governance_agents = {
            "synthetic_evaluator_agent": SyntheticEvaluatorAgent(),
            "amendment_diff_agent": AmendmentDiffAgent(),
            "evidence_validator_agent": EvidenceValidatorAgent(),
        }
    except ImportError:
        logger.warning("Governance agents not yet available; skipping registration.")
        _governance_agents = {}

    registry = {
        "scout_agent": ScoutAgent(),
        "fit_agent": FitAgent(),
        "alert_agent": AlertAgent(),
        "ranking_agent": RankingAgent(),
        "opportunity_agent": OpportunityAgent(),
        "strategy_agent": StrategyAgent(),
        "research_agent": ResearchAgent(),
        "capture_agent": CaptureAgent(),
        "rfp_analyst_agent": RFPAnalystAgent(),
        "past_performance_agent": PastPerformanceAgent(),
        "solution_architect_agent": SolutionArchitectAgent(),
        "proposal_writer_agent": ProposalWriterAgent(),
        "pricing_agent": PricingAgent(),
        "compliance_agent": ComplianceAgent(),
        "red_team_agent": RedTeamAgent(),
        "qa_agent": QAAgent(),
        "legal_agent": LegalAgent(),
        "marketing_agent": MarketingAgent(),
        "teaming_agent": TeamingAgent(),
        "submission_agent": SubmissionAgent(),
        "communication_agent": CommunicationAgent(),
        "contract_agent": ContractAgent(),
        "security_compliance_agent": SecurityComplianceAgent(),
        "learning_agent": LearningAgent(),
        "workforce_agent": WorkforceAgent(),
        "ato_agent": ATOAgent(),
        "forecasting_agent": ForecastingAgent(),
        "competitor_sim_agent": CompetitorSimAgent(),
    }
    registry.update(_governance_agents)
    return registry


_agent_registry = None


def get_registry():
    global _agent_registry
    if _agent_registry is None:
        _agent_registry = _get_agent_registry()
    return _agent_registry


async def _create_hitl_approval(
    deal_id: str,
    approval_type: str,
    agent_results: list[dict],
) -> dict | None:
    """Create a HITL approval request in Django after an agent chain completes.

    This ensures a human must review and approve before the deal can
    transition past critical gate stages (bid/no-bid, final review, submit).
    """
    import httpx

    # Summarise agent chain results for the human reviewer
    successes = [r for r in agent_results if r.get("status") == "completed"]
    failures = [r for r in agent_results if r.get("status") == "failed"]
    summary_parts = [f"{len(successes)}/{len(agent_results)} agents succeeded."]
    if failures:
        summary_parts.append(
            f"Failed: {', '.join(r['agent'] for r in failures)}."
        )

    # Compute an AI confidence score based on agent success rate
    confidence = len(successes) / max(len(agent_results), 1)
    recommendation = "approve" if confidence >= 0.8 and not failures else "review_needed"

    body = {
        "approval_type": approval_type,
        "ai_recommendation": recommendation,
        "ai_confidence": round(confidence, 2),
        "ai_rationale": " ".join(summary_parts),
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{DJANGO_API_URL}/api/deals/deals/{deal_id}/request-approval/",
                json=body,
                headers=_auth_headers(),
            )
            if resp.status_code < 300:
                data = resp.json()
                logger.info(
                    "HITL approval request created for deal %s (type=%s, id=%s)",
                    deal_id, approval_type, data.get("id"),
                )
                return data
            else:
                logger.warning(
                    "HITL approval request failed (%s): %s",
                    resp.status_code, resp.text[:300],
                )
    except Exception as exc:
        logger.warning("Could not create HITL approval for deal %s: %s", deal_id, exc)

    return None


async def _fetch_deal_context(deal_id: str) -> dict:
    """Fetch deal details from Django to provide proper input to agents.

    Some agents need fields beyond deal_id (e.g. StrategyAgent needs
    opportunity_id, ResearchAgent needs a query string).  We fetch the
    deal once and derive these fields.
    """
    import httpx

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{DJANGO_API_URL}/api/deals/deals/{deal_id}/",
                headers=_auth_headers(),
            )
            if resp.status_code == 200:
                return resp.json()
    except Exception as exc:
        logger.warning("Could not fetch deal context for %s: %s", deal_id, exc)
    return {}


def _build_agent_input(
    agent_name: str,
    action: str,
    deal_id: str,
    to_stage: str,
    from_stage: str,
    deal_context: dict,
) -> dict:
    """Build the input dict tailored to each agent's expected schema.

    Most agents just need deal_id, but some require specific fields.
    """
    base = {
        "deal_id": deal_id,
        "action": action,
        "stage": to_stage,
        "from_stage": from_stage,
    }

    opportunity_id = str(deal_context.get("opportunity") or deal_context.get("opportunity_id") or "")

    if agent_name == "strategy_agent":
        base["opportunity_id"] = opportunity_id
    elif agent_name == "research_agent":
        # Build a meaningful research query from the deal/action context
        title = deal_context.get("title") or deal_context.get("opportunity_title") or ""
        agency = deal_context.get("agency") or ""
        query_map = {
            "agency_due_diligence": f"Agency background and procurement history for {agency or title}",
            "competitor_intelligence": f"Competitor landscape analysis for {title}",
            "market_analysis": f"Market analysis for {title}",
        }
        base["query"] = query_map.get(action, f"Research for deal: {title}")
        base["research_type"] = action
    elif agent_name in ("fit_agent", "scout_agent", "opportunity_agent"):
        base["opportunity_id"] = opportunity_id

    return base


async def execute_agent_chain(event: dict) -> list[dict]:
    """
    Execute the agent chain specified in a stage-change event.

    Args:
        event: Dict with keys: deal_id, from_stage, to_stage, agent_chain
               agent_chain is a list of {agent, action} dicts.

    Returns:
        List of result dicts from each agent execution.
    """
    deal_id = event.get("deal_id", "")
    to_stage = event.get("to_stage", "")
    from_stage = event.get("from_stage", "")
    agent_chain = event.get("agent_chain", [])
    results = []

    logger.info(
        "Executing agent chain for deal %s -> stage %s: %s",
        deal_id, to_stage,
        [a["agent"] for a in agent_chain],
    )

    registry = get_registry()

    # Fetch deal context once so we can build proper inputs for each agent
    deal_context = await _fetch_deal_context(deal_id) if deal_id else {}

    from src.run_recorder import record_run_completed, record_run_failed, record_run_started

    for step in agent_chain:
        agent_name = step["agent"]
        action = step.get("action", "run")
        agent = registry.get(agent_name)

        if not agent:
            logger.warning("Agent '%s' not found in registry, skipping.", agent_name)
            results.append({
                "agent": agent_name,
                "status": "skipped",
                "reason": "Agent not found in registry",
            })
            continue

        run_id = str(uuid.uuid4())
        t0 = time.time()
        await record_run_started(run_id, agent_name, deal_id, action=action)

        input_data = _build_agent_input(
            agent_name, action, deal_id, to_stage, from_stage, deal_context,
        )

        try:
            logger.info("Running agent '%s' (action=%s) for deal %s", agent_name, action, deal_id)
            result = await agent.run(input_data)
            latency = int((time.time() - t0) * 1000)
            has_error = result.get("error") if isinstance(result, dict) else False
            if has_error:
                await record_run_failed(run_id, str(has_error), latency_ms=latency)
            else:
                await record_run_completed(run_id, latency_ms=latency, success=True)
            results.append({
                "agent": agent_name,
                "action": action,
                "status": "completed",
                "result": result,
            })
            logger.info("Agent '%s' completed for deal %s", agent_name, deal_id)

        except Exception as exc:
            latency = int((time.time() - t0) * 1000)
            await record_run_failed(run_id, str(exc), latency_ms=latency)
            logger.error(
                "Agent '%s' failed for deal %s: %s",
                agent_name, deal_id, exc,
                exc_info=True,
            )
            results.append({
                "agent": agent_name,
                "action": action,
                "status": "failed",
                "error": str(exc),
            })

    # After the agent chain completes, create HITL approval request if this
    # is a gate stage. This ensures a human reviews before advancing further.
    hitl_approval_type = HITL_GATE_STAGES.get(to_stage)
    if hitl_approval_type:
        approval = await _create_hitl_approval(deal_id, hitl_approval_type, results)
        if approval:
            results.append({
                "agent": "_hitl_gate",
                "action": hitl_approval_type,
                "status": "pending_approval",
                "approval_id": approval.get("id"),
            })

    return results


async def listen_for_stage_changes(redis_url: str = "redis://localhost:6379/0"):
    """
    Long-running listener that subscribes to deal.stage_changed events
    on Redis and dispatches agent chains.

    This is the main entry point for the stage trigger system.
    """
    import redis.asyncio as aioredis

    r = aioredis.from_url(redis_url)
    pubsub = r.pubsub()
    await pubsub.subscribe("a2a:deal.stage_changed")

    logger.info("Stage trigger listener started, subscribed to a2a:deal.stage_changed")

    try:
        async for message in pubsub.listen():
            if message["type"] != "message":
                continue

            try:
                event = json.loads(message["data"])
                logger.info(
                    "Received stage_changed event: deal=%s %s->%s",
                    event.get("deal_id"), event.get("from_stage"), event.get("to_stage"),
                )
                # Execute in background to not block the listener
                asyncio.create_task(execute_agent_chain(event))

            except json.JSONDecodeError:
                logger.warning("Invalid JSON in stage_changed event: %s", message["data"])
            except Exception:
                logger.exception("Error processing stage_changed event")

    finally:
        await pubsub.unsubscribe("a2a:deal.stage_changed")
        await r.close()
