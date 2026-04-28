# dashscope/cli_agentic_rl.py
# -*- coding: utf-8 -*-
"""
Agentic RL Fine-Tuning CLI
Production-grade command-line interface built with Typer, Rich, and AsyncIO.
"""
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any, Union

import typer
import yaml
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.json import JSON

from dashscope.finetune.agentic_rl import AgenticRL
from dashscope.finetune.reinforcement.common.errors import OutputError
from dashscope.finetune.reinforcement import (logger,
                                              set_api_key,
                                              serialize_for_output,
                                              AgenticRLTuning,
                                              RolloutFunctionComponent,
                                              RewardFunctionComponent,
                                              FunctionType,
                                              RewardInput,
                                              RolloutInput,
                                              RewardOutput,
                                              RolloutOutput)


app = typer.Typer(
    name="agentic-rl",
    help="🚀 Agentic RL Fine-Tuning CLI",
    add_completion=False,
    rich_markup_mode="rich",
)
console = Console()


# ================= Configuration & Utility Functions =================
def format_output(data: Any, fmt: str = "table") -> None:
    """Unified output formatter: table | json | yaml"""
    if hasattr(data, "model_dump"):
        data = data.model_dump()
    elif hasattr(data, "__dict__"):
        data = data.__dict__

    if fmt == "json":
        console.print(JSON.from_data(data))
    elif fmt == "yaml":
        console.print(yaml.dump(data, default_flow_style=False, allow_unicode=True))
    else:
        if isinstance(data, dict):
            table = Table(title="Result", show_header=True, header_style="bold cyan")
            table.add_column("Key", style="cyan")
            table.add_column("Value", style="green")
            for k, v in data.items():
                val = str(v) if not isinstance(v, (dict, list)) else json.dumps(v, ensure_ascii=False, indent=2)
                table.add_row(str(k), val)
            console.print(table)
        else:
            console.print(data)


def load_json_input(data_str: str) -> Dict[str, Any]:
    """Auto-detect and parse JSON string or file path."""
    # 1. Try parsing as JSON string
    try:
        return json.loads(data_str)
    except json.JSONDecodeError:
        pass

    # 2. Try reading as file path
    path = Path(data_str)
    if path.exists() and path.is_file():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    raise ValueError(f"Invalid input: '{data_str}' is neither a valid JSON string nor an existing file path.")


# ================= CLI Commands =================
async def _register_fc_async(
        rollout_classpaths: Optional[List[str]],
        reward_classpaths: Optional[List[str]],
        group_reward_classpaths: Optional[List[str]],
        workspace_dir: str = './',
        lazy_load: bool = True,
        api_key: Optional[str] = '',
) -> Dict[str, Any]:
    """🧩 Register Rollout/Reward/Group-reward function components, returns entity_id & instance_id"""
    # Validate at least one parameter is provided
    if not rollout_classpaths and not reward_classpaths and not group_reward_classpaths:
        console.print(
            "[red]❌ At least one of rollout_classpaths or reward_classpaths or group_reward_classpaths must be provided[/red]")
        raise typer.Exit(1)

    try:
        client = AgenticRL(api_key=api_key)

        if rollout_classpaths or reward_classpaths or group_reward_classpaths:
            client.tuning.fcs = []
            client.tuning.add_function_components(
                type=FunctionType.ROLLOUT,
                classpaths=rollout_classpaths,
                workspace_dir=workspace_dir)
            client.tuning.add_function_components(
                type=FunctionType.REWARD,
                classpaths=reward_classpaths,
                workspace_dir=workspace_dir)
            client.tuning.add_function_components(
                type=FunctionType.GROUP_REWARD,
                classpaths=group_reward_classpaths,
                workspace_dir=workspace_dir)

        rollout_eids, reward_eids, group_reward_eids, rollout_iids, reward_iids, group_reward_iids = await client.register_functions(
            lazy_load=lazy_load,
        )

        return {
            "rollout_entity_ids": rollout_eids,
            "reward_entity_ids": reward_eids,
            "group_reward_entity_ids": group_reward_eids,
            "rollout_instance_ids": rollout_iids,
            "reward_instance_ids": reward_iids,
            "group_reward_instance_ids": group_reward_iids,
        }

    except Exception as e:
        console.print(f"[red]❌ FC registration failed: {str(e)}[/red]")
        logger.error("FC registration error", exc_info=True)
        raise typer.Exit(1)


