"""Shared pytest configuration for AI orchestrator tests."""
import pytest


# Override the asyncio mode to "auto" so that all async test functions
# are automatically recognized without requiring @pytest.mark.asyncio.
# This avoids conflicts with the project-level strict mode setting.
def pytest_collection_modifyitems(items):
    """Automatically add asyncio marker to all async test functions."""
    for item in items:
        if item.get_closest_marker("asyncio") is None:
            if hasattr(item, "function") and hasattr(item.function, "__wrapped__"):
                pass  # already wrapped
            import asyncio
            if asyncio.iscoroutinefunction(getattr(item, "function", None)):
                item.add_marker(pytest.mark.asyncio)
