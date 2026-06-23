# -*- coding: utf-8 -*-
"""``threads`` sub-command group."""
import json
from typing import Optional

import typer

import dashscope
from dashscope.cli.common import console, error, handle_sdk_error

app = typer.Typer(
    name="threads",
    help="Thread management commands",
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
@handle_sdk_error("Create thread failed")
def create(
    messages: Optional[str] = typer.Option(
        None,
        "--messages",
        help="Initial messages as a JSON array string",
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
    """Create a thread."""
    response = dashscope.Threads.create(
        messages=_parse_json_array(messages, "messages"),
        metadata=_parse_json_object(metadata, "metadata"),
        workspace=workspace,
    )
    console.print_json(
        json.dumps(
            response,
            default=lambda value: value.__dict__,
            ensure_ascii=False,
        ),
    )


@app.command("update")
@handle_sdk_error("Update thread failed")
def update_thread(
    thread_id: str = typer.Argument(..., help="The thread id"),
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
    """Update a thread."""
    response = dashscope.Threads.update(
        thread_id,
        metadata=_parse_json_object(metadata, "metadata"),
        workspace=workspace,
    )
    console.print_json(
        json.dumps(
            response,
            default=lambda value: value.__dict__,
            ensure_ascii=False,
        ),
    )


@app.command("get")
@handle_sdk_error("Retrieve thread failed")
def get_thread(
    thread_id: str = typer.Argument(..., help="The thread id"),
    workspace: Optional[str] = typer.Option(
        None,
        "-w",
        "--workspace",
        help="The DashScope workspace id",
    ),
):
    """Retrieve a thread."""
    response = dashscope.Threads.retrieve(
        thread_id,
        workspace=workspace,
    )
    console.print_json(
        json.dumps(
            response,
            default=lambda value: value.__dict__,
            ensure_ascii=False,
        ),
    )


@app.command("delete")
@handle_sdk_error("Delete thread failed")
def delete_thread(
    thread_id: str = typer.Argument(..., help="The thread id"),
    workspace: Optional[str] = typer.Option(
        None,
        "-w",
        "--workspace",
        help="The DashScope workspace id",
    ),
):
    """Delete a thread."""
    response = dashscope.Threads.delete(
        thread_id,
        workspace=workspace,
    )
    console.print_json(
        json.dumps(
            response,
            default=lambda value: value.__dict__,
            ensure_ascii=False,
        ),
    )


@app.command("create-and-run")
@handle_sdk_error("Create thread and run failed")
def create_and_run(
    assistant_id: str = typer.Option(
        ...,
        "--assistant-id",
        help="The assistant id",
    ),
    thread: Optional[str] = typer.Option(
        None,
        "--thread",
        help="Thread as a JSON object string",
    ),
    model: Optional[str] = typer.Option(
        None,
        "-m",
        "--model",
        help="The model to use",
    ),
    instructions: Optional[str] = typer.Option(
        None,
        "--instructions",
        help="Run instructions",
    ),
    additional_instructions: Optional[str] = typer.Option(
        None,
        "--additional-instructions",
        help="Additional run instructions",
    ),
    tools: Optional[str] = typer.Option(
        None,
        "--tools",
        help="Tools as a JSON array string",
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
    """Create a thread and run it."""
    response = dashscope.Threads.create_and_run(
        assistant_id=assistant_id,
        thread=_parse_json_object(thread, "thread"),
        model=model,
        instructions=instructions,
        additional_instructions=additional_instructions,
        tools=_parse_json_array(tools, "tools"),
        metadata=_parse_json_object(metadata, "metadata"),
        workspace=workspace,
    )
    console.print_json(
        json.dumps(
            response,
            default=lambda value: value.__dict__,
            ensure_ascii=False,
        ),
    )
