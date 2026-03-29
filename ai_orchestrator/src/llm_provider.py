"""
Centralized LLM provider factory for the AI Orchestrator.

Supports multiple LLM backends that users can switch between via
environment variables or runtime configuration:

  - **anthropic**: Anthropic Claude (claude-sonnet-4-6, claude-haiku-4-5-20251001, etc.)
  - **openai**: OpenAI ChatGPT (gpt-4o, gpt-4o-mini, etc.)
  - **ollama**: Local Ollama instance (deepseek-r1:7b, llama3, mistral, etc.)

Configuration
-------------
Set these environment variables (or pass overrides at call time):

    LLM_PROVIDER=anthropic          # "anthropic", "openai", or "ollama"
    LLM_MODEL=claude-sonnet-4-6     # Model name for the chosen provider

    # Provider-specific keys / URLs
    ANTHROPIC_API_KEY=sk-ant-...
    OPENAI_API_KEY=sk-...
    OLLAMA_BASE_URL=http://localhost:12434   # Ollama server URL

Public API
----------
get_chat_model(...)   -> LangChain BaseChatModel (for agents / LangGraph)
get_provider_info()   -> dict with current provider, model, and status
SUPPORTED_PROVIDERS   -> list of supported provider identifiers
"""

import logging
import os
from typing import Any

logger = logging.getLogger("ai_orchestrator.llm_provider")

SUPPORTED_PROVIDERS = ["anthropic", "openai", "ollama"]

# Default models per provider
_DEFAULT_MODELS: dict[str, str] = {
    "anthropic": "claude-sonnet-4-6",
    "openai": "gpt-4o",
    "ollama": "deepseek-r1:7b",
}


def _get_provider() -> str:
    """Return the configured LLM provider name (lowercase)."""
    return os.getenv("LLM_PROVIDER", "anthropic").lower().strip()


def _get_model(provider: str | None = None) -> str:
    """Return the configured model name, falling back to provider default."""
    model = os.getenv("LLM_MODEL", "")
    if model:
        return model
    p = provider or _get_provider()
    return _DEFAULT_MODELS.get(p, "claude-sonnet-4-6")


def get_chat_model(
    provider: str | None = None,
    model: str | None = None,
    max_tokens: int = 3000,
    callbacks: list | None = None,
    **kwargs: Any,
):
    """
    Return a LangChain-compatible chat model for the requested provider.

    Args:
        provider: Override LLM_PROVIDER env var ("anthropic", "openai", "ollama").
        model: Override LLM_MODEL env var.
        max_tokens: Maximum tokens for the response.
        callbacks: LangChain callback handlers (observability, etc.).
        **kwargs: Extra keyword arguments forwarded to the model constructor.

    Returns:
        A LangChain BaseChatModel instance.

    Raises:
        ValueError: If the provider is not supported.
        ImportError: If the required LangChain integration package is missing.
    """
    p = (provider or _get_provider()).lower().strip()
    m = model or _get_model(p)

    if p == "anthropic":
        return _build_anthropic(m, max_tokens, callbacks, **kwargs)
    elif p == "openai":
        return _build_openai(m, max_tokens, callbacks, **kwargs)
    elif p == "ollama":
        return _build_ollama(m, max_tokens, callbacks, **kwargs)
    else:
        raise ValueError(
            f"Unsupported LLM provider: '{p}'. "
            f"Supported: {', '.join(SUPPORTED_PROVIDERS)}"
        )


def get_provider_info() -> dict[str, Any]:
    """Return a dict describing the current LLM configuration and readiness."""
    provider = _get_provider()
    model = _get_model(provider)

    info: dict[str, Any] = {
        "provider": provider,
        "model": model,
        "supported_providers": SUPPORTED_PROVIDERS,
        "status": "unknown",
    }

    if provider == "anthropic":
        info["status"] = "configured" if os.getenv("ANTHROPIC_API_KEY") else "missing_api_key"
    elif provider == "openai":
        info["status"] = "configured" if os.getenv("OPENAI_API_KEY") else "missing_api_key"
    elif provider == "ollama":
        info["status"] = "configured"  # Ollama doesn't need an API key
        info["ollama_base_url"] = os.getenv("OLLAMA_BASE_URL", "http://localhost:12434")

    return info


# ---------------------------------------------------------------------------
# Provider builders
# ---------------------------------------------------------------------------


def _build_anthropic(model: str, max_tokens: int, callbacks: list | None, **kwargs):
    from langchain_anthropic import ChatAnthropic  # type: ignore[import]

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY is not set. Please set it in your environment "
            "or switch LLM_PROVIDER to 'openai' or 'ollama'."
        )

    return ChatAnthropic(
        model=model,
        api_key=api_key,
        max_tokens=max_tokens,
        callbacks=callbacks if callbacks else None,
        **kwargs,
    )


def _build_openai(model: str, max_tokens: int, callbacks: list | None, **kwargs):
    from langchain_openai import ChatOpenAI  # type: ignore[import]

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY is not set. Please set it in your environment "
            "or switch LLM_PROVIDER to 'anthropic' or 'ollama'."
        )

    return ChatOpenAI(
        model=model,
        api_key=api_key,
        max_tokens=max_tokens,
        callbacks=callbacks if callbacks else None,
        **kwargs,
    )


def _build_ollama(model: str, max_tokens: int, callbacks: list | None, **kwargs):
    from langchain_ollama import ChatOllama  # type: ignore[import]

    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:12434")

    return ChatOllama(
        model=model,
        base_url=base_url,
        num_predict=max_tokens,
        callbacks=callbacks if callbacks else None,
        **kwargs,
    )
