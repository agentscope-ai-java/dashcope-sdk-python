# -*- coding: utf-8 -*-
# Copyright (c) Alibaba, Inc. and its affiliates.

from types import SimpleNamespace

from typer.testing import CliRunner

from dashscope.cli import messages


class TestCliMessages:
    def test_create(self, monkeypatch):
        captured_thread_id = None
        captured_request = {}

        def mock_create(thread_id, **kwargs):
            nonlocal captured_thread_id
            captured_thread_id = thread_id
            captured_request.update(kwargs)
            return SimpleNamespace(
                id="msg-1234",
                object="thread.message",
                thread_id=thread_id,
                role=kwargs["role"],
                content=kwargs["content"],
                file_ids=kwargs["file_ids"],
                metadata=kwargs["metadata"],
            )

        monkeypatch.setattr(
            messages.dashscope.Messages,
            "create",
            mock_create,
        )

        result = CliRunner().invoke(
            messages.app,
            [
                "create",
                "thread-1234",
                "--content",
                "如何做出美味的牛肉炖土豆？",
                "--role",
                "user",
                "--file-id",
                "file-1",
                "--file-id",
                "file-2",
                "--metadata",
                '{"key":"value"}',
                "--workspace",
                "workspace-id",
            ],
        )

        assert result.exit_code == 0
        assert captured_thread_id == "thread-1234"
        assert captured_request == {
            "content": "如何做出美味的牛肉炖土豆？",
            "role": "user",
            "file_ids": ["file-1", "file-2"],
            "metadata": {"key": "value"},
            "workspace": "workspace-id",
        }
        assert "msg-1234" in result.output
        assert "thread-1234" in result.output

    def test_list(self, monkeypatch):
        captured_thread_id = None
        captured_request = {}

        def mock_list(thread_id, **kwargs):
            nonlocal captured_thread_id
            captured_thread_id = thread_id
            captured_request.update(kwargs)
            return SimpleNamespace(
                first_id="msg-1234",
                last_id="msg-5678",
                has_more=False,
                data=[
                    SimpleNamespace(
                        id="msg-1234",
                        object="thread.message",
                        thread_id=thread_id,
                        role="user",
                    )
                ],
            )

        monkeypatch.setattr(
            messages.dashscope.Messages,
            "list",
            mock_list,
        )

        result = CliRunner().invoke(
            messages.app,
            [
                "list",
                "thread-1234",
                "--limit",
                "10",
                "--order",
                "asc",
                "--after",
                "msg-0001",
                "--before",
                "msg-9999",
                "--workspace",
                "workspace-id",
            ],
        )

        assert result.exit_code == 0
        assert captured_thread_id == "thread-1234"
        assert captured_request == {
            "limit": 10,
            "order": "asc",
            "after": "msg-0001",
            "before": "msg-9999",
            "workspace": "workspace-id",
        }
        assert "msg-1234" in result.output
        assert "thread-1234" in result.output

    def test_get(self, monkeypatch):
        captured_message_id = None
        captured_request = {}

        def mock_retrieve(message_id, **kwargs):
            nonlocal captured_message_id
            captured_message_id = message_id
            captured_request.update(kwargs)
            return SimpleNamespace(
                id=message_id,
                object="thread.message",
                thread_id=kwargs["thread_id"],
                role="user",
                content="hello",
                metadata={},
            )

        monkeypatch.setattr(
            messages.dashscope.Messages,
            "retrieve",
            mock_retrieve,
        )

        result = CliRunner().invoke(
            messages.app,
            [
                "get",
                "thread-1234",
                "msg-1234",
                "--workspace",
                "workspace-id",
            ],
        )

        assert result.exit_code == 0
        assert captured_message_id == "msg-1234"
        assert captured_request == {
            "thread_id": "thread-1234",
            "workspace": "workspace-id",
        }
        assert "msg-1234" in result.output
        assert "thread-1234" in result.output

    def test_update(self, monkeypatch):
        captured_message_id = None
        captured_request = {}

        def mock_update(message_id, **kwargs):
            nonlocal captured_message_id
            captured_message_id = message_id
            captured_request.update(kwargs)
            return SimpleNamespace(
                id=message_id,
                object="thread.message",
                thread_id=kwargs["thread_id"],
                role="user",
                metadata=kwargs["metadata"],
            )

        monkeypatch.setattr(
            messages.dashscope.Messages,
            "update",
            mock_update,
        )

        result = CliRunner().invoke(
            messages.app,
            [
                "update",
                "thread-1234",
                "msg-1234",
                "--metadata",
                '{"key":"value"}',
                "--workspace",
                "workspace-id",
            ],
        )

        assert result.exit_code == 0
        assert captured_message_id == "msg-1234"
        assert captured_request == {
            "thread_id": "thread-1234",
            "metadata": {"key": "value"},
            "workspace": "workspace-id",
        }
        assert "msg-1234" in result.output
        assert "key" in result.output

    def test_list_files(self, monkeypatch):
        captured_message_id = None
        captured_request = {}

        def mock_list(message_id, **kwargs):
            nonlocal captured_message_id
            captured_message_id = message_id
            captured_request.update(kwargs)
            return SimpleNamespace(
                first_id="file-1234",
                last_id="file-5678",
                has_more=False,
                data=[
                    SimpleNamespace(
                        id="file-1234",
                        object="thread.message.file",
                        message_id=message_id,
                    )
                ],
            )

        monkeypatch.setattr(
            messages.MessageFiles,
            "list",
            mock_list,
        )

        result = CliRunner().invoke(
            messages.app,
            [
                "files",
                "list",
                "thread-1234",
                "msg-1234",
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
        assert captured_message_id == "msg-1234"
        assert captured_request == {
            "thread_id": "thread-1234",
            "limit": 10,
            "order": "asc",
            "after": "file-0001",
            "before": "file-9999",
            "workspace": "workspace-id",
        }
        assert "file-1234" in result.output
        assert "msg-1234" in result.output

    def test_get_file(self, monkeypatch):
        captured_file_id = None
        captured_request = {}

        def mock_retrieve(file_id, **kwargs):
            nonlocal captured_file_id
            captured_file_id = file_id
            captured_request.update(kwargs)
            return SimpleNamespace(
                id=file_id,
                object="thread.message.file",
                message_id=kwargs["message_id"],
            )

        monkeypatch.setattr(
            messages.MessageFiles,
            "retrieve",
            mock_retrieve,
        )

        result = CliRunner().invoke(
            messages.app,
            [
                "files",
                "get",
                "thread-1234",
                "msg-1234",
                "file-1234",
                "--workspace",
                "workspace-id",
            ],
        )

        assert result.exit_code == 0
        assert captured_file_id == "file-1234"
        assert captured_request == {
            "thread_id": "thread-1234",
            "message_id": "msg-1234",
            "workspace": "workspace-id",
        }
        assert "file-1234" in result.output
        assert "msg-1234" in result.output
