# -*- coding: utf-8 -*-
# Copyright (c) Alibaba, Inc. and its affiliates.

from types import SimpleNamespace

from typer.testing import CliRunner

from dashscope.cli import image_generation


class TestCliImageGeneration:
    def test_create(self, monkeypatch):
        captured_request = {}

        def mock_call(**kwargs):
            captured_request.update(kwargs)
            return SimpleNamespace(
                status_code=200,
                output={
                    "choices": [
                        {
                            "message": {
                                "content": [
                                    {
                                        "image": (
                                            "https://example.com/generated.png"
                                        ),
                                    },
                                ],
                            },
                        },
                    ],
                },
                usage={"input_tokens": 10, "output_tokens": 8},
            )

        monkeypatch.setattr(
            image_generation.ImageGeneration,
            "call",
            mock_call,
        )

        result = CliRunner().invoke(
            image_generation.app,
            [
                "create",
                "--model",
                "wan2.6-image",
                "--text",
                "参考图的风格生成番茄炒蛋",
                "--image",
                "https://example.com/reference-1.png",
                "--image",
                "https://example.com/reference-2.png",
                "--workspace",
                "workspace-id",
                "--size",
                "1024*1024",
                "--n",
                "1",
                "--max-images",
                "3",
            ],
        )

        assert result.exit_code == 0
        assert captured_request["model"] == "wan2.6-image"
        assert captured_request["workspace"] == "workspace-id"
        assert captured_request["size"] == "1024*1024"
        assert captured_request["n"] == 1
        assert captured_request["max_images"] == 3
        assert len(captured_request["messages"]) == 1
        message = captured_request["messages"][0]
        assert message["role"] == "user"
        assert message["content"] == [
            {"text": "参考图的风格生成番茄炒蛋"},
            {"image": "https://example.com/reference-1.png"},
            {"image": "https://example.com/reference-2.png"},
        ]
        assert "generated.png" in result.output
        assert "input_tokens" in result.output
