# -*- coding: utf-8 -*-
"""``oss.upload`` sub-command."""
import os

from dashscope.utils.oss_utils import OssUtils
from dashscope.cli.common import add_base_url_arg


# ---------------------------------------------------------------------------
# Command handler
# ---------------------------------------------------------------------------


def upload(args):
    """Handle ``dashscope oss.upload``."""
    print(f"Start oss.upload: model={args.model}, file={args.file}")

    if not args.file or not args.model:
        print("Please specify the model and file path")
        return

    file_path = os.path.expanduser(args.file)
    if not os.path.exists(file_path):
        print(f"File {file_path} does not exist")
        return

    api_key = os.environ.get("DASHSCOPE_API_KEY", args.api_key)
    if not api_key:
        print(
            "Please set your DashScope API key as environment variable "
            "DASHSCOPE_API_KEY or pass it as argument by -k/--api_key",
        )
        return

    oss_url, _ = OssUtils.upload(
        model=args.model,
        file_path=file_path,
        api_key=api_key,
        base_address=args.base_url,
    )

    if not oss_url:
        print(f"Failed to upload file: {file_path}")
        return

    print(f"Uploaded oss url: {oss_url}")


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


def register(sub_parsers):
    """Register the ``oss.upload`` sub-parser."""
    p = sub_parsers.add_parser("oss.upload")
    p.add_argument(
        "-f",
        "--file",
        type=str,
        required=True,
        help="The file path to upload",
    )
    p.add_argument(
        "-m",
        "--model",
        type=str,
        required=True,
        help="The model name",
    )
    p.add_argument(
        "-k",
        "--api_key",
        type=str,
        required=False,
        help="The dashscope api key",
    )
    add_base_url_arg(p)
    p.set_defaults(func=upload)
