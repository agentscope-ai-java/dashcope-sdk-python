# -*- coding: utf-8 -*-
"""DashScope unified CLI — single Typer application.

All sub-commands are registered via ``add_typer()`` from their respective
modules.
"""
import typer

from dashscope.cli import (
    deployments,
    files,
    fine_tunes,
    generation,
    oss,
)

app = typer.Typer(
    name="dashscope",
    help="DashScope command line tools.",
    add_completion=False,
    no_args_is_help=True,
    rich_markup_mode="rich",
)

# Register sub-command groups
app.add_typer(generation.app)
app.add_typer(fine_tunes.app)
app.add_typer(files.app)
app.add_typer(deployments.app)
app.add_typer(oss.app)


def _register_rl_app():
    """Lazily import and register the Agentic-RL Typer app.

    Wrapped in a function so that a missing optional dependency
    won't crash the entire CLI at import time.
    """
    try:
        from dashscope.finetune.reinforcement.common.cli import app as rl_app

        app.add_typer(
            rl_app,
            name="rl",
            help="🚀 Agentic RL fine-tuning commands",
        )
    except ImportError:
        # reinforcement module not available — skip silently
        pass
    except Exception:
        # Any other issue — skip silently
        pass


_register_rl_app()


def main():
    """Entry point for the ``dashscope`` console script."""
    app()
