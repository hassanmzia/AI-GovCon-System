"""
Centralized LLM provider for Django backend services.

Provides async chat completion using the configured LLM provider,
without requiring LangChain. Supports:

  - **anthropic**: Anthropic Claude API (default)
  - **openai**: OpenAI ChatGPT API
  - **ollama**: Local Ollama instance (OpenAI-compatible API)

Configuration priority:
    1. Database SystemSetting (editable from Settings UI)
    2. Environment variables (LLM_PROVIDER, LLM_MODEL, OLLAMA_BASE_URL)
    3. Built-in defaults
"""

import logging
import os
from typing import Any

logger = logging.getLogger("ai_deal_manager.core.llm_provider")

SUPPORTED_PROVIDERS = ["anthropic", "openai", "ollama"]

DEFAULT_MODELS: dict[str, str] = {
    "anthropic": "claude-sonnet-4-6",
    "openai": "gpt-4o",
    "ollama": "deepseek-r1:7b",
}

PROVIDER_MODELS: dict[str, list[str]] = {
    "anthropic": ["claude-sonnet-4-6", "claude-haiku-4-5-20251001"],
    "openai": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
    "ollama": ["deepseek-r1:7b", "llama3", "mistral", "codellama", "phi3"],
}


def _db_settings() -> dict[str, Any]:
    """Read LLM settings from Redis first, then database. Returns {} if unavailable."""
    # Try Redis first (fast, shared with orchestrator)
    try:
        import json
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

    # Fall back to database
    try:
        from apps.core.models import SystemSetting
        return SystemSetting.get("llm_config", {}) or {}
    except Exception:
        return {}


def _get_provider() -> str:
    db = _db_settings()
    return (
        db.get("provider")
        or os.getenv("LLM_PROVIDER", "anthropic")
    ).lower().strip()


def _get_model(provider: str | None = None) -> str:
    db = _db_settings()
    if db.get("model"):
        return db["model"]
    model = os.getenv("LLM_MODEL", "")
    if model:
        return model
    p = provider or _get_provider()
    return DEFAULT_MODELS.get(p, "claude-sonnet-4-6")


def _get_ollama_url() -> str:
    db = _db_settings()
    return (
        db.get("ollama_base_url")
        or os.getenv("OLLAMA_BASE_URL", "http://172.168.1.95:12434")
    )


def get_provider_info() -> dict[str, Any]:
    """Return current LLM configuration status."""
    provider = _get_provider()
    model = _get_model(provider)
    info: dict[str, Any] = {
        "provider": provider,
        "model": model,
        "supported_providers": SUPPORTED_PROVIDERS,
        "default_models": DEFAULT_MODELS,
        "provider_models": PROVIDER_MODELS,
    }
    if provider == "anthropic":
        info["status"] = "configured" if os.getenv("ANTHROPIC_API_KEY") else "missing_api_key"
    elif provider == "openai":
        info["status"] = "configured" if os.getenv("OPENAI_API_KEY") else "missing_api_key"
    elif provider == "ollama":
        info["status"] = "configured"
        info["ollama_base_url"] = _get_ollama_url()
    return info


def update_settings(provider: str, model: str, ollama_base_url: str = "") -> dict[str, Any]:
    """Persist LLM settings to DB, Redis, and env vars.

    Redis is used to share settings with the AI orchestrator (separate process).
    """
    import json

    from apps.core.models import SystemSetting

    if provider not in SUPPORTED_PROVIDERS:
        raise ValueError(f"Unsupported provider: '{provider}'")

    config = {"provider": provider, "model": model}
    if ollama_base_url:
        config["ollama_base_url"] = ollama_base_url

    # 1. Persist to database (survives restarts)
    SystemSetting.put("llm_config", config)

    # 2. Publish to Redis (AI orchestrator reads this)
    try:
        import redis
        r = redis.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            decode_responses=True,
        )
        r.set("llm_config", json.dumps(config))
        logger.info("LLM config written to Redis")
    except Exception as exc:
        logger.warning("Failed to write LLM config to Redis: %s", exc)

    # 3. Set env vars for this Django process
    os.environ["LLM_PROVIDER"] = provider
    os.environ["LLM_MODEL"] = model
    if ollama_base_url:
        os.environ["OLLAMA_BASE_URL"] = ollama_base_url

    logger.info("LLM settings updated: provider=%s model=%s", provider, model)
    return get_provider_info()


