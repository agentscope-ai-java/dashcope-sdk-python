# -*- coding: utf-8 -*-
# Copyright (c) Alibaba, Inc. and its affiliates.

import yaml
from pathlib import Path
from typing import Union, List, Optional, ClassVar, Dict, Any
from typing_extensions import Self

from dashscope.client.base_api import CreateMixin
from dashscope.finetune.customize_types import (
    FineTune,
    FineTuneCancel,
    FineTuneDelete,
    FineTuneList,
)
from dashscope.finetune.finetunes import FineTunes
from dashscope.finetune.reinforcement import AgenticRLFunctionComponent, \
    RolloutFunctionComponent, RewardFunctionComponent, Dataset, \
    TrainingDataset, ValidationDataset
from dashscope.finetune.reinforcement import AgenticRLTuning, TuningModel
from dashscope.finetune.reinforcement import DASHSCOPE_HTTP_BASE_URL
from dashscope.finetune.reinforcement import FunctionType, DatasetsType, \
    TrainingType, DataSourceType
from dashscope.finetune.reinforcement import RewardInput, RolloutInput, \
    GroupRewardInput
from dashscope.finetune.reinforcement import logger
from dashscope.finetune.reinforcement import set_api_key, generate_random_id, \
    get_func_type_id, deep_remove_none
from dashscope.finetune.reinforcement.common.errors import (
    RegistrationError, ValidationError, IOErrorWithCode, RuntimeErrorWithCode,
    ValueErrorWithCode, DatasetsError
)


