# -*- coding: utf-8 -*-
# Copyright (c) Alibaba, Inc. and its affiliates.
"""SSE (Server-Sent Events) stream iterators backed by ``httpx-sse``.

The AgentStudio stream is documented as::

    event: message
    data: <json>

    : keepalive

The ``event:`` field is always the literal ``"message"`` and never used
for routing – the actual event type lives in ``data.type``. The server
does not emit ``id:`` lines; reconnection is performed via
``GET /sessions/{id}/events`` with ``created_at[gt]=...`` plus
client-side dedup by ``data.id``.

This module wraps ``httpx_sse.EventSource`` in iterator classes that
yield parsed JSON dicts for consumption by the typed event stream layer.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Dict, Iterator

import httpx
from httpx_sse import EventSource

from dashscope.agentstudio import exceptions
from dashscope.common.logging import logger


# ---------------------------------------------------------------------------
# Iterators
# ---------------------------------------------------------------------------


@dataclass
class EventStream:
    """Synchronous iterator over an SSE response backed by ``httpx-sse``.

    Emits dict payloads (the parsed ``data`` JSON of each frame). Comment
    / keepalive frames are silently skipped. The underlying response is
    closed when iteration completes or :meth:`close` is invoked.
    """

    response: httpx.Response
    _event_source: EventSource = field(init=False)
    _closed: bool = False

    def __post_init__(self) -> None:
        self._event_source = EventSource(self.response)

    def __enter__(self) -> "EventStream":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def __iter__(self) -> Iterator[Dict[str, Any]]:
        return self._iter()

    def _iter(self) -> Iterator[Dict[str, Any]]:
        if self._closed:
            raise exceptions.StreamClosedError("stream already closed")
        try:
            for sse in self._event_source.iter_sse():
                if sse.data:
                    try:
                        payload = json.loads(sse.data)
                    except json.JSONDecodeError:
                        logger.warning("SSE frame contains invalid JSON")
                        yield {"_raw": sse.data}
                        continue
                    if not payload:
                        continue
                    yield payload
        finally:
            self.close()

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        try:
            self.response.close()
        except Exception:  # pragma: no cover
            pass


@dataclass
class AsyncEventStream:
    """Async iterator over an SSE response backed by ``httpx-sse``."""

    response: httpx.Response
    _event_source: EventSource = field(init=False)
    _closed: bool = False

    def __post_init__(self) -> None:
        self._event_source = EventSource(self.response)

    async def __aenter__(self) -> "AsyncEventStream":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.aclose()

    def __aiter__(self) -> AsyncIterator[Dict[str, Any]]:
        return self._aiter()

    async def _aiter(self) -> AsyncIterator[Dict[str, Any]]:
        if self._closed:
            raise exceptions.StreamClosedError("stream already closed")
        try:
            async for sse in self._event_source.aiter_sse():
                if sse.data:
                    try:
                        payload = json.loads(sse.data)
                    except json.JSONDecodeError:
                        logger.warning("SSE frame contains invalid JSON")
                        yield {"_raw": sse.data}
                        continue
                    if not payload:
                        continue
                    yield payload
        finally:
            await self.aclose()

    async def aclose(self) -> None:
        if self._closed:
            return
        self._closed = True
        try:
            await self.response.aclose()
        except Exception:  # pragma: no cover
            pass
