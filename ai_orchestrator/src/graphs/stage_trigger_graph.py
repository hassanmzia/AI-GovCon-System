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
from typing import Any

logger = logging.getLogger("ai_orchestrator.graphs.stage_trigger")

DJANGO_API_URL = os.getenv("DJANGO_API_URL", "http://django-api:8001")
DJANGO_SERVICE_TOKEN = os.getenv("DJANGO_SERVICE_TOKEN", "")


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

    return {
        "scout_agent": ScoutAgent(),
        "fit_agent": FitAgent(),
        "alert_agent": AlertAgent(),
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


_agent_registry = None


def get_registry():
    global _agent_registry
    if _agent_registry is None:
        _agent_registry = _get_agent_registry()
    return _agent_registry


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
    agent_chain = event.get("agent_chain", [])
    results = []

    logger.info(
        "Executing agent chain for deal %s -> stage %s: %s",
        deal_id, to_stage,
        [a["agent"] for a in agent_chain],
    )

    registry = get_registry()

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

        try:
            logger.info("Running agent '%s' (action=%s) for deal %s", agent_name, action, deal_id)
            result = await agent.run({
                "deal_id": deal_id,
                "action": action,
                "stage": to_stage,
                "from_stage": event.get("from_stage", ""),
            })
            results.append({
                "agent": agent_name,
                "action": action,
                "status": "completed",
                "result": result,
            })
            logger.info("Agent '%s' completed for deal %s", agent_name, deal_id)

        except Exception as exc:
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