class AgenticRL(AgenticRLTuning, CreateMixin):
    SUB_PATH: ClassVar[str] = "fine-tunes"

    def __init__(self, api_key: str = None):
        super().__init__()
        self._config: Dict[str, Any] = {}

        try:
            set_api_key(api_key)
        except Exception as e:
            logger.error("API key initialization failed", exc_info=True)
            raise ValueErrorWithCode("Invalid API key configuration",
                                     error_code=3000) from e

    def _tuningmodel_from_cfg(self, cfg: Dict[str, Any]) -> TuningModel:
        """Map configuration to internal TuningModel state"""
        self.tuning = TuningModel()

        ########################################################################################## name
        self.tuning.name = cfg.get("job_name", "agentic-rl-job")

        ########################################################################################## AgenticRLFunctionComponent
        workspace_dir = cfg.get("workspace_dir", "./")

        # classpaths & runtimes:
        self.tuning.functions = []
        functions = cfg.get("functions", [])
        functions = [functions] if not isinstance(functions,
                                                  List) else functions
        for f in functions:
            ftype = f.get("type", None)
            name = f.get("name", None)
            weight = f.get("weight", None)
            timeout = f.get("timeout", None)
            reward_metric_weight = f.get("reward_metric_weight", None)
            runtime = f.get("runtime", None)
            fcmodel = f.get("fcmodel", None)

            self.tuning.add_function_components(
                function_type=FunctionType(ftype) if ftype is not None else None,
                classpaths=fcmodel.get("classpath", None) if fcmodel else None,
                entity_ids=fcmodel.get("entity_id", None) if fcmodel else None,
                runtimes=runtime,
                names=name,
                weights=weight,
                timeouts=timeout,
                reward_metric_weights=reward_metric_weight,
                workspace_dir=workspace_dir)

        ########################################################################################## Datasets
        # Sync dataset IDs to Datasets model
        if "datasets" in cfg:
            for ds in cfg["datasets"]:
                type = ds.get("type", None)
                data_source_type = ds.get("data_source_type", None)
                file_name = ds.get("file_name", None)
                file_id = ds.get("file_id", None)
                download_url = ds.get("download_url", None)
                mount_storage = ds.get("mount_storage", None)

                dataset = Dataset(
                    type=DatasetsType(type) if type else DatasetsType.TRAINING,
                    data_source_type=DataSourceType(
                        data_source_type) if data_source_type else DataSourceType.FILE_ID,
                    file_name=file_name if data_source_type == DataSourceType.FILE_ID else None,
                    file_id=file_id if data_source_type == DataSourceType.FILE_ID else None,
                    download_url=download_url if data_source_type == DataSourceType.DOWNLOAD_URL else None,
                    mount_storage=mount_storage if data_source_type == DataSourceType.OSS_MOUNT else None
                )
                self.tuning.datasets.append(dataset)

        ########################################################################################## FoundationModel
        if "model" in cfg:
            self.tuning.model.name = cfg["model"]

        ########################################################################################## Training
        if "mode" in cfg:
            # Support both string and enum types
            self.tuning.training.type = cfg["mode"] if isinstance(cfg["mode"],
                                                                  TrainingType) else TrainingType(
                cfg["mode"])

        if "training" in cfg:
            if "hyper_parameters" in cfg["training"]:
                # Ensure hyperparameters are in Dict[str, str] format
                self.tuning.training.hyperparameters = {
                    str(k): str(v) for k, v in
                    cfg["training"]["hyper_parameters"].items()
                }
            if "resources" in cfg["training"]:
                # Ensure resources are in Dict[str, str] format
                self.tuning.training.resources = {
                    str(k): str(v) for k, v in
                    cfg["training"]["resources"].items()
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
                    logger.error(f"YAML configuration load failed: {str(e)}",
                                 exc_info=True)
                    raise IOErrorWithCode(
                        f"Failed to load configuration: {str(e)}",
                        error_code=3100) from e

        # Merge CLI/code overrides into the configuration
        cfg.update(kwargs)

        self._tuningmodel_from_cfg(cfg)
        self._config = cfg

        return self

    async def register_functions(
            self,
            functions: Optional[Union[List[Union[
                RolloutFunctionComponent, RewardFunctionComponent]], RolloutFunctionComponent, RewardFunctionComponent]] = None,
            lazy_load: Optional[bool] = True,
    ) -> tuple[
        List[str], List[str], List[str], List[str], List[str], List[str]]:
        """Register function components and return entity/instance IDs."""
        if functions:
            self.tuning.functions = functions

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
            logger.error("Function component registration failed",
                         exc_info=True)
            raise RegistrationError("Function registration error",
                                    error_code=3200) from e

        return (rollout_entity_ids,
                reward_entity_ids,
                group_reward_entity_ids,
                rollout_instance_ids,
                reward_instance_ids,
                group_reward_instance_ids)

    async def upload_datasets(
            self,
            datasets: Optional[List[Dataset]] = None,
            training_files: Optional[Union[List[str], str]] = None,
            validation_files: Optional[Union[List[str], str]] = None,
    ) -> tuple[List[str], List[str]]:
        if datasets:
            self.tuning.datasets = datasets

        try:
            uploaded_training_ids, uploaded_validation_ids = await self.tuning.upload_datasets(
                training_files=training_files,
                validation_files=validation_files,
            )
            logger.info("Datasets uploaded")
        except Exception as e:
            logger.error("Datasets upload failed", exc_info=True)
            raise DatasetsError("Datasets upload error",
                                error_code=3300) from e

        return uploaded_training_ids, uploaded_validation_ids

    def submit_job(
            self,
            model: Optional[str] = None,
            # training_file_ids: Optional[Union[List[str], str]] = None,
            # validation_file_ids: Optional[Union[List[str], str]] = None,
            datasets: Optional[List[Dataset]] = None,
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

        # rollouts/rewards
        if functions:
            self.tuning.functions = functions
        try:
            rollouts = self.tuning.combine_ids_runtimes(
                type=FunctionType.ROLLOUT)
            rewards = self.tuning.combine_ids_runtimes(
                type=FunctionType.REWARD)
            rewards.extend(self.tuning.combine_ids_runtimes(
                type=FunctionType.GROUP_REWARD,
                id_str=get_func_type_id(FunctionType.REWARD)))
        except Exception as e:
            logger.error(f"Tuning combine ids and runtimes failed: {str(e)}",
                         exc_info=True)
            raise
        # names of functions
        if not self.tuning.check_function_names():
            raise ValueErrorWithCode(
                "Duplicate function names detected. All function names must be unique.",
                error_code=3401
            )

        # datasets
        datasets = datasets or self.tuning.datasets
        if not datasets:
            raise ValueError("No datasets specified")
        training_datasets = [ds for ds in datasets if
                             ds.type == DatasetsType.TRAINING]
        validation_datasets = [ds for ds in datasets if
                               ds.type == DatasetsType.VALIDATION]

        # resources
        resource_config = kwargs.get("resource_config")

        request = {
            "model": model or self.tuning.model.name,
            # "training_file_ids": training_file_ids or self.tuning.datasets.uploaded_training_ids,
            # "validation_file_ids": validation_file_ids or self.tuning.datasets.uploaded_validation_ids,
            "training_datasets": [ds.model_dump() for ds in training_datasets],
            "validation_datasets": [ds.model_dump() for ds in
                                    validation_datasets],
            "rollout": rollouts[0] if rollouts else None,
            "rewards": rewards,
            "hyper_parameters": hyper_parameters or self.tuning.training.hyperparameters,
            "resource_config": resource_config or self.tuning.training.resources,
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
            raise RuntimeErrorWithCode("Job submission error",
                                       error_code=3400) from e

        return FineTune(**resp)

    async def run(
            self,
            model: Optional[str] = None,

            # Datasets parameters
            # training_files: Optional[Union[List[str], str]] = None,
            # validation_files: Optional[Union[List[str], str]] = None,
            # datasets: Optional[List[Dataset]] = None,
            training_datasets: Optional[List[TrainingDataset]] = None,
            validation_datasets: Optional[List[ValidationDataset]] = None,

            # Path-driven parameters (auto-register & upload)
            functions: Optional[Union[List[Union[
                RolloutFunctionComponent, RewardFunctionComponent, AgenticRLFunctionComponent]],
            RolloutFunctionComponent, RewardFunctionComponent, AgenticRLFunctionComponent]] = None,

            # Common parameters
            hyper_parameters: Optional[Dict[str, str]] = None,
            job_name: Optional[str] = None,
            # workspace_dir: str = "./",
            **kwargs,
    ) -> FineTune:
        """
        Execute RL tuning workflow.
        """
        try:
            logger.info(
                "🟦 Path-Driven mode: Registering functions & uploading datasets...")
            await self.register_functions(
                functions=functions,
                lazy_load=True,
            )

            # await self.upload_datasets(
            #     training_files=training_files,
            #     validation_files=validation_files,
            # )
            datasets = list(training_datasets or []) + list(
                validation_datasets or [])
            await self.upload_datasets(
                datasets=datasets,
            )

            return self.submit_job(
                model=model,
                datasets=datasets,
                hyper_parameters=hyper_parameters,
                job_name=job_name,
                **kwargs
            )
        except Exception as e:
            logger.error("RL tuning workflow failed", exc_info=True)
            raise RuntimeErrorWithCode(f"RL tuning workflow failed: {str(e)}",
                                       error_code=3500) from e

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
            function_type: FunctionType,
            input_data: Dict[str, Any],
            api_key: str = None):
        try:
            set_api_key(api_key)

            if function_type == FunctionType.ROLLOUT:
                value = RolloutInput.model_validate(input_data)
            elif function_type == FunctionType.REWARD:
                value = RewardInput.model_validate(input_data)
            elif function_type == FunctionType.GROUP_REWARD:
                value = GroupRewardInput.model_validate(input_data)
            else:
                raise ValueErrorWithCode(f"Unsupported function type: {function_type}",
                                         error_code=3600)

            logger.info(
                f"Starting {str(function_type)} verification",
                extra={
                    "instance_id": instance_id,
                    "input_params": value.model_dump(exclude={"api_key"})
                }
            )

            return await AgenticRLFunctionComponent.verify_function(value,
                                                                    instance_id)

        except Exception as e:
            logger.error(f"Failure during {str(function_type)} test: {str(e)}",
                         exc_info=True)
            raise ValidationError(f"Function test failed: {str(e)}",
                                  error_code=3601) from e