async def chat_completion(
    messages: list[dict[str, Any]],
    system: str = "",
    provider: str | None = None,
    model: str | None = None,
    max_tokens: int = 4096,
) -> str:
    """
    Send a chat completion request to the configured LLM provider.

    Args:
        messages: List of message dicts, e.g. [{"role": "user", "content": "..."}].
        system: Optional system prompt (handled differently per provider).
        provider: Override the configured provider.
        model: Override the configured model.
        max_tokens: Maximum tokens in response.

    Returns:
        The assistant's response text.
    """
    p = (provider or _get_provider()).lower().strip()
    m = model or _get_model(p)

    if p == "anthropic":
        return await _anthropic_chat(messages, system, m, max_tokens)
    elif p == "openai":
        return await _openai_chat(messages, system, m, max_tokens)
    elif p == "ollama":
        return await _ollama_chat(messages, system, m, max_tokens)
    else:
        raise ValueError(
            f"Unsupported LLM provider: '{p}'. "
            f"Supported: {', '.join(SUPPORTED_PROVIDERS)}"
        )


# ---------------------------------------------------------------------------
# Provider implementations
# ---------------------------------------------------------------------------


async def _anthropic_chat(
    messages: list[dict], system: str, model: str, max_tokens: int
) -> str:
    import anthropic

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY is not set. Set it or switch LLM_PROVIDER to 'openai' or 'ollama'."
        )

    client = anthropic.AsyncAnthropic(api_key=api_key)
    kwargs: dict[str, Any] = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": messages,
    }
    if system:
        kwargs["system"] = system

    try:
        message = await client.messages.create(**kwargs)
        return message.content[0].text
    except anthropic.BadRequestError as exc:
        error_msg = str(exc)
        if "credit balance" in error_msg.lower() or "billing" in error_msg.lower():
            raise ValueError(
                "Anthropic API credit balance is too low. Please add credits at "
                "console.anthropic.com or switch to a different LLM provider in Settings."
            ) from exc
        raise


async def _openai_chat(
    messages: list[dict], system: str, model: str, max_tokens: int
) -> str:
    import openai  # type: ignore

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY is not set. Set it or switch LLM_PROVIDER to 'anthropic' or 'ollama'."
        )

    client = openai.AsyncOpenAI(api_key=api_key)
    all_messages = []
    if system:
        all_messages.append({"role": "system", "content": system})
    all_messages.extend(messages)

    resp = await client.chat.completions.create(
        model=model,
        messages=all_messages,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content or ""


async def _ollama_chat(
    messages: list[dict], system: str, model: str, max_tokens: int
) -> str:
    """Call Ollama via its OpenAI-compatible API endpoint."""
    import httpx

    base_url = _get_ollama_url()

    all_messages = []
    if system:
        all_messages.append({"role": "system", "content": system})
    all_messages.extend(messages)

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{base_url}/v1/chat/completions",
                json={
                    "model": model,
                    "messages": all_messages,
                    "max_tokens": max_tokens,
                    "stream": False,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"] or ""
    except httpx.ConnectError:
        raise RuntimeError(
            f"Cannot connect to Ollama at {base_url}. "
            f"Make sure Ollama is running on port 12434 and the model '{model}' is pulled. "
            f"Start Ollama and run: ollama pull {model}"
        )
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise RuntimeError(
                f"Ollama model '{model}' not found. Pull it first: ollama pull {model}"
            )
        raise
