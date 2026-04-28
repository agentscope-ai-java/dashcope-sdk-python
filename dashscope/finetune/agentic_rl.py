# -*- coding: utf-8 -*-
# Copyright (c) Alibaba, Inc. and its affiliates.

import os
import time
import yaml
from pathlib import Path
from http import HTTPStatus
from typing import Iterator, Union, List, Optional, ClassVar, Dict, Any
from typing_extensions import Self

from dashscope.client.base_api import CreateMixin
from dashscope.common.constants import TaskStatus

from dashscope.finetune.customize_types import (
    FineTune,
    FineTuneCancel,
    FineTuneDelete,
    FineTuneEvent,
    FineTuneList,
)
from dashscope.finetune.finetunes import FineTunes

from dashscope.finetune.reinforcement.common.errors import (
   OSSUploadError, RegistrationError, ValidationError, IOErrorWithCode, RuntimeErrorWithCode, ValueErrorWithCode,
)
from dashscope.finetune.reinforcement import logger
from dashscope.finetune.reinforcement import DASHSCOPE_HTTP_BASE_URL
from dashscope.finetune.reinforcement import set_api_key, get_filepath_classname, generate_random_id, get_func_type_id, deep_remove_none
from dashscope.finetune.reinforcement import FunctionType, FileSpec, TrainingType, AgenticRLFunctionComponent, RolloutFunctionComponent, RewardFunctionComponent, Datasets
from dashscope.finetune.reinforcement import AgenticRLTuning, TuningModel
from dashscope.finetune.reinforcement import RewardInput, RolloutInput, GroupRewardInput


