# -*- coding: utf-8 -*-
"""``deployments`` sub-command group."""
import time
from typing import Optional

import typer

import dashscope
from dashscope.common.constants import DeploymentStatus
from dashscope.cli.common import (
    POLL_INTERVAL,
    console,
    err_console,
    ensure_ok,
    logger,
    success,
)

app = typer.Typer(
    name="deployments",
    help="Model deployment commands",
    add_completion=False,
    invoke_without_command=True,
)


@app.callback()
def callback(ctx: typer.Context):
    """Show help if no subcommand is provided."""
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _wait_for_deployment(deployed_model: str):
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
                console.print(f"Deployment {deployed_model} is {status}")
                time.sleep(POLL_INTERVAL)
                continue

            console.print(f"Deployment: {deployed_model} status: {status}")
            return
    except typer.Exit:
        raise
    except Exception as exc:
        logger.debug("wait_for_deployment error", exc_info=exc)
        err_console.print(
            f"You can get deployment status via: "
            f"[cyan]dashscope deployments get {deployed_model}[/cyan]",
        )


def _print_deployments(output):
    """Pretty-print a list of deployments from *output*."""
    if (
        output is None
        or "deployments" not in output
        or not output["deployments"]
    ):
        console.print("There is no deployed model!")
        return
    for dep in output["deployments"]:
        console.print(
            f"Deployed_model: {dep['deployed_model']}, "
            f"model: {dep['model_name']}, "
            f"status: {dep['status']}",
        )


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@app.command("create")
def create(
    model: str = typer.Option(..., "-m", "--model", help="The model ID"),
    suffix: Optional[str] = typer.Option(
        None,
        "-s",
        "--suffix",
        help="Deployment suffix, lower-cased, 8 chars max.",
    ),
    capacity: int = typer.Option(
        1,
        "-c",
        "--capacity",
        help="The target capacity",
    ),
):
    """Create a model deployment."""
    rsp = dashscope.Deployments.call(
        model=model,
        capacity=capacity,
        suffix=suffix,  # type: ignore[arg-type]
    )
    output = ensure_ok(rsp)
    deployed_model = output["deployed_model"]
    success(f"Create model: {deployed_model} deployment")
    _wait_for_deployment(deployed_model)


# Backward compatibility alias
@app.command("call", hidden=True)
def call(
    model: str = typer.Option(..., "-m", "--model", help="The model ID"),
    suffix: Optional[str] = typer.Option(
        None,
        "-s",
        "--suffix",
        help="Deployment suffix, lower-cased, 8 chars max.",
    ),
    capacity: int = typer.Option(
        1,
        "-c",
        "--capacity",
        help="The target capacity",
    ),
):
    """(Deprecated: use 'create' instead) Create a model deployment."""
    create(
        model=model,
        suffix=suffix,
        capacity=capacity,
    )


@app.command("get")
def get(
    deployed_model: str = typer.Argument(..., help="The deployed model name"),
):
    """Get deployment status."""
    rsp = dashscope.Deployments.get(deployed_model)
    output = ensure_ok(rsp)
    console.print(
        f"Deployed model: {output['deployed_model']} "
        f"capacity: {output['capacity']} "
        f"status: {output['status']}",
    )


@app.command("list")
def list_deployments(
    page: int = typer.Option(1, "-p", "--page", help="Page number"),
    size: int = typer.Option(10, "-s", "--size", help="Page size"),
):
    """List model deployments."""
    rsp = dashscope.Deployments.list(page_no=page, page_size=size)
    output = ensure_ok(rsp)
    if output is None or not output.get("deployments"):
        console.print("There is no deployed model.")
        return
    _print_deployments(output)


@app.command("scale")
def scale(
    deployed_model: str = typer.Argument(
        ...,
        help="The deployed model to scale",
    ),
    capacity: int = typer.Option(
        ...,
        "-c",
        "--capacity",
        help="The target capacity",
    ),
):
    """Scale a deployment's capacity."""
    rsp = dashscope.Deployments.scale(deployed_model, capacity)
    output = ensure_ok(rsp)
    if output is None:
        console.print("There is no deployed model.")
        return
    console.print(
        f"Deployed_model: {output['deployed_model']}, "
        f"model: {output['model_name']}, "
        f"status: {output['status']}",
    )


@app.command("delete")
def delete(
    deployed_model: str = typer.Argument(..., help="The deployed model name"),
):
    """Delete a deployment."""
    ensure_ok(dashscope.Deployments.delete(deployed_model))
    success(f"Deployed model: {deployed_model} delete success")
