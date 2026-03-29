"""
Centralized LLM provider for Django backend services.

Provides async chat completion using the configured LLM provider,
without requiring LangChain. Supports:

  - **anthropic**: Anthropic Claude API (default)
  - **openai**: OpenAI ChatGPT API
  - **ollama**: Local Ollama instance (OpenAI-compatible API)

Configuration via environment variables:
    LLM_PROVIDER, LLM_MODEL, ANTHROPIC_API_KEY, OPENAI_API_KEY, OLLAMA_BASE_URL
"""

import logging
import os
from typing import Any

logger = logging.getLogger("ai_deal_manager.core.llm_provider")

SUPPORTED_PROVIDERS = ["anthropic", "openai", "ollama"]

_DEFAULT_MODELS: dict[str, str] = {
    "anthropic": "claude-sonnet-4-6",
    "openai": "gpt-4o",
    "ollama": "deepseek-r1:7b",
}


def _get_provider() -> str:
    return os.getenv("LLM_PROVIDER", "anthropic").lower().strip()


def _get_model(provider: str | None = None) -> str:
    model = os.getenv("LLM_MODEL", "")
    if model:
        return model
    p = provider or _get_provider()
    return _DEFAULT_MODELS.get(p, "claude-sonnet-4-6")


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
        provider: Override LLM_PROVIDER env var.
        model: Override LLM_MODEL env var.
        max_tokens: Maximum tokens in response.

    Returns:
        The assistant's response text.

    Raises:
        ValueError: If provider is not supported or API key is missing.
        Exception: If the API call fails.
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


def get_provider_info() -> dict[str, Any]:
    """Return current LLM configuration status."""
    provider = _get_provider()
    model = _get_model(provider)
    info: dict[str, Any] = {
        "provider": provider,
        "model": model,
        "supported_providers": SUPPORTED_PROVIDERS,
    }
    if provider == "anthropic":
        info["status"] = "configured" if os.getenv("ANTHROPIC_API_KEY") else "missing_api_key"
    elif provider == "openai":
        info["status"] = "configured" if os.getenv("OPENAI_API_KEY") else "missing_api_key"
    elif provider == "ollama":
        info["status"] = "configured"
        info["ollama_base_url"] = os.getenv("OLLAMA_BASE_URL", "http://localhost:12434")
    return info


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

    message = await client.messages.create(**kwargs)
    return message.content[0].text


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

    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:12434")

    all_messages = []
    if system:
        all_messages.append({"role": "system", "content": system})
    all_messages.extend(messages)

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
