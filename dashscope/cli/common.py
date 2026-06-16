# -*- coding: utf-8 -*-
"""Shared utilities, constants, and helpers for the dashscope CLI."""
import logging
import os
from functools import wraps
from http import HTTPStatus
from typing import Callable, NoReturn, TypeVar
from urllib.parse import urlparse

import typer
from rich.console import Console

logger = logging.getLogger("dashscope.cli")
CommandFunction = TypeVar("CommandFunction", bound=Callable)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
POLL_INTERVAL = 30  # seconds between polling requests
LOG_PAGE_SIZE = 1000  # log lines per request
DEFAULT_PAGE_SIZE = 10
DEFAULT_START_PAGE = 1

# ---------------------------------------------------------------------------
# Rich consoles
# ---------------------------------------------------------------------------
console = Console()
err_console = Console(stderr=True)

# ---------------------------------------------------------------------------
# Response helpers
# ---------------------------------------------------------------------------


def print_failed_message(rsp):
    """Print a standardised error message for a failed API response."""
    err_console.print(
        f"[red]Failed[/red] request_id: {rsp.request_id}, "
        f"status_code: {rsp.status_code}, "
        f"code: {rsp.code}, message: {rsp.message}",
    )


def ensure_ok(rsp):
    """Return *rsp.output* when the response is OK; otherwise print the error
    and exit with code 1.

    This eliminates the repetitive ``if rsp.status_code == OK … else …``
    pattern that appears in every command handler.
    """
    if rsp.status_code == HTTPStatus.OK:
        return rsp.output
    print_failed_message(rsp)
    raise typer.Exit(1)


def success(message: str):
    """Print a success message in green."""
    console.print(f"[green]✓[/green] {message}")


def info(message: str):
    """Print an info message."""
    console.print(message)


def error(message: str, exit_code: int = 1) -> NoReturn:
    """Print an error message in red and exit."""
    err_console.print(f"[red]Error:[/red] {message}")
    raise typer.Exit(exit_code)


def handle_sdk_error(action: str):
    """Convert unexpected SDK exceptions into friendly CLI errors."""

    def decorator(command_function: CommandFunction) -> CommandFunction:
        @wraps(command_function)
        def wrapper(*args, **kwargs):
            try:
                return command_function(*args, **kwargs)
            except typer.Exit:
                raise
            except Exception as exception:
                error(f"{action}: {exception}")

        return wrapper  # type: ignore[return-value]

    return decorator


def normalize_local_path_or_url(value: str, option_name: str) -> str:
    """Return expanded local path or URL, failing early for missing files."""
    parsed_value = urlparse(value)
    if parsed_value.scheme:
        return value

    file_path = os.path.expanduser(value)
    if not os.path.exists(file_path):
        error(f"{option_name} file {file_path} does not exist")
    return file_path
