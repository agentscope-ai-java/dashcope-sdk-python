# -*- coding: utf-8 -*-
"""Shared utilities, constants, and helpers for the dashscope CLI."""
import argparse
import logging
import sys
from http import HTTPStatus

logger = logging.getLogger("dashscope.cli")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
POLL_INTERVAL = 30  # seconds between polling requests
LOG_PAGE_SIZE = 1000  # log lines per request
DEFAULT_PAGE_SIZE = 10
DEFAULT_START_PAGE = 1

AGENTIC_RL_PREFIXES = {"agentic-rl", "rl"}

# ---------------------------------------------------------------------------
# Response helpers
# ---------------------------------------------------------------------------


def print_failed_message(rsp):
    """Print a standardised error message for a failed API response."""
    print(
        f"Failed, request_id: {rsp.request_id}, status_code: "
        f"{rsp.status_code}, code: {rsp.code}, message: {rsp.message}",
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
    sys.exit(1)


# ---------------------------------------------------------------------------
# argparse helpers
# ---------------------------------------------------------------------------


class ParseKVAction(argparse.Action):
    """Parse ``key=value`` pairs from the command line into a dict.

    Usage::

        parser.add_argument(
            "--hyper-parameters",
            nargs="+",
            dest="params",
            action=ParseKVAction,
            metavar="KEY1=VALUE1",
        )
    """

    def __call__(self, parser, namespace, values, option_string=None):
        result = {}
        for each in values:
            try:
                key, value = each.split("=", 1)
                result[key] = value
            except ValueError as exc:
                message = (
                    f"\nTraceback: {exc}"
                    f"\nError on '{each}' || It should be 'key=value'"
                )
                raise argparse.ArgumentError(self, message)
        setattr(namespace, self.dest, result)


def add_pagination_args(parser):
    """Add the common ``-s/--start_page`` and ``-p/--page_size`` arguments."""
    parser.add_argument(
        "-s",
        "--start_page",
        type=int,
        default=DEFAULT_START_PAGE,
        help=f"Start of page, default {DEFAULT_START_PAGE}",
    )
    parser.add_argument(
        "-p",
        "--page_size",
        type=int,
        default=DEFAULT_PAGE_SIZE,
        help=f"The page size, default {DEFAULT_PAGE_SIZE}",
    )


def add_base_url_arg(parser):
    """Add the ``-u/--base_url`` argument shared by Files / Oss commands."""
    parser.add_argument(
        "-u",
        "--base_url",
        type=str,
        help="The base url.",
        required=False,
    )
