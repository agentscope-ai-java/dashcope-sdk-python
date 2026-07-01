# -*- coding: utf-8 -*-
# Copyright (c) Alibaba, Inc. and its affiliates.
"""Cursor-based pagination.

AgentStudio uses opaque cursor pagination: callers pass ``limit`` and
``page`` (a cursor token returned by the previous page in
``next_page``).
"""

from __future__ import annotations

from typing import (
    Any,
    AsyncIterator,
    Callable,
    Dict,
    Generic,
    Iterator,
    List,
    Optional,
    TypeVar,
)

T = TypeVar("T")


class CursorPage(Generic[T]):
    """Synchronous page over an opaque ``page`` cursor."""

    def __init__(
        self,
        *,
        data: List[T],
        next_page: Optional[str],
        request_id: Optional[str],
        fetch_next: Optional[Callable[[str], "CursorPage[T]"]] = None,
    ) -> None:
        self.data = data
        self.next_page = next_page
        self.request_id = request_id
        self._fetch_next = fetch_next

    def has_next(self) -> bool:
        return bool(self.next_page) and self._fetch_next is not None

    def get_next(self) -> Optional["CursorPage[T]"]:
        if not self.has_next():
            return None
        assert self._fetch_next is not None and self.next_page is not None
        return self._fetch_next(self.next_page)

    def __iter__(self) -> Iterator[T]:
        page: Optional[CursorPage[T]] = self
        while page is not None:
            for item in page.data:
                yield item
            page = page.get_next()

    def __len__(self) -> int:
        """Return the number of items on *this* page only.

        .. note::
           ``__iter__`` auto-paginates across all pages, so ``len(page)``
           may differ from ``sum(1 for _ in page)``.  Use
           ``len(page.data)`` for an explicit current-page count.
        """
        return len(self.data)


class AsyncCursorPage(Generic[T]):
    """Asynchronous page over an opaque ``page`` cursor."""

    def __init__(
        self,
        *,
        data: List[T],
        next_page: Optional[str],
        request_id: Optional[str],
        fetch_next: Optional[Callable[[str], "AsyncCursorPage[T]"]] = None,
    ) -> None:
        self.data = data
        self.next_page = next_page
        self.request_id = request_id
        self._fetch_next = fetch_next

    def has_next(self) -> bool:
        return bool(self.next_page) and self._fetch_next is not None

    async def get_next(self) -> Optional["AsyncCursorPage[T]"]:
        if not self.has_next():
            return None
        assert self._fetch_next is not None and self.next_page is not None
        result = self._fetch_next(self.next_page)
        if hasattr(result, "__await__"):
            result = await result  # type: ignore[assignment]
        return result  # type: ignore[return-value]

    def __aiter__(self) -> AsyncIterator[T]:
        return self._aiter()

    async def _aiter(self) -> AsyncIterator[T]:
        page: Optional[AsyncCursorPage[T]] = self
        while page is not None:
            for item in page.data:
                yield item
            page = await page.get_next()

    def __len__(self) -> int:
        """Return the number of items on *this* page only.

        .. note::
           ``__aiter__`` auto-paginates across all pages, so ``len(page)``
           may differ from the total number of items.  Use
           ``len(page.data)`` for an explicit current-page count.
        """
        return len(self.data)


def build_page(
    *,
    payload: Dict[str, Any],
    item_factory: Callable[[Dict[str, Any]], T],
    fetch_next: Optional[Callable[[str], Any]] = None,
    request_id: Optional[str] = None,
    page_cls: type = CursorPage,
) -> Any:
    """Hydrate a page object from a normalized payload."""

    items_raw = payload.get("data") or []
    items: List[T] = [
        item_factory(it) for it in items_raw if isinstance(it, dict)
    ]
    next_page = payload.get("next_page")
    return page_cls(
        data=items,
        next_page=next_page,
        request_id=request_id,
        fetch_next=fetch_next,
    )
