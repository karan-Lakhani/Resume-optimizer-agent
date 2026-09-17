import anthropic
from groq import Groq
from config.settings import get_settings
from src.common.logging import get_logger

logger = get_logger(__name__)


class LLMEmptyResponseError(RuntimeError):
    """Raised when a provider returns no usable text (e.g. it spent the
    whole token budget on hidden reasoning, or was truncated before writing
    any content). Callers can catch this to retry."""


def call_llm(prompt: str, system: str = "") -> str:
    """
    Send a prompt to the LLM and return the response text.
    Routes to the provider named by LLM_PROVIDER in .env.
    """
    settings = get_settings()
    logger.info("Calling LLM with provider=%s model=%s", settings.llm_provider, settings.llm_model)

    if settings.llm_provider == "anthropic":
        return _call_anthropic(settings, prompt, system)
    elif settings.llm_provider == "agentrouter":
        return _call_agentrouter(settings, prompt, system)
    elif settings.llm_provider == "groq":
        return _call_groq(settings, prompt, system)
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {settings.llm_provider!r}")


def _call_anthropic(settings, prompt: str, system: str) -> str:
    client = anthropic.Anthropic(api_key=settings.llm_api_key)

    response = client.messages.create(
        model=settings.llm_model,
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )

    result = next((block.text for block in response.content if block.type == "text"), None)
    if not result:
        raise LLMEmptyResponseError(
            f"Anthropic returned no text content (stop_reason={response.stop_reason})"
        )
    logger.info("LLM response received, length: %d chars", len(result))
    return result


def _call_agentrouter(settings, prompt: str, system: str) -> str:
    """
    AgentRouter (agentrouter.org) is a free gateway that proxies the
    Anthropic Messages API. It uses Bearer auth (auth_token), not the
    x-api-key header the direct Anthropic API expects — hence auth_token=
    here, not api_key=. Base URL must NOT include a trailing /v1.

    thinking is disabled because the routed models (e.g. deepseek-v4-flash)
    default to extended thinking and, without this, spend the entire
    max_tokens budget on the hidden thinking block, leaving no room for
    the actual answer (stop_reason "max_tokens", no text block at all).
    """
    client = anthropic.Anthropic(
        auth_token=settings.llm_api_key,
        base_url="https://agentrouter.org",
    )

    response = client.messages.create(
        model=settings.llm_model,
        max_tokens=4096,
        system=system,
        thinking={"type": "disabled"},
        messages=[{"role": "user", "content": prompt}],
    )

    result = next((block.text for block in response.content if block.type == "text"), None)
    if not result:
        raise LLMEmptyResponseError(
            f"AgentRouter returned no text content (stop_reason={response.stop_reason})"
        )
    logger.info("LLM response received, length: %d chars", len(result))
    return result


def _call_groq(settings, prompt: str, system: str) -> str:
    client = Groq(api_key=settings.llm_api_key)

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=messages,
        temperature=0.3,
        max_tokens=4096,
        reasoning_effort="low",
    )

    result = response.choices[0].message.content
    if not result:
        raise LLMEmptyResponseError(
            f"Groq returned no text content (finish_reason={response.choices[0].finish_reason})"
        )
    logger.info("LLM response received, length: %d chars", len(result))
    return result