class AgenticRL(AgenticRLTuning, CreateMixin):
    SUB_PATH: ClassVar[str] = "fine-tunes"

    def __init__(self, api_key: str = None):
        super().__init__()
        self._config: Dict[str, Any] = {}

        try:
            set_api_key(api_key)
        except Exception as e:
            logger.error("API key initialization failed", exc_info=True)
            raise ValueErrorWithCode("Invalid API key configuration", error_code=3000) from e

    def _tuningmodel_from_cfg(self, cfg: Dict[str, Any]) -> TuningModel:
        """Map configuration to internal TuningModel state"""
        self.tuning = TuningModel()

        ########################################################################################## name
        self.tuning.name = cfg.get("job_name", "agentic-rl-job")

        ########################################################################################## AgenticRLFunctionComponent
        workspace_dir = cfg.get("workspace_dir", "./")

        # classpaths & runtimes:
        self.tuning.fcs = []
        functions = cfg.get("functions", [])
        functions = [functions] if not isinstance(functions, List) else functions
        for f in functions:
            type = f.get("type", None)
            names = f.get("names", None)
            weights = f.get("weights", None)
            reward_metric_weights = f.get("reward_metric_weights", None)
            classpaths = f.get("classpaths", None)
            runtimes = f.get("runtimes", None)
            self.tuning.add_function_components(
                type=FunctionType(type) if type is not None else None,
                classpaths=classpaths,
                runtimes=runtimes,
                names=names,
                weights=weights,
                reward_metric_weights=reward_metric_weights,
                workspace_dir=workspace_dir)

        ########################################################################################## Datasets
        # Sync dataset IDs to Datasets model
        if "training_files" in cfg:
            for path in cfg["training_files"]:
                component = FileSpec(path=path)
                self.tuning.datasets.training_files.append(component)
        if "validation_files" in cfg:
            for path in cfg["validation_files"]:
                component = FileSpec(path=path)
                self.tuning.datasets.validation_files.append(component)

        ########################################################################################## FoundationModel
        if "model" in cfg:
            self.tuning.model.name = cfg["model"]

        ########################################################################################## Training
        if "mode" in cfg:
            # Support both string and enum types
            self.tuning.training.type = cfg["mode"] if isinstance(cfg["mode"], TrainingType) else TrainingType(
                cfg["mode"])
        if "hyper_parameters" in cfg:
            # Ensure hyperparameters are in Dict[str, str] format
            self.tuning.training.hyperparameters = {
                str(k): str(v) for k, v in cfg["hyper_parameters"].items()
            }

        return self.tuning

    def init(
            self,
            config_path: Optional[str] = None,
            **kwargs) -> Self:
        """
        Initialize an AgenticRL instance from a YAML configuration file.
        """
        cfg = {}
        if config_path:
            path = Path(config_path)
            if not path.exists():
                logger.warning(f"Configuration file not found: {config_path}")
            else:
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        cfg = yaml.safe_load(f) or {}
                except Exception as e:
                    logger.error(f"YAML configuration load failed: {str(e)}", exc_info=True)
                    raise IOErrorWithCode(f"Failed to load configuration: {str(e)}", error_code=3100) from e

        # Merge CLI/code overrides into the configuration
        cfg.update(kwargs)

        self._tuningmodel_from_cfg(cfg)
        self._config = cfg

        return self

    async def register_functions(
            self,
            functions: Optional[Union[List[Union[RolloutFunctionComponent, RewardFunctionComponent]], RolloutFunctionComponent, RewardFunctionComponent]] = None,
            lazy_load: Optional[bool] = True,
    ) -> tuple[List[str], List[str], List[str], List[str]]:
        """Register function components and return entity/instance IDs."""
        if functions:
            self.tuning.fcs = functions

        try:
            (rollout_entity_ids,
             reward_entity_ids,
             group_reward_entity_ids,
             rollout_instance_ids,
             reward_instance_ids,
             group_reward_instance_ids) = await self.tuning.register_functions(
                lazy_load=lazy_load,
            )
            logger.info("Function components registered")
        except Exception as e:
            logger.error("Function component registration failed", exc_info=True)
            raise RegistrationError("Function registration error", error_code=3200) from e

        return (rollout_entity_ids,
                reward_entity_ids,
                group_reward_entity_ids,
                rollout_instance_ids,
                reward_instance_ids,
                group_reward_instance_ids)

    async def upload_datasets(
            self,
            training_files: Optional[List[str]] = None,
            validation_files: Optional[List[str]] = None,
    ) -> tuple[List[str], List[str]]:
        """Upload datasets and return platform file IDs."""
        if training_files:
            self.tuning.datasets = Datasets(
                name='',
                training_files=[FileSpec(path=f, descriptions='') for f in training_files],
                validation_files=[FileSpec(path=f, descriptions='') for f in
                                  validation_files] if validation_files else None)

        try:
            uploaded_training_ids, uploaded_validation_ids = await self.tuning.register_datasets()
            logger.info("Datasets registration completed")
        except Exception as e:
            logger.error("Dataset registration failed", exc_info=True)
            raise OSSUploadError("Dataset upload error", error_code=3300) from e

        return uploaded_training_ids, uploaded_validation_ids

    def submit_job(
            self,
            model: Optional[str] = None,
            training_file_ids: Optional[Union[List[str], str]] = None,
            validation_file_ids: Optional[Union[List[str], str]] = None,
            functions: Optional[Union[List[Union[
                RolloutFunctionComponent, RewardFunctionComponent, AgenticRLFunctionComponent]],
                RolloutFunctionComponent, RewardFunctionComponent, AgenticRLFunctionComponent]] = None,
            hyper_parameters: Optional[Dict[str, str]] = None,
            job_name: Optional[str] = None,
            **kwargs,
    ) -> FineTune:
        """
        Submit RL tuning job to the platform.
        """
        # Resolve job name (fallback to class default)
        resolved_job_name = job_name or self.tuning.name
        job_name_with_suffix = f"{resolved_job_name}-{generate_random_id()[:8]}"

        if functions:
            self.tuning.fcs = functions

        try:
            rollouts = self.tuning.combine_ids_runtimes(type=FunctionType.ROLLOUT)
            rewards = self.tuning.combine_ids_runtimes(type=FunctionType.REWARD)
            rewards.extend(self.tuning.combine_ids_runtimes(
                type=FunctionType.GROUP_REWARD,
                id_str=get_func_type_id(FunctionType.REWARD)))
        except Exception as e:
            logger.error(f"Tuning combine ids and runtimes failed: {str(e)}", exc_info=True)
            raise

        if not self.tuning.check_function_names():
            raise ValueErrorWithCode(
                "Duplicate function names detected. All function names must be unique.",
                error_code=3401
            )

        request = {
            "model": model or self.tuning.model.name,
            "training_file_ids": training_file_ids or self.tuning.datasets.uploaded_training_ids,
            "validation_file_ids": validation_file_ids or self.tuning.datasets.uploaded_validation_ids,
            "rollout": rollouts[0] if rollouts else None,
            "rewards": rewards,
            "hyper_parameters": hyper_parameters or self.tuning.training.hyperparameters,
            "training_type": str(self.tuning.training.type),
            "job_name": job_name_with_suffix,
        }
        request = deep_remove_none(request)
        logger.info(f"agentic_rl submit_job request: {request}")

        kwargs['base_address'] = DASHSCOPE_HTTP_BASE_URL
        try:
            resp = super().call(
                request,
                workspace=None,
                **kwargs,
            )
        except Exception as e:
            logger.error("Job submission failed", exc_info=True)
            raise RuntimeErrorWithCode("Job submission error", error_code=3400) from e

        return FineTune(**resp)

    async def run(
            self,
            model: Optional[str] = None,

            # Datasets parameters
            training_files: Optional[Union[List[str], str]] = None,
            validation_files: Optional[Union[List[str], str]] = None,

            # Path-driven parameters (auto-register & upload)
            functions: Optional[Union[List[Union[
                RolloutFunctionComponent, RewardFunctionComponent, AgenticRLFunctionComponent]],
            RolloutFunctionComponent, RewardFunctionComponent, AgenticRLFunctionComponent]] = None,

            # Common parameters
            hyper_parameters: Optional[Dict[str, str]] = None,
            job_name: Optional[str] = None,
            workspace_dir: str = "./",
            **kwargs,
    ) -> FineTune:
        """
        Execute RL tuning workflow.
        """
        try:
            logger.info("🟦 Path-Driven mode: Registering functions & uploading datasets...")
            await self.register_functions(
                functions=functions,
                lazy_load=True,
            )

            await self.upload_datasets(
                training_files=training_files,
                validation_files=validation_files,
            )

            return self.submit_job(
                model=model,
                hyper_parameters=hyper_parameters,
                job_name=job_name,
                **kwargs
            )
        except Exception as e:
            logger.error("RL tuning workflow failed", exc_info=True)
            raise RuntimeErrorWithCode(f"RL tuning workflow failed: {str(e)}", error_code=3500) from e

    @classmethod
    def cancel(
            cls,
            job_id: str,
            api_key: str = None,
            workspace: str = None,
            **kwargs,
    ) -> FineTuneCancel:
        """Cancel a running fine-tune job."""
        kwargs['base_address'] = DASHSCOPE_HTTP_BASE_URL

        return FineTunes.cancel(
            job_id,
            api_key=api_key,
            workspace=workspace,
            **kwargs,
        )

    @classmethod
    def list(
            cls,
            page_no=1,
            page_size=10,
            api_key: str = None,
            workspace: str = None,
            **kwargs,
    ) -> FineTuneList:
        """List fine-tune jobs."""
        kwargs['base_address'] = DASHSCOPE_HTTP_BASE_URL

        return FineTunes.list(
            page_no=page_no,
            page_size=page_size,
            api_key=api_key,
            workspace=workspace,
            **kwargs,
        )

    @classmethod
    def get(
            cls,
            job_id: str,
            api_key: str = None,
            workspace: str = None,
            **kwargs,
    ) -> FineTune:
        """Get fine-tune job information."""
        kwargs['base_address'] = DASHSCOPE_HTTP_BASE_URL

        return FineTunes.get(
            job_id,
            api_key=api_key,
            workspace=workspace,
            **kwargs,
        )

    @classmethod
    def delete(
            cls,
            job_id: str,
            api_key: str = None,
            workspace: str = None,
            **kwargs,
    ) -> FineTuneDelete:
        """Delete a fine-tune job."""
        kwargs['base_address'] = DASHSCOPE_HTTP_BASE_URL

        return FineTunes.delete(
            job_id,
            api_key=api_key,
            workspace=workspace,
            **kwargs,
        )

    @classmethod
    def stream_events(
            cls,
            job_id: str,
            api_key: str = None,
            workspace: str = None,
            **kwargs,
    ) -> Iterator[FineTuneEvent]:
        """Stream fine-tune job events."""
        kwargs['base_address'] = DASHSCOPE_HTTP_BASE_URL

        responses = FineTunes.stream_events(
            job_id,
            api_key=api_key,
            workspace=workspace,
            **kwargs,
        )
        for rsp in responses:
            yield FineTuneEvent(**rsp)

    @classmethod
    def logs(
            cls,
            job_id: str,
            offset: int = 1,
            lines: int = 1000,
            api_key: str = None,
            workspace: str = None,
            **kwargs,
    ) -> FineTune:
        """Get job logs."""
        kwargs['base_address'] = DASHSCOPE_HTTP_BASE_URL

        return FineTunes.logs(
            job_id,
            offset=offset,
            line=lines,
            api_key=api_key,
            workspace=workspace,
            **kwargs,
        )

    @classmethod
    async def test_functions(
            cls,
            instance_id: str,
            type: FunctionType,
            input_data: Dict[str, Any],
            api_key: str = None):
        try:
            set_api_key(api_key)

            if type == FunctionType.ROLLOUT:
                input = RolloutInput.model_validate(input_data)
            elif type == FunctionType.REWARD:
                input = RewardInput.model_validate(input_data)
            elif type == FunctionType.GROUP_REWARD:
                input = GroupRewardInput.model_validate(input_data)
            else:
                raise ValueErrorWithCode(f"Unsupported function type: {type}", error_code=3600)

            logger.info(
                f"Starting {str(type)} verification",
                extra={
                    "instance_id": instance_id,
                    "input_params": input.model_dump(exclude={"api_key"})
                }
            )

            return await AgenticRLFunctionComponent.verify_function(input, instance_id)

        except Exception as e:
            logger.error(f"Failure during {str(type)} test: {str(e)}", exc_info=True)
            raise ValidationError(f"Function test failed: {str(e)}", error_code=3601) from e
