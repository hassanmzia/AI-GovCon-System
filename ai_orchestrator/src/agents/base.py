import json
import logging
import os
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger("ai_orchestrator.agents")

# Redis pub/sub channel prefix for agent events
_AGENT_CHANNEL_PREFIX = "agent:events"


def _get_redis_url() -> str:
    return os.environ.get("REDIS_URL", "redis://localhost:6379/0")


class BaseAgent(ABC):
    """
    Abstract base class for all AI agents in the orchestrator.

    Subclasses must implement:
        - agent_name: A unique identifier for the agent.
        - run(): The main execution method for the agent's task.
    """

    @property
    @abstractmethod
    def agent_name(self) -> str:
        """Unique name identifying this agent."""
        ...

    @abstractmethod
    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Execute the agent's primary task.

        Args:
            input_data: A dictionary containing the input parameters for the agent.

        Returns:
            A dictionary containing the agent's output/results.
        """
        ...

    async def emit_event(
        self,
        event_type: str,
        data: dict[str, Any],
        execution_id: str | None = None,
    ) -> None:
        """
        Publish an A2A (Agent-to-Agent) event to Redis pub/sub.

        Events are published to two channels:
          - ``agent:events:<execution_id>``  (execution-scoped — frontend SSE / Node realtime)
          - ``agent:events:broadcast``       (global — other agents can subscribe)

        Args:
            event_type: The type of event ('thinking', 'tool_call', 'output', 'error').
            data: The event payload.
            execution_id: Optional execution ID for tracking the agent run.
        """
        payload = {
            "agent_name": self.agent_name,
            "event_type": event_type,
            "execution_id": execution_id,
            "data": data,
        }

        log_level = logging.ERROR if event_type == "error" else logging.INFO
        logger.log(
            log_level,
            "Agent '%s' event [%s] (exec=%s)",
            self.agent_name,
            event_type,
            execution_id,
        )

        # Best-effort Redis publish — never crash the agent on pub/sub failure
        try:
            await _publish_to_redis(payload, execution_id)
        except Exception as exc:
            logger.warning(
                "emit_event: Redis publish failed for agent '%s' event '%s': %s",
                self.agent_name,
                event_type,
                exc,
            )


async def _publish_to_redis(payload: dict[str, Any], execution_id: str | None) -> None:
    """Publish payload to Redis pub/sub using redis-py async client."""
    try:
        import redis.asyncio as aioredis
    except ImportError:
        logger.debug("redis-py async not available — skipping pub/sub publish")
        return

    message = json.dumps(payload, default=str)

    async with aioredis.from_url(_get_redis_url(), decode_responses=True) as r:
        # Execution-scoped channel — frontend SSE and Node realtime listen here
        if execution_id:
            await r.publish(f"{_AGENT_CHANNEL_PREFIX}:{execution_id}", message)

        # Broadcast channel — any agent or service subscribed to the firehose
        await r.publish(f"{_AGENT_CHANNEL_PREFIX}:broadcast", message)
