# -*- coding: utf-8 -*-
# Copyright (c) Alibaba, Inc. and its affiliates.

from unittest.mock import patch

import pytest

import dashscope
from dashscope.audio.qwen_tts_realtime.qwen_tts_realtime import (
    QwenTtsRealtime,
)


class FakeConnectedSock:
    connected = True


class FakeWebSocketApp:
    def __init__(self, *_args, on_close=None, **_kwargs):
        self.sock = FakeConnectedSock()
        self.on_close = on_close

    def run_forever(self):
        pass


class FakeClosingWebSocketApp(FakeWebSocketApp):
    def run_forever(self):
        self.on_close(self, 401, "unauthorized")


class ImmediateThread:
    def __init__(self, target):
        self.target = target
        self.daemon = False

    def start(self):
        self.target()


class NoopThread:
    def __init__(self, target):
        self.target = target
        self.daemon = False

    def start(self):
        pass


@pytest.fixture(autouse=True)
def set_api_key():
    dashscope.api_key = "test-api-key"


class TestQwenTtsRealtimeConnect:
    def test_connect_stops_waiting_when_websocket_closes(self):
        realtime_client = QwenTtsRealtime(model="qwen-tts-realtime")

        with patch(
            "dashscope.audio.qwen_tts_realtime.qwen_tts_realtime.websocket.WebSocketApp",
            FakeClosingWebSocketApp,
        ), patch(
            "dashscope.audio.qwen_tts_realtime.qwen_tts_realtime.threading.Thread",
            ImmediateThread,
        ), patch(
            "dashscope.audio.qwen_tts_realtime.qwen_tts_realtime.time.sleep",
        ) as sleep_mock:
            with pytest.raises(TimeoutError):
                realtime_client.connect()

        sleep_mock.assert_not_called()

    def test_connect_session_wait_uses_remaining_timeout(self):
        realtime_client = QwenTtsRealtime(model="qwen-tts-realtime")
        sleep_durations = []

        def record_sleep(duration):
            sleep_durations.append(duration)

        with patch(
            "dashscope.audio.qwen_tts_realtime.qwen_tts_realtime.websocket.WebSocketApp",
            FakeWebSocketApp,
        ), patch(
            "dashscope.audio.qwen_tts_realtime.qwen_tts_realtime.threading.Thread",
            NoopThread,
        ), patch(
            "dashscope.audio.qwen_tts_realtime.qwen_tts_realtime.time.monotonic",
            side_effect=[100.0, 104.95, 105.0],
        ), patch(
            "dashscope.audio.qwen_tts_realtime.qwen_tts_realtime.time.sleep",
            side_effect=record_sleep,
        ):
            with pytest.raises(TimeoutError):
                realtime_client.connect()

        assert sleep_durations == [pytest.approx(0.05)]
