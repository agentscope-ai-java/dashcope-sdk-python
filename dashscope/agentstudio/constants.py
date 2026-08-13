# -*- coding: utf-8 -*-
# Copyright (c) Alibaba, Inc. and its affiliates.
"""AgentStudio wire-protocol and configuration constants."""

import enum
import sys

import httpx

if sys.version_info >= (3, 11):
    from enum import StrEnum
else:

    class StrEnum(str, enum.Enum):  # type: ignore[no-redef]
        """Minimal StrEnum shim for Python < 3.11."""


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_HOST = "https://{workspace}.{region}.maas.aliyuncs.com"
AGENTSTUDIO_BASE_URL_TEMPLATE = _HOST + "/api/v1/agentstudio"
AGENTSTUDIO_DEFAULT_REGION = "cn-beijing"
AGENTSTUDIO_DEFAULT_TIMEOUT = httpx.Timeout(600.0, connect=10.0)
AGENTSTUDIO_MAX_RETRIES = 2


# ---------------------------------------------------------------------------
# Wire-protocol enums
# ---------------------------------------------------------------------------


class SSEEventType(StrEnum):
    """Server-sent event types (the value of ``event.type`` in SSE payloads).

    Client-sendable: MESSAGE, INTERRUPT, TOOL_CONFIRMATION,
    FUNCTION_CALL_OUTPUT, TOOL_CALL_OUTPUT, DEFINE_OUTCOME.
    Server-emitted: all types.
    """

    # Client-sendable
    MESSAGE = "message"
    INTERRUPT = "interrupt"
    TOOL_CONFIRMATION = "tool_confirmation"
    FUNCTION_CALL_OUTPUT = "function_call_output"
    TOOL_CALL_OUTPUT = "tool_call_output"
    DEFINE_OUTCOME = "define_outcome"

    # Server-emitted
    FUNCTION_CALL = "function_call"
    TOOL_CALL = "tool_call"
    REASONING = "reasoning"
    MCP_CALL = "mcp_call"
    MCP_CALL_OUTPUT = "mcp_call_output"
    THREAD_MESSAGE_SENT = "thread_message_sent"
    THREAD_MESSAGE_RECEIVED = "thread_message_received"
    THREAD_CONTEXT_COMPACTED = "thread_context_compacted"
    SESSION_STATUS = "session_status"
    ERROR = "error"
    SESSION_UPDATED = "session_updated"
    THREAD_CREATED = "thread_created"
    THREAD_STATUS = "thread_status"
    MODEL_REQUEST_START = "model_request_start"
    MODEL_REQUEST_END = "model_request_end"
    OUTCOME_EVALUATION = "outcome_evaluation"


class MessageRole(StrEnum):
    """Roles used in message/event payloads."""

    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class BlockType(StrEnum):
    """Content block types (``block.type`` values)."""

    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    DATA = "data"
    FILE = "file"
    REFUSAL = "refusal"
    ERROR = "error"


class SessionStatus(StrEnum):
    """Session run-status values (``session_status``)."""

    IDLE = "idle"
    RUNNING = "running"
    RESCHEDULING = "rescheduling"
    TERMINATED = "terminated"
