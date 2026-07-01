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

A wall-clock ``idle_timeout`` (default 300 s) guards against the server
silently dropping business events while still sending ``: keepalive``
frames — ``httpx``'s read timeout gets reset by every keepalive, so
without an application-level watchdog the iterator would block forever.
When no business event arrives for ``idle_timeout`` seconds, the
underlying response is forcibly closed so ``iter_sse()`` unblocks.
"""

from __future__ import annotations

import asyncio
import json
import threading
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Dict, Iterator, Optional

import httpx
from httpx_sse import EventSource

from dashscope.agentstudio import exceptions
from dashscope.common.logging import logger

_DEFAULT_IDLE_TIMEOUT = 300.0


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
    idle_timeout: Optional[float] = _DEFAULT_IDLE_TIMEOUT
    _event_source: EventSource = field(init=False)
    _closed: bool = False
    _timer: Optional[threading.Timer] = field(init=False, default=None)

    def __post_init__(self) -> None:
        self._event_source = EventSource(self.response)
        self._arm_timer()

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
                self._arm_timer()
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

    def _arm_timer(self) -> None:
        """Schedule a watchdog that closes the response on idle."""
        self._disarm_timer()
        if not self.idle_timeout or self._closed:
            return
        self._timer = threading.Timer(
            self.idle_timeout,
            self._on_idle_timeout,
        )
        self._timer.daemon = True
        self._timer.start()

    def _disarm_timer(self) -> None:
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None

    def _on_idle_timeout(self) -> None:
        logger.warning(
            "SSE stream idle for %ss, closing response",
            self.idle_timeout,
        )
        try:
            self.response.close()
        except Exception:  # pragma: no cover
            pass

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._disarm_timer()
        try:
            self.response.close()
        except Exception:  # pragma: no cover
            pass


@dataclass
class AsyncEventStream:
    """Async iterator over an SSE response backed by ``httpx-sse``."""

    response: httpx.Response
    idle_timeout: Optional[float] = _DEFAULT_IDLE_TIMEOUT
    _event_source: EventSource = field(init=False)
    _closed: bool = False
    _watcher: Optional[asyncio.Task] = field(init=False, default=None)

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
        self._arm_watcher()
        try:
            async for sse in self._event_source.aiter_sse():
                self._arm_watcher()
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

    def _arm_watcher(self) -> None:
        """(Re)schedule an asyncio watchdog that closes on idle."""
        self._disarm_watcher()
        if not self.idle_timeout or self._closed:
            return
        try:
            self._watcher = asyncio.create_task(self._watch_idle())
        except RuntimeError:
            # No running loop — caller is not in async context.
            self._watcher = None

    def _disarm_watcher(self) -> None:
        if self._watcher is not None:
            self._watcher.cancel()
            self._watcher = None

    async def _watch_idle(self) -> None:
        assert self.idle_timeout is not None
        await asyncio.sleep(self.idle_timeout)
        if self._closed:
            return
        logger.warning(
            "SSE stream idle for %ss, closing response",
            self.idle_timeout,
        )
        try:
            await self.response.aclose()
        except Exception:  # pragma: no cover
            pass

    async def aclose(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._disarm_watcher()
        try:
            await self.response.aclose()
        except Exception:  # pragma: no cover
            pass
