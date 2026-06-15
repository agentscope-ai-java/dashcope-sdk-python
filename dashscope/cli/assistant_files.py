# -*- coding: utf-8 -*-
"""``assistant-files`` sub-command group."""
import json
from typing import Optional

import typer

from dashscope.assistants.files import Files
from dashscope.cli.common import console, handle_sdk_error

app = typer.Typer(
    name="assistant-files",
    help="Assistant file management commands",
    add_completion=False,
    invoke_without_command=True,
)


@app.callback()
def callback(ctx: typer.Context):
    """Show help if no subcommand is provided."""
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


@app.command("create")
@handle_sdk_error("Create assistant file failed")
def create(
    assistant_id: str = typer.Argument(..., help="The assistant id"),
    file_id: str = typer.Option(..., "--file-id", help="The file id"),
    workspace: Optional[str] = typer.Option(
        None,
        "-w",
        "--workspace",
        help="The DashScope workspace id",
    ),
):
    """Create an assistant file."""
    response = Files.create(
        assistant_id,
        file_id=file_id,
        workspace=workspace,
    )
    console.print_json(
        json.dumps(response, default=lambda value: value.__dict__, ensure_ascii=False),
    )


@app.command("get")
@handle_sdk_error("Retrieve assistant file failed")
def get_file(
    assistant_id: str = typer.Argument(..., help="The assistant id"),
    file_id: str = typer.Argument(..., help="The file id"),
    workspace: Optional[str] = typer.Option(
        None,
        "-w",
        "--workspace",
        help="The DashScope workspace id",
    ),
):
    """Retrieve an assistant file."""
    response = Files.retrieve(
        file_id,
        assistant_id=assistant_id,
        workspace=workspace,
    )
    console.print_json(
        json.dumps(response, default=lambda value: value.__dict__, ensure_ascii=False),
    )


@app.command("delete")
@handle_sdk_error("Delete assistant file failed")
def delete_file(
    assistant_id: str = typer.Argument(..., help="The assistant id"),
    file_id: str = typer.Argument(..., help="The file id"),
    workspace: Optional[str] = typer.Option(
        None,
        "-w",
        "--workspace",
        help="The DashScope workspace id",
    ),
):
    """Delete an assistant file."""
    response = Files.delete(
        file_id,
        assistant_id=assistant_id,
        workspace=workspace,
    )
    console.print_json(
        json.dumps(response, default=lambda value: value.__dict__, ensure_ascii=False),
    )


@app.command("list")
@handle_sdk_error("List assistant files failed")
def list_files(
    assistant_id: str = typer.Argument(..., help="The assistant id"),
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
    """List assistant files."""
    response = Files.list(
        assistant_id,
        limit=limit,
        order=order,
        after=after,
        before=before,
        workspace=workspace,
    )
    console.print_json(
        json.dumps(response, default=lambda value: value.__dict__, ensure_ascii=False),
    )
