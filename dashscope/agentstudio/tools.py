# -*- coding: utf-8 -*-
# Copyright (c) Alibaba, Inc. and its affiliates.
"""@tool decorator, ToolSpec, and session tool runners."""

from __future__ import annotations

import inspect
import json
import re
import threading
import time
import typing
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import (
    Any,
    Callable,
    Dict,
    AsyncIterator,
    Iterator,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Union,
    get_args,
    get_origin,
)

from dashscope.agentstudio.types import (
    user_custom_tool_result,
    AgentCustomToolUseEvent,
)
from dashscope.agentstudio.constants import SSEEventType, SessionStatus
from dashscope.common.logging import logger

# ---------------------------------------------------------------------------
# Schema helpers
# ---------------------------------------------------------------------------

_PRIMITIVE_MAP: Dict[Any, str] = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    list: "array",
    dict: "object",
    type(None): "null",
}


def _python_type_to_schema(py_type: Any) -> Dict[str, Any]:
    if py_type is inspect.Parameter.empty or py_type is Any:
        return {}
    origin = get_origin(py_type)
    if origin is Union:
        non_none = [a for a in get_args(py_type) if a is not type(None)]
        if len(non_none) == 1:
            return _python_type_to_schema(non_none[0])
        return {"oneOf": [_python_type_to_schema(a) for a in non_none]}
    if origin in (list, List):
        args = get_args(py_type)
        if args:
            return {"type": "array", "items": _python_type_to_schema(args[0])}
        return {"type": "array"}
    if origin in (dict, Dict):
        return {"type": "object"}
    mapped = _PRIMITIVE_MAP.get(py_type)
    if mapped is not None:
        return {"type": mapped}
    return {"type": "object"}


def _parse_docstring(doc: str) -> Tuple[str, Dict[str, str]]:
    """Split a docstring into (summary, {param: description})."""
    if not doc:
        return "", {}
    raw = inspect.cleandoc(doc)
    lines = raw.splitlines()
    descs: Dict[str, str] = {}

    # Sphinx / NumPy ``:param name:`` style
    summary_end = len(lines)
    sphinx_re = re.compile(r"^:param\s+([a-zA-Z_][\w]*)\s*:\s*(.*)$")
    current: Optional[str] = None
    for idx, line in enumerate(lines):
        m = sphinx_re.match(line)
        if m:
            if current is None:
                summary_end = min(summary_end, idx)
            current = m.group(1)
            descs[current] = m.group(2).strip()
        elif current and line.startswith((" ", "\t")) and line.strip():
            descs[current] = (descs[current] + " " + line.strip()).strip()
        elif line.strip() == "" and current:
            current = None
    if descs:
        return "\n".join(lines[:summary_end]).strip(), descs

    # Google / Napoleon ``Args:`` style
    section_re = re.compile(r"^\s*(Args|Arguments|Parameters)\s*:\s*$", flags=re.IGNORECASE)
    section_idx: Optional[int] = None
    for idx, line in enumerate(lines):
        if section_re.match(line):
            section_idx = idx
            break
    if section_idx is None:
        return raw.strip(), {}

    summary = "\n".join(lines[:section_idx]).strip()
    entry_re = re.compile(r"^\s+([a-zA-Z_][\w]*)\s*(?:\([^)]*\))?\s*:\s*(.*)$")
    current = None
    for line in lines[section_idx + 1 :]:
        if not line.strip():
            current = None
            continue
        if re.match(r"^\S+\s*:\s*$", line):
            break
        m = entry_re.match(line)
        if m:
            current = m.group(1)
            descs[current] = m.group(2).strip()
        elif current and line.startswith((" ", "\t")):
            descs[current] = (descs[current] + " " + line.strip()).strip()
    return summary, descs


# ---------------------------------------------------------------------------
# ToolSpec
# ---------------------------------------------------------------------------

@dataclass
class ToolSpec:
    """Server-facing description of a client-executed tool."""

    name: str
    description: str
    func: Optional[Callable[..., Any]] = None
    is_async: bool = False
    parameters: Dict[str, Any] = field(default_factory=dict)

    def to_descriptor(self) -> Dict[str, Any]:
        """Serialize to the wire format for ``POST /agents``.

        The BMA backend does not accept a ``type`` field for custom tools,
        so we omit it (only ``name``, ``description``, ``input_schema``).
        """
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.parameters,
        }

    @classmethod
    def from_dict(
        cls,
        descriptor: Mapping[str, Any],
        *,
        func: Optional[Callable[..., Any]] = None,
    ) -> "ToolSpec":
        """Construct from a hand-written descriptor."""
        if "name" not in descriptor or "input_schema" not in descriptor:
            raise ValueError("ToolSpec.from_dict requires at least 'name' and 'input_schema'")
        return cls(
            name=str(descriptor["name"]),
            description=str(descriptor.get("description", "")),
            func=func,
            is_async=inspect.iscoroutinefunction(func) if func else False,
            parameters=dict(descriptor["input_schema"]),
        )


