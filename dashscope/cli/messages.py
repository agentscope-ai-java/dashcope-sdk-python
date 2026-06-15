# -*- coding: utf-8 -*-
"""``messages`` sub-command group."""
import json
from typing import List, Optional

import typer

import dashscope
from dashscope.cli.common import console, error, handle_sdk_error
from dashscope.threads.messages.files import Files as MessageFiles

app = typer.Typer(
    name="messages",
    help="Thread message management commands",
    add_completion=False,
    invoke_without_command=True,
)
files_app = typer.Typer(
    name="files",
    help="Thread message file management commands",
    add_completion=False,
    invoke_without_command=True,
)
app.add_typer(files_app, name="files")


@app.callback()
def callback(ctx: typer.Context):
    """Show help if no subcommand is provided."""
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


@files_app.callback()
def files_callback(ctx: typer.Context):
    """Show help if no message file subcommand is provided."""
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


@app.command("create")
@handle_sdk_error("Create message failed")
def create(
    thread_id: str = typer.Argument(..., help="The thread id"),
    content: str = typer.Option(..., "-c", "--content", help="Message content"),
    role: str = typer.Option("user", "--role", help="Message role"),
    file_ids: Optional[List[str]] = typer.Option(
        None,
        "--file-id",
        help="File id, can be used multiple times",
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
    """Create a thread message."""
    response = dashscope.Messages.create(
        thread_id,
        content=content,
        role=role,
        file_ids=file_ids or [],
        metadata=_parse_json_object(metadata, "metadata"),
        workspace=workspace,
    )
    console.print_json(
        json.dumps(response, default=lambda value: value.__dict__, ensure_ascii=False),
    )


@app.command("list")
@handle_sdk_error("List messages failed")
def list_messages(
    thread_id: str = typer.Argument(..., help="The thread id"),
    limit: Optional[int] = typer.Option(None, "--limit", help="Maximum number of messages"),
    order: Optional[str] = typer.Option(None, "--order", help="Sort order by created_at"),
    after: Optional[str] = typer.Option(None, "--after", help="Cursor after message id"),
    before: Optional[str] = typer.Option(None, "--before", help="Cursor before message id"),
    workspace: Optional[str] = typer.Option(
        None,
        "-w",
        "--workspace",
        help="The DashScope workspace id",
    ),
):
    """List thread messages."""
    response = dashscope.Messages.list(
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


@app.command("get")
@handle_sdk_error("Retrieve message failed")
def get_message(
    thread_id: str = typer.Argument(..., help="The thread id"),
    message_id: str = typer.Argument(..., help="The message id"),
    workspace: Optional[str] = typer.Option(
        None,
        "-w",
        "--workspace",
        help="The DashScope workspace id",
    ),
):
    """Retrieve a thread message."""
    response = dashscope.Messages.retrieve(
        message_id,
        thread_id=thread_id,
        workspace=workspace,
    )
    console.print_json(
        json.dumps(response, default=lambda value: value.__dict__, ensure_ascii=False),
    )


@app.command("update")
@handle_sdk_error("Update message failed")
def update_message(
    thread_id: str = typer.Argument(..., help="The thread id"),
    message_id: str = typer.Argument(..., help="The message id"),
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
    """Update a thread message."""
    response = dashscope.Messages.update(
        message_id,
        thread_id=thread_id,
        metadata=_parse_json_object(metadata, "metadata"),
        workspace=workspace,
    )
    console.print_json(
        json.dumps(response, default=lambda value: value.__dict__, ensure_ascii=False),
    )


@files_app.command("list")
@handle_sdk_error("List message files failed")
def list_message_files(
    thread_id: str = typer.Argument(..., help="The thread id"),
    message_id: str = typer.Argument(..., help="The message id"),
    limit: Optional[int] = typer.Option(None, "--limit", help="Maximum number of files"),
    order: Optional[str] = typer.Option(None, "--order", help="Sort order by created_at"),
    after: Optional[str] = typer.Option(None, "--after", help="Cursor after file id"),
    before: Optional[str] = typer.Option(None, "--before", help="Cursor before file id"),
    workspace: Optional[str] = typer.Option(
        None,
        "-w",
        "--workspace",
        help="The DashScope workspace id",
    ),
):
    """List thread message files."""
    response = MessageFiles.list(
        message_id,
        thread_id=thread_id,
        limit=limit,
        order=order,
        after=after,
        before=before,
        workspace=workspace,
    )
    console.print_json(
        json.dumps(response, default=lambda value: value.__dict__, ensure_ascii=False),
    )


@files_app.command("get")
@handle_sdk_error("Retrieve message file failed")
def get_message_file(
    thread_id: str = typer.Argument(..., help="The thread id"),
    message_id: str = typer.Argument(..., help="The message id"),
    file_id: str = typer.Argument(..., help="The file id"),
    workspace: Optional[str] = typer.Option(
        None,
        "-w",
        "--workspace",
        help="The DashScope workspace id",
    ),
):
    """Retrieve a thread message file."""
    response = MessageFiles.retrieve(
        file_id,
        thread_id=thread_id,
        message_id=message_id,
        workspace=workspace,
    )
    console.print_json(
        json.dumps(response, default=lambda value: value.__dict__, ensure_ascii=False),
    )
