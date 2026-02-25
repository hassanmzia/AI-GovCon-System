"""Research LangGraph workflow export."""
# The compiled research graph is built in research_agent.py and re-exported here
# so other modules can import it without circular dependencies.
from src.agents.research_agent import research_graph  # noqa: F401

__all__ = ["research_graph"]
