"""
A2A (Agent-to-Agent) Event System.

Provides pub/sub event bus for inter-agent communication using Redis.
All 65+ A2A events flow through this system.
"""

import json
import logging
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Coroutine

logger = logging.getLogger("ai_orchestrator.events")


class EventType(str, Enum):
    """All A2A event types in the system."""

    # Opportunity Intelligence Agent
    OPPORTUNITY_DISCOVERED = "opportunity.discovered"
    OPPORTUNITY_SCORED = "opportunity.scored"
    OPPORTUNITY_ENRICHED = "opportunity.enriched"
    OPPORTUNITY_RECOMMENDED = "opportunity.recommended"
    OPPORTUNITY_DIGEST_READY = "opportunity.digest_ready"

    # Strategy Agent
    STRATEGY_SCORE_COMPUTED = "strategy.score_computed"
    STRATEGY_ALIGNMENT_CHECKED = "strategy.alignment_checked"
    STRATEGY_PORTFOLIO_UPDATED = "strategy.portfolio_updated"
    STRATEGY_GOAL_PROGRESS = "strategy.goal_progress"

    # Deep Research Agent
    RESEARCH_STARTED = "research.started"
    RESEARCH_COMPLETED = "research.completed"
    RESEARCH_FAILED = "research.failed"
    COMPETITOR_PROFILE_UPDATED = "research.competitor_profile_updated"
    MARKET_INTEL_AVAILABLE = "research.market_intel_available"

    # Deal Pipeline Agent
    DEAL_CREATED = "deal.created"
    DEAL_STAGE_CHANGED = "deal.stage_changed"
    DEAL_TASK_ASSIGNED = "deal.task_assigned"
    DEAL_APPROVAL_REQUIRED = "deal.approval_required"
    DEAL_APPROVAL_GRANTED = "deal.approval_granted"
    DEAL_WON = "deal.won"
    DEAL_LOST = "deal.lost"

    # RFP Analyst Agent
    RFP_UPLOADED = "rfp.uploaded"
    RFP_PARSED = "rfp.parsed"
    RFP_REQUIREMENTS_EXTRACTED = "rfp.requirements_extracted"
    RFP_COMPLIANCE_MATRIX_READY = "rfp.compliance_matrix_ready"
    RFP_AMENDMENT_DETECTED = "rfp.amendment_detected"
    RFP_AMENDMENT_DIFFED = "rfp.amendment_diffed"

    # Past Performance Agent
    PAST_PERFORMANCE_MATCHED = "past_performance.matched"
    PAST_PERFORMANCE_SCORED = "past_performance.scored"

    # Proposal Writer Agent
    PROPOSAL_SECTION_DRAFTED = "proposal.section_drafted"
    PROPOSAL_REVIEW_REQUESTED = "proposal.review_requested"
    PROPOSAL_REVIEW_COMPLETED = "proposal.review_completed"
    PROPOSAL_SECTION_APPROVED = "proposal.section_approved"
    PROPOSAL_ASSEMBLED = "proposal.assembled"

    # Solutions Architect Agent
    SOLUTION_ARCHITECTURE_DESIGNED = "solution.architecture_designed"
    SOLUTION_DIAGRAM_GENERATED = "solution.diagram_generated"
    SOLUTION_MANAGEMENT_VOLUME_READY = "solution.management_volume_ready"
    SOLUTION_LOE_ESTIMATED = "solution.loe_estimated"

    # Pricing Engine Agent
    PRICING_COST_MODEL_BUILT = "pricing.cost_model_built"
    PRICING_SCENARIO_GENERATED = "pricing.scenario_generated"
    PRICING_PTW_ANALYZED = "pricing.ptw_analyzed"
    PRICING_APPROVAL_REQUIRED = "pricing.approval_required"
    PRICING_APPROVED = "pricing.approved"

    # Marketing Agent
    WIN_THEMES_GENERATED = "marketing.win_themes_generated"
    CAPABILITY_STATEMENT_READY = "marketing.capability_statement_ready"
    EXECUTIVE_SUMMARY_DRAFTED = "marketing.executive_summary_drafted"
    GHOST_TEAM_ANALYZED = "marketing.ghost_team_analyzed"

    # Legal Agent
    COMPLIANCE_ASSESSMENT_COMPLETED = "legal.compliance_assessment_completed"
    LEGAL_RISK_IDENTIFIED = "legal.legal_risk_identified"
    FAR_ANALYSIS_COMPLETED = "legal.far_analysis_completed"
    CONTRACT_REVIEW_COMPLETED = "legal.contract_review_completed"

    # Teaming Agent
    TEAMING_PARTNERS_MATCHED = "teaming.partners_matched"
    TEAMING_TEAM_EVALUATED = "teaming.team_evaluated"
    TEAMING_OCI_CHECKED = "teaming.oci_checked"
    TEAMING_AGREEMENT_DRAFTED = "teaming.agreement_drafted"

    # Security Compliance Agent
    SECURITY_FRAMEWORKS_IDENTIFIED = "security.frameworks_identified"
    SECURITY_CONTROLS_MAPPED = "security.controls_mapped"
    SECURITY_GAPS_ASSESSED = "security.gaps_assessed"
    SECURITY_POAM_GENERATED = "security.poam_generated"
    SECURITY_COMPLIANCE_REPORT_READY = "security.compliance_report_ready"

    # Knowledge Vault
    DOCUMENT_PROCESSED = "knowledge.document_processed"
    DOCUMENT_EMBEDDED = "knowledge.document_embedded"
    SEARCH_COMPLETED = "knowledge.search_completed"
    RAG_CONTEXT_RETRIEVED = "knowledge.rag_context_retrieved"

    # Contract Management Agent
    CONTRACT_GENERATED = "contract.generated"
    CONTRACT_MILESTONE_DUE = "contract.milestone_due"
    CONTRACT_MILESTONE_OVERDUE = "contract.milestone_overdue"
    CONTRACT_MODIFICATION_REQUESTED = "contract.modification_requested"

    # Communications
    CLARIFICATION_SUBMITTED = "communication.clarification_submitted"
    CLARIFICATION_ANSWERED = "communication.clarification_answered"
    QA_IMPACT_IDENTIFIED = "communication.qa_impact_identified"

    # Policy & Governance
    GATE_REVIEW_REQUIRED = "policy.gate_review_required"
    GATE_REVIEW_COMPLETED = "policy.gate_review_completed"
    POLICY_RULE_TRIGGERED = "policy.rule_triggered"

    # Orchestrator
    AGENT_STARTED = "orchestrator.agent_started"
    AGENT_COMPLETED = "orchestrator.agent_completed"
    AGENT_FAILED = "orchestrator.agent_failed"
    WORKFLOW_STARTED = "orchestrator.workflow_started"
    WORKFLOW_COMPLETED = "orchestrator.workflow_completed"


