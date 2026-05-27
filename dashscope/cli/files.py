# -*- coding: utf-8 -*-
"""``files.*`` sub-commands."""
import json

import dashscope
from dashscope.common.constants import FilePurpose
from dashscope.cli.common import add_base_url_arg, ensure_ok


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------


def upload(args):
    """Handle ``dashscope files.upload``."""
    rsp = dashscope.Files.upload(
        file_path=args.file,
        purpose=args.purpose,
        description=args.description,
        base_address=args.base_url,
    )
    output = ensure_ok(rsp)
    file_id = output["uploaded_files"][0]["file_id"]
    print(f"Upload success, file id: {file_id}")


def get(args):
    """Handle ``dashscope files.get``."""
    rsp = dashscope.Files.get(file_id=args.id, base_address=args.base_url)
    output = ensure_ok(rsp)
    if output:
        print(
            f"file info:\n"
            f"{json.dumps(output, ensure_ascii=False, indent=4)}",
        )
    else:
        print("There is no uploaded file.")


def list_files(args):
    """Handle ``dashscope files.list``."""
    rsp = dashscope.Files.list(
        page=args.start_page,
        page_size=args.page_size,
        base_address=args.base_url,
    )
    output = ensure_ok(rsp)
    if output:
        print(
            f"file list info:\n"
            f"{json.dumps(output, ensure_ascii=False, indent=4)}",
        )
    else:
        print("There is no uploaded files.")


def delete(args):
    """Handle ``dashscope files.delete``."""
    ensure_ok(dashscope.Files.delete(args.id, base_address=args.base_url))
    print("Delete success")


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


def register(sub_parsers):
    """Register all ``files.*`` sub-parsers."""

    # -- files.upload -----------------------------------------------------
    p = sub_parsers.add_parser("files.upload")
    p.add_argument(
        "-f",
        "--file",
        type=str,
        required=True,
        help="The file path to upload",
    )
    p.add_argument(
        "-p",
        "--purpose",
        default=FilePurpose.fine_tune,
        const=FilePurpose.fine_tune,
        nargs="?",
        help="Purpose to upload file[fine-tune]",
        required=True,
    )
    p.add_argument(
        "-d",
        "--description",
        type=str,
        required=False,
        help="The file description.",
    )
    add_base_url_arg(p)
    p.set_defaults(func=upload)

    # -- files.get --------------------------------------------------------
    p = sub_parsers.add_parser("files.get")
    p.add_argument(
        "-i",
        "--id",
        type=str,
        required=True,
        help="The file ID",
    )
    add_base_url_arg(p)
    p.set_defaults(func=get)

    # -- files.delete -----------------------------------------------------
    p = sub_parsers.add_parser("files.delete")
    p.add_argument(
        "-i",
        "--id",
        type=str,
        required=True,
        help="The files ID",
    )
    add_base_url_arg(p)
    p.set_defaults(func=delete)

    # -- files.list -------------------------------------------------------
    p = sub_parsers.add_parser("files.list")
    p.add_argument(
        "-s",
        "--start_page",
        type=int,
        default=1,
        help="Start of page, default 1",
    )
    p.add_argument(
        "-p",
        "--page_size",
        type=int,
        default=10,
        help="The page size, default 10",
    )
    add_base_url_arg(p)
    p.set_defaults(func=list_files)
