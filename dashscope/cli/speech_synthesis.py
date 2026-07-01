# -*- coding: utf-8 -*-
"""``speech-synthesis`` sub-command group."""
import json
from typing import Optional

import typer

import dashscope
from dashscope.cli.common import console, handle_sdk_error

app = typer.Typer(
    name="speech-synthesis",
    help="Speech synthesis commands",
    add_completion=False,
    invoke_without_command=True,
)


@app.callback()
def callback(ctx: typer.Context):
    """Show help if no subcommand is provided."""
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


@app.command("create")
@handle_sdk_error("Speech synthesis request failed")
def create(
    model: str = typer.Option(..., "-m", "--model", help="The model to call"),
    text: str = typer.Option(..., "-t", "--text", help="Text to synthesize"),
    voice: str = typer.Option(..., "--voice", help="Voice name"),
    audio_format: str = typer.Option(
        "wav",
        "--audio-format",
        help="Audio format, such as wav, pcm or mp3",
    ),
    sample_rate: int = typer.Option(
        24000,
        "--sample-rate",
        help="Audio sample rate",
    ),
    workspace: Optional[str] = typer.Option(
        None,
        "-w",
        "--workspace",
        help="The DashScope workspace id",
    ),
    url: Optional[str] = typer.Option(
        None,
        "--url",
        help="Custom HTTP base URL",
    ),
    volume: Optional[int] = typer.Option(
        None,
        "--volume",
        help="Volume value",
    ),
    rate: Optional[int] = typer.Option(
        None,
        "--rate",
        help="Speech rate value",
    ),
    pitch: Optional[int] = typer.Option(None, "--pitch", help="Pitch value"),
):
    """Call HTTP speech synthesis API."""
    result = dashscope.HttpSpeechSynthesizer.call(
        model=model,
        text=text,
        voice=voice,
        audio_format=audio_format,
        sample_rate=sample_rate,
        workspace=workspace,
        url=url,
        volume=volume,
        rate=rate,
        pitch=pitch,
    )
    output = {
        "audio_url": result.audio_url,
        "audio_id": result.audio_id,
        "expires_at": result.expires_at,
        "sentences": result.sentences,
    }
    console.print_json(json.dumps(output, ensure_ascii=False))
