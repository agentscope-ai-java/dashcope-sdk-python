"""Chat / completion / DashScope response → GenAI InputMessage / OutputMessage conversion."""

from __future__ import annotations

import json
from typing import Any, List

from dashscope.finetune.reinforcement.component.observability.genai._core import (
    GENAI_AVAILABLE,
    InputMessage,
    OutputMessage,
    Text,
    ToolCall,
)


def unwrap_openai_completion(completion: Any) -> Any:
    """Best-effort unwrap OpenAI-compatible completion containers.

    Some clients return wrapper response objects (e.g. LegacyAPIResponse) where
    the parsed payload lives on `.parsed` or behind `.parse()`.
    """
    try:
        if completion is None:
            return None
        if isinstance(completion, dict):
            return completion
        if getattr(completion, "choices", None) is not None:
            return completion
        parsed = getattr(completion, "parsed", None)
        if parsed is not None:
            return parsed
        parse_fn = getattr(completion, "parse", None)
        if callable(parse_fn):
            return parse_fn()
        return completion
    except Exception:
        return completion


def tool_calls_to_parts(tool_calls: Any) -> List[Any]:
    """Convert common ``tool_calls`` structures found on OpenAI and DashScope messages to ``ToolCall`` parts."""
    if not tool_calls or not GENAI_AVAILABLE:
        return []
    parts: List[Any] = []
    for tc in tool_calls:
        fn = getattr(tc, "function", None)
        if fn is None and isinstance(tc, dict):
            fn = tc.get("function")
        name = ""
        args = "{}"
        tid = None
        if fn is not None:
            name = getattr(fn, "name", "") or (fn.get("name") if isinstance(fn, dict) else "")
            args = getattr(fn, "arguments", "{}") or (
                fn.get("arguments", "{}") if isinstance(fn, dict) else "{}"
            )
        else:
            name = getattr(tc, "name", "") or (tc.get("name") if isinstance(tc, dict) else "")
        tid = getattr(tc, "id", None) if not isinstance(tc, dict) else tc.get("id")
        parts.append(
            ToolCall(
                name=name or "tool",
                arguments=args,
                id=tid,
            )
        )
    return parts


def openai_chat_messages_to_input_messages(messages: Any) -> List[Any]:
    """Convert an OpenAI-style ``messages`` list to a list of ``InputMessage`` objects.

    Handles both dict-based messages (``{"role": ..., "content": ...}``) and
    object-based messages (attributes ``role`` / ``content``).  Multi-part content
    lists are JSON-serialised into a single ``Text`` part.
    """
    if not messages:
        return []
    out: List[Any] = []
    for m in messages:
        if isinstance(m, dict):
            role = m.get("role") or "user"
            content = m.get("content")
        else:
            role = getattr(m, "role", "user")
            content = getattr(m, "content", None)
        parts: List[Any] = []
        if content is None:
            parts.append(Text(content=""))
        elif isinstance(content, str):
            parts.append(Text(content=content))
        elif isinstance(content, list):
            parts.append(Text(content=json.dumps(content, ensure_ascii=False, default=str)))
        else:
            parts.append(Text(content=str(content)))
        out.append(InputMessage(role=role, parts=parts))
    return out


def openai_completion_to_output_messages(completion: Any) -> List[Any]:
    """Convert an OpenAI ``ChatCompletion`` response to a list of ``OutputMessage`` objects.

    Each choice becomes one ``OutputMessage``.  Both text content and ``tool_calls``
    are extracted; an empty ``Text`` part is appended when a choice has neither.
    """
    completion = unwrap_openai_completion(completion)

    # OpenAI-compatible SDKs sometimes return plain dicts (e.g. http clients or
    # wrappers). Handle both object- and dict-shaped responses.
    if isinstance(completion, dict):
        choices = completion.get("choices") or []
    else:
        choices = getattr(completion, "choices", None) or []
    if not choices:
        return []
    result: List[Any] = []
    for ch in choices:
        if isinstance(ch, dict):
            msg = ch.get("message")
            finish = ch.get("finish_reason") or "stop"
        else:
            msg = getattr(ch, "message", None)
            finish = getattr(ch, "finish_reason", None) or "stop"

        if isinstance(msg, dict):
            role = msg.get("role") or "assistant"
        else:
            role = getattr(msg, "role", "assistant") if msg is not None else "assistant"
        parts: List[Any] = []
        if msg is not None:
            if isinstance(msg, dict):
                content = msg.get("content")
            else:
                content = getattr(msg, "content", None)
            if content:
                parts.append(
                    Text(content=content if isinstance(content, str) else str(content))
                )
            if isinstance(msg, dict):
                tool_calls = msg.get("tool_calls")
            else:
                tool_calls = getattr(msg, "tool_calls", None)
            if tool_calls:
                parts.extend(tool_calls_to_parts(tool_calls))
        if not parts:
            parts.append(Text(content=""))
        result.append(OutputMessage(role=role, parts=parts, finish_reason=finish))
    return result


def dashscope_response_to_output_messages(response: Any) -> List[Any]:
    """Convert a non-streaming ``GenerationResponse`` from ``Generation.call`` to a list of ``OutputMessage`` objects."""
    if not GENAI_AVAILABLE:
        return []
    output = getattr(response, "output", None)
    if output is None:
        return []
    choices = getattr(output, "choices", None)
    if choices:
        result: List[Any] = []
        for ch in choices:
            finish = getattr(ch, "finish_reason", None) or "stop"
            msg = getattr(ch, "message", None)
            role = "assistant"
            parts: List[Any] = []
            if msg is not None:
                if isinstance(msg, dict):
                    role = msg.get("role") or "assistant"
                    content = msg.get("content")
                    tool_calls = msg.get("tool_calls")
                else:
                    role = getattr(msg, "role", None) or "assistant"
                    content = getattr(msg, "content", None)
                    tool_calls = getattr(msg, "tool_calls", None)
                if content:
                    parts.append(
                        Text(content=content if isinstance(content, str) else str(content))
                    )
                if tool_calls:
                    parts.extend(tool_calls_to_parts(tool_calls))
            if not parts:
                parts.append(Text(content=""))
            result.append(OutputMessage(role=role, parts=parts, finish_reason=finish))
        return result
    text = getattr(output, "text", None)
    if text:
        return [
            OutputMessage(
                role="assistant",
                parts=[Text(content=text if isinstance(text, str) else str(text))],
                finish_reason="stop",
            )
        ]
    return []
