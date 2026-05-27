# -*- coding: utf-8 -*-
"""``fine_tunes.*`` sub-commands."""
import time

import dashscope
from dashscope.common.constants import TaskStatus
from dashscope.cli.common import (
    LOG_PAGE_SIZE,
    POLL_INTERVAL,
    ParseKVAction,
    ensure_ok,
    logger,
    print_failed_message,
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _wait_for_job(job_id):
    """Block until the fine-tune job reaches a terminal state."""
    try:
        while True:
            rsp = dashscope.FineTunes.get(job_id)
            output = ensure_ok(rsp)
            status = output["status"]

            if status == TaskStatus.FAILED:
                print("Fine-tune FAILED!")
                return
            if status == TaskStatus.CANCELED:
                print("Fine-tune task CANCELED")
                return
            if status == TaskStatus.RUNNING:
                print("Fine-tuning is RUNNING, start get output stream.")
                _stream_events(job_id)
                return
            if status == TaskStatus.SUCCEEDED:
                print(
                    f"Fine-tune task success, fine-tuned model:"
                    f"{output['finetuned_output']}",
                )
                return

            # Otherwise still pending — poll again later
            print(f"The fine-tune task is: {status}")
            time.sleep(POLL_INTERVAL)
    except Exception as exc:
        logger.debug("wait_for_job error", exc_info=exc)
        print(
            f"You can stream output via: "
            f"dashscope fine_tunes.stream -j {job_id}",
        )


def _stream_events(job_id):
    """Stream real-time events for *job_id*, then dump logs on completion."""
    # Check if job is already in a terminal state
    rsp = dashscope.FineTunes.get(job_id)
    if rsp.status_code != 200:
        print_failed_message(rsp)
        return

    if rsp.output["status"] in (
        TaskStatus.FAILED,
        TaskStatus.CANCELED,
        TaskStatus.SUCCEEDED,
    ):
        print(f"Fine-tune job: {job_id} is {rsp.output['status']}")
        _dump_logs(job_id)
        return

    # Live-stream events
    try:
        for rsp in dashscope.FineTunes.stream_events(job_id):
            if rsp.status_code == 200:
                print(rsp.output)
            else:
                print_failed_message(rsp)
    except Exception as exc:
        logger.debug("stream_events error", exc_info=exc)
        print(
            f"You can stream output via: "
            f"dashscope fine-tunes.stream -j {job_id}",
        )


def _dump_logs(job_id):
    """Page through and print all logs for *job_id*."""
    offset = 1
    while True:
        rsp = dashscope.FineTunes.logs(
            job_id, offset=offset, line=LOG_PAGE_SIZE
        )
        output = ensure_ok(rsp)
        for line in output["logs"]:
            print(line)
        if output["total"] < LOG_PAGE_SIZE:
            break
        offset += LOG_PAGE_SIZE


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------


def call(args):
    """Handle ``dashscope fine_tunes.call``."""
    params = {}
    if args.n_epochs is not None:
        params["n_epochs"] = args.n_epochs
    if args.batch_size is not None:
        params["batch_size"] = args.batch_size
    if args.learning_rate is not None:
        params["learning_rate"] = args.learning_rate
    if args.prompt_loss is not None:
        params["prompt_loss"] = args.prompt_loss
    if args.params:
        params.update(args.params)

    rsp = dashscope.FineTunes.call(
        model=args.model,
        training_file_ids=args.training_file_ids,
        validation_file_ids=args.validation_file_ids,
        mode=args.mode,
        hyper_parameters=params,
    )
    output = ensure_ok(rsp)
    print(f"Create fine-tune job success, job_id: {output['job_id']}")
    _wait_for_job(output["job_id"])


def get(args):
    """Handle ``dashscope fine_tunes.get``."""
    rsp = dashscope.FineTunes.get(args.job)
    output = ensure_ok(rsp)
    status = output["status"]

    if status == TaskStatus.FAILED:
        print("Fine-tune failed!")
    elif status == TaskStatus.CANCELED:
        print("Fine-tune task canceled")
    elif status == TaskStatus.SUCCEEDED:
        print(
            f"Fine-tune task success, fine-tuned model : "
            f"{output['finetuned_output']}",
        )
    else:
        print(f"The fine-tune task is: {status}")


def list_jobs(args):
    """Handle ``dashscope fine_tunes.list``."""
    rsp = dashscope.FineTunes.list(
        page=args.start_page,
        page_size=args.page_size,
    )
    output = ensure_ok(rsp)
    if output is None or not output.get("jobs"):
        print("There is no fine-tuned model.")
        return

    for job in output["jobs"]:
        line = (
            f"job: {job['job_id']}, status: {job['status']}, "
            f"base model: {job['model']}"
        )
        if job["status"] == TaskStatus.SUCCEEDED:
            line += f", fine-tuned model: {job['finetuned_output']}"
        print(line)


def events(args):
    """Handle ``dashscope fine_tunes.stream``."""
    _stream_events(args.job)


def cancel(args):
    """Handle ``dashscope fine_tunes.cancel``."""
    ensure_ok(dashscope.FineTunes.cancel(args.job))
    print(f"Cancel fine-tune job: {args.job} success!")


def delete(args):
    """Handle ``dashscope fine_tunes.delete``."""
    ensure_ok(dashscope.FineTunes.delete(args.job))
    print(f"fine_tune job: {args.job} delete success")


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


def register(sub_parsers):
    """Register all ``fine_tunes.*`` sub-parsers."""

    # -- fine_tunes.call --------------------------------------------------
    p = sub_parsers.add_parser("fine_tunes.call")
    p.add_argument(
        "-t",
        "--training_file_ids",
        required=True,
        nargs="+",
        help="Training file ids which upload by File command.",
    )
    p.add_argument(
        "-v",
        "--validation_file_ids",
        required=False,
        nargs="+",
        default=[],
        help="Validation file ids which upload by File command.",
    )
    p.add_argument(
        "-m",
        "--model",
        type=str,
        required=True,
        help="The based model to start fine-tune.",
    )
    p.add_argument(
        "--mode",
        type=str,
        required=False,
        choices=["sft", "efficient_sft"],
        help="Select fine-tune mode sft or efficient_sft",
    )
    p.add_argument(
        "-e",
        "--n_epochs",
        type=int,
        required=False,
        help="How many epochs to fine-tune.",
    )
    p.add_argument(
        "-b",
        "--batch_size",
        type=int,
        required=False,
        help="How big is batch_size.",
    )
    p.add_argument(
        "-l",
        "--learning_rate",
        type=float,
        required=False,
        help="The fine-tune learning rate.",
    )
    p.add_argument(
        "-p",
        "--prompt_loss",
        type=float,
        required=False,
        help="The fine-tune prompt loss.",
    )
    p.add_argument(
        "--hyper_parameters",
        nargs="+",
        dest="params",
        action=ParseKVAction,
        help="Extra hyper parameters accepts by key1=value1 key2=value2",
        metavar="KEY1=VALUE1",
    )
    p.set_defaults(func=call)

    # -- fine_tunes.get ---------------------------------------------------
    p = sub_parsers.add_parser("fine_tunes.get")
    p.add_argument(
        "-j",
        "--job",
        type=str,
        required=True,
        help="The fine-tune job id.",
    )
    p.set_defaults(func=get)

    # -- fine_tunes.delete ------------------------------------------------
    p = sub_parsers.add_parser("fine_tunes.delete")
    p.add_argument(
        "-j",
        "--job",
        type=str,
        required=True,
        help="The fine-tune job id.",
    )
    p.set_defaults(func=delete)

    # -- fine_tunes.stream ------------------------------------------------
    p = sub_parsers.add_parser("fine_tunes.stream")
    p.add_argument(
        "-j",
        "--job",
        type=str,
        required=True,
        help="The fine-tune job id.",
    )
    p.set_defaults(func=events)

    # -- fine_tunes.list --------------------------------------------------
    p = sub_parsers.add_parser("fine_tunes.list")
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
    p.set_defaults(func=list_jobs)

    # -- fine_tunes.cancel ------------------------------------------------
    p = sub_parsers.add_parser("fine_tunes.cancel")
    p.add_argument(
        "-j",
        "--job",
        type=str,
        required=True,
        help="The fine-tune job id.",
    )
    p.set_defaults(func=cancel)
