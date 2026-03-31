"""
Django signals for deal stage transitions.

Emits events to the AI orchestrator via Redis when deals change stages,
enabling the Central Nervous System pattern where the deal pipeline
orchestrates all domain agents.
"""

import json
import logging

from django.conf import settings

logger = logging.getLogger(__name__)

# Maps deal stages to the agent chain(s) that should execute.
# Each entry is a list of dicts with agent_type and optional config.
STAGE_AGENT_CHAINS = {
    "intake": [
        {"agent": "scout_agent", "action": "assess_opportunity"},
    ],
    "qualify": [
        {"agent": "fit_agent", "action": "score_fit"},
        {"agent": "strategy_agent", "action": "bid_no_bid_assessment"},
        {"agent": "regulatory_classifier_agent", "action": "classify_regulations"},
    ],
    "bid_no_bid": [
        {"agent": "strategy_agent", "action": "strategic_alignment"},
        {"agent": "research_agent", "action": "agency_due_diligence"},
        {"agent": "marketing_agent", "action": "develop_win_themes"},
    ],
    "capture_plan": [
        {"agent": "capture_agent", "action": "generate_capture_plan"},
        {"agent": "research_agent", "action": "competitor_intelligence"},
        {"agent": "competitor_sim_agent", "action": "simulate_competitors"},
        {"agent": "teaming_agent", "action": "identify_partners"},
    ],
    "proposal_dev": [
        {"agent": "rfp_analyst_agent", "action": "parse_rfp"},
        {"agent": "past_performance_agent", "action": "match_records"},
        {"agent": "solution_architect_agent", "action": "design_solution"},
        {"agent": "proposal_writer_agent", "action": "draft_sections"},
        {"agent": "pricing_agent", "action": "build_scenarios"},
        {"agent": "price_intelligence_agent", "action": "benchmark_pricing"},
        {"agent": "security_compliance_agent", "action": "map_controls"},
    ],
    "red_team": [
        {"agent": "red_team_agent", "action": "evaluate_proposal"},
        {"agent": "compliance_agent", "action": "verify_compliance"},
        {"agent": "qa_agent", "action": "quality_check"},
        {"agent": "synthetic_evaluator_agent", "action": "simulate_evaluation"},
    ],
    "final_review": [
        {"agent": "marketing_agent", "action": "finalize_win_themes"},
        {"agent": "legal_agent", "action": "final_compliance_review"},
    ],
    "submit": [
        {"agent": "submission_agent", "action": "package_submission"},
    ],
    "post_submit": [
        {"agent": "communication_agent", "action": "monitor_qa"},
    ],
    "award_pending": [],
    "contract_setup": [
        {"agent": "contract_agent", "action": "generate_contract"},
    ],
    "delivery": [
        {"agent": "contract_agent", "action": "monitor_deliverables"},
    ],
    "closed_won": [
        {"agent": "learning_agent", "action": "record_win"},
        {"agent": "adaptive_learning_agent", "action": "adapt_from_win"},
    ],
    "closed_lost": [
        {"agent": "learning_agent", "action": "record_loss"},
        {"agent": "adaptive_learning_agent", "action": "adapt_from_loss"},
    ],
    "no_bid": [
        {"agent": "learning_agent", "action": "record_no_bid"},
        {"agent": "adaptive_learning_agent", "action": "adapt_from_no_bid"},
    ],
}


def on_deal_stage_changed(deal_id: str, from_stage: str, to_stage: str, user_id=None):
    """
    Called after a deal stage transition.

    Publishes event to Redis for the AI orchestrator to pick up
    and fire the appropriate agent chain.
    """
    agents = STAGE_AGENT_CHAINS.get(to_stage, [])
    if not agents:
        logger.info(
            "No agent chain configured for stage '%s' (deal %s)", to_stage, deal_id
        )
        return

    event = {
        "event_type": "deal.stage_changed",
        "deal_id": deal_id,
        "from_stage": from_stage,
        "to_stage": to_stage,
        "user_id": str(user_id) if user_id else None,
        "agent_chain": agents,
    }

    try:
        import redis
        redis_url = getattr(settings, "CELERY_BROKER_URL", "redis://localhost:6379/0")
        r = redis.from_url(redis_url)
        r.publish("a2a:deal.stage_changed", json.dumps(event))
        # Also publish to deal-specific channel
        r.publish(f"a2a:deal:{deal_id}", json.dumps(event))
        logger.info(
            "Published stage_changed event for deal %s: %s -> %s (agents: %s)",
            deal_id, from_stage, to_stage,
            [a["agent"] for a in agents],
        )
    except Exception:
        logger.warning(
            "Failed to publish stage_changed event for deal %s to Redis",
            deal_id,
            exc_info=True,
        )


def on_deal_created(deal_id: str, opportunity_id: str, user_id=None):
    """Publish event when a new deal is created."""
    event = {
        "event_type": "deal.created",
        "deal_id": deal_id,
        "opportunity_id": opportunity_id,
        "user_id": str(user_id) if user_id else None,
    }

    try:
        import redis
        redis_url = getattr(settings, "CELERY_BROKER_URL", "redis://localhost:6379/0")
        r = redis.from_url(redis_url)
        r.publish("a2a:deal.created", json.dumps(event))
        logger.info("Published deal.created event for deal %s", deal_id)
    except Exception:
        logger.warning(
            "Failed to publish deal.created event for deal %s to Redis",
            deal_id,
            exc_info=True,
        )


def on_deal_outcome(deal_id: str, outcome: str, user_id=None):
    """Publish event when a deal reaches a terminal outcome (won/lost/no_bid)."""
    event_type_map = {
        "won": "deal.won",
        "lost": "deal.lost",
        "no_bid": "deal.no_bid",
        "cancelled": "deal.cancelled",
    }
    event_type = event_type_map.get(outcome, "deal.outcome_changed")

    event = {
        "event_type": event_type,
        "deal_id": deal_id,
        "outcome": outcome,
        "user_id": str(user_id) if user_id else None,
    }

    try:
        import redis
        redis_url = getattr(settings, "CELERY_BROKER_URL", "redis://localhost:6379/0")
        r = redis.from_url(redis_url)
        r.publish(f"a2a:{event_type}", json.dumps(event))
        r.publish(f"a2a:deal:{deal_id}", json.dumps(event))
        logger.info("Published %s event for deal %s", event_type, deal_id)
    except Exception:
        logger.warning(
            "Failed to publish %s event for deal %s to Redis",
            event_type, deal_id,
            exc_info=True,
        )
