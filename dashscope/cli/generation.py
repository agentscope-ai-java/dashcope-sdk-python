# -*- coding: utf-8 -*-
"""``generation`` sub-command group."""
from http import HTTPStatus
from typing import Optional

import typer

from dashscope.aigc import Generation
from dashscope.cli.common import console, print_failed_message

app = typer.Typer(
    name="generation",
    help="Text generation commands",
    add_completion=False,
    invoke_without_command=True,
)


@app.callback()
def callback(ctx: typer.Context):
    """Show help if no subcommand is provided."""
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


@app.command("create")
def create(
    prompt: str = typer.Option(..., "-p", "--prompt", help="Input prompt"),
    model: str = typer.Option(..., "-m", "--model", help="The model to call"),
    stream: bool = typer.Option(
        False,
        "-s",
        "--stream",
        help="Use stream mode",
    ),
    history: Optional[str] = typer.Option(  # pylint: disable=unused-argument
        None,
        "--history",
        help="The history of the request",
    ),
):
    """Call text generation API."""
    response = Generation.call(model, prompt, stream=stream)

    if stream:
        for rsp in response:
            if rsp.status_code == HTTPStatus.OK:
                console.print(rsp.output)
                console.print(rsp.usage)
            else:
                print_failed_message(rsp)
    else:
        if response.status_code == HTTPStatus.OK:
            console.print(response.output)
            console.print(response.usage)
        else:
            print_failed_message(response)
            raise typer.Exit(1)


# Backward compatibility alias
@app.command("call", hidden=True)
def call(
    prompt: str = typer.Option(..., "-p", "--prompt", help="Input prompt"),
    model: str = typer.Option(..., "-m", "--model", help="The model to call"),
    stream: bool = typer.Option(
        False,
        "-s",
        "--stream",
        help="Use stream mode",
    ),
    history: Optional[str] = typer.Option(  # pylint: disable=unused-argument
        None,
        "--history",
        help="The history of the request",
    ),
):
    """(Deprecated: use 'create' instead) Call text generation API."""
    create(
        prompt=prompt,
        model=model,
        stream=stream,
        history=history,
    )