def tool(
    _func: Optional[Callable[..., Any]] = None,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
) -> Any:
    """Decorate a callable to expose it as a custom tool."""

    def _wrap(func: Callable[..., Any]) -> Callable[..., Any]:
        sig = inspect.signature(func)
        type_hints = typing.get_type_hints(func)
        summary, param_docs = _parse_docstring(inspect.getdoc(func) or "")
        properties: Dict[str, Any] = {}
        required: List[str] = []
        for pname, param in sig.parameters.items():
            if pname in ("self", "cls"):
                continue
            if param.kind in (
                inspect.Parameter.VAR_POSITIONAL,
                inspect.Parameter.VAR_KEYWORD,
            ):
                continue
            schema = _python_type_to_schema(type_hints.get(pname, param.annotation))
            schema = dict(schema or {"type": "string"})
            doc = param_docs.get(pname)
            if doc:
                schema["description"] = doc
            if param.default is not inspect.Parameter.empty:
                # Include default=None in schema so the API knows it is optional
                schema["default"] = param.default
            properties[pname] = schema
            if param.default is inspect.Parameter.empty:
                required.append(pname)
        spec = ToolSpec(
            name=name or func.__name__,
            description=description or summary,
            func=func,
            is_async=inspect.iscoroutinefunction(func),
            parameters={
                "type": "object",
                "properties": properties,
                "required": required,
                "additionalProperties": False,
            },
        )
        func.__tool_spec__ = spec  # type: ignore[attr-defined]
        return func

    if _func is not None and callable(_func):
        return _wrap(_func)
    return _wrap


