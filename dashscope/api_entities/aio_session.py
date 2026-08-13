# -*- coding: utf-8 -*-
# Copyright (c) Alibaba, Inc. and its affiliates.
"""Shared aiohttp session pool with cached SSL context.

Provides connection reuse across async API calls. Each event loop gets
its own ClientSession (aiohttp sessions are loop-bound). The SSL context
is created once and shared across all sessions.
"""
import asyncio
import ssl
import threading
import weakref
from typing import Optional

import aiohttp
import certifi

_shared_ssl_context: Optional[ssl.SSLContext] = None
_aio_sessions: "weakref.WeakKeyDictionary" = weakref.WeakKeyDictionary()
_lock = threading.RLock()


def get_ssl_context() -> ssl.SSLContext:
    global _shared_ssl_context
    with _lock:
        if _shared_ssl_context is None:
            _shared_ssl_context = ssl.create_default_context(
                cafile=certifi.where(),
            )
    return _shared_ssl_context


async def get_shared_aio_session() -> aiohttp.ClientSession:
    """Return a shared aiohttp.ClientSession bound to the running event loop.

    The session is lazily created on first use and reused for all
    subsequent calls on the same event loop. Connection pooling (keep-alive)
    is handled by the underlying TCPConnector.
    """
    loop = asyncio.get_running_loop()

    with _lock:
        session = _aio_sessions.get(loop)
        if session is not None and not session.closed:
            return session

        connector = aiohttp.TCPConnector(ssl=get_ssl_context())
        session = aiohttp.ClientSession(connector=connector, trust_env=True)

        # Register finalizer to close session when it's garbage collected.
        # This prevents resource leaks even if
        # close_shared_aio_session() is not called.
        weakref.finalize(session, _sync_close_session, id(session))

        _aio_sessions[loop] = session
    return session


def _sync_close_session(session_id: int) -> None:
    """Synchronous callback when session is garbage collected.

    Note: This runs during GC, so we cannot await. We try to close
    synchronously if possible, otherwise log a warning.
    """
    try:
        loop = asyncio.get_event_loop()
        if not loop.is_closed() and not loop.is_running():
            # Loop exists and is not running, we can use it
            # Find the session in our cache
            with _lock:
                for stored_session in _aio_sessions.values():
                    if (
                        id(stored_session) == session_id
                        and not stored_session.closed
                    ):
                        try:
                            loop.run_until_complete(stored_session.close())
                        except Exception:
                            pass
                        break
    except RuntimeError:
        # No event loop available, can't close asynchronously
        pass
    except Exception:
        # Ignore errors during cleanup
        pass


async def close_shared_aio_session() -> None:
    """Close the shared session for the current event loop."""
    loop = asyncio.get_running_loop()
    with _lock:
        session = _aio_sessions.pop(loop, None)
    if session is not None and not session.closed:
        await session.close()
