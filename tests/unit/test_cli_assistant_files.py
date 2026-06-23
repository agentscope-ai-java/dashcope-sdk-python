# -*- coding: utf-8 -*-
# Copyright (c) Alibaba, Inc. and its affiliates.

from types import SimpleNamespace

from typer.testing import CliRunner

from dashscope.cli import assistant_files


class TestCliAssistantFiles:
    def test_create(self, monkeypatch):
        captured_assistant_id = None
        captured_request = {}

        def mock_create(assistant_id, **kwargs):
            nonlocal captured_assistant_id
            captured_assistant_id = assistant_id
            captured_request.update(kwargs)
            return SimpleNamespace(
                id=kwargs["file_id"],
                object="assistant.file",
                created_at=111111,
                assistant_id=assistant_id,
            )

        monkeypatch.setattr(
            assistant_files.Files,
            "create",
            mock_create,
        )

        result = CliRunner().invoke(
            assistant_files.app,
            [
                "create",
                "asst-1234",
                "--file-id",
                "file-1234",
                "--workspace",
                "workspace-id",
            ],
        )

        assert result.exit_code == 0
        assert captured_assistant_id == "asst-1234"
        assert captured_request == {
            "file_id": "file-1234",
            "workspace": "workspace-id",
        }
        assert "file-1234" in result.output
        assert "asst-1234" in result.output

    def test_get(self, monkeypatch):
        captured_file_id = None
        captured_request = {}

        def mock_retrieve(file_id, **kwargs):
            nonlocal captured_file_id
            captured_file_id = file_id
            captured_request.update(kwargs)
            return SimpleNamespace(
                id=file_id,
                object="assistant.file",
                created_at=111111,
                assistant_id=kwargs["assistant_id"],
            )

        monkeypatch.setattr(
            assistant_files.Files,
            "retrieve",
            mock_retrieve,
        )

        result = CliRunner().invoke(
            assistant_files.app,
            [
                "get",
                "asst-1234",
                "file-1234",
                "--workspace",
                "workspace-id",
            ],
        )

        assert result.exit_code == 0
        assert captured_file_id == "file-1234"
        assert captured_request == {
            "assistant_id": "asst-1234",
            "workspace": "workspace-id",
        }
        assert "file-1234" in result.output
        assert "asst-1234" in result.output

    def test_delete(self, monkeypatch):
        captured_file_id = None
        captured_request = {}

        def mock_delete(file_id, **kwargs):
            nonlocal captured_file_id
            captured_file_id = file_id
            captured_request.update(kwargs)
            return SimpleNamespace(
                id=file_id,
                object="assistant.file",
                created_at=111111,
                deleted=True,
            )

        monkeypatch.setattr(
            assistant_files.Files,
            "delete",
            mock_delete,
        )

        result = CliRunner().invoke(
            assistant_files.app,
            [
                "delete",
                "asst-1234",
                "file-1234",
                "--workspace",
                "workspace-id",
            ],
        )

        assert result.exit_code == 0
        assert captured_file_id == "file-1234"
        assert captured_request == {
            "assistant_id": "asst-1234",
            "workspace": "workspace-id",
        }
        assert "file-1234" in result.output
        assert "true" in result.output

    def test_list(self, monkeypatch):
        captured_assistant_id = None
        captured_request = {}

        def mock_list(assistant_id, **kwargs):
            nonlocal captured_assistant_id
            captured_assistant_id = assistant_id
            captured_request.update(kwargs)
            return SimpleNamespace(
                first_id="file-1234",
                last_id="file-5678",
                has_more=False,
                data=[
                    SimpleNamespace(
                        id="file-1234",
                        object="assistant.file",
                        created_at=111111,
                        assistant_id=assistant_id,
                    ),
                ],
            )

        monkeypatch.setattr(
            assistant_files.Files,
            "list",
            mock_list,
        )

        result = CliRunner().invoke(
            assistant_files.app,
            [
                "list",
                "asst-1234",
                "--limit",
                "10",
                "--order",
                "asc",
                "--after",
                "file-0001",
                "--before",
                "file-9999",
                "--workspace",
                "workspace-id",
            ],
        )

        assert result.exit_code == 0
        assert captured_assistant_id == "asst-1234"
        assert captured_request == {
            "limit": 10,
            "order": "asc",
            "after": "file-0001",
            "before": "file-9999",
            "workspace": "workspace-id",
        }
        assert "file-1234" in result.output
        assert "asst-1234" in result.output
