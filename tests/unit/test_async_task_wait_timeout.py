# -*- coding: utf-8 -*-
# Copyright (c) Alibaba, Inc. and its affiliates.

from http import HTTPStatus
from unittest.mock import AsyncMock, patch

import pytest

from dashscope.aigc.image_synthesis import ImageSynthesis
from dashscope.aigc.video_synthesis import VideoSynthesis
from dashscope.api_entities.dashscope_response import DashScopeAPIResponse
from dashscope.client import base_api
from dashscope.client.base_api import BaseAsyncAioApi, BaseAsyncApi
from dashscope.embeddings.batch_text_embedding import BatchTextEmbedding
from dashscope.common.constants import TaskStatus
from dashscope.common.error import TimeoutException


class TimeoutWaitTestAsyncApi(BaseAsyncApi):
    pass


class TimeoutCallTestAsyncApi(BaseAsyncApi):
    captured_async_call_kwargs = {}
    captured_wait_kwargs = {}

    @classmethod
    def async_call(cls, *_args, **kwargs):
        cls.captured_async_call_kwargs = kwargs
        return DashScopeAPIResponse(
            request_id="request-id",
            status_code=HTTPStatus.OK,
            code=None,
            output={"task_id": "task-id"},
            usage=None,
            message="",
        )

    @classmethod
    def wait(cls, task, api_key=None, workspace=None, **kwargs):
        cls.captured_wait_kwargs = kwargs
        return task


class LegacyWaitSignatureTestAsyncApi(BaseAsyncApi):
    @classmethod
    def async_call(cls, *_args, **_kwargs):
        return DashScopeAPIResponse(
            request_id="request-id",
            status_code=HTTPStatus.OK,
            code=None,
            output={"task_id": "task-id"},
            usage=None,
            message="",
        )

    @classmethod
    def wait(cls, task, api_key=None, workspace=None):
        return task


class TimeoutTestAsyncAioApi(BaseAsyncAioApi):
    pass


@pytest.fixture(autouse=True)
def reset_timeout_test_api():
    TimeoutCallTestAsyncApi.captured_async_call_kwargs = {}
    TimeoutCallTestAsyncApi.captured_wait_kwargs = {}


