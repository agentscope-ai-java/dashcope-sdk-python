# -*- coding: utf-8 -*-
"""``deployments.*`` sub-commands."""
import time

import dashscope
from dashscope.common.constants import DeploymentStatus
from dashscope.cli.common import POLL_INTERVAL, ensure_ok, logger


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _wait_for_deployment(deployed_model):
    """Block until the deployment reaches a non-pending state."""
    try:
        while True:
            rsp = dashscope.Deployments.get(deployed_model)
            output = ensure_ok(rsp)
            status = output["status"]

            if status in (
                DeploymentStatus.PENDING,
                DeploymentStatus.DEPLOYING,
            ):
                print(f"Deployment {deployed_model} is {status}")
                time.sleep(POLL_INTERVAL)
                continue

            print(f"Deployment: {deployed_model} status: {status}")
            return
    except Exception as exc:
        logger.debug("wait_for_deployment error", exc_info=exc)
        print(
            f"You can get deployment status via: "
            f"dashscope deployments.get -d {deployed_model}",
        )


def _print_deployments(output):
    """Pretty-print a list of deployments from *output*."""
    if (
        output is None
        or "deployments" not in output
        or not output["deployments"]
    ):
        print("There is no deployed model!")
        return
    for dep in output["deployments"]:
        print(
            f"Deployed_model: {dep['deployed_model']}, "
            f"model: {dep['model_name']}, "
            f"status: {dep['status']}",
        )


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------


def call(args):
    """Handle ``dashscope deployments.call``."""
    rsp = dashscope.Deployments.call(
        model=args.model,
        capacity=args.capacity,
        suffix=args.suffix,
    )
    output = ensure_ok(rsp)
    deployed_model = output["deployed_model"]
    print(f"Create model: {deployed_model} deployment")
    _wait_for_deployment(deployed_model)


def get(args):
    """Handle ``dashscope deployments.get``."""
    rsp = dashscope.Deployments.get(args.deploy)
    output = ensure_ok(rsp)
    print(
        f"Deployed model: {output['deployed_model']} "
        f"capacity: {output['capacity']} "
        f"status: {output['status']}",
    )


def list_deployments(args):
    """Handle ``dashscope deployments.list``."""
    rsp = dashscope.Deployments.list(
        page_no=args.start_page,
        page_size=args.page_size,
    )
    output = ensure_ok(rsp)
    if output is None or not output.get("deployments"):
        print("There is no deployed model.")
        return
    _print_deployments(output)


def update(args):
    """Handle ``dashscope deployments.update``."""
    rsp = dashscope.Deployments.update(args.deployed_model, args.version)
    output = ensure_ok(rsp)
    _print_deployments(output)


def scale(args):
    """Handle ``dashscope deployments.scale``."""
    rsp = dashscope.Deployments.scale(args.deployed_model, args.capacity)
    output = ensure_ok(rsp)
    if output is None:
        print("There is no deployed model.")
        return
    print(
        f"Deployed_model: {output['deployed_model']}, "
        f"model: {output['model_name']}, "
        f"status: {output['status']}",
    )


def delete(args):
    """Handle ``dashscope deployments.delete``."""
    ensure_ok(dashscope.Deployments.delete(args.deploy))
    print(f"Deployed model: {args.deploy} delete success")


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


def register(sub_parsers):
    """Register all ``deployments.*`` sub-parsers."""

    # -- deployments.call -------------------------------------------------
    p = sub_parsers.add_parser("deployments.call")
    p.add_argument(
        "-m",
        "--model",
        required=True,
        help="The model ID",
    )
    p.add_argument(
        "-s",
        "--suffix",
        required=False,
        help="Deployment suffix, lower-cased, 8 chars max.",
    )
    p.add_argument(
        "-c",
        "--capacity",
        type=int,
        required=False,
        default=1,
        help="The target capacity",
    )
    p.set_defaults(func=call)

    # -- deployments.get --------------------------------------------------
    p = sub_parsers.add_parser("deployments.get")
    p.add_argument(
        "-d",
        "--deploy",
        required=True,
        help="The deployed model.",
    )
    p.set_defaults(func=get)

    # -- deployments.delete -----------------------------------------------
    p = sub_parsers.add_parser("deployments.delete")
    p.add_argument(
        "-d",
        "--deploy",
        required=True,
        help="The deployed model.",
    )
    p.set_defaults(func=delete)

    # -- deployments.list -------------------------------------------------
    p = sub_parsers.add_parser("deployments.list")
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
    p.set_defaults(func=list_deployments)

    # -- deployments.scale ------------------------------------------------
    p = sub_parsers.add_parser("deployments.scale")
    p.add_argument(
        "-d",
        "--deployed_model",
        type=str,
        required=True,
        help="The deployed model to scale",
    )
    p.add_argument(
        "-c",
        "--capacity",
        type=int,
        required=True,
        help="The target capacity",
    )
    p.set_defaults(func=scale)
