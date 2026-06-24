# -*- coding: utf-8 -*-
# Copyright (c) Alibaba, Inc. and its affiliates.

from types import SimpleNamespace

from typer.testing import CliRunner

from dashscope.cli import assistants


class TestCliAssistants:
    def test_create(self, monkeypatch):
        captured_request = {}

        def mock_create(**kwargs):
            captured_request.update(kwargs)
            return SimpleNamespace(
                id="asst-1234",
                object="assistant",
                model=kwargs["model"],
                name=kwargs["name"],
                description=kwargs["description"],
                instructions=kwargs["instructions"],
                tools=kwargs["tools"],
                file_ids=kwargs["file_ids"],
                metadata=kwargs["metadata"],
            )

        monkeypatch.setattr(
            assistants.dashscope.Assistants,
            "create",
            mock_create,
        )

        result = CliRunner().invoke(
            assistants.app,
            [
                "create",
                "--model",
                "qwen-max",
                "--name",
                "smart helper",
                "--description",
                "A tool helper.",
                "--instructions",
                "You are a helpful assistant.",
                "--tools",
                '[{"type":"search"},{"type":"wanx"}]',
                "--file-id",
                "file-1",
                "--file-id",
                "file-2",
                "--metadata",
                '{"key":"value"}',
                "--workspace",
                "workspace-id",
                "--top-p",
                "0.9",
                "--top-k",
                "50",
                "--temperature",
                "0.8",
                "--max-tokens",
                "1024",
            ],
        )

        assert result.exit_code == 0
        assert captured_request == {
            "model": "qwen-max",
            "name": "smart helper",
            "description": "A tool helper.",
            "instructions": "You are a helpful assistant.",
            "tools": [{"type": "search"}, {"type": "wanx"}],
            "file_ids": ["file-1", "file-2"],
            "metadata": {"key": "value"},
            "workspace": "workspace-id",
            "top_p": 0.9,
            "top_k": 50,
            "temperature": 0.8,
            "max_tokens": 1024,
        }
        assert "asst-1234" in result.output
        assert "smart helper" in result.output

    def test_get(self, monkeypatch):
        captured_assistant_id = None
        captured_request = {}

        def mock_retrieve(assistant_id, **kwargs):
            nonlocal captured_assistant_id
            captured_assistant_id = assistant_id
            captured_request.update(kwargs)
            return SimpleNamespace(
                id="asst-1234",
                object="assistant",
                model="qwen-max",
                name="smart helper",
                instructions="You are a helpful assistant.",
            )

        monkeypatch.setattr(
            assistants.dashscope.Assistants,
            "retrieve",
            mock_retrieve,
        )

        result = CliRunner().invoke(
            assistants.app,
            [
                "get",
                "asst-1234",
                "--workspace",
                "workspace-id",
            ],
        )

        assert result.exit_code == 0
        assert captured_assistant_id == "asst-1234"
        assert captured_request == {"workspace": "workspace-id"}
        assert "asst-1234" in result.output
        assert "qwen-max" in result.output

    def test_delete(self, monkeypatch):
        captured_assistant_id = None
        captured_request = {}

        def mock_delete(assistant_id, **kwargs):
            nonlocal captured_assistant_id
            captured_assistant_id = assistant_id
            captured_request.update(kwargs)
            return SimpleNamespace(
                id=assistant_id,
                object="assistant.deleted",
                deleted=True,
            )

        monkeypatch.setattr(
            assistants.dashscope.Assistants,
            "delete",
            mock_delete,
        )

        result = CliRunner().invoke(
            assistants.app,
            [
                "delete",
                "asst-1234",
                "--workspace",
                "workspace-id",
            ],
        )

        assert result.exit_code == 0
        assert captured_assistant_id == "asst-1234"
        assert captured_request == {"workspace": "workspace-id"}
        assert "assistant.deleted" in result.output
        assert "true" in result.output

    def test_update(self, monkeypatch):
        captured_assistant_id = None
        captured_request = {}

        def mock_update(assistant_id, **kwargs):
            nonlocal captured_assistant_id
            captured_assistant_id = assistant_id
            captured_request.update(kwargs)
            return SimpleNamespace(
                id=assistant_id,
                object="assistant",
                model=kwargs["model"],
                name=kwargs["name"],
                description=kwargs["description"],
                instructions=kwargs["instructions"],
                tools=kwargs["tools"],
                file_ids=kwargs["file_ids"],
                metadata=kwargs["metadata"],
            )

        monkeypatch.setattr(
            assistants.dashscope.Assistants,
            "update",
            mock_update,
        )

        result = CliRunner().invoke(
            assistants.app,
            [
                "update",
                "asst-1234",
                "--model",
                "qwen-max",
                "--name",
                "smart helper",
                "--description",
                "Updated description.",
                "--instructions",
                "You are a helpful assistant.",
                "--tools",
                '[{"type":"search"}]',
                "--file-id",
                "file-1",
                "--metadata",
                '{"key":"value"}',
                "--workspace",
                "workspace-id",
                "--top-p",
                "0.9",
                "--top-k",
                "50",
                "--temperature",
                "0.8",
                "--max-tokens",
                "1024",
            ],
        )

        assert result.exit_code == 0
        assert captured_assistant_id == "asst-1234"
        assert captured_request == {
            "model": "qwen-max",
            "name": "smart helper",
            "description": "Updated description.",
            "instructions": "You are a helpful assistant.",
            "tools": [{"type": "search"}],
            "file_ids": ["file-1"],
            "metadata": {"key": "value"},
            "workspace": "workspace-id",
            "top_p": 0.9,
            "top_k": 50,
            "temperature": 0.8,
            "max_tokens": 1024,
        }
        assert "asst-1234" in result.output
        assert "Updated description" in result.output

    def test_list(self, monkeypatch):
        captured_request = {}

        def mock_list(**kwargs):
            captured_request.update(kwargs)
            return SimpleNamespace(
                object="list",
                data=[SimpleNamespace(id="asst-1234", model="qwen-max")],
                first_id="asst-1234",
                last_id="asst-1234",
                has_more=False,
            )

        monkeypatch.setattr(
            assistants.dashscope.Assistants,
            "list",
            mock_list,
        )

        result = CliRunner().invoke(
            assistants.app,
            [
                "list",
                "--limit",
                "10",
                "--order",
                "asc",
                "--after",
                "asst-0001",
                "--before",
                "asst-9999",
                "--workspace",
                "workspace-id",
            ],
        )

        assert result.exit_code == 0
        assert captured_request == {
            "limit": 10,
            "order": "asc",
            "after": "asst-0001",
            "before": "asst-9999",
            "workspace": "workspace-id",
        }
        assert "asst-1234" in result.output
        assert "qwen-max" in result.output