def tool_from_spec(
    descriptor: Mapping[str, Any],
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator factory that binds a hand-written descriptor to a callable."""

    def _wrap(func: Callable[..., Any]) -> Callable[..., Any]:
        spec = ToolSpec.from_dict(descriptor, func=func)
        func.__tool_spec__ = spec  # type: ignore[attr-defined]
        return func

    return _wrap


def collect_specs(items: Any) -> List[ToolSpec]:
    """Resolve ``@tool``-decorated callables into a list of ToolSpec."""
    specs: List[ToolSpec] = []
    for it in items:
        spec = getattr(it, "__tool_spec__", None)
        if isinstance(spec, ToolSpec):
            specs.append(spec)
        elif isinstance(it, ToolSpec):
            specs.append(it)
        elif isinstance(it, Mapping):
            specs.append(ToolSpec.from_dict(it))
        elif callable(it):
            wrapped = tool(it)
            specs.append(getattr(wrapped, "__tool_spec__"))
        else:
            raise TypeError(f"Unsupported tool entry: {it!r}")
    return specs


# ---------------------------------------------------------------------------
# Runners
# ---------------------------------------------------------------------------

@dataclass
class DispatchedTool:
    """Bookkeeping record emitted by a runner."""

    name: str
    custom_tool_use_id: str
    arguments: Dict[str, Any]
    output: Any
    is_error: bool
    duration_ms: int


def _coerce_args(raw: Any) -> Dict[str, Any]:
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            raise ValueError(
                f"Tool arguments must be valid JSON, got: {raw!r}"
            ) from None
    return raw or {}


def _extract_tool_call(event: AgentCustomToolUseEvent) -> Optional[Dict[str, Any]]:
    content = event.content or []
    for block in content:
        block_dict = block.to_dict() if hasattr(block, "to_dict") else dict(block)
        # function_call events: data is nested inside a "data" key
        inner = block_dict.get("data") or {}
        if isinstance(inner, dict) and inner.get("name") and inner.get("call_id"):
            return {
                "name": inner["name"],
                "custom_tool_use_id": inner["call_id"],
                "arguments": _coerce_args(inner.get("arguments")),
            }
        if "name" in block_dict and (
            "custom_tool_use_id" in block_dict or "tool_use_id" in block_dict
        ):
            return {
                "name": block_dict["name"],
                "custom_tool_use_id": block_dict.get("custom_tool_use_id")
                or block_dict.get("tool_use_id"),
                "arguments": _coerce_args(block_dict.get("arguments") or block_dict.get("input")),
            }
    meta = event.metadata or {}
    if isinstance(meta, dict) and meta.get("name") and meta.get("custom_tool_use_id"):
        return {
            "name": meta["name"],
            "custom_tool_use_id": meta["custom_tool_use_id"],
            "arguments": _coerce_args(meta.get("arguments")),
        }
    return None


def _format_output(value: Any) -> Any:
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, ensure_ascii=False)
    except TypeError:
        return repr(value)


def _extract_session_status(event: Any) -> Optional[str]:
    """Extract session_status string from a session_status event.

    The status lives in ``content[0].data.session_status``.  Returns ``None``
    when the event does not carry the expected structure.
    """
    content = event.content or []
    for block in content:
        block_dict = block.to_dict() if hasattr(block, "to_dict") else dict(block)
        data = block_dict.get("data")
        if isinstance(data, dict):
            return data.get("session_status")
    return None


class SessionToolRunner:
    """Sync runner; iterate to receive :class:`DispatchedTool` records."""

    def __init__(
        self,
        *,
        client: Any,
        session_id: str,
        tools: Sequence[Any],
        events: Optional[Sequence[Any]] = None,
        max_idle_seconds: int = 300,
        max_concurrent: int = 4,
    ) -> None:
        self._client = client
        self._session_id = session_id
        self._specs: Dict[str, ToolSpec] = {
            spec.name: spec for spec in collect_specs(tools)
        }
        self._events = events
        self._max_idle = max_idle_seconds
        self._executor = ThreadPoolExecutor(
            max_workers=max(1, int(max_concurrent)),
            thread_name_prefix="agentstudio-tool",
        )
        self._stopped = False
        self._last_activity = time.monotonic()
        self._lock = threading.Lock()

    def __enter__(self) -> "SessionToolRunner":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def close(self) -> None:
        if self._stopped:
            return
        self._stopped = True
        self._executor.shutdown(wait=False)

    def __iter__(self) -> Iterator[DispatchedTool]:
        return self.run()

    def run(self) -> Iterator[DispatchedTool]:
        """Stream events and yield each completed tool dispatch.

        If ``events`` were provided at construction time, they are sent
        before opening the stream.  The server immediately returns HTTP
        headers on the SSE connection, so the stream can be opened after
        sending without blocking.

        Tool functions are submitted to a ``ThreadPoolExecutor`` so that
        multiple tools can execute concurrently while the event stream
        continues to be consumed.
        """
        from concurrent.futures import Future

        pending: Dict[Future, Dict[str, Any]] = {}

        # Send events first (server now flushes headers immediately).
        if self._events:
            self._client.sessions.events.send(
                self._session_id, events=self._events,
            )
            self._events = None

        try:
            with self._client.sessions.events.stream(
                self._session_id,
                timeout=self._max_idle,
            ) as stream:
                for event in stream:
                    if event.type in (SSEEventType.TOOL_CALL, SSEEventType.FUNCTION_CALL):
                        self._last_activity = time.monotonic()
                        call = _extract_tool_call(event)
                        if call is None:
                            logger.warning("custom_tool_use without identifiable name/id; skipping")
                            continue
                        future = self._executor.submit(self._dispatch_call, call)
                        pending[future] = call
                    elif event.type == SSEEventType.SESSION_STATUS:
                        session_status = _extract_session_status(event)
                        if session_status in (SessionStatus.IDLE, SessionStatus.TERMINATED):
                            yield from self._drain(pending)
                            if session_status == SessionStatus.TERMINATED:
                                return
                            if self._idle_exceeded():
                                logger.debug("session idle for too long, stopping runner")
                                return
                            return
                    yield from self._harvest(pending)
        finally:
            self.close()

    def _harvest(self, pending: Dict) -> Iterator[DispatchedTool]:
        """Yield records for any futures that have completed so far."""
        from concurrent.futures import Future

        done = [f for f in list(pending) if f.done()]
        for future in done:
            pending.pop(future)
            try:
                record = future.result()
            except Exception:  # pragma: no cover
                logger.exception("tool dispatch future raised")
                continue
            if record is not None:
                yield record

    def _drain(self, pending: Dict) -> Iterator[DispatchedTool]:
        """Block until all pending futures complete and yield their records."""
        from concurrent.futures import wait, FIRST_COMPLETED

        while pending:
            done_set, _ = wait(list(pending), return_when=FIRST_COMPLETED)
            for future in done_set:
                pending.pop(future, None)
                try:
                    record = future.result()
                except Exception:  # pragma: no cover
                    logger.exception("tool dispatch future raised")
                    continue
                if record is not None:
                    yield record

    def _idle_exceeded(self) -> bool:
        return (time.monotonic() - self._last_activity) >= self._max_idle

    def _dispatch(self, event: Any) -> Optional[DispatchedTool]:
        """Legacy single-dispatch entry point (kept for backward compat)."""
        call = _extract_tool_call(event)
        if call is None:
            return None
        return self._dispatch_call(call)

    def _dispatch_call(self, call: Dict[str, Any]) -> Optional[DispatchedTool]:
        """Execute a single tool call extracted from *call* dict."""
        name = call["name"]
        spec = self._specs.get(name)
        if spec is None:
            self._post_result(
                custom_tool_use_id=call["custom_tool_use_id"],
                output=f"Tool '{name}' not registered with this runner.",
                is_error=True,
            )
            return DispatchedTool(
                name=name,
                custom_tool_use_id=call["custom_tool_use_id"],
                arguments=call["arguments"],
                output=None,
                is_error=True,
                duration_ms=0,
            )

        started = time.monotonic()
        try:
            if spec.func is None:
                result = f"Tool '{name}' is a descriptor-only tool (no callable registered)"
                is_error = True
            else:
                result = spec.func(**call["arguments"])
                is_error = False
        except Exception as exc:  # noqa: BLE001
            logger.exception("tool %r raised", name)
            result = f"{type(exc).__name__}: {exc}"
            is_error = True
        duration_ms = int((time.monotonic() - started) * 1000)

        formatted = _format_output(result)
        self._post_result(
            custom_tool_use_id=call["custom_tool_use_id"],
            output=formatted,
            is_error=is_error,
        )
        return DispatchedTool(
            name=name,
            custom_tool_use_id=call["custom_tool_use_id"],
            arguments=call["arguments"],
            output=formatted,
            is_error=is_error,
            duration_ms=duration_ms,
        )

    def _post_result(self, *, custom_tool_use_id: str, output: Any, is_error: bool) -> None:
        evt = user_custom_tool_result(
            custom_tool_use_id=custom_tool_use_id,
            content=output,
            is_error=is_error,
        )
        try:
            self._client.sessions.events.send(
                self._session_id, [evt],
            )
        except Exception:  # pragma: no cover
            logger.exception("failed to post tool result")


class AsyncSessionToolRunner:
    """Async counterpart of :class:`SessionToolRunner`."""

    def __init__(
        self,
        *,
        client: Any,
        session_id: str,
        tools: Sequence[Any],
        events: Optional[Sequence[Any]] = None,
        max_idle_seconds: int = 300,
        max_concurrent: int = 4,
    ) -> None:
        self._client = client
        self._session_id = session_id
        self._specs: Dict[str, ToolSpec] = {
            spec.name: spec for spec in collect_specs(tools)
        }
        self._events = events
        self._max_idle = max_idle_seconds
        self._max_concurrent = max(1, int(max_concurrent))
        self._pending_tasks: set = set()

    async def __aenter__(self) -> "AsyncSessionToolRunner":
        return self

    async def __aexit__(self, *exc) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        """Cancel any pending tool dispatch tasks."""
        for task in self._pending_tasks:
            task.cancel()
        self._pending_tasks.clear()

    def __aiter__(self):
        return self.run()

    async def run(self) -> AsyncIterator[DispatchedTool]:
        """Async generator yielding :class:`DispatchedTool` records.

        If ``events`` were provided at construction time, they are sent
        before opening the stream.  The server immediately returns HTTP
        headers on the SSE connection, so the stream can be opened after
        sending without blocking.

        Tool dispatches are spawned as ``asyncio.Task`` objects so that
        multiple tools can execute concurrently while the event stream
        continues to be consumed.  A semaphore bounds the number of
        concurrent dispatches to ``max_concurrent``.
        """
        import asyncio

        loop = asyncio.get_running_loop()
        last_activity = loop.time()
        sem = asyncio.Semaphore(self._max_concurrent)
        self._pending_tasks.clear()

        async def _guarded_dispatch(call: Dict[str, Any]) -> Optional[DispatchedTool]:
            async with sem:
                return await self._dispatch_call(call)

        # Send events first (server now flushes headers immediately).
        if self._events:
            await self._client.sessions.events.send(
                self._session_id, events=self._events,
            )
            self._events = None

        async with await self._client.sessions.events.stream(
            self._session_id,
            timeout=self._max_idle,
        ) as stream:
            async for event in stream:
                if event.type in (SSEEventType.TOOL_CALL, SSEEventType.FUNCTION_CALL):
                    last_activity = loop.time()
                    call = _extract_tool_call(event)
                    if call is None:
                        continue
                    task = asyncio.create_task(_guarded_dispatch(call))
                    self._pending_tasks.add(task)
                elif event.type == SSEEventType.SESSION_STATUS:
                    session_status = _extract_session_status(event)
                    if session_status in (SessionStatus.IDLE, SessionStatus.TERMINATED):
                        # Drain pending tasks before exiting.
                        async for record in self._drain(self._pending_tasks):
                            yield record
                        if session_status == SessionStatus.TERMINATED:
                            return
                        if loop.time() - last_activity >= self._max_idle:
                            return
                        return
                # Yield completed dispatches (non-blocking).
                async for record in self._harvest(self._pending_tasks):
                    yield record

    async def _harvest(self, pending: set) -> AsyncIterator[DispatchedTool]:
        """Yield records for any tasks that have completed so far."""
        done = {t for t in pending if t.done()}
        for task in done:
            pending.discard(task)
            try:
                record = task.result()
            except Exception:  # pragma: no cover
                logger.exception("tool dispatch task raised")
                continue
            if record is not None:
                yield record

    async def _drain(self, pending: set) -> AsyncIterator[DispatchedTool]:
        """Wait for all pending tasks to complete and yield their records."""
        import asyncio

        while pending:
            done, still_pending = await asyncio.wait(
                pending, return_when=asyncio.FIRST_COMPLETED,
            )
            for task in done:
                pending.discard(task)
                try:
                    record = task.result()
                except Exception:  # pragma: no cover
                    logger.exception("tool dispatch task raised")
                    continue
                if record is not None:
                    yield record

    async def _dispatch(self, event: Any) -> Optional[DispatchedTool]:
        """Legacy single-dispatch entry point (kept for backward compat)."""
        call = _extract_tool_call(event)
        if call is None:
            return None
        return await self._dispatch_call(call)

    async def _dispatch_call(self, call: Dict[str, Any]) -> Optional[DispatchedTool]:
        import asyncio

        spec = self._specs.get(call["name"])
        if spec is None:
            await self._post_result(
                call["custom_tool_use_id"],
                output=f"Tool '{call['name']}' not registered with this runner.",
                is_error=True,
            )
            return DispatchedTool(
                name=call["name"],
                custom_tool_use_id=call["custom_tool_use_id"],
                arguments=call["arguments"],
                output=None,
                is_error=True,
                duration_ms=0,
            )

        loop = asyncio.get_running_loop()
        started = loop.time()
        try:
            if spec.func is None:
                result = f"Tool '{call['name']}' is a descriptor-only tool (no callable registered)"
                is_error = True
            elif spec.is_async:
                result = await spec.func(**call["arguments"])
                is_error = False
            else:
                result = await loop.run_in_executor(
                    None, lambda: spec.func(**call["arguments"])
                )
                is_error = False
        except Exception as exc:  # noqa: BLE001
            logger.exception("tool %r raised", call["name"])
            result = f"{type(exc).__name__}: {exc}"
            is_error = True
        duration_ms = int((loop.time() - started) * 1000)
        formatted = _format_output(result)
        await self._post_result(
            call["custom_tool_use_id"], output=formatted, is_error=is_error
        )
        return DispatchedTool(
            name=call["name"],
            custom_tool_use_id=call["custom_tool_use_id"],
            arguments=call["arguments"],
            output=formatted,
            is_error=is_error,
            duration_ms=duration_ms,
        )

    async def _post_result(
        self, custom_tool_use_id: str, *, output: Any, is_error: bool
    ) -> None:
        evt = user_custom_tool_result(
            custom_tool_use_id=custom_tool_use_id,
            content=output,
            is_error=is_error,
        )
        try:
            await self._client.sessions.events.send(
                self._session_id, [evt],
            )
        except Exception:  # pragma: no cover
            logger.exception("failed to post tool result")
