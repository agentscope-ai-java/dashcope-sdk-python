# -*- coding: utf-8 -*-
"""Shared utilities, constants, and helpers for the dashscope CLI."""
import logging
from http import HTTPStatus
from typing import NoReturn

import typer
from rich.console import Console

logger = logging.getLogger("dashscope.cli")

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
