# -*- coding: utf-8 -*-
# Copyright (c) Alibaba, Inc. and its affiliates.

import re
from types import SimpleNamespace

from typer.testing import CliRunner

from dashscope.cli import runs


def strip_ansi_codes(text):
    """Remove ANSI escape codes from text."""
    ansi_escape = re.compile(r"\x1b\[[0-9;]*m")
    return ansi_escape.sub("", text)


class TestCliRuns:
    def test_create(self, monkeypatch):
        captured_thread_id = None
        captured_request = {}

        def mock_create(thread_id, **kwargs):
            nonlocal captured_thread_id
            captured_thread_id = thread_id
            captured_request.update(kwargs)
            return SimpleNamespace(
                id="run-1234",
                object="thread.run",
                thread_id=thread_id,
                assistant_id=kwargs["assistant_id"],
                model=kwargs["model"],
                instructions=kwargs["instructions"],
                metadata=kwargs["metadata"],
            )

        monkeypatch.setattr(
            runs.dashscope.Runs,
            "create",
            mock_create,
        )

        result = CliRunner().invoke(
            runs.app,
            [
                "create",
                "thread-1234",
                "--assistant-id",
                "asst-1234",
                "--model",
                "qwen-max",
                "--instructions",
                "You are a helpful assistant.",
                "--additional-instructions",
                "Answer briefly.",
                "--tools",
                '[{"type":"search"}]',
                "--metadata",
                '{"key":"value"}',
                "--extra-body",
                '{"custom":"field"}',
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
        assert captured_thread_id == "thread-1234"
        assert captured_request == {
            "assistant_id": "asst-1234",
            "model": "qwen-max",
            "instructions": "You are a helpful assistant.",
            "additional_instructions": "Answer briefly.",
            "tools": [{"type": "search"}],
            "metadata": {"key": "value"},
            "extra_body": {"custom": "field"},
            "workspace": "workspace-id",
            "top_p": 0.9,
            "top_k": 50,
            "temperature": 0.8,
            "max_tokens": 1024,
        }
        assert "run-1234" in result.output
        assert "thread-1234" in result.output

    def test_create_rejects_invalid_tools_json(self):
        result = CliRunner().invoke(
            runs.app,
            [
                "create",
                "thread-1234",
                "--assistant-id",
                "asst-1234",
                "--tools",
                "not-json",
            ],
        )

        assert result.exit_code == 1
        assert "Invalid tools JSON" in result.output

    def test_update_rejects_metadata_json_array(self):
        result = CliRunner().invoke(
            runs.app,
            [
                "update",
                "run-1234",
                "--thread-id",
                "thread-1234",
                "--metadata",
                '["wrong"]',
            ],
        )

        assert result.exit_code == 1
        assert "metadata must be a JSON object" in result.output

    def test_get_requires_thread_id(self):
        result = CliRunner().invoke(runs.app, ["get", "run-1234"])

        assert result.exit_code != 0
        clean_output = strip_ansi_codes(result.output)
        assert "Missing option" in clean_output
        assert "--thread-id" in clean_output

    def test_get(self, monkeypatch):
        captured_run_id = None
        captured_request = {}

        def mock_retrieve(run_id, **kwargs):
            nonlocal captured_run_id
            captured_run_id = run_id
            captured_request.update(kwargs)
            return SimpleNamespace(
                id="run-1234",
                object="thread.run",
                thread_id=kwargs["thread_id"],
                status="completed",
            )

        monkeypatch.setattr(
            runs.dashscope.Runs,
            "retrieve",
            mock_retrieve,
        )

        result = CliRunner().invoke(
            runs.app,
            [
                "get",
                "run-1234",
                "--thread-id",
                "thread-1234",
                "--workspace",
                "workspace-id",
            ],
        )

        assert result.exit_code == 0
        assert captured_run_id == "run-1234"
        assert captured_request == {
            "thread_id": "thread-1234",
            "workspace": "workspace-id",
        }
        assert "run-1234" in result.output
        assert "completed" in result.output

    def test_submit_tool_outputs(self, monkeypatch):
        captured_run_id = None
        captured_request = {}

        def mock_submit_tool_outputs(run_id, **kwargs):
            nonlocal captured_run_id
            captured_run_id = run_id
            captured_request.update(kwargs)
            return SimpleNamespace(
                id=run_id,
                object="thread.run",
                thread_id=kwargs["thread_id"],
                status="queued",
            )

        monkeypatch.setattr(
            runs.dashscope.Runs,
            "submit_tool_outputs",
            mock_submit_tool_outputs,
        )

        result = CliRunner().invoke(
            runs.app,
            [
                "submit-tool-outputs",
                "run-1234",
                "--thread-id",
                "thread-1234",
                "--tool-outputs",
                '[{"tool_call_id":"call-1234","output":"42"}]',
                "--extra-body",
                '{"custom":"field"}',
                "--workspace",
                "workspace-id",
            ],
        )

        assert result.exit_code == 0
        assert captured_run_id == "run-1234"
        assert captured_request == {
            "thread_id": "thread-1234",
            "tool_outputs": [{"tool_call_id": "call-1234", "output": "42"}],
            "extra_body": {"custom": "field"},
            "workspace": "workspace-id",
        }
        assert "run-1234" in result.output
        assert "queued" in result.output

    def test_wait(self, monkeypatch):
        captured_run_id = None
        captured_request = {}

        def mock_wait(run_id, **kwargs):
            nonlocal captured_run_id
            captured_run_id = run_id
            captured_request.update(kwargs)
            return SimpleNamespace(
                id=run_id,
                object="thread.run",
                thread_id=kwargs["thread_id"],
                status="completed",
            )

        monkeypatch.setattr(
            runs.dashscope.Runs,
            "wait",
            mock_wait,
        )

        result = CliRunner().invoke(
            runs.app,
            [
                "wait",
                "run-1234",
                "--thread-id",
                "thread-1234",
                "--timeout-seconds",
                "30",
                "--workspace",
                "workspace-id",
            ],
        )

        assert result.exit_code == 0
        assert captured_run_id == "run-1234"
        assert captured_request == {
            "thread_id": "thread-1234",
            "timeout_seconds": 30.0,
            "workspace": "workspace-id",
        }
        assert "run-1234" in result.output
        assert "completed" in result.output

    def test_update(self, monkeypatch):
        captured_run_id = None
        captured_request = {}

        def mock_update(run_id, **kwargs):
            nonlocal captured_run_id
            captured_run_id = run_id
            captured_request.update(kwargs)
            return SimpleNamespace(
                id=run_id,
                object="thread.run",
                thread_id=kwargs["thread_id"],
                metadata=kwargs["metadata"],
            )

        monkeypatch.setattr(
            runs.dashscope.Runs,
            "update",
            mock_update,
        )

        result = CliRunner().invoke(
            runs.app,
            [
                "update",
                "run-1234",
                "--thread-id",
                "thread-1234",
                "--metadata",
                '{"key":"value"}',
                "--workspace",
                "workspace-id",
            ],
        )

        assert result.exit_code == 0
        assert captured_run_id == "run-1234"
        assert captured_request == {
            "thread_id": "thread-1234",
            "metadata": {"key": "value"},
            "workspace": "workspace-id",
        }
        assert "run-1234" in result.output
        assert "key" in result.output

    def test_cancel(self, monkeypatch):
        captured_run_id = None
        captured_request = {}

        def mock_cancel(run_id, **kwargs):
            nonlocal captured_run_id
            captured_run_id = run_id
            captured_request.update(kwargs)
            return SimpleNamespace(
                id=run_id,
                object="thread.run",
                thread_id=kwargs["thread_id"],
                status="cancelled",
            )

        monkeypatch.setattr(
            runs.dashscope.Runs,
            "cancel",
            mock_cancel,
        )

        result = CliRunner().invoke(
            runs.app,
            [
                "cancel",
                "run-1234",
                "--thread-id",
                "thread-1234",
                "--workspace",
                "workspace-id",
            ],
        )

        assert result.exit_code == 0
        assert captured_run_id == "run-1234"
        assert captured_request == {
            "thread_id": "thread-1234",
            "workspace": "workspace-id",
        }
        assert "run-1234" in result.output
        assert "cancelled" in result.output

    def test_list(self, monkeypatch):
        captured_thread_id = None
        captured_request = {}

        def mock_list(thread_id, **kwargs):
            nonlocal captured_thread_id
            captured_thread_id = thread_id
            captured_request.update(kwargs)
            return SimpleNamespace(
                object="list",
                data=[SimpleNamespace(id="run-1234", status="completed")],
                first_id="run-1234",
                last_id="run-1234",
                has_more=False,
            )

        monkeypatch.setattr(
            runs.dashscope.Runs,
            "list",
            mock_list,
        )

        result = CliRunner().invoke(
            runs.app,
            [
                "list",
                "thread-1234",
                "--limit",
                "10",
                "--order",
                "asc",
                "--after",
                "run-0001",
                "--before",
                "run-9999",
                "--workspace",
                "workspace-id",
            ],
        )

        assert result.exit_code == 0
        assert captured_thread_id == "thread-1234"
        assert captured_request == {
            "limit": 10,
            "order": "asc",
            "after": "run-0001",
            "before": "run-9999",
            "workspace": "workspace-id",
        }
        assert "run-1234" in result.output
        assert "completed" in result.output
