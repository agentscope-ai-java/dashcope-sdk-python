# -*- coding: utf-8 -*-
# Copyright (c) Alibaba, Inc. and its affiliates.

from types import SimpleNamespace

from typer.testing import CliRunner

from dashscope.cli import steps


class TestCliSteps:
    def test_list(self, monkeypatch):
        captured_run_id = None
        captured_request = {}

        def mock_list(run_id, **kwargs):
            nonlocal captured_run_id
            captured_run_id = run_id
            captured_request.update(kwargs)
            return SimpleNamespace(
                object="list",
                data=[
                    SimpleNamespace(id="step-1234", type="message_creation"),
                ],
                first_id="step-1234",
                last_id="step-1234",
                has_more=False,
            )

        monkeypatch.setattr(
            steps.dashscope.Steps,
            "list",
            mock_list,
        )

        result = CliRunner().invoke(
            steps.app,
            [
                "list",
                "run-1234",
                "--thread-id",
                "thread-1234",
                "--limit",
                "10",
                "--order",
                "asc",
                "--after",
                "step-0001",
                "--before",
                "step-9999",
                "--workspace",
                "workspace-id",
            ],
        )

        assert result.exit_code == 0
        assert captured_run_id == "run-1234"
        assert captured_request == {
            "thread_id": "thread-1234",
            "limit": 10,
            "order": "asc",
            "after": "step-0001",
            "before": "step-9999",
            "workspace": "workspace-id",
        }
        assert "step-1234" in result.output
        assert "message_creation" in result.output

    def test_get(self, monkeypatch):
        captured_step_id = None
        captured_request = {}

        def mock_retrieve(step_id, **kwargs):
            nonlocal captured_step_id
            captured_step_id = step_id
            captured_request.update(kwargs)
            return SimpleNamespace(
                id="step-1234",
                object="thread.run.step",
                type="message_creation",
                thread_id=kwargs["thread_id"],
                run_id=kwargs["run_id"],
            )

        monkeypatch.setattr(
            steps.dashscope.Steps,
            "retrieve",
            mock_retrieve,
        )

        result = CliRunner().invoke(
            steps.app,
            [
                "get",
                "step-1234",
                "--thread-id",
                "thread-1234",
                "--run-id",
                "run-1234",
                "--workspace",
                "workspace-id",
            ],
        )

        assert result.exit_code == 0
        assert captured_step_id == "step-1234"
        assert captured_request == {
            "thread_id": "thread-1234",
            "run_id": "run-1234",
            "workspace": "workspace-id",
        }
        assert "step-1234" in result.output
        assert "thread.run.step" in result.output
