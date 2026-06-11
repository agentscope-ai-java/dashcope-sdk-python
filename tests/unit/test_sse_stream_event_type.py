# -*- coding: utf-8 -*-
# Copyright (c) Alibaba, Inc. and its affiliates.
# pylint: disable=protected-access

from http import HTTPStatus

import pytest

from dashscope.api_entities.aiohttp_request import AioHttpRequest
from dashscope.client.base_api import StreamEventMixin
from dashscope.common.utils import _handle_aio_stream, _handle_stream


class FakeSyncSseResponse:
    status_code = HTTPStatus.OK
    headers = {}

    def iter_lines(self):
        return iter(
            [
                b"event: done",
                b"data: ignored",
                b"\n",
                b"data: delivered",
            ],
        )


class FakeAsyncSseContent:
    def __init__(self):
        self.lines = iter(
            [
                b"event: done",
                b"data: ignored",
                b"\n",
                b"data: delivered",
            ],
        )

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self.lines)
        except StopIteration as stop_iteration:
            raise StopAsyncIteration from stop_iteration


class FakeAsyncSseResponse:
    status = HTTPStatus.OK
    headers = {}

    def __init__(self):
        self.content = FakeAsyncSseContent()


class TestSseStreamEventType:
    def test_common_sync_stream_resets_event_type_after_empty_line(self):
        response = FakeSyncSseResponse()

        stream_items = list(_handle_stream(response))

        assert len(stream_items) == 1
        assert stream_items[0][0] is False
        assert stream_items[0][1] == HTTPStatus.BAD_REQUEST
        assert stream_items[0][2].data == "delivered"

    def test_sync_stream_resets_event_type_after_empty_line(self):
        response = FakeSyncSseResponse()

        stream_items = list(StreamEventMixin._handle_stream(response))

        assert stream_items == [
            (False, HTTPStatus.INTERNAL_SERVER_ERROR, " delivered"),
        ]

    @pytest.mark.asyncio
    async def test_common_aio_stream_resets_event_type_after_empty_line(self):
        response = FakeAsyncSseResponse()

        stream_items = [item async for item in _handle_aio_stream(response)]

        assert stream_items == [
            (False, HTTPStatus.BAD_REQUEST, " delivered"),
        ]

    @pytest.mark.asyncio
    async def test_aiohttp_request_stream_resets_event_type_after_empty_line(
        self,
    ):
        response = FakeAsyncSseResponse()

        stream_items = [
            item
            async for item in AioHttpRequest._handle_stream(None, response)
        ]

        assert stream_items == [
            (False, HTTPStatus.BAD_REQUEST, " delivered"),
        ]
