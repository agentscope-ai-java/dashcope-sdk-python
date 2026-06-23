# -*- coding: utf-8 -*-
# Copyright (c) Alibaba, Inc. and its affiliates.

from types import SimpleNamespace

from typer.testing import CliRunner

from dashscope.cli import threads


class TestCliThreads:
    def test_create(self, monkeypatch):
        captured_request = {}

        def mock_create(**kwargs):
            captured_request.update(kwargs)
            return SimpleNamespace(
                id="thread-1234",
                object="thread",
                created_at=1699012949,
                metadata=kwargs["metadata"],
            )

        monkeypatch.setattr(
            threads.dashscope.Threads,
            "create",
            mock_create,
        )

        result = CliRunner().invoke(
            threads.app,
            [
                "create",
                "--messages",
                '[{"role":"user","content":"如何做出美味的牛肉炖土豆？"}]',
                "--metadata",
                '{"key":"value"}',
                "--workspace",
                "workspace-id",
            ],
        )

        assert result.exit_code == 0
        assert captured_request == {
            "messages": [
                {
                    "role": "user",
                    "content": "如何做出美味的牛肉炖土豆？",
                },
            ],
            "metadata": {"key": "value"},
            "workspace": "workspace-id",
        }
        assert "thread-1234" in result.output
        assert "key" in result.output

    def test_update(self, monkeypatch):
        captured_thread_id = None
        captured_request = {}

        def mock_update(thread_id, **kwargs):
            nonlocal captured_thread_id
            captured_thread_id = thread_id
            captured_request.update(kwargs)
            return SimpleNamespace(
                id=thread_id,
                object="thread",
                created_at=1699012949,
                metadata=kwargs["metadata"],
            )

        monkeypatch.setattr(
            threads.dashscope.Threads,
            "update",
            mock_update,
        )

        result = CliRunner().invoke(
            threads.app,
            [
                "update",
                "thread-1234",
                "--metadata",
                '{"key":"value"}',
                "--workspace",
                "workspace-id",
            ],
        )

        assert result.exit_code == 0
        assert captured_thread_id == "thread-1234"
        assert captured_request == {
            "metadata": {"key": "value"},
            "workspace": "workspace-id",
        }
        assert "thread-1234" in result.output
        assert "key" in result.output

    def test_get(self, monkeypatch):
        captured_thread_id = None
        captured_request = {}

        def mock_retrieve(thread_id, **kwargs):
            nonlocal captured_thread_id
            captured_thread_id = thread_id
            captured_request.update(kwargs)
            return SimpleNamespace(
                id=thread_id,
                object="thread",
                created_at=1699012949,
                metadata={"key": "value"},
            )

        monkeypatch.setattr(
            threads.dashscope.Threads,
            "retrieve",
            mock_retrieve,
        )

        result = CliRunner().invoke(
            threads.app,
            [
                "get",
                "thread-1234",
                "--workspace",
                "workspace-id",
            ],
        )

        assert result.exit_code == 0
        assert captured_thread_id == "thread-1234"
        assert captured_request == {"workspace": "workspace-id"}
        assert "thread-1234" in result.output
        assert "key" in result.output

    def test_delete(self, monkeypatch):
        captured_thread_id = None
        captured_request = {}

        def mock_delete(thread_id, **kwargs):
            nonlocal captured_thread_id
            captured_thread_id = thread_id
            captured_request.update(kwargs)
            return SimpleNamespace(
                id=thread_id,
                object="thread",
                created_at=1699012949,
                deleted=True,
            )

        monkeypatch.setattr(
            threads.dashscope.Threads,
            "delete",
            mock_delete,
        )

        result = CliRunner().invoke(
            threads.app,
            [
                "delete",
                "thread-1234",
                "--workspace",
                "workspace-id",
            ],
        )

        assert result.exit_code == 0
        assert captured_thread_id == "thread-1234"
        assert captured_request == {"workspace": "workspace-id"}
        assert "thread-1234" in result.output
        assert "true" in result.output

    def test_create_and_run(self, monkeypatch):
        captured_request = {}

        def mock_create_and_run(**kwargs):
            captured_request.update(kwargs)
            return SimpleNamespace(
                id="run-1234",
                object="thread.run",
                thread_id="thread-1234",
                assistant_id=kwargs["assistant_id"],
                model=kwargs["model"],
                instructions=kwargs["instructions"],
                metadata=kwargs["metadata"],
            )

        monkeypatch.setattr(
            threads.dashscope.Threads,
            "create_and_run",
            mock_create_and_run,
        )

        result = CliRunner().invoke(
            threads.app,
            [
                "create-and-run",
                "--assistant-id",
                "asst-1234",
                "--thread",
                '{"messages":[{"role":"user","content":"hello"}]}',
                "--model",
                "qwen-max",
                "--instructions",
                "You are helpful.",
                "--additional-instructions",
                "Answer briefly.",
                "--tools",
                '[{"type":"search"}]',
                "--metadata",
                '{"key":"value"}',
                "--workspace",
                "workspace-id",
            ],
        )

        assert result.exit_code == 0
        assert captured_request == {
            "assistant_id": "asst-1234",
            "thread": {"messages": [{"role": "user", "content": "hello"}]},
            "model": "qwen-max",
            "instructions": "You are helpful.",
            "additional_instructions": "Answer briefly.",
            "tools": [{"type": "search"}],
            "metadata": {"key": "value"},
            "workspace": "workspace-id",
        }
        assert "run-1234" in result.output
        assert "thread-1234" in result.output
