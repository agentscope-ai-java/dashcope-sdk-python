# -*- coding: utf-8 -*-
"""``generation.call`` sub-command."""
from http import HTTPStatus

from dashscope.aigc import Generation
from dashscope.cli.common import print_failed_message


# ---------------------------------------------------------------------------
# Command handler
# ---------------------------------------------------------------------------


def call(args):
    """Handle ``dashscope generation.call``."""
    response = Generation.call(args.model, args.prompt, stream=args.stream)
    if args.stream:
        for rsp in response:
            if rsp.status_code == HTTPStatus.OK:
                print(rsp.output)
                print(rsp.usage)
            else:
                print_failed_message(rsp)
    else:
        if response.status_code == HTTPStatus.OK:
            print(response.output)
            print(response.usage)
        else:
            print_failed_message(response)


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


def register(sub_parsers):
    """Register the ``generation.call`` sub-parser."""
    parser = sub_parsers.add_parser("generation.call")
    parser.add_argument(
        "-p",
        "--prompt",
        type=str,
        required=True,
        help="Input prompt",
    )
    parser.add_argument(
        "-m",
        "--model",
        type=str,
        required=True,
        help="The model to call.",
    )
    parser.add_argument(
        "--history",
        type=str,
        required=False,
        help="The history of the request.",
    )
    parser.add_argument(
        "-s",
        "--stream",
        default=False,
        action="store_true",
        help="Use stream mode, default false.",
    )
    parser.set_defaults(func=call)
