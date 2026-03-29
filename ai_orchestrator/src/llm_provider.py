"""
Centralized LLM provider factory for the AI Orchestrator.

Supports multiple LLM backends that users can switch between via
the Settings UI, environment variables, or runtime overrides:

  - **anthropic**: Anthropic Claude (claude-sonnet-4-6, etc.)
  - **openai**: OpenAI ChatGPT (gpt-4o, gpt-4o-mini, etc.)
  - **ollama**: Local Ollama instance (deepseek-r1:7b, llama3, etc.)

Configuration priority:
    1. Redis key ``llm_config`` (written by Django Settings UI)
    2. Environment variables (LLM_PROVIDER, LLM_MODEL, OLLAMA_BASE_URL)
    3. Built-in defaults

Public API
----------
get_chat_model(...)   -> LangChain BaseChatModel (for agents / LangGraph)
get_provider_info()   -> dict with current provider, model, and status
SUPPORTED_PROVIDERS   -> list of supported provider identifiers
"""

import json
import logging
import os
from typing import Any

logger = logging.getLogger("ai_orchestrator.llm_provider")


class LLMProviderError(Exception):
    """Raised when the LLM provider is misconfigured or unavailable."""
    pass


class LLMCreditError(LLMProviderError):
    """Raised when the LLM provider rejects requests due to billing/credit issues."""
    pass


SUPPORTED_PROVIDERS = ["anthropic", "openai", "ollama"]

# Default models per provider
_DEFAULT_MODELS: dict[str, str] = {
    "anthropic": "claude-sonnet-4-6",
    "openai": "gpt-4o",
    "ollama": "deepseek-r1:7b",
}


# ---------------------------------------------------------------------------
# Redis-backed config (shared with Django backend)
# ---------------------------------------------------------------------------

def _redis_config() -> dict[str, Any]:
    """Read LLM settings from Redis. Returns {} if unavailable."""
    try:
        import redis
        r = redis.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            decode_responses=True,
        )
        raw = r.get("llm_config")
        if raw:
            return json.loads(raw)
    except Exception:
        pass
    return {}


def _get_provider() -> str:
    """Return the configured LLM provider (Redis > env var > default)."""
    cfg = _redis_config()
    return (
        cfg.get("provider")
        or os.getenv("LLM_PROVIDER", "anthropic")
    ).lower().strip()


def _get_model(provider: str | None = None) -> str:
    """Return the configured model name (Redis > env var > provider default)."""
    cfg = _redis_config()
    if cfg.get("model"):
        return cfg["model"]
    model = os.getenv("LLM_MODEL", "")
    if model:
        return model
    p = provider or _get_provider()
    return _DEFAULT_MODELS.get(p, "claude-sonnet-4-6")


def _get_ollama_url() -> str:
    cfg = _redis_config()
    return (
        cfg.get("ollama_base_url")
        or os.getenv("OLLAMA_BASE_URL", "http://localhost:12434")
    )


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
        provider: Override configured provider ("anthropic", "openai", "ollama").
        model: Override configured model.
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

    logger.info("Building LLM: provider=%s model=%s", p, m)

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
        info["status"] = "configured"
        info["ollama_base_url"] = _get_ollama_url()

    return info


# ---------------------------------------------------------------------------
# Provider builders
# ---------------------------------------------------------------------------


def _build_anthropic(model: str, max_tokens: int, callbacks: list | None, **kwargs):
    from langchain_anthropic import ChatAnthropic  # type: ignore[import]

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise LLMProviderError(
            "ANTHROPIC_API_KEY is not set. Please set it in your environment "
            "or switch to a different LLM provider in Settings."
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
        raise LLMProviderError(
            "OPENAI_API_KEY is not set. Please set it in your environment "
            "or switch to a different LLM provider in Settings."
        )

    return ChatOpenAI(
        model=model,
        api_key=api_key,
        max_tokens=max_tokens,
        callbacks=callbacks if callbacks else None,
        **kwargs,
    )


def check_llm_error(exc: Exception) -> None:
    """Re-raise as LLMCreditError or LLMProviderError if the exception
    indicates a billing, authentication, or configuration issue.

    Call this in except blocks around LLM invocations to convert opaque
    SDK exceptions into actionable errors that stop the agent pipeline
    immediately instead of continuing with broken output.
    """
    msg = str(exc).lower()

    # Credit / billing errors
    credit_keywords = ["credit balance", "insufficient_quota", "billing", "exceeded your current quota"]
    if any(kw in msg for kw in credit_keywords):
        raise LLMCreditError(
            "LLM API credit balance is too low. Please add credits to your account "
            "or switch to a different LLM provider in Settings."
        ) from exc

    # Authentication errors
    auth_keywords = ["invalid api key", "invalid x-api-key", "authentication", "unauthorized", "permission denied"]
    if any(kw in msg for kw in auth_keywords):
        raise LLMProviderError(
            "LLM API key is invalid or expired. Please check your API key "
            "in Settings or switch to a different provider."
        ) from exc

    # Connection errors (Ollama / local LLM not reachable)
    conn_keywords = ["connection refused", "connect error", "all connection attempts failed",
                     "connection reset", "name or service not known", "nodename nor servname"]
    if any(kw in msg for kw in conn_keywords):
        raise LLMProviderError(
            "LLM service is not reachable. If using Ollama, make sure it is running "
            "and accessible. Check Settings for the correct Ollama URL."
        ) from exc


def _build_ollama(model: str, max_tokens: int, callbacks: list | None, **kwargs):
    from langchain_ollama import ChatOllama  # type: ignore[import]

    base_url = _get_ollama_url()
    logger.info("Connecting to Ollama at %s with model %s", base_url, model)

    # Quick connectivity check so we fail fast with a clear message
    try:
        import httpx
        resp = httpx.get(f"{base_url}/api/version", timeout=5.0)
        resp.raise_for_status()
    except Exception as exc:
        raise LLMProviderError(
            f"Cannot connect to Ollama at {base_url}. "
            f"Make sure Ollama is running with OLLAMA_HOST=0.0.0.0:12434 "
            f"so Docker containers can reach it, and the model '{model}' is pulled. "
            f"Run: ollama pull {model}"
        ) from exc

    return ChatOllama(
        model=model,
        base_url=base_url,
        num_predict=max_tokens,
        callbacks=callbacks if callbacks else None,
        **kwargs,
    )


async def safe_llm_call(
    system: str,
    human: str,
    max_tokens: int = 3000,
    provider: str | None = None,
    model: str | None = None,
) -> str:
    """High-level async LLM call with proper error handling.

    Use this in agent graph nodes instead of rolling your own try/except.
    Raises LLMCreditError or LLMProviderError on billing/auth issues
    so agent pipelines fail fast with actionable messages.
    """
    from langchain_core.messages import HumanMessage, SystemMessage

    llm = get_chat_model(provider=provider, model=model, max_tokens=max_tokens)
    try:
        response = await llm.ainvoke([
            SystemMessage(content=system),
            HumanMessage(content=human),
        ])
        return response.content
    except (LLMCreditError, LLMProviderError):
        raise
    except Exception as exc:
        check_llm_error(exc)
        raise
