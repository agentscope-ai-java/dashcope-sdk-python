# -*- coding: utf-8 -*-
# Copyright (c) Alibaba, Inc. and its affiliates.

from types import SimpleNamespace

from typer.testing import CliRunner

from dashscope.cli import image_synthesis


class TestCliImageSynthesis:
    def test_create(self, monkeypatch):
        captured_request = {}

        def mock_call(**kwargs):
            captured_request.update(kwargs)
            return SimpleNamespace(
                status_code=200,
                output={
                    "task_id": "task-1234",
                    "task_status": "SUCCEEDED",
                    "results": [
                        {
                            "url": "https://example.com/image.png",
                        },
                    ],
                },
                usage={"image_count": 1},
            )

        monkeypatch.setattr(
            image_synthesis.dashscope.ImageSynthesis,
            "call",
            mock_call,
        )

        result = CliRunner().invoke(
            image_synthesis.app,
            [
                "create",
                "--model",
                "wanx2.1-t2i-turbo",
                "--prompt",
                "一间有着精致窗户的花店",
                "--negative-prompt",
                "低清晰度",
                "--workspace",
                "workspace-id",
                "--n",
                "1",
                "--size",
                "1024*1024",
            ],
        )

        assert result.exit_code == 0
        assert captured_request == {
            "model": "wanx2.1-t2i-turbo",
            "prompt": "一间有着精致窗户的花店",
            "negative_prompt": "低清晰度",
            "workspace": "workspace-id",
            "n": 1,
            "size": "1024*1024",
        }
        assert "task-1234" in result.output
        assert "image_count" in result.output
