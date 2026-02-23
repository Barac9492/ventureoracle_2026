"""Claude API client wrapper with structured outputs and rate limiting."""

import time
from typing import TypeVar

import anthropic
from pydantic import BaseModel

from ventureoracle.config import get_settings

T = TypeVar("T", bound=BaseModel)

_client = None


def get_client() -> anthropic.Anthropic:
    """Get or create the Anthropic client."""
    global _client
    if _client is None:
        settings = get_settings()
        _client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    return _client


def ask_claude(
    prompt: str,
    system: str = "",
    model: str | None = None,
    max_tokens: int | None = None,
    temperature: float = 0.7,
) -> str:
    """Send a prompt to Claude and return the text response."""
    settings = get_settings()
    client = get_client()

    msg = client.messages.create(
        model=model or settings.claude_model,
        max_tokens=max_tokens or settings.claude_max_tokens,
        system=system or "You are a helpful assistant.",
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
    )
    return msg.content[0].text


def ask_claude_json(
    prompt: str,
    system: str = "",
    model: str | None = None,
    max_tokens: int | None = None,
) -> str:
    """Send a prompt to Claude and return JSON response."""
    settings = get_settings()
    client = get_client()

    msg = client.messages.create(
        model=model or settings.claude_model,
        max_tokens=max_tokens or settings.claude_max_tokens,
        system=(system or "You are a helpful assistant.") + "\n\nRespond with valid JSON only.",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    return msg.content[0].text


def ask_claude_with_retry(
    prompt: str,
    system: str = "",
    model: str | None = None,
    max_retries: int = 3,
) -> str:
    """Send a prompt with exponential backoff on rate limit errors."""
    for attempt in range(max_retries):
        try:
            return ask_claude(prompt, system=system, model=model)
        except anthropic.RateLimitError:
            if attempt == max_retries - 1:
                raise
            wait = 2 ** (attempt + 1)
            time.sleep(wait)
    return ""  # unreachable
