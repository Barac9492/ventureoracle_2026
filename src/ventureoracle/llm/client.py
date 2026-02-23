import uuid
from typing import TypeVar, Optional, Union

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


def ensure_unique_tool_ids(messages: list[dict]) -> list[dict]:
    """
    Ensures that all tool_use IDs in a message history are unique.
    Maps old IDs to new UUIDs to maintain tool_use <-> tool_result linkage.
    """
    id_map = {}
    new_messages = []

    for msg in messages:
        content = msg.get("content")
        if isinstance(content, list):
            new_content = []
            for block in content:
                if block.get("type") == "tool_use":
                    old_id = block["id"]
                    new_id = f"tool_{uuid.uuid4().hex}"
                    id_map[old_id] = new_id
                    new_block = block.copy()
                    new_block["id"] = new_id
                    new_content.append(new_block)
                elif block.get("type") == "tool_result":
                    old_id = block["tool_use_id"]
                    new_id = id_map.get(old_id, old_id)
                    new_block = block.copy()
                    new_block["tool_use_id"] = new_id
                    new_content.append(new_block)
                else:
                    new_content.append(block)
            new_msg = msg.copy()
            new_msg["content"] = new_content
            new_messages.append(new_msg)
        else:
            new_messages.append(msg)

    return new_messages


def ask_claude(
    prompt: str,
    system: str = "",
    model: Optional[str] = None,
    max_tokens: Optional[int] = None,
    temperature: float = 0.7,
) -> str:
    """Send a prompt to Claude and return the text response."""
    settings = get_settings()
    client = get_client()

    msg = client.messages.create(
        model=model or settings.claude_model,
        max_tokens=max_tokens or settings.claude_max_tokens,
        system=system or "You are a helpful assistant.",
        messages=ensure_unique_tool_ids([{"role": "user", "content": prompt}]),
        temperature=temperature,
    )
    return msg.content[0].text


def ask_claude_json(
    prompt: str,
    system: str = "",
    model: Optional[str] = None,
    max_tokens: Optional[int] = None,
) -> str:
    """Send a prompt to Claude and return JSON response."""
    settings = get_settings()
    client = get_client()

    msg = client.messages.create(
        model=model or settings.claude_model,
        max_tokens=max_tokens or settings.claude_max_tokens,
        system=(system or "You are a helpful assistant.") + "\n\nRespond with valid JSON only.",
        messages=ensure_unique_tool_ids([{"role": "user", "content": prompt}]),
        temperature=0.3,
    )
    return msg.content[0].text


def ask_claude_with_retry(
    prompt: str,
    system: str = "",
    model: Optional[str] = None,
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
