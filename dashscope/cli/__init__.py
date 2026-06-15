# -*- coding: utf-8 -*-
# pylint: disable=wrong-import-position
"""DashScope command-line entry point.

This package is intentionally thin — all command-specific logic lives in
sub-modules (generation, fine_tunes, files, etc.).
"""
import sys
import warnings

# Suppress urllib3 NotOpenSSLWarning on systems with LibreSSL
warnings.filterwarnings(
    "ignore",
    message=".*urllib3.*only supports OpenSSL.*",
    category=Warning,
)

import typer  # noqa: E402

import dashscope  # noqa: E402
from dashscope.cli import (  # noqa: E402
    deployments,
    files,
    fine_tunes,
    generation,
    oss,
)


# ---------------------------------------------------------------------------
# Legacy command compatibility layer
# ---------------------------------------------------------------------------

# Command name mapping: old -> new
_COMMAND_MAP = {
    "fine_tunes.call": "fine-tunes create",
    "fine_tunes.get": "fine-tunes get",
    "fine_tunes.list": "fine-tunes list",
    "fine_tunes.stream": "fine-tunes stream",
    "fine_tunes.cancel": "fine-tunes cancel",
    "fine_tunes.delete": "fine-tunes delete",
    "generation.call": "generation create",
    "files.upload": "files upload",
    "files.get": "files get",
    "files.list": "files list",
    "files.delete": "files delete",
    "deployments.call": "deployments create",
    "deployments.get": "deployments get",
    "deployments.list": "deployments list",
    "deployments.scale": "deployments scale",
    "deployments.delete": "deployments delete",
    "oss.upload": "oss upload",
}

# Parameter name mapping: old -> new (underscore to dash)
_PARAM_MAP = {
    "--training_file_ids": "--training-file-ids",
    "--validation_file_ids": "--validation-file-ids",
    "--n_epochs": "--n-epochs",
    "--batch_size": "--batch-size",
    "--learning_rate": "--learning-rate",
    "--prompt_loss": "--prompt-loss",
    "--hyper_parameters": "--hyper-parameters",
    "--file_id": "--file-id",
    "--deployed_model": "--deployed-model",
    "--base_url": "--base-url",
    "--api_key": "--api-key",
    "--start_page": "--start-page",
    "--page_size": "--page-size",
}


def _translate_legacy_args(argv):
    """Translate legacy argparse command format to Typer format.

    Legacy format:  dashscope fine_tunes.call --training_file_ids ...
    New format:     dashscope fine-tunes call --training-file-ids ...

    Returns modified argv list.
    """
    if len(argv) < 2:
        return argv

    new_argv = [argv[0]]  # Keep program name
    i = 1

    # Check if first arg is a legacy command
    if i < len(argv) and argv[i] in _COMMAND_MAP:
        # Split "fine_tunes.call" into ["fine-tunes", "call"]
        new_cmd = _COMMAND_MAP[argv[i]].split()
        new_argv.extend(new_cmd)
        i += 1

    # Process remaining args
    while i < len(argv):
        arg = argv[i]

        # Translate parameter names
        if arg in _PARAM_MAP:
            new_argv.append(_PARAM_MAP[arg])
        elif arg.startswith("--") and "=" in arg:
            opt, val = arg.split("=", 1)
            if opt in _PARAM_MAP:
                new_argv.append(f"{_PARAM_MAP[opt]}={val}")
            else:
                new_argv.append(arg)
        else:
            new_argv.append(arg)

        i += 1

    return new_argv


def _extract_global_api_key(argv):
    """Extract global -k/--api-key from argv and set dashscope.api_key.

    Returns modified argv with api-key args removed.
    """
    new_argv = []
    i = 0
    while i < len(argv):
        arg = argv[i]

        # Check for -k or --api-key
        if arg in ("-k", "--api-key"):
            # Next arg should be the key value
            if i + 1 < len(argv):
                dashscope.api_key = argv[i + 1]
                i += 2  # Skip both -k and the value
                continue
        elif arg.startswith("--api-key="):
            # Handle --api-key=value format
            dashscope.api_key = arg.split("=", 1)[1]
            i += 1
            continue

        new_argv.append(arg)
        i += 1

    return new_argv


# ---------------------------------------------------------------------------
# Typer app
# ---------------------------------------------------------------------------

app = typer.Typer(
    name="dashscope",
    help="DashScope command line tools.",
    add_completion=False,
    no_args_is_help=True,
    rich_markup_mode="rich",
)

# Register sub-command groups
app.add_typer(generation.app)
app.add_typer(fine_tunes.app, name="ft")
app.add_typer(fine_tunes.app, name="fine-tunes", hidden=True)
app.add_typer(files.app)
app.add_typer(deployments.app)
app.add_typer(oss.app)


def _register_rl_app():
    """Lazily import and register the Agentic-RL Typer app.

    Wrapped in a function so that a missing optional dependency
    won't crash the entire CLI at import time.
    """
    try:
        from dashscope.cli.agentic_rl import app as rl_app

        app.add_typer(
            rl_app,
            name="rl",
            help="🚀 Agentic RL fine-tuning commands",
        )
    except ImportError:
        pass
    except Exception:
        pass


_register_rl_app()


def main():
    """Entry point for the ``dashscope`` console script."""
    # Extract global api-key parameter FIRST
    argv = _extract_global_api_key(sys.argv)

    # Then translate legacy command format
    argv = _translate_legacy_args(argv)

    # Update sys.argv for Typer
    sys.argv = argv

    app()
