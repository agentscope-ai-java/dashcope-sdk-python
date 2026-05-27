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
)


@app.command("call")
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