@app.command("register_functions")
def register_fc(
        rollout_classpaths: Optional[List[str]] = typer.Option(None,
                                                               help="List for rollout class path (file.py:ClassName)"),
        reward_classpaths: Optional[List[str]] = typer.Option(None,
                                                              help="List for reward class path (file.py:ClassName)"),
        group_reward_classpaths: Optional[List[str]] = typer.Option(None,
                                                                    help="List for group-reward class path (file.py:ClassName)"),

        workspace_dir: str = typer.Option("./", help="Local workspace directory"),
        lazy_load: bool = typer.Option(True, help="Delay instance loading (set False for debugging)"),
        api_key: Optional[str] = typer.Option(
            None, "--api-key", envvar="DASHSCOPE_API_KEY",
            help="DashScope API Key (uses DASHSCOPE_API_KEY env var if omitted)"
        ),
        output_format: str = typer.Option("json", "--output-format", "-o", help="Output format: table|json|yaml"),
):
    """🧩 Register Rollout/Reward function components, returns entity_id & instance_id

    Requires at least one of:
    - rollout_classpath
    - reward_classpaths
    """
    try:
        result = asyncio.run(_register_fc_async(
            rollout_classpaths=rollout_classpaths or [],
            reward_classpaths=reward_classpaths or [],
            group_reward_classpaths=group_reward_classpaths or [],
            workspace_dir=workspace_dir,
            lazy_load=lazy_load,
            api_key=api_key,
        ))

        format_output(result, fmt=output_format)

    except Exception as e:
        console.print(f"[red]❌ FC registration failed: {str(e)}[/red]")
        logger.error("FC registration error", exc_info=True)
        raise typer.Exit(1)


async def _test_fc_async(
        instance_id: str,
        func_type: str,
        input_data: Dict[str, Any],
        api_key: Optional[str]
) -> dict:
    """Core asynchronous testing logic."""
    try:
        client = AgenticRL(api_key=api_key)
        result = await client.test_functions(
            instance_id=instance_id,
            type=func_type,
            input_data=input_data,
            api_key=api_key,
        )
        return result

    except Exception as e:
        console.print(f"[red]❌ Function test failed: {str(e)}[/red]")
        logger.error("Function test error", exc_info=True)
        raise typer.Exit(1)


@app.command("test_functions")
def test_fc(
        instance_id: str = typer.Argument(..., help="Target function instance ID (e.g., ro-ins-xxx or rw-ins-xxx)"),
        type: str = typer.Option(..., "--type", "-t", help="Function type: ROLLOUT or REWARD"),
        input_data: str = typer.Option(..., "--input", "-i", help="JSON string or file path containing test payload"),
        api_key: Optional[str] = typer.Option(
            None, "--api-key", envvar="DASHSCOPE_API_KEY",
            help="DashScope API Key (uses DASHSCOPE_API_KEY env var if omitted)"
        ),
        output_format: str = typer.Option("json", "--output-format", "-o", help="Output format: table|json|yaml"),
):
    """🧪 Test a registered Rollout/Reward function instance with custom input data."""
    try:
        input_dict = load_json_input(input_data)
        result = asyncio.run(_test_fc_async(
            instance_id=instance_id,
            func_type=type,
            input_data=input_dict,
            api_key=api_key,
        ))

        format_output(result, fmt=output_format)
    except Exception as e:
        console.print(f"[red]❌ Function test failed: {str(e)}[/red]")
        logger.error("Function test error", exc_info=True)
        raise typer.Exit(1)


async def _upload_data_async(
        training_files: List[str],
        validation_files: Optional[List[str]] = None,
        api_key: Optional[str] = '',
):
    """📦 Upload training/validation datasets to the platform, returns file IDs"""
    try:
        client = AgenticRL(api_key=api_key)
        train_ids, val_ids = await client.upload_datasets(
            training_files=training_files,
            validation_files=validation_files
        )
        return {
            "uploaded_training_ids": train_ids,
            "uploaded_validation_ids": val_ids or []
        }

    except Exception as e:
        console.print(f"[red]❌ Dataset upload failed: {str(e)}[/red]")
        logger.error("Dataset upload error", exc_info=True)
        raise typer.Exit(1)


