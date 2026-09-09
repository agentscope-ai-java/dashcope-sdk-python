# -*- coding: utf-8 -*-
"""``image-generation`` sub-command group."""
import json
from typing import List, Optional

import typer

from dashscope.aigc.image_generation import ImageGeneration
from dashscope.api_entities.dashscope_response import Message, Role
from dashscope.cli.common import (
    console,
    ensure_ok,
    handle_sdk_error,
    normalize_local_path_or_url,
)

app = typer.Typer(
    name="image-generation",
    help="Image generation commands",
    add_completion=False,
    invoke_without_command=True,
)


@app.callback()
def callback(ctx: typer.Context):
    """Show help if no subcommand is provided."""
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


@app.command("create")
@handle_sdk_error("Image generation request failed")
def create(
    model: str = typer.Option(..., "-m", "--model", help="The model to call"),
    text: str = typer.Option(..., "-t", "--text", help="User text prompt"),
    images: Optional[List[str]] = typer.Option(
        None,
        "--image",
        help=(
            "Reference image URL or local file path, "
            "can be used multiple times"
        ),
    ),
    workspace: Optional[str] = typer.Option(
        None,
        "-w",
        "--workspace",
        help="The DashScope workspace id",
    ),
    size: Optional[str] = typer.Option(
        None,
        "--size",
        help="Output image size",
    ),
    n: Optional[int] = typer.Option(
        None,
        "-n",
        "--n",
        help="Number of images",
    ),
    max_images: Optional[int] = typer.Option(
        None,
        "--max-images",
        help="Maximum number of images",
    ),
):
    """Call image generation API."""
    content = [{"text": text}]
    if images:
        content.extend(
            {"image": normalize_local_path_or_url(image, "--image")}
            for image in images
        )

    response = ImageGeneration.call(
        model=model,
        messages=[Message(role=Role.USER, content=content)],
        workspace=workspace,
        size=size,
        n=n,
        max_images=max_images,
    )
    output = ensure_ok(response)
    console.print_json(json.dumps(output, ensure_ascii=False))
    usage = getattr(response, "usage", None)
    if usage:
        console.print_json(json.dumps(usage, ensure_ascii=False))
