"""Helpers for manual Langfuse observations on LangGraph nodes."""

from __future__ import annotations

from typing import Any

from langchain_core.messages import BaseMessage

DEFAULT_CHAT_MODEL = "gpt-4o-mini"


def lc_messages_to_trace_input(
    messages: list[BaseMessage],
    *,
    limit: int = 30,
    content_chars: int = 4000,
) -> list[dict[str, Any]]:
    """Compact message list for Langfuse generation/span input (size-bounded)."""
    out: list[dict[str, Any]] = []
    for m in messages[-limit:]:
        role = getattr(m, "type", "unknown")
        content: Any = getattr(m, "content", "")
        if isinstance(content, str):
            text = content[:content_chars]
        else:
            text = str(content)[:content_chars]
        out.append({"role": role, "content": text})
    return out


def trace_usage_from_message(msg: Any) -> dict[str, Any] | None:
    """Map LangChain / OpenAI response_metadata to Langfuse usage_details."""
    meta = getattr(msg, "response_metadata", None) or {}
    usage = meta.get("token_usage") or meta.get("usage")
    if not isinstance(usage, dict):
        return None
    details: dict[str, Any] = {}
    if "prompt_tokens" in usage:
        details["input_tokens"] = usage["prompt_tokens"]
    elif "input_tokens" in usage:
        details["input_tokens"] = usage["input_tokens"]
    if "completion_tokens" in usage:
        details["output_tokens"] = usage["completion_tokens"]
    elif "output_tokens" in usage:
        details["output_tokens"] = usage["output_tokens"]
    return details or None
