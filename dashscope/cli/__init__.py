# -*- coding: utf-8 -*-
"""DashScope command-line entry point.

This package is intentionally thin — all command-specific logic lives in
sub-modules (generation, fine_tunes, files, etc.).
"""
import argparse
import sys

import dashscope
from dashscope.cli.common import AGENTIC_RL_PREFIXES
from dashscope.cli import deployments, files, fine_tunes, generation, oss


def main():
    # -----------------------------------------------------------------
    # 1. Route check: forward Agentic-RL commands to the Typer app
    # -----------------------------------------------------------------
    if len(sys.argv) > 1 and sys.argv[1] in AGENTIC_RL_PREFIXES:
        # Use a local copy so we don't mutate sys.argv for other code
        forwarded_argv = sys.argv[1:]  # drop program name
        forwarded_argv.pop(0)  # drop the prefix token

        # pylint: disable=no-name-in-module
        from dashscope.finetune.reinforcement import app

        sys.argv = [sys.argv[0]] + forwarded_argv
        app()
        return 0

    # -----------------------------------------------------------------
    # 2. Build the argparse parser and register all sub-commands
    # -----------------------------------------------------------------
    parser = argparse.ArgumentParser(
        prog="dashscope",
        description="dashscope command line tools.",
    )
    parser.add_argument("-k", "--api-key", help="Dashscope API key.")

    sub_parsers = parser.add_subparsers(help="Api subcommands")

    # Each module exposes a ``register(sub_parsers)`` function that adds
    # its own sub-commands and wires up ``set_defaults(func=handler)``.
    generation.register(sub_parsers)
    fine_tunes.register(sub_parsers)
    oss.register(sub_parsers)
    files.register(sub_parsers)
    deployments.register(sub_parsers)

    # -----------------------------------------------------------------
    # 3. Parse and dispatch
    # -----------------------------------------------------------------
    args = parser.parse_args()

    if args.api_key is not None:
        dashscope.api_key = args.api_key

    if not hasattr(args, "func"):
        # No sub-command given — show help and exit with an error code
        parser.print_help()
        return 1

    args.func(args)
    return 0