@app.command("upload_data")
def upload_data(
        training_files: List[str] = typer.Option(..., help="List of training dataset file paths"),
        validation_files: Optional[List[str]] = typer.Option(None, help="List of validation dataset file paths"),
        api_key: Optional[str] = typer.Option(
            None, "--api-key", envvar="DASHSCOPE_API_KEY",
            help="DashScope API Key (uses DASHSCOPE_API_KEY env var if omitted)"
        ),
        output_format: str = typer.Option("json", "--output-format", "-o", help="Output format: table|json|yaml"),
):
    """📦 Upload training/validation datasets to the platform, returns file IDs"""
    try:
        result = asyncio.run(_upload_data_async(
            training_files=training_files,
            validation_files=validation_files,
            api_key=api_key,
        ))

        format_output(result, fmt=output_format)
    except Exception as e:
        console.print(f"[red]❌ Dataset upload failed: {str(e)}[/red]")
        logger.error("Dataset upload error", exc_info=True)
        raise typer.Exit(1)


@app.command("submit")
def submit_job(
        model: str = typer.Option(..., help="Base model name"),
        training_file_ids: List[str] = typer.Option(..., help="Comma-separated list of training file_ids"),

        rollout_id: str = typer.Option(..., help="Pre-registered Rollout entity_id"),
        reward_ids: Optional[List[str]] = typer.Option(None, help="Comma-separated list of reward entity_ids"),
        group_reward_ids: Optional[List[str]] = typer.Option(None,
                                                             help="Comma-separated list of group-reward entity_ids"),

        rollout_runtime: Optional[str] = typer.Option(None, help="Rollout runtime as JSON string"),
        reward_runtimes: Optional[str] = typer.Option(None, help="Reward runtimes as JSON string"),
        group_reward_runtimes: Optional[str] = typer.Option(None, help="Group-reward runtimes as JSON string"),

        rollout_name: Optional[str] = typer.Option(None, help="Pre-registered Rollout entity_name"),
        reward_names: Optional[List[str]] = typer.Option(None, help="Comma-separated list of reward entity_names"),
        group_reward_names: Optional[List[str]] = typer.Option(None,
                                                             help="Comma-separated list of group-reward entity_names"),

        rollout_weight: Optional[float] = typer.Option(None, help="Pre-registered Rollout entity_weight"),
        reward_weights: Optional[List[float]] = typer.Option(None, help="Comma-separated list of reward entity_weights"),
        group_reward_weights: Optional[List[float]] = typer.Option(None,
                                                             help="Comma-separated list of group-reward entity_weights"),

        reward_metric_weights: Optional[str] = typer.Option(None,
                                                             help="Reward metric weights as JSON string (list of dicts)"),

        validation_file_ids: Optional[str] = typer.Option(None, help="Comma-separated list of validation file_ids"),
        hyper_parameters: Optional[str] = typer.Option(None, help="Hyperparameters as JSON string"),

        job_name: Optional[str] = typer.Option(None, help="Job name"),
        api_key: Optional[str] = typer.Option(
            None, "--api-key", envvar="DASHSCOPE_API_KEY",
            help="DashScope API Key (uses DASHSCOPE_API_KEY env var if omitted)"
        ),
        output_format: str = typer.Option("table", "--output-format", "-o", help="Output format: table|json|yaml"),
):
    """📤 Submit fine-tuning job (requires pre-registered FCs & uploaded datasets)"""
    try:
        # Parse JSON inputs with error handling
        try:
            rollout_runtime_dict = json.loads(rollout_runtime) if rollout_runtime else {}
            reward_runtimes_list = json.loads(reward_runtimes) if reward_runtimes else []
            group_reward_runtimes_list = json.loads(group_reward_runtimes) if group_reward_runtimes else []
            reward_metric_weights_list = json.loads(reward_metric_weights) if reward_metric_weights else None
            hyper_dict = json.loads(hyper_parameters) if hyper_parameters else {}
        except json.JSONDecodeError as e:
            console.print(f"[red]❌ JSON parsing error: {str(e)}[/red]")
            logger.error("JSON parsing error", exc_info=True)
            raise typer.Exit(1)

        client = AgenticRL(api_key=api_key)
        if rollout_id or reward_ids or group_reward_ids:
            client.tuning.fcs = []
            if rollout_id:
                client.tuning.add_function_components(
                    type=FunctionType.ROLLOUT,
                    entity_ids=rollout_id,
                    runtimes=rollout_runtime_dict,
                    names=rollout_name,
                    weights=rollout_weight,
                )
            if reward_ids:
                client.tuning.add_function_components(
                    type=FunctionType.REWARD,
                    entity_ids=reward_ids,
                    runtimes=reward_runtimes_list,
                    names=reward_names,
                    weights=reward_weights,
                    reward_metric_weights=reward_metric_weights_list,
                )
            if group_reward_ids:
                client.tuning.add_function_components(
                    type=FunctionType.GROUP_REWARD,
                    entity_ids=group_reward_ids,
                    runtimes=group_reward_runtimes_list,
                    names=group_reward_names,
                    weights=group_reward_weights,
                )

        result = client.submit_job(
            model=model,
            training_file_ids=training_file_ids,
            validation_file_ids=validation_file_ids,
            hyper_parameters=hyper_dict,
            job_name=job_name,
        )

        # Handle API response errors
        if result.status_code != 200:
            raise OutputError(f"API returned status {result.status_code}: {result.message}")

        format_output({
            "job_id": result.output.job_id,
            "status": result.output.status,
            "message": getattr(result, "message", "")
        }, fmt=output_format)

    except json.JSONDecodeError as e:
        console.print(f"[red]❌ JSON parsing error: {str(e)}[/red]")
        logger.error("JSON parsing error", exc_info=True)
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ Job submission failed: {str(e)}[/red]")
        logger.error("Job submission error", exc_info=True)
        raise typer.Exit(1)