class TestAsyncTaskWaitTimeout:
    def test_base_async_api_wait_raises_timeout(self):
        response = DashScopeAPIResponse(
            request_id="request-id",
            status_code=HTTPStatus.OK,
            code=None,
            output={"task_status": TaskStatus.RUNNING},
            usage=None,
            message="",
        )

        with patch.object(
            TimeoutWaitTestAsyncApi,
            "_get",
            return_value=response,
        ):
            with pytest.raises(TimeoutException):
                TimeoutWaitTestAsyncApi.wait("task-id", wait_timeout_seconds=0)

    def test_base_async_api_wait_accepts_string_timeout(self):
        response = DashScopeAPIResponse(
            request_id="request-id",
            status_code=HTTPStatus.OK,
            code=None,
            output={"task_status": TaskStatus.RUNNING},
            usage=None,
            message="",
        )

        with patch.object(
            TimeoutWaitTestAsyncApi,
            "_get",
            return_value=response,
        ):
            with pytest.raises(TimeoutException):
                TimeoutWaitTestAsyncApi.wait(
                    "task-id",
                    wait_timeout_seconds="0",
                )

    def test_base_async_api_wait_sleep_does_not_exceed_remaining_timeout(
        self,
    ):
        response = DashScopeAPIResponse(
            request_id="request-id",
            status_code=HTTPStatus.OK,
            code=None,
            output={"task_status": TaskStatus.RUNNING},
            usage=None,
            message="",
        )

        with patch.object(
            TimeoutWaitTestAsyncApi,
            "_get",
            return_value=response,
        ):
            with patch.object(
                base_api.time,
                "monotonic",
                side_effect=[100.0, 100.2, 100.2],
            ):
                with patch.object(
                    base_api.time,
                    "sleep",
                    side_effect=TimeoutException("stop test"),
                ) as sleep_mock:
                    with pytest.raises(TimeoutException):
                        TimeoutWaitTestAsyncApi.wait(
                            "task-id",
                            wait_timeout_seconds=0.5,
                        )

        sleep_mock.assert_called_once()
        assert sleep_mock.call_args.args[0] == pytest.approx(0.3)

    @pytest.mark.asyncio
    async def test_base_async_aio_api_wait_raises_timeout(self):
        response = DashScopeAPIResponse(
            request_id="request-id",
            status_code=HTTPStatus.OK,
            code=None,
            output={"task_status": TaskStatus.RUNNING},
            usage=None,
            message="",
        )

        with patch.object(
            TimeoutTestAsyncAioApi,
            "_get",
            AsyncMock(return_value=response),
        ):
            with pytest.raises(TimeoutException):
                await TimeoutTestAsyncAioApi.wait(
                    "task-id",
                    wait_timeout_seconds=0,
                )

    @pytest.mark.asyncio
    async def test_base_async_aio_api_wait_accepts_string_timeout(self):
        response = DashScopeAPIResponse(
            request_id="request-id",
            status_code=HTTPStatus.OK,
            code=None,
            output={"task_status": TaskStatus.RUNNING},
            usage=None,
            message="",
        )

        with patch.object(
            TimeoutTestAsyncAioApi,
            "_get",
            AsyncMock(return_value=response),
        ):
            with pytest.raises(TimeoutException):
                await TimeoutTestAsyncAioApi.wait(
                    "task-id",
                    wait_timeout_seconds="0",
                )

    @pytest.mark.asyncio
    async def test_async_aio_wait_sleep_uses_remaining_timeout(
        self,
    ):
        response = DashScopeAPIResponse(
            request_id="request-id",
            status_code=HTTPStatus.OK,
            code=None,
            output={"task_status": TaskStatus.RUNNING},
            usage=None,
            message="",
        )

        with patch.object(
            TimeoutTestAsyncAioApi,
            "_get",
            AsyncMock(return_value=response),
        ):
            with patch.object(
                base_api.time,
                "monotonic",
                side_effect=[100.0, 100.2, 100.2],
            ):
                with patch.object(
                    base_api.asyncio,
                    "sleep",
                    AsyncMock(side_effect=TimeoutException("stop test")),
                ) as sleep_mock:
                    with pytest.raises(TimeoutException):
                        await TimeoutTestAsyncAioApi.wait(
                            "task-id",
                            wait_timeout_seconds=0.5,
                        )

        sleep_mock.assert_awaited_once()
        assert sleep_mock.await_args.args[0] == pytest.approx(0.3)

    def test_base_async_call_does_not_pass_default_wait_timeout(
        self,
    ):
        response = LegacyWaitSignatureTestAsyncApi.call(
            "model",
            "input",
            api_key="api-key",
        )

        assert response.output["task_id"] == "task-id"

    def test_base_async_call_excludes_wait_timeout_from_request(
        self,
    ):
        response = TimeoutCallTestAsyncApi.call(
            "model",
            "input",
            api_key="api-key",
            wait_timeout_seconds=10,
            custom_param="custom-value",
        )

        assert response.output["task_id"] == "task-id"
        assert (
            "wait_timeout_seconds"
            not in TimeoutCallTestAsyncApi.captured_async_call_kwargs
        )
        assert (
            TimeoutCallTestAsyncApi.captured_async_call_kwargs["custom_param"]
            == "custom-value"
        )
        assert (
            TimeoutCallTestAsyncApi.captured_wait_kwargs[
                "wait_timeout_seconds"
            ]
            == 10
        )

    @pytest.mark.asyncio
    async def test_base_async_aio_call_excludes_wait_timeout_from_request(
        self,
    ):
        async_call_response = DashScopeAPIResponse(
            request_id="request-id",
            status_code=HTTPStatus.OK,
            code=None,
            output={"task_id": "task-id"},
            usage=None,
            message="",
        )
        wait_response = DashScopeAPIResponse(
            request_id="request-id",
            status_code=HTTPStatus.OK,
            code=None,
            output={"task_status": TaskStatus.SUCCEEDED},
            usage=None,
            message="",
        )

        with patch.object(
            BaseAsyncAioApi,
            "async_call",
            AsyncMock(return_value=async_call_response),
        ) as async_call_mock:
            with patch.object(
                BaseAsyncAioApi,
                "wait",
                AsyncMock(return_value=wait_response),
            ) as wait_mock:
                response = await BaseAsyncAioApi.call(
                    "model",
                    "input",
                    "task-group",
                    api_key="api-key",
                    wait_timeout_seconds=10,
                    custom_param="custom-value",
                )

        assert response is wait_response
        assert "wait_timeout_seconds" not in async_call_mock.call_args.kwargs
        assert (
            async_call_mock.call_args.kwargs["custom_param"] == "custom-value"
        )
        assert wait_mock.call_args.kwargs["wait_timeout_seconds"] == 10

    @pytest.mark.parametrize(
        "api_class",
        [ImageSynthesis, VideoSynthesis, BatchTextEmbedding],
    )
    def test_overridden_wait_accepts_wait_timeout(
        self,
        api_class,
    ):
        wait_response = DashScopeAPIResponse(
            request_id="request-id",
            status_code=HTTPStatus.BAD_REQUEST,
            code="InvalidParameter",
            output=None,
            usage=None,
            message="invalid parameter",
        )

        with patch.object(
            BaseAsyncApi,
            "wait",
            return_value=wait_response,
        ) as wait_mock:
            response = api_class.wait(
                "task-id",
                api_key="api-key",
                wait_timeout_seconds=10,
            )

        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert wait_mock.call_args.kwargs["wait_timeout_seconds"] == 10
