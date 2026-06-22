# -*- coding: utf-8 -*-
"""Tests for SessionToolRunner and AsyncSessionToolRunner using mocked client."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock

import pytest

from dashscope.agentstudio import Client, AsyncClient
from dashscope.agentstudio.tools import SessionToolRunner, AsyncSessionToolRunner, tool
from dashscope.agentstudio.types import (
    AgentCustomToolUseEvent,
    SessionStatusIdleEvent,
)


# ---------------------------------------------------------------------------
# Sync helpers
# ---------------------------------------------------------------------------

class _FakeStream:
    def __init__(self, events: List[Any]):
        self._events = events

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        pass

    def __iter__(self):
        return iter(self._events)

    def close(self):
        pass


def _make_client():
    return Client(api_key="test-key")


# ---------------------------------------------------------------------------
# Async helpers
# ---------------------------------------------------------------------------

class _FakeAsyncStream:
    def __init__(self, events: List[Any]):
        self._events = events

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        pass

    def __aiter__(self):
        return self._aiter()

    async def _aiter(self):
        for evt in self._events:
            yield evt

    async def aclose(self):
        pass


def _make_async_client():
    return AsyncClient(api_key="test-key")


# ---------------------------------------------------------------------------
# Sync runner tests
# ---------------------------------------------------------------------------

def test_runner_dispatches_custom_tool_and_posts_result():
    @tool
    def add(a: int, b: int) -> int:
        """Sum two integers."""
        return a + b

    server_events = [
        AgentCustomToolUseEvent(
            id="evt_1", type="tool_call",
            content=[{"type": "data", "name": "add", "custom_tool_use_id": "ctu_1", "arguments": {"a": 2, "b": 3}}],
        ),
        SessionStatusIdleEvent(
            id="evt_2", type="session_status",
            content=[{"type": "data", "data": {"session_status": "idle", "stop_reason": "end_turn"}}],
        ),
    ]

    sent: List[Dict[str, Any]] = []
    client = _make_client()
    client.sessions.events.stream = MagicMock(return_value=_FakeStream(server_events))
    client.sessions.events.send = MagicMock(side_effect=lambda sid, evts, **kw: sent.extend(evts))

    runner = SessionToolRunner(client=client, session_id="sesn_1", tools=[add], max_idle_seconds=0)
    records = list(runner)

    assert len(records) == 1
    assert records[0].name == "add"
    assert records[0].is_error is False
    assert records[0].output in ("5", 5)
    assert len(sent) == 1
    posted = sent[0]
    assert posted["type"] == "function_call_output"
    assert posted["role"] == "tool"
    assert posted["content"][0]["data"]["call_id"] == "ctu_1"


def test_runner_reports_unknown_tool_as_error():
    server_events = [
        AgentCustomToolUseEvent(
            id="evt_1", type="tool_call",
            content=[{"type": "data", "name": "missing", "custom_tool_use_id": "ctu_2", "arguments": {}}],
        ),
        SessionStatusIdleEvent(
            id="evt_2", type="session_status",
            content=[{"type": "data", "data": {"session_status": "idle", "stop_reason": "end_turn"}}],
        ),
    ]

    sent: List[Dict[str, Any]] = []
    client = _make_client()
    client.sessions.events.stream = MagicMock(return_value=_FakeStream(server_events))
    client.sessions.events.send = MagicMock(side_effect=lambda sid, evts, **kw: sent.extend(evts))

    runner = SessionToolRunner(client=client, session_id="sesn_2", tools=[], max_idle_seconds=0)
    records = list(runner)

    assert len(records) == 1
    assert records[0].is_error is True
    assert len(sent) == 1
    assert sent[0]["is_error"] is True


# ---------------------------------------------------------------------------
# Async runner tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_async_runner_dispatches_custom_tool_and_posts_result():
    @tool
    def add(a: int, b: int) -> int:
        """Sum two integers."""
        return a + b

    server_events = [
        AgentCustomToolUseEvent(
            id="evt_1", type="tool_call",
            content=[{"type": "data", "name": "add", "custom_tool_use_id": "ctu_1", "arguments": {"a": 2, "b": 3}}],
        ),
        SessionStatusIdleEvent(
            id="evt_2", type="session_status",
            content=[{"type": "data", "data": {"session_status": "idle", "stop_reason": "end_turn"}}],
        ),
    ]

    sent: List[Dict[str, Any]] = []
    client = _make_async_client()
    client.sessions.events.stream = AsyncMock(return_value=_FakeAsyncStream(server_events))
    client.sessions.events.send = AsyncMock(side_effect=lambda sid, evts, **kw: sent.extend(evts))

    runner = AsyncSessionToolRunner(client=client, session_id="sesn_1", tools=[add], max_idle_seconds=0)
    records = [record async for record in runner]

    assert len(records) == 1
    assert records[0].name == "add"
    assert records[0].is_error is False
    assert records[0].output in ("5", 5)
    assert len(sent) == 1
    posted = sent[0]
    assert posted["type"] == "function_call_output"
    assert posted["role"] == "tool"
    assert posted["content"][0]["data"]["call_id"] == "ctu_1"


@pytest.mark.asyncio
async def test_async_runner_reports_unknown_tool_as_error():
    server_events = [
        AgentCustomToolUseEvent(
            id="evt_1", type="tool_call",
            content=[{"type": "data", "name": "missing", "custom_tool_use_id": "ctu_2", "arguments": {}}],
        ),
        SessionStatusIdleEvent(
            id="evt_2", type="session_status",
            content=[{"type": "data", "data": {"session_status": "idle", "stop_reason": "end_turn"}}],
        ),
    ]

    sent: List[Dict[str, Any]] = []
    client = _make_async_client()
    client.sessions.events.stream = AsyncMock(return_value=_FakeAsyncStream(server_events))
    client.sessions.events.send = AsyncMock(side_effect=lambda sid, evts, **kw: sent.extend(evts))

    runner = AsyncSessionToolRunner(client=client, session_id="sesn_2", tools=[], max_idle_seconds=0)
    records = [record async for record in runner]

    assert len(records) == 1
    assert records[0].is_error is True
    assert len(sent) == 1
    assert sent[0]["is_error"] is True


@pytest.mark.asyncio
async def test_async_runner_parallel_send_and_stream():
    stream_opened = asyncio.Event()
    send_started = asyncio.Event()

    async def _fake_stream(*args, **kwargs):
        stream_opened.set()
        await asyncio.sleep(0.1)
        return _FakeAsyncStream([])

    async def _fake_send(*args, **kwargs):
        send_started.set()

    client = _make_async_client()
    client.sessions.events.stream = _fake_stream
    client.sessions.events.send = _fake_send

    runner = AsyncSessionToolRunner(
        client=client, session_id="sesn_3", tools=[],
        events=[{"role": "user", "type": "message", "content": [{"type": "text", "text": "hi"}]}],
        max_idle_seconds=0,
    )
    async for _ in runner:
        pass

    assert stream_opened.is_set()
    assert send_started.is_set()


@pytest.mark.asyncio
async def test_async_runner_with_events_parameter():
    captured_events: List[Any] = []

    async def _fake_stream(*args, **kwargs):
        return _FakeAsyncStream([])

    async def _fake_send(session_id, events, **kwargs):
        captured_events.extend(list(events))

    client = _make_async_client()
    client.sessions.events.stream = _fake_stream
    client.sessions.events.send = _fake_send

    runner = AsyncSessionToolRunner(
        client=client, session_id="sesn_4", tools=[],
        events=[{"role": "user", "type": "message", "content": [{"type": "text", "text": "hello"}]}],
        max_idle_seconds=0,
    )
    async for _ in runner:
        pass

    assert len(captured_events) == 1
    assert captured_events[0]["type"] == "message"