async def _run_workflow_async(
        config_path: Optional[str],
        api_key: Optional[str],
        functions: Optional[Union[List[Union[RolloutFunctionComponent, RewardFunctionComponent]], RolloutFunctionComponent, RewardFunctionComponent]],
        run_kwargs: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Execute the RL tuning workflow asynchronously.

    Args:
        config_path: Path to YAML configuration file (optional)
        api_key: DashScope API key for authentication
        run_kwargs: Workflow parameters passed from CLI

    Returns:
        Result dictionary containing job information

    Raises:
        ValueError: If required parameters are missing
        RuntimeError: If workflow execution fails
    """
    try:
        client = AgenticRL(api_key=api_key)
        client.init(config_path=config_path, **run_kwargs)
        result = await client.run(functions=functions)
        return result
    except Exception as e:
        logger.error("Workflow execution error", exc_info=True)
        raise RuntimeError(f"Workflow execution failed: {str(e)}") from e


@app.command()
def run(
        config: Optional[Path] = typer.Option(None, "-c", "--config", help="Path to YAML configuration file"),

        model: Optional[str] = typer.Option(None, help="Base model identifier"),
        training_files: Optional[List[str]] = typer.Option(None, help="Paths to training dataset files"),
        validation_files: Optional[List[str]] = typer.Option(None, help="Paths to validation dataset files"),

        rollout_classpath: Optional[str] = typer.Option(None,
                                                        help="Python import path to rollout class (module:Class)"),
        reward_classpaths: Optional[List[str]] = typer.Option(None,
                                                              help="List for reward class path (file.py:ClassName)"),
        group_reward_classpaths: Optional[List[str]] = typer.Option(None,
                                                                    help="List for group-reward class path (file.py:ClassName)"),

        rollout_name: Optional[str] = typer.Option(None, help="Pre-registered Rollout entity_name"),
        reward_names: Optional[List[str]] = typer.Option(None, help="Comma-separated list of reward entity_names"),
        group_reward_names: Optional[List[str]] = typer.Option(None,
                                                             help="Comma-separated list of group-reward entity_names"),

        rollout_weight: Optional[str] = typer.Option(None, help="Pre-registered Rollout entity_weight"),
        reward_weights: Optional[List[float]] = typer.Option(None, help="Comma-separated list of reward entity_weights"),
        group_reward_weights: Optional[List[float]] = typer.Option(None,
                                                             help="Comma-separated list of group-reward entity_weights"),

        reward_metric_weights: Optional[str] = typer.Option(None,
                                                             help="Reward metric weights as JSON string (list of dicts)"),

        rollout_runtime: Optional[str] = typer.Option(None, help="Rollout runtime as JSON string"),
        reward_runtimes: Optional[str] = typer.Option(None, help="Reward runtimes as JSON string"),
        group_reward_runtimes: Optional[str] = typer.Option(None, help="Group-reward runtimes as JSON string"),

        hyper_parameters: Optional[str] = typer.Option(None, help="JSON string of hyperparameters"),

        job_name: Optional[str] = typer.Option(None, help="Custom name for the tuning job"),
        api_key: Optional[str] = typer.Option(
            None, "--api-key", envvar="DASHSCOPE_API_KEY",
            help="DashScope API Key (uses DASHSCOPE_API_KEY env var if omitted)"
        ),
        workspace_dir: Optional[str] = typer.Option("./", help="Workspace directory for job artifacts"),

        output_format: str = typer.Option("table", "--output-format", "-o", help="Output format: table|json|yaml"),
        verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable detailed error traces"),
):
    """
    🚀 Launch the complete RL tuning workflow (function registration → dataset upload → job submission)

    Execution modes:
    1. Configuration-driven: Use -c/--config to specify a YAML file
    2. Direct parameter: Provide all required arguments via CLI options

    Required parameters:
    - rollout_classpath
    - reward_classpaths (at least one)
    - training_files (at least one)
    """
    # Parse JSON inputs with error handling
    try:
        rollout_runtime_dict = json.loads(rollout_runtime) if rollout_runtime else {}
        reward_runtimes_list = json.loads(reward_runtimes) if reward_runtimes else []
        group_reward_runtimes_list = json.loads(group_reward_runtimes) if group_reward_runtimes else []
        reward_metric_weights_list = json.loads(reward_metric_weights) if reward_metric_weights else None
        hyper_dict = json.loads(hyper_parameters) if hyper_parameters else {}
    except json.JSONDecodeError as e:
        console.print(f"[red]❌ JSON parsing error: {str(e)}[/red]")
        logger.error("JSON parsing error", exc_info=True)
        raise typer.Exit(1)

    functions = None
    if rollout_classpath or reward_classpaths or group_reward_classpaths:
        client = AgenticRL()
        client.tuning.fcs = []
        if rollout_classpath:
            client.tuning.add_function_components(
                type=FunctionType.ROLLOUT,
                classpaths=rollout_classpath,
                runtimes=rollout_runtime_dict,
                names=rollout_name,
                weights=rollout_weight,
                workspace_dir=workspace_dir,
            )
        if reward_classpaths:
            client.tuning.add_function_components(
                type=FunctionType.REWARD,
                classpaths=reward_classpaths,
                runtimes=reward_runtimes_list,
                names=reward_names,
                weights=reward_weights,
                reward_metric_weights=reward_metric_weights_list,
                workspace_dir=workspace_dir,
            )
        if group_reward_classpaths:
            client.tuning.add_function_components(
                type=FunctionType.GROUP_REWARD,
                classpaths=group_reward_classpaths,
                runtimes=group_reward_runtimes_list,
                names=group_reward_names,
                weights=group_reward_weights,
                workspace_dir=workspace_dir,
            )
        functions = client.tuning.fcs

    # Prepare workflow parameters
    run_kwargs = {
        "job_name": job_name,
        "model": model,
        "training_files": training_files,
        "validation_files": validation_files,
        "hyper_parameters": hyper_dict,
    }

    # Remove None values to avoid overriding config defaults
    run_kwargs = {k: v for k, v in run_kwargs.items() if v is not None}

    # Validate direct execution parameters
    if not config:
        required_params = ["training_files"]
        missing = [p for p in required_params if p not in run_kwargs]
        if missing:
            console.print(f"[red]❌ Missing required parameters: {', '.join(missing)}[/red]")
            raise typer.Exit(1)

    try:
        with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True
        ) as progress:
            task = progress.add_task("🔄 Executing RL tuning workflow...", total=None)

            # Execute async workflow
            result = asyncio.run(_run_workflow_async(
                config_path=str(config) if config else None,
                api_key=api_key,
                functions=functions,
                run_kwargs=run_kwargs
            ))

            # Handle API response errors
            if result.status_code != 200:
                raise OutputError(f"API returned status {result.status_code}: {result.message}")

            progress.update(task, description="[green]✅ Job submitted successfully![/green]")
            format_output({
                "job_id": result.output.job_id,
                "status": result.output.status,
                "message": getattr(result, "message", "")
            }, fmt=output_format)

    except ValueError as ve:
        console.print(f"[red]❌ Validation error: {str(ve)}[/red]")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ Workflow execution failed: {str(e)}[/red]")
        if verbose:
            console.print_exception()
        logger.error("Workflow execution error", exc_info=True)
        raise typer.Exit(1)


@app.command()
def get(job_id: str = typer.Argument(..., help="Target job ID"),
           api_key: Optional[str] = typer.Option(
               None, "--api-key", envvar="DASHSCOPE_API_KEY",
               help="DashScope API Key (uses DASHSCOPE_API_KEY env var if omitted)"
           ),
           output_format: str = typer.Option("table", "--output-format", "-o")):
    """📊 Query the current status and metadata of a specific job"""
    try:
        result = AgenticRL.get(
            job_id=job_id,
            api_key=api_key)

        # Handle API response errors
        if result.status_code != 200:
            raise OutputError(f"API returned status {result.status_code}: {result.message}")

        format_output({
            "job_id": result.output.job_id,
            "status": result.output.status,
            "created_at": result.output.creator,
        }, fmt=output_format)
    except Exception as e:
        console.print(f"[red]❌ Query failed: {str(e)}[/red]")
        logger.error("Status query error", exc_info=True)
        raise typer.Exit(1)


@app.command("list")
def list_jobs(page: int = typer.Option(1, "-p", "--page", help="Page number"),
              size: int = typer.Option(10, "-s", "--size", help="Items per page"),
              api_key: Optional[str] = typer.Option(
                  None, "--api-key", envvar="DASHSCOPE_API_KEY",
                  help="DashScope API Key (uses DASHSCOPE_API_KEY env var if omitted)"
              ),
              output_format: str = typer.Option("table", "--output-format", "-o")):
    """📋 List historical fine-tuning jobs with pagination"""
    try:
        result = AgenticRL.list(
            page_no=page,
            page_size=size,
            api_key=api_key)

        # Handle API response errors
        if result.status_code != 200:
            raise OutputError(f"API returned status {result.status_code}: {result.message}")

        output_data = serialize_for_output(result.output if hasattr(result, "output") else result)
        format_output(output_data, fmt=output_format)
    except Exception as e:
        console.print(f"[red]❌ List query failed: {str(e)}[/red]")
        logger.error("List jobs error", exc_info=True)
        raise typer.Exit(1)


@app.command()
def cancel(
        job_id: str = typer.Argument(..., help="Target job ID"),
        api_key: Optional[str] = typer.Option(
            None, "--api-key", envvar="DASHSCOPE_API_KEY",
            help="DashScope API Key (uses DASHSCOPE_API_KEY env var if omitted)"
        )):
    """🛑 Cancel a running job"""
    try:
        result = AgenticRL.cancel(
            job_id=job_id,
            api_key=api_key)

        # Handle API response errors
        if result.status_code != 200:
            raise OutputError(f"API returned status {result.status_code}: {result.message}")

        console.print(f"[green]✅ Job {job_id} canceled successfully[/green]")
    except Exception as e:
        console.print(f"[red]❌ Cancellation failed: {str(e)}[/red]")
        logger.error("Cancel job error", exc_info=True)
        raise typer.Exit(1)


@app.command()
def delete(
        job_id: str = typer.Argument(..., help="Target job ID"),
        api_key: Optional[str] = typer.Option(
            None, "--api-key", envvar="DASHSCOPE_API_KEY",
            help="DashScope API Key (uses DASHSCOPE_API_KEY env var if omitted)"
        )):
    """🗑️ Delete a job record (releases metadata)"""
    try:
        result = AgenticRL.delete(
            job_id=job_id,
            api_key=api_key)

        # Handle API response errors
        if result.status_code != 200:
            raise OutputError(f"API returned status {result.status_code}: {result.message}")

        console.print(f"[green]✅ Job {job_id} deleted successfully[/green]")
    except Exception as e:
        console.print(f"[red]❌ Deletion failed: {str(e)}[/red]")
        logger.error("Delete job error", exc_info=True)
        raise typer.Exit(1)


@app.command()
def logs(
        job_id: str = typer.Argument(..., help="Target job ID"),
        offset: int = typer.Option(1, help="Starting line number"),
        lines: int = typer.Option(1000, help="Number of log lines to return"),
        api_key: Optional[str] = typer.Option(
            None, "--api-key", envvar="DASHSCOPE_API_KEY",
            help="DashScope API Key (uses DASHSCOPE_API_KEY env var if omitted)"
        ),
        output_format: str = typer.Option("table", "--output-format", "-o")):
    """📜 Fetch job execution logs (supports pagination)"""
    try:
        result = AgenticRL.logs(
            job_id=job_id,
            offset=offset,
            lines=lines,
            api_key=api_key)

        # Handle API response errors
        if result.status_code != 200:
            raise OutputError(f"API returned status {result.status_code}: {result.message}")

        format_output({
            "job_id": job_id,
            "logs": result.output.get("logs", "")
        }, fmt=output_format)
    except Exception as e:
        console.print(f"[red]❌ Log retrieval failed: {str(e)}[/red]")
        logger.error("Log retrieval error", exc_info=True)
        raise typer.Exit(1)

# if __name__ == "__main__":
#     app()
