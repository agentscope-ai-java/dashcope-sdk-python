# -*- coding: utf-8 -*-
"""``assistants`` sub-command group."""
import json
from typing import List, Optional

import typer

import dashscope
from dashscope.cli.common import console, error, handle_sdk_error

app = typer.Typer(
    name="assistants",
    help="Assistant management commands",
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
@handle_sdk_error("Create assistant failed")
def create(
    model: str = typer.Option(..., "-m", "--model", help="The model to use"),
    name: Optional[str] = typer.Option(None, "--name", help="Assistant name"),
    description: Optional[str] = typer.Option(
        None,
        "--description",
        help="Assistant description",
    ),
    instructions: Optional[str] = typer.Option(
        None,
        "--instructions",
        help="Assistant instructions",
    ),
    tools: Optional[str] = typer.Option(
        None,
        "--tools",
        help="Tools as a JSON array string",
    ),
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
    top_p: Optional[float] = typer.Option(
        None,
        "--top-p",
        help="Top-p sampling",
    ),
    top_k: Optional[int] = typer.Option(
        None,
        "--top-k",
        help="Top-k sampling",
    ),
    temperature: Optional[float] = typer.Option(
        None,
        "--temperature",
        help="Sampling temperature",
    ),
    max_tokens: Optional[int] = typer.Option(
        None,
        "--max-tokens",
        help="Maximum output tokens",
    ),
):
    """Create an assistant."""
    response = dashscope.Assistants.create(
        model=model,
        name=name,
        description=description,
        instructions=instructions,
        tools=_parse_json_array(tools, "tools"),
        file_ids=file_ids or [],
        metadata=_parse_json_object(metadata, "metadata"),
        workspace=workspace,
        top_p=top_p,
        top_k=top_k,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    console.print_json(
        json.dumps(
            response,
            default=lambda value: value.__dict__,
            ensure_ascii=False,
        ),
    )


@app.command("list")
@handle_sdk_error("List assistants failed")
def list_assistants(
    limit: Optional[int] = typer.Option(
        None,
        "--limit",
        help="Maximum number of assistants",
    ),
    order: Optional[str] = typer.Option(
        None,
        "--order",
        help="Sort order by created_at",
    ),
    after: Optional[str] = typer.Option(
        None,
        "--after",
        help="Cursor after assistant id",
    ),
    before: Optional[str] = typer.Option(
        None,
        "--before",
        help="Cursor before assistant id",
    ),
    workspace: Optional[str] = typer.Option(
        None,
        "-w",
        "--workspace",
        help="The DashScope workspace id",
    ),
):
    """List assistants."""
    response = dashscope.Assistants.list(
        limit=limit,
        order=order,
        after=after,
        before=before,
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
@handle_sdk_error("Retrieve assistant failed")
def get_assistant(
    assistant_id: str = typer.Argument(..., help="The assistant id"),
    workspace: Optional[str] = typer.Option(
        None,
        "-w",
        "--workspace",
        help="The DashScope workspace id",
    ),
):
    """Retrieve an assistant."""
    response = dashscope.Assistants.retrieve(
        assistant_id,
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
@handle_sdk_error("Update assistant failed")
def update_assistant(
    assistant_id: str = typer.Argument(..., help="The assistant id"),
    model: Optional[str] = typer.Option(
        None,
        "-m",
        "--model",
        help="The model to use",
    ),
    name: Optional[str] = typer.Option(None, "--name", help="Assistant name"),
    description: Optional[str] = typer.Option(
        None,
        "--description",
        help="Assistant description",
    ),
    instructions: Optional[str] = typer.Option(
        None,
        "--instructions",
        help="Assistant instructions",
    ),
    tools: Optional[str] = typer.Option(
        None,
        "--tools",
        help="Tools as a JSON array string",
    ),
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
    top_p: Optional[float] = typer.Option(
        None,
        "--top-p",
        help="Top-p sampling",
    ),
    top_k: Optional[int] = typer.Option(
        None,
        "--top-k",
        help="Top-k sampling",
    ),
    temperature: Optional[float] = typer.Option(
        None,
        "--temperature",
        help="Sampling temperature",
    ),
    max_tokens: Optional[int] = typer.Option(
        None,
        "--max-tokens",
        help="Maximum output tokens",
    ),
):
    """Update an assistant."""
    response = dashscope.Assistants.update(
        assistant_id,
        model=model,
        name=name,
        description=description,
        instructions=instructions,
        tools=_parse_json_array(tools, "tools"),
        file_ids=file_ids or [],
        metadata=_parse_json_object(metadata, "metadata"),
        workspace=workspace,
        top_p=top_p,
        top_k=top_k,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    console.print_json(
        json.dumps(
            response,
            default=lambda value: value.__dict__,
            ensure_ascii=False,
        ),
    )


@app.command("delete")
@handle_sdk_error("Delete assistant failed")
def delete_assistant(
    assistant_id: str = typer.Argument(..., help="The assistant id"),
    workspace: Optional[str] = typer.Option(
        None,
        "-w",
        "--workspace",
        help="The DashScope workspace id",
    ),
):
    """Delete an assistant."""
    response = dashscope.Assistants.delete(
        assistant_id,
        workspace=workspace,
    )
    console.print_json(
        json.dumps(
            response,
            default=lambda value: value.__dict__,
            ensure_ascii=False,
        ),
    )