@dataclass
class A2AEvent:
    """An Agent-to-Agent event."""

    event_type: str
    source_agent: str
    data: dict[str, Any]
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    deal_id: str | None = None
    correlation_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, data: str) -> "A2AEvent":
        return cls(**json.loads(data))


# Type alias for event handlers
EventHandler = Callable[[A2AEvent], Coroutine[Any, Any, None]]


class EventBus:
    """
    In-process event bus with Redis pub/sub for cross-service events.

    Supports:
    - Local in-process subscriptions (for agents within the orchestrator)
    - Redis pub/sub (for cross-service communication with Django, Node.js)
    """

    def __init__(self):
        self._handlers: dict[str, list[EventHandler]] = {}
        self._redis = None
        self._running = False

    async def connect(self, redis_url: str = "redis://localhost:6379/0"):
        """Connect to Redis for cross-service pub/sub."""
        try:
            import redis.asyncio as aioredis

            self._redis = aioredis.from_url(redis_url)
            self._running = True
            logger.info("EventBus connected to Redis at %s", redis_url)
        except Exception as e:
            logger.warning("EventBus running without Redis: %s", e)

    async def disconnect(self):
        """Disconnect from Redis."""
        self._running = False
        if self._redis:
            await self._redis.close()
            logger.info("EventBus disconnected from Redis")

    def subscribe(self, event_type: str, handler: EventHandler):
        """Subscribe a handler to an event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        logger.debug("Handler subscribed to %s", event_type)

    def subscribe_pattern(self, pattern: str, handler: EventHandler):
        """Subscribe to events matching a pattern (e.g., 'deal.*')."""
        self._handlers.setdefault(f"pattern:{pattern}", []).append(handler)

    async def publish(self, event: A2AEvent):
        """Publish an event to local handlers and Redis."""
        logger.info(
            "Event published: %s from %s (deal=%s)",
            event.event_type,
            event.source_agent,
            event.deal_id,
        )

        # Dispatch to local handlers
        handlers = self._handlers.get(event.event_type, [])

        # Check pattern subscriptions
        for key, pattern_handlers in self._handlers.items():
            if key.startswith("pattern:"):
                pattern = key[8:]
                if _matches_pattern(event.event_type, pattern):
                    handlers.extend(pattern_handlers)

        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error(
                    "Error in event handler for %s: %s",
                    event.event_type,
                    e,
                    exc_info=True,
                )

        # Publish to Redis for cross-service consumption
        if self._redis:
            try:
                channel = f"a2a:{event.event_type}"
                await self._redis.publish(channel, event.to_json())
                # Also publish to deal-specific channel if deal_id present
                if event.deal_id:
                    await self._redis.publish(
                        f"a2a:deal:{event.deal_id}", event.to_json()
                    )
            except Exception as e:
                logger.error("Failed to publish to Redis: %s", e)


def _matches_pattern(event_type: str, pattern: str) -> bool:
    """Simple glob-style pattern matching for event types."""
    if pattern.endswith(".*"):
        prefix = pattern[:-2]
        return event_type.startswith(prefix + ".")
    return event_type == pattern


# Global singleton
event_bus = EventBus()
