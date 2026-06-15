# -*- coding: utf-8 -*-
"""``runs`` sub-command group."""
import json
from typing import Optional

import typer

import dashscope
from dashscope.cli.common import console, error, handle_sdk_error

app = typer.Typer(
    name="runs",
    help="Thread run management commands",
    add_completion=False,
    invoke_without_command=True,
)


@app.callback()
def callback(ctx: typer.Context):
    """Show help if no subcommand is provided."""
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


def _parse_json_object(value: Optional[str], option_name: str):
    if value is None:
        return None
    try:
        parsed_value = json.loads(value)
    except json.JSONDecodeError as exception:
        error(f"Invalid {option_name} JSON: {exception.msg}")
    if not isinstance(parsed_value, dict):
        error(f"{option_name} must be a JSON object")
    return parsed_value


def _parse_json_array(value: Optional[str], option_name: str):
    if value is None:
        return None
    try:
        parsed_value = json.loads(value)
    except json.JSONDecodeError as exception:
        error(f"Invalid {option_name} JSON: {exception.msg}")
    if not isinstance(parsed_value, list):
        error(f"{option_name} must be a JSON array")
    return parsed_value


@app.command("create")
@handle_sdk_error("Create run failed")
def create(
    thread_id: str = typer.Argument(..., help="The thread id"),
    assistant_id: str = typer.Option(
        ...,
        "--assistant-id",
        help="The assistant id to run",
    ),
    model: Optional[str] = typer.Option(None, "-m", "--model", help="The model to use"),
    instructions: Optional[str] = typer.Option(None, "--instructions", help="Run instructions"),
    additional_instructions: Optional[str] = typer.Option(
        None,
        "--additional-instructions",
        help="Additional instructions appended for this run",
    ),
    tools: Optional[str] = typer.Option(None, "--tools", help="Tools as a JSON array string"),
    metadata: Optional[str] = typer.Option(None, "--metadata", help="Metadata as a JSON object string"),
    extra_body: Optional[str] = typer.Option(None, "--extra-body", help="Extra body as a JSON object string"),
    workspace: Optional[str] = typer.Option(
        None,
        "-w",
        "--workspace",
        help="The DashScope workspace id",
    ),
    top_p: Optional[float] = typer.Option(None, "--top-p", help="Top-p sampling"),
    top_k: Optional[int] = typer.Option(None, "--top-k", help="Top-k sampling"),
    temperature: Optional[float] = typer.Option(None, "--temperature", help="Sampling temperature"),
    max_tokens: Optional[int] = typer.Option(None, "--max-tokens", help="Maximum output tokens"),
):
    """Create a run."""
    response = dashscope.Runs.create(
        thread_id,
        assistant_id=assistant_id,
        model=model,
        instructions=instructions,
        additional_instructions=additional_instructions,
        tools=_parse_json_array(tools, "tools"),
        metadata=_parse_json_object(metadata, "metadata"),
        extra_body=_parse_json_object(extra_body, "extra_body"),
        workspace=workspace,
        top_p=top_p,
        top_k=top_k,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    console.print_json(
        json.dumps(response, default=lambda value: value.__dict__, ensure_ascii=False),
    )


@app.command("get")
@handle_sdk_error("Retrieve run failed")
def get_run(
    run_id: str = typer.Argument(..., help="The run id"),
    thread_id: str = typer.Option(
        ...,
        "--thread-id",
        help="The thread id",
    ),
    workspace: Optional[str] = typer.Option(
        None,
        "-w",
        "--workspace",
        help="The DashScope workspace id",
    ),
):
    """Retrieve a run."""
    response = dashscope.Runs.retrieve(
        run_id,
        thread_id=thread_id,
        workspace=workspace,
    )
    console.print_json(
        json.dumps(response, default=lambda value: value.__dict__, ensure_ascii=False),
    )


@app.command("list")
@handle_sdk_error("List runs failed")
def list_runs(
    thread_id: str = typer.Argument(..., help="The thread id"),
    limit: Optional[int] = typer.Option(None, "--limit", help="Maximum number of runs"),
    order: Optional[str] = typer.Option(None, "--order", help="Sort order by created_at"),
    after: Optional[str] = typer.Option(None, "--after", help="Cursor after run id"),
    before: Optional[str] = typer.Option(None, "--before", help="Cursor before run id"),
    workspace: Optional[str] = typer.Option(
        None,
        "-w",
        "--workspace",
        help="The DashScope workspace id",
    ),
):
    """List runs of a thread."""
    response = dashscope.Runs.list(
        thread_id,
        limit=limit,
        order=order,
        after=after,
        before=before,
        workspace=workspace,
    )
    console.print_json(
        json.dumps(response, default=lambda value: value.__dict__, ensure_ascii=False),
    )


@app.command("submit-tool-outputs")
@handle_sdk_error("Submit tool outputs failed")
def submit_tool_outputs(
    run_id: str = typer.Argument(..., help="The run id"),
    thread_id: str = typer.Option(
        ...,
        "--thread-id",
        help="The thread id",
    ),
    tool_outputs: str = typer.Option(
        ...,
        "--tool-outputs",
        help="Tool outputs as a JSON array string",
    ),
    extra_body: Optional[str] = typer.Option(
        None,
        "--extra-body",
        help="Extra body as a JSON object string",
    ),
    workspace: Optional[str] = typer.Option(
        None,
        "-w",
        "--workspace",
        help="The DashScope workspace id",
    ),
):
    """Submit tool outputs to a run."""
    response = dashscope.Runs.submit_tool_outputs(
        run_id,
        thread_id=thread_id,
        tool_outputs=_parse_json_array(tool_outputs, "tool_outputs"),
        extra_body=_parse_json_object(extra_body, "extra_body"),
        workspace=workspace,
    )
    console.print_json(
        json.dumps(response, default=lambda value: value.__dict__, ensure_ascii=False),
    )


@app.command("wait")
@handle_sdk_error("Wait run failed")
def wait_run(
    run_id: str = typer.Argument(..., help="The run id"),
    thread_id: str = typer.Option(
        ...,
        "--thread-id",
        help="The thread id",
    ),
    timeout_seconds: float = typer.Option(
        float("inf"),
        "--timeout-seconds",
        help="Maximum seconds to wait",
    ),
    workspace: Optional[str] = typer.Option(
        None,
        "-w",
        "--workspace",
        help="The DashScope workspace id",
    ),
):
    """Wait for a run to reach a terminal status."""
    response = dashscope.Runs.wait(
        run_id,
        thread_id=thread_id,
        timeout_seconds=timeout_seconds,
        workspace=workspace,
    )
    console.print_json(
        json.dumps(response, default=lambda value: value.__dict__, ensure_ascii=False),
    )


@app.command("update")
@handle_sdk_error("Update run failed")
def update_run(
    run_id: str = typer.Argument(..., help="The run id"),
    thread_id: str = typer.Option(
        ...,
        "--thread-id",
        help="The thread id",
    ),
    metadata: Optional[str] = typer.Option(
        None,
        "--metadata",
        help="Metadata as a JSON object string",
    ),
    workspace: Optional[str] = typer.Option(
        None,
        "-w",
        "--workspace",
        help="The DashScope workspace id",
    ),
):
    """Update a run."""
    response = dashscope.Runs.update(
        run_id,
        thread_id=thread_id,
        metadata=_parse_json_object(metadata, "metadata"),
        workspace=workspace,
    )
    console.print_json(
        json.dumps(response, default=lambda value: value.__dict__, ensure_ascii=False),
    )


@app.command("cancel")
@handle_sdk_error("Cancel run failed")
def cancel_run(
    run_id: str = typer.Argument(..., help="The run id"),
    thread_id: str = typer.Option(
        ...,
        "--thread-id",
        help="The thread id",
    ),
    workspace: Optional[str] = typer.Option(
        None,
        "-w",
        "--workspace",
        help="The DashScope workspace id",
    ),
):
    """Cancel a run."""
    response = dashscope.Runs.cancel(
        run_id,
        thread_id=thread_id,
        workspace=workspace,
    )
    console.print_json(
        json.dumps(response, default=lambda value: value.__dict__, ensure_ascii=False),
    )
