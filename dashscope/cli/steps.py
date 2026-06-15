# -*- coding: utf-8 -*-
"""``steps`` sub-command group."""
import json
from typing import Optional

import typer

import dashscope
from dashscope.cli.common import console, handle_sdk_error

app = typer.Typer(
    name="steps",
    help="Run step management commands",
    add_completion=False,
    invoke_without_command=True,
)


@app.callback()
def callback(ctx: typer.Context):
    """Show help if no subcommand is provided."""
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


@app.command("list")
@handle_sdk_error("List run steps failed")
def list_steps(
    run_id: str = typer.Argument(..., help="The run id"),
    thread_id: str = typer.Option(
        ...,
        "--thread-id",
        help="The thread id",
    ),
    limit: Optional[int] = typer.Option(None, "--limit", help="Maximum number of steps"),
    order: Optional[str] = typer.Option(None, "--order", help="Sort order by created_at"),
    after: Optional[str] = typer.Option(None, "--after", help="Cursor after step id"),
    before: Optional[str] = typer.Option(None, "--before", help="Cursor before step id"),
    workspace: Optional[str] = typer.Option(
        None,
        "-w",
        "--workspace",
        help="The DashScope workspace id",
    ),
):
    """List run steps."""
    response = dashscope.Steps.list(
        run_id,
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


@app.command("get")
@handle_sdk_error("Retrieve run step failed")
def get_step(
    step_id: str = typer.Argument(..., help="The step id"),
    thread_id: str = typer.Option(
        ...,
        "--thread-id",
        help="The thread id",
    ),
    run_id: str = typer.Option(
        ...,
        "--run-id",
        help="The run id",
    ),
    workspace: Optional[str] = typer.Option(
        None,
        "-w",
        "--workspace",
        help="The DashScope workspace id",
    ),
):
    """Retrieve a run step."""
    response = dashscope.Steps.retrieve(
        step_id,
        thread_id=thread_id,
        run_id=run_id,
        workspace=workspace,
    )
    console.print_json(
        json.dumps(response, default=lambda value: value.__dict__, ensure_ascii=False),
    )
