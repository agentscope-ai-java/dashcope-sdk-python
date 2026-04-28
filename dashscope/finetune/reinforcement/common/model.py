# Standard Library
import os
import json
import asyncio
import shutil
import zipfile
from pathlib import Path
import tempfile
from typing import Any, Dict, List, Optional, Union

# Third-party Libraries
import yaml
from pydantic import BaseModel, Field, PrivateAttr, computed_field, model_validator, ConfigDict
from typing_extensions import Self

# Local Application
from dashscope.finetune.reinforcement import (
    DASHSCOPE_API_KEY,
    FC_API_KEY,
    FC_FILES_START,
    FC_LOAD_API,
    FC_QUERY_API,
    FC_REGISTER_REWARD_API,
    FC_REGISTER_ROLLOUT_API,
    FC_REGISTER_GROUP_REWARD_API,
    FC_UPLOAD_OSS_API,
    FC_LAYER_NAME,
    FC_REQUIREMENTS_FILE,
    FC_OFFLINE_INSTALLATION,
    FC_LAYER_CREATE_API,
    LOG_LEVEL,
)
from dashscope.finetune.reinforcement.common.errors import (
    InputError, OutputError, ConnectionError,
    OSSConnectionError, OSSUploadError, DeploymentError, RegistrationError,
    FunctionLoadError, InstanceWarmupError, InstanceQueryError, FunctionLayerError,
    ValidationError, IOErrorWithCode, ValueErrorWithCode,
)
from dashscope.finetune.reinforcement import logger
from dashscope.finetune.reinforcement import (
    check_file,
    client_fc,
    create_deployment_files,
    deep_mask,
    generate_random_id,
    upload_zip_to_oss_and_by_signed_url,
    zip_dir,
    to_bailian_data,
    get_filepath_classname,
    get_func_type_id,
    get_weights_from_file,
)
from dashscope.finetune.reinforcement import (
    FileSpec,
    FunctionType,
    RequestFC,
    ResponseFC,
    Status,
    StatusType,
    TrainingType,
)
from dashscope.finetune.reinforcement import (
    RewardInput,
    RewardOutput,
    RolloutInput,
    RolloutOutput,
    GroupRewardInput,
    GroupRewardOutput,
)


class Datasets(BaseModel):
    name: str = ''
    training_files: Optional[List[FileSpec]] = []
    validation_files: Optional[List[FileSpec]] = []

    uploaded_training_ids: Optional[List[str]] = []
    uploaded_validation_ids: Optional[List[str]] = []

    async def upload_datasets(self) -> List:
        try:
            if self.training_files:
                self.uploaded_training_ids = await to_bailian_data(self.training_files)
            if self.validation_files:
                self.uploaded_validation_ids = await to_bailian_data(self.validation_files)
        except Exception as e:
            logger.error(f"Dataset upload failed: {str(e)}", exc_info=True)
            raise OSSUploadError(f"Failed to upload datasets: {str(e)}", error_code=1100) from e


class FoundationModel(BaseModel):
    name: str = ''


class Training(BaseModel):
    type: TrainingType = TrainingType.TRAINING_TYPE
    hyperparameters: Dict[str, str] = {}


class Observability(BaseModel):
    def __init__(self, **data):
        super().__init__(**data)


class Models(BaseModel):
    @classmethod
    def load_from_yaml(cls, file_path: str) -> Self:
        try:
            check_file(file_path)
            with open(file_path, "r") as f:
                d = yaml.load(f.read(), Loader=yaml.SafeLoader)
            logger.info(f"Loaded from YAML: {file_path}")
        except Exception as e:
            logger.error(f"YAML load failed: {str(e)}", exc_info=True)
            raise IOErrorWithCode(f"Failed to load YAML file: {str(e)}", error_code=1000, path=file_path) from e

        return cls(**d)

    def to_yaml(self, file_path: str, overwrite: bool = True) -> None:
        path = Path(file_path)
        if path.exists() and not overwrite:
            raise FileExistsError(f"File already exists: {file_path}, use overwrite=True to force overwrite")

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            model_dict = self.model_dump(mode='json')
            logger.debug(f"The struct of Models class: {model_dict if LOG_LEVEL=='DEBUG' else deep_mask(model_dict)}")
            with open(path, 'w') as f:
                yaml.safe_dump(
                    model_dict,
                    f,
                    encoding='utf-8',
                    allow_unicode=True,
                    sort_keys=False
                )
        except Exception as e:
            logger.error(f"YAML save failed: {str(e)}", exc_info=True)
            raise IOErrorWithCode(f"Failed to write file: {str(e)}", error_code=1001) from e


class FunctionComponentModel(BaseModel):
    """Model representing function component configuration and operations."""
    zipdir: str = Field(
        default='./',
        description="Local directory path containing function code"
    )
    classpath: Optional[str] = Field(
        default=None,
        description="Entrypoint class path for the function"
    )

    filepath: str = Field(
        default='',
        description="Main Python filepath containing function logic"
    )
    classname: str = Field(
        default='',
        description="Entrypoint class name for the function"
    )

    requirements_path: Optional[str] = Field(
        default=FC_REQUIREMENTS_FILE,
        description="Specify Python dependencies"
    )
    extra_files: Optional[List[str]] = Field(
        default='',
        description="Additional deployment files required for function execution"
    )

    oss_id: Optional[str] = Field(
        default='',
        description="Unique identifier for OSS storage resource"
    )
    oss_signed_url: Optional[str] = Field(
        default='',
        description="Pre-signed URL for OSS bucket access"
    )

    def generate_id(self, func_type: FunctionType) -> str:
        """Generate unique OSS resource identifier."""
        self.oss_id = generate_random_id(func_type.value)
        logger.debug(
            f"Generated OSS ID | Type: {func_type.name}, ID: {self.oss_id}"
        )
        return self.oss_id

    async def get_oss(self, oss_id: Optional[str] = None) -> str:
        """Retrieve OSS signed URL for deployment package."""
        try:
            if oss_id:
                self.oss_id = oss_id

            result = await client_fc(
                FC_API_KEY,
                FC_UPLOAD_OSS_API,
                {'unique_key': self.oss_id}
            )
            self.oss_signed_url = result.get('output', {}).get('url', '')
            if not self.oss_signed_url:
                raise OSSConnectionError(f"Empty OSS URL received: {result}", error_code=2000)

            logger.debug(
                f"Obtained OSS signed URL | ID: {self.oss_id}, "
                f"URL: {self.oss_signed_url}"
            )
            return self.oss_signed_url

        except Exception as e:
            logger.error(
                f"OSS connection failed | ID: {self.oss_id}, Error: {str(e)}",
                exc_info=True
            )
            raise OSSConnectionError(
                f"Failed to obtain OSS URL: {str(e)}", error_code=2001
            ) from e

    async def create_layer(
            self,
            name: str = FC_LAYER_NAME,
            requirements_file: str = FC_REQUIREMENTS_FILE) -> str:
        """Retrieve OSS signed URL for deployment package."""
        layer_code = None
        try:
            # Validate requirements file if provided
            requirements = None
            if requirements_file and requirements_file.strip():
                req_path = os.path.join(self.zipdir, requirements_file)
                check_file(req_path)
                logger.debug(f"Found requirements file: {req_path}")
                with open(req_path, 'r', encoding='utf-8') as f:
                    requirements = f.read()

            # response: {
            #     "code": 0,
            #     "message": "success",
            #     "data": {
            #         "layer_code": "layer-xxxx",
            #         "status": "building"
            #     }
            # }
            layer_name = name + '-' + generate_random_id()[:8]
            result = await client_fc(
                FC_API_KEY,
                FC_LAYER_CREATE_API,
                {
                    "layer_name": layer_name,
                    "requirements_content": requirements
                }
            )
            if result.get('status', '').get('code', 500) == 200:
                layer_code = result.get('output', {}).get('layer_code', '')

            logger.debug(f"Create function layer | layer-name: {layer_name} | layer_code: {layer_code}")

        except Exception as e:
            logger.error(
                f"Create function layer failed | layer-name: {name}, Error: {str(e)}",
                exc_info=True
            )
        finally:
            return layer_code

    async def to_oss(
            self,
            func_type: FunctionType,
            signed_url: Optional[str] = None,
            function_layer_created: bool = False
    ) -> None:
        """Upload function package to OSS storage."""
        url = signed_url or self.oss_signed_url

        try:
            # Create deploy files
            create_deployment_files(
                type=func_type,
                dirpath=self.zipdir,
                filepath=self.filepath,
                classname=self.classname,
                requirements_path=self.requirements_path,
                function_layer_created=function_layer_created,
            )

            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
                zip_dir(
                    output_zip=tmp.name,
                    dirpath=self.zipdir,
                    extra_files=self.extra_files,
                    rw_type="w",
                )

                await upload_zip_to_oss_and_by_signed_url(url, tmp.name)
                logger.debug(
                    f"Package uploaded | Size: {os.path.getsize(tmp.name)} bytes, "
                    f"Files: {len(self.extra_files) + 1}"
                )

                self._clean_temp_files(tmp.name)

        except Exception as e:
            logger.error(
                f"OSS upload failed | URL: {url}, Error: {str(e)}",
                exc_info=True
            )
            raise OSSUploadError(
                f"Package upload failed: {str(e)}", error_code=2003, endpoint=url
            ) from e

    def _clean_temp_files(self, tmp_path: str) -> None:
        """Cleanup temporary deployment files."""
        try:
            for f in [tmp_path]:
                if os.path.exists(f):
                    os.remove(f) if os.path.isfile(f) else shutil.rmtree(f)
        except Exception as e:
            logger.warning(f"Temp file cleanup failed: {str(e)}")

    def _split_classpath(self):
        self.filepath, self.classname = get_filepath_classname(self.classpath)

    def _get_sub_function_weights(self):
        if not self.filepath and self.classpath:
            self._split_classpath()
        return get_weights_from_file(self.filepath, self.classname)


class FunctionComponentRuntime(BaseModel):
    """Runtime configuration for a function component"""

    layer_code: Optional[str] = None
    """Code of function layer"""

    cpu: Optional[float] = None
    """Number of CPU cores allocated (in vCPU units)"""

    memory_size: Optional[int] = None
    """Memory allocation size (in MB)"""

    disk_size: Optional[int] = None
    """Disk storage capacity (in MB)"""

    concurrency: Optional[int] = None
    """Maximum number of concurrent executions per instance (unitless count)"""

    capacity: Optional[int] = None
    """Current number of active instances (unitless count)"""

    max_capacity: Optional[int] = None
    """Maximum allowed instances for scaling (unitless count)"""

    min_capacity: Optional[int] = None
    """Minimum required instances for scaling (unitless count)"""

    memory_scale_threshold: Optional[float] = None
    """Memory utilization percentage threshold for scaling (0-100%)"""

    concurrency_scale_threshold: Optional[float] = None
    """Concurrency utilization percentage threshold for scaling (0-100%)"""

    enable_vpc_config: Optional[bool] = None
    """Flag indicating if VPC configuration is enabled (boolean)"""

    security_group_id: Optional[str] = None
    """ID of the security group (string identifier)"""

    switch_ids: Optional[List[str]] = None
    """List of network switch IDs (string identifiers)"""

    vpc_id: Optional[str] = None
    """Virtual Private Cloud ID (string identifier)"""

    vpc_role: Optional[str] = None
    """IAM role for VPC access (string identifier)"""

    enable_log: Optional[bool] = None
    """Flag indicating if logging is enabled (boolean)"""

    env: Optional[Dict[str, Any]] = None
    """
    Environment variables for the function runtime environment.

    Key-value pairs where:
    - Key: Environment variable name (string)
    - Value: Environment variable value (any serializable type)

    Example:
        {
            "ENABLE_TRAJECTORY": True
        }

    Best Practices:
    1. Use UPPER_SNAKE_CASE for variable names
    2. Keep values as strings when possible for maximum compatibility
    3. Avoid storing sensitive secrets directly - use secret management systems
    """


class AgenticRLFunctionComponent(Models, BaseModel):
    """Main class managing function component lifecycle operations."""
    type: FunctionType = Field(
        default=FunctionType.ROLLOUT,
        description="Type of function component"
    )
    name: Optional[str] = Field(
        default=None,
        description="Function name"
    )

    # for register
    fcmodel: Optional[FunctionComponentModel] = Field(
        default_factory=FunctionComponentModel,
        description="Function component model"
    )
    # for load
    runtime: Optional[FunctionComponentRuntime] = Field(
        default=None,
        description="Function component runtime"
    )

    entity_id: Optional[str] = Field(
        default='',
        description="System-generated registration identifier"
    )
    instance_id: Optional[str] = Field(
        default='',
        description="Deployed instance identifier"
    )
    instance_status: Optional[int] = Field(
        default=-1,
        description="Current instance state (-1=Unknown, 0=Initialized, 1=Deploying, 2=Active)"
    )
    instance_url: Optional[str] = Field(
        default='',
        description="Endpoint URL for deployed instance"
    )
    instance_token: Optional[str] = Field(
        default='',
        description="Authentication token for instance access"
    )

    model_config = ConfigDict(extra="allow")


    async def register(
            self,
            oss_id: Optional[str] = None,
            oss_url: Optional[str] = None,
    ) -> ResponseFC:
        """Register function in the deployment system."""
        try:
            # Create function layer
            if FC_OFFLINE_INSTALLATION:
                if self.runtime is None:
                    self.runtime = FunctionComponentRuntime()
                self.runtime.layer_code = await self.fcmodel.create_layer()

        except Exception as e:
            logger.error(
                f"Function layer create failed | URL: {url}, Error: {str(e)}",
                exc_info=True
            )
            raise FunctionLayerError(
                f"Function layer create failed: {str(e)}", error_code=2102
            ) from e

        try:
            # Handle OSS configuration
            if oss_id and oss_url:
                self.fcmodel.oss_id = oss_id
                self.fcmodel.oss_signed_url = oss_url
            else:
                self.fcmodel.generate_id(self.type)
                await self.fcmodel.get_oss()

            # Split: classpath to filepath & classname
            if self.fcmodel.classpath:
                self.fcmodel._split_classpath()

            # Upload
            await self.fcmodel.to_oss(
                func_type=self.type,
                signed_url=self.fcmodel.oss_signed_url,
                function_layer_created=self.runtime is not None and self.runtime.layer_code is not None,
            )

        except Exception as e:
            logger.error(
                f"Registration failed | Type: {self.type.name}, "
                f"OSS: {self.fcmodel.oss_id}, Error: {str(e)}",
                exc_info=True
            )
            return ResponseFC(
                status=Status(
                    task=StatusType.FAILED,
                    name='DeploymentError',
                    code=524,
                    message=f"Full deployment failed: {str(e)}"
                ),
                output={}
            )

        try:
            # Register
            request = RequestFC(
                unique_key=self.fcmodel.oss_id,
                name=self.fcmodel.filepath,
                func=self.fcmodel.classname,
                code_url=self.fcmodel.oss_signed_url
            )

            if self.type == FunctionType.ROLLOUT:
                endpoint = FC_REGISTER_ROLLOUT_API
            elif self.type == FunctionType.REWARD:
                endpoint = FC_REGISTER_REWARD_API
            elif self.type == FunctionType.GROUP_REWARD:
                endpoint = FC_REGISTER_GROUP_REWARD_API
            else:
                raise RegistrationError(f"Not exist type: {self.type.name}", error_code=2100)

            result = await client_fc(FC_API_KEY, endpoint, request.model_dump())
            func_type_id = get_func_type_id(self.type)
            self.entity_id = result.get('output', {}).get(func_type_id, '')

            if not self.entity_id:
                raise RegistrationError(f"Empty entity ID received: {result}", error_code=2101)

            logger.info(
                f"Function registered | Type: {self.type.name}, "
                f"ID: {self.entity_id}, OSS: {self.fcmodel.oss_id}"
            )

            return ResponseFC(
                status=Status(
                    task=StatusType.SUCCEEDED,
                    name='FunctionRegistered',
                    code=200,
                    message=f"{self.type.name} function registered successfully"
                ),
                output={'entity_id': self.entity_id}
            )

        except Exception as e:
            logger.error(
                f"Registration failed | Type: {self.type.name}, "
                f"Request: {request.model_dump()}, Error: {str(e)}",
                exc_info=True
            )

            return ResponseFC(
                status=Status(
                    task=StatusType.FAILED,
                    name='DeploymentError',
                    code=521,
                    message=f"Full deployment failed: {str(e)}"
                ),
                output={}
            )

    async def load(
            self,
            entity_id: Optional[str] = None,
            runtime: Optional[FunctionComponentRuntime] = None,
            warmup: bool = False
    ) -> ResponseFC:
        """Load and initialize a registered function instance."""
        try:
            # Resolve target registration ID
            target_entity_id = entity_id or self.entity_id
            if not target_entity_id:
                raise ValueErrorWithCode("No valid registration ID provided", error_code=2200)

            # Load function instance
            runtime = runtime or self.runtime
            job_id = generate_random_id()
            url = f"{FC_LOAD_API}/jobId-{job_id}/{target_entity_id}"
            result = await client_fc(FC_API_KEY, url, {**runtime.model_dump()} if runtime else {})
            self.instance_id = result.get('output', {}).get('instanceId', '')
            if not self.instance_id:
                raise FunctionLoadError(f"Empty instance ID received: {result}", error_code=2201)

            self.instance_url = result.get('output', {}).get('trigger_url', '')
            self.instance_token = result.get('output', {}).get('trigger_token', '')
            if (not self.instance_url) or (not self.instance_token):
                raise FunctionLoadError("Missing instance URL or token", error_code=2202)

            logger.info(
                f"Instance initialized | EntityID: {target_entity_id}, "
                f"InstanceID: {self.instance_id}, "
                f"Endpoint: {self.instance_url}, "
                f"Response: {result if LOG_LEVEL=='DEBUG' else deep_mask(result)}"
            )

        except Exception as e:
            logger.error(
                f"Instance initialization failed | EntityID: {target_entity_id}, "
                f"Error: {str(e)}",
                exc_info=True
            )
            return ResponseFC(
                status=Status(
                    task=StatusType.FAILED,
                    name='FunctionLoadError',
                    code=522,
                    message=f"Instance initialization failed: {str(e)}"
                ),
                output={}
            )

        # Perform instance warmup if requested
        if warmup:
            try:
                if not self.instance_url.startswith(('http://', 'https://')):
                    raise ValueErrorWithCode("Invalid instance URL format", error_code=2203)

                url = f"{self.instance_url.rstrip('/')}/health"
                result = await client_fc(self.instance_token, url, {}, 'GET')
                status = result.get('status', str(StatusType.UNKNOWN))
                if status != StatusType.HEALTH:
                    raise InstanceWarmupError(f"Health check failed: {result}", error_code=2204, instance_url=url)

                logger.info(
                    f"Instance warmup completed | Instance: {self.instance_id if self.instance_id else 'N/A'}"
                )

            except Exception as e:
                logger.error(
                    f"Warmup failed | InstanceID: {self.instance_id}, "
                    f"Error: {str(e)}",
                    exc_info=True
                )
                return ResponseFC(
                    status=Status(
                        task=StatusType.FAILED,
                        name='InstanceWarmupError',
                        code=511,
                        message=f"Instance warmup failed: {str(e)}"
                    ),
                    output={'instance_id': self.instance_id}
                )

        return ResponseFC(
            status=Status(
                task=StatusType.SUCCEEDED,
                name='InstanceReady',
                code=200,
                message="Function instance ready for requests"
            ),
            output={
                'instance_id': self.instance_id,
                'endpoint': self.instance_url,
                'status': 2  # 2 = Active status
            }
    )

    @classmethod
    async def query(
            cls,
            instance_id: str
    ) -> ResponseFC:
        """Retrieve current status of a function instance."""
        try:
            if not instance_id:
                raise InputError("No instance ID available for query", error_code=2300)

            url = f"{FC_QUERY_API}/{instance_id}"
            result = await client_fc(FC_API_KEY, url, {})
            status = result.get('output', {}).get('status', -1)
            if status == -1:
                raise InstanceQueryError(f"Invalid status received: {result}", error_code=2301)

            logger.debug(
                f"Status query completed | InstanceID: {instance_id} | Status: {status}."
            )

        except Exception as e:
            logger.error(
                f"Status query failed | InstanceID: {instance_id}, "
                f"Error: {str(e)}",
                exc_info=True
            )
            return ResponseFC(
                status=Status(
                    task=StatusType.FAILED,
                    name='InstanceQueryError',
                    code=523,
                    message=f"Status query failed: {str(e)}"
                ),
                output={'instance_id': instance_id}
            )

        return ResponseFC(
            status=Status(
                task=StatusType.SUCCEEDED,
                name='InstanceStatus',
                code=200,
                message="Instance status retrieved"
            ),
            output=result
        )

    @classmethod
    async def verify_function(
            cls,
            input_data: Union[RolloutInput, RewardInput, GroupRewardInput],
            instance_id: Optional[str] = None,
            instance_url: Optional[str] = None,
            instance_token: Optional[str] = None
    ) -> dict:
        """Validate deployed function functionality."""
        try:
            # Get instance metadata
            result = await cls.query(instance_id)
            if result.status.task != StatusType.SUCCEEDED:
                raise InstanceQueryError('Status query failed', error_code=2400)
            instance_url = instance_url or result.output.get('output', {}).get('trigger_url', '')
            instance_token = instance_token or result.output.get('output', {}).get('trigger_token', '')
            if (not instance_url) or (not instance_token):
                raise OutputError("No instance url/token provided", error_code=2401)

            input_data_dict = input_data.model_dump(mode='json', exclude_none=True)
            if 'model_resource' in input_data_dict and 'api_key' in input_data_dict['model_resource']:
                input_data_dict['model_resource']['api_key'] = input_data.model_resource.api_key.get_secret_value()

            # Execute test request
            response = await client_fc(
                instance_token,
                f"{instance_url}/api/v1",
                input_data_dict
            )

            # Validate response format
            if isinstance(input_data, RolloutInput):
                validator = RolloutOutput
            elif isinstance(input_data, RewardInput):
                validator = RewardOutput
            elif isinstance(input_data, GroupRewardInput):
                validator = GroupRewardOutput
            else:
                raise ValidationError("Unsupported input type", error_code=2402)

            validated = validator.model_validate(response)

            logger.info(
                f"Validation succeeded | "
                f"Input: {input_data_dict if LOG_LEVEL=='DEBUG' else deep_mask(input_data_dict)}, "
                f"Output: {validated.model_dump_json()}, "
                f"Status: {response.get('status', StatusType.SUCCEEDED)}"
            )
            return validated.model_dump()

        except Exception as e:
            logger.error(
                f"Validation failed | Instance: {instance_id}, "
                f"Error: {str(e)}",
                exc_info=True
            )
            raise ValidationError(
                f"Function verification failed: {str(e)}", error_code=2403
            ) from e


class RolloutFunctionComponent(AgenticRLFunctionComponent):
    """Rollout function component with type fixed as ROLLOUT."""

    type: FunctionType = Field(
        default=FunctionType.ROLLOUT,
        description="Type of function component"
    )

    # PLACEHOLDER
    weight: Optional[float] = Field(
        default=None,
        description="[PLACEHOLDER] Function weight mapping. This field is currently not used by the system."
    )
    reward_metric_weight: Optional[Dict[str, float]] = Field(
        default=None,
        description="[PLACEHOLDER] Reward metric weight mapping. This field is currently not used by the system."
    )


class RewardFunctionComponent(AgenticRLFunctionComponent):
    """Reward function component with type fixed as REWARD."""

    type: FunctionType = Field(
        default=FunctionType.REWARD,
        description="Type of function component"
    )
    weight: Optional[float] = Field(
        default=None,
        description="Function weight"
    )
    reward_metric_weight: Optional[Dict[str, float]] = Field(
        default=None,
        description="Reward metric weight mapping"
    )

    async def register(
            self,
            oss_id: Optional[str] = None,
            oss_url: Optional[str] = None,
    ) -> ResponseFC:
        if not self.reward_metric_weight:
            self.reward_metric_weight = self.fcmodel._get_sub_function_weights()
        result = await super().register(oss_id=oss_id, oss_url=oss_url)
        return result


class TuningModel(BaseModel):
    """Core configuration model for managing model tuning tasks."""

    name: str = Field(default='agentic-rl', min_length=1, max_length=256)
    fcs: List[AgenticRLFunctionComponent] = []
    datasets: Datasets = Datasets()
    model: FoundationModel = FoundationModel()
    training: Training = Training()
    observability: Optional[Observability] = Observability()

    async def register_functions(
            self,
            lazy_load: bool = True,
    ) -> tuple[List[str], List[str], List[str], List[str]]:
        """Register function compute components (FCs) for the tuning job."""
        entity_rollout_ids = []
        entity_reward_ids = []
        entity_group_reward_ids = []
        instance_rollout_ids = []
        instance_reward_ids = []
        instance_group_reward_ids = []

        try:
            for fc in self.fcs:
                if fc.entity_id:
                    entity_id = fc.entity_id
                else:
                    reg_result = await fc.register()
                    if reg_result.status.success:
                        entity_id = reg_result.output.get('entity_id', '')
                        if not entity_id:
                            raise RegistrationError("Empty entity ID after registration", error_code=2500)
                        logger.debug(
                            f"Registered new function component: "
                            f"Type={fc.type.value}, RegisterID={entity_id}"
                        )
                    else:
                        raise RegistrationError(f"Registration failed: {reg_result}", error_code=2501)

                if fc.type == FunctionType.ROLLOUT:
                    entity_rollout_ids.append(entity_id)
                elif fc.type == FunctionType.REWARD:
                    entity_reward_ids.append(entity_id)
                elif fc.type == FunctionType.GROUP_REWARD:
                    entity_group_reward_ids.append(entity_id)

                if not lazy_load:
                    load_result = await fc.load(entity_id=entity_id)
                    if load_result.status.success:
                        instance_id = load_result.output.get('instance_id', '')
                        if not instance_id:
                            raise FunctionLoadError("Empty instance ID after load", error_code=2502)
                        logger.debug(
                            f"Loaded function component instance: "
                            f"RegisterID={entity_id}, InstanceID={instance_id}"
                        )
                        if fc.type == FunctionType.ROLLOUT:
                            instance_rollout_ids.append(instance_id)
                        elif fc.type == FunctionType.REWARD:
                            instance_reward_ids.append(instance_id)
                        elif fc.type == FunctionType.GROUP_REWARD:
                            instance_group_reward_ids.append(instance_id)
                    else:
                        raise FunctionLoadError(f"Load failed: {load_result}", error_code=2503)

        except Exception as e:
            logger.error(f"Function component registration failed: {e}", exc_info=True)
            raise RegistrationError("Function component registration error", error_code=2504) from e

        return (entity_rollout_ids, entity_reward_ids, entity_group_reward_ids,
                instance_rollout_ids, instance_reward_ids, instance_group_reward_ids)

    async def register_datasets(self) -> tuple[List[str], List[str]]:
        """Register and validate training/validation datasets."""
        try:
            # Perform dataset validation and upload
            await self.datasets.upload_datasets()

            logger.info(
                f"Successfully registered datasets: "
                f"{len(self.datasets.uploaded_training_ids)} training, "
                f"{len(self.datasets.uploaded_validation_ids)} validation"
            )

        except Exception as e:
            logger.error(
                "Unexpected error during dataset registration",
                exc_info=True,
                stack_info=True
            )
            raise OSSUploadError(
                "Critical failure in dataset registration process", error_code=2600
            ) from e

        return self.datasets.uploaded_training_ids, self.datasets.uploaded_validation_ids

    def get_entity_ids(self, type: FunctionType):
        ids = []
        for fc in self.fcs:
            if type == fc.type and fc.entity_id:
                ids.append(fc.entity_id)
        return ids

    def get_runtimes(self, type: FunctionType):
        runtimes = []
        for fc in self.fcs:
            if type == fc.type and fc.runtime:
                runtimes.append(fc.runtime.model_dump())
        return runtimes

    def get_names(self, type: FunctionType):
        """Get name values for function components of the given type."""
        names = []
        for fc in self.fcs:
            if type == fc.type:
                names.append(getattr(fc, 'name', None))
        return names

    def set_names(self, type: FunctionType):
        """Set name values for function components of the given type."""
        for fc in self.fcs:
            if type == fc.type and not fc.name:
                fc.name = '-'.join((str(fc.type), generate_random_id()[:8]))
                logger.debug(f"Generate a random name: {fc.name} for {type}")

    def get_weights(self, type: FunctionType):
        """Get weight values for function components of the given type."""
        weights = []
        for fc in self.fcs:
            if type == fc.type:
                weights.append(getattr(fc, 'weight', None))
        return weights

    def get_reward_metric_weights(self, type: FunctionType):
        """Get reward_metric_weight values for function components of the given type."""
        metric_weights = []
        for fc in self.fcs:
            if type == fc.type and type == FunctionType.REWARD:
                metric_weights.append(getattr(fc, 'reward_metric_weight', None))
        return metric_weights

    def combine_ids_runtimes(
            self,
            type: FunctionType,
            ids: Union[List[str], str] = None,
            runtimes: Union[List[Dict[str, Any]], Dict[str, Any]] = None,
            id_str: str = None):

        if ids:
            ids = [ids] if isinstance(ids, str) else ids
        if runtimes:
            runtimes = [runtimes] if isinstance(runtimes, Dict) else runtimes
        function_ids = ids or self.get_entity_ids(type)
        function_runtimes = runtimes or self.get_runtimes(type)

        self.set_names(type)
        function_names = self.get_names(type)
        function_weights = self.get_weights(type)
        function_metric_weights = self.get_reward_metric_weights(type)

        id_str = id_str or get_func_type_id(type)
        functions = []
        for i in range(len(function_ids)):
            function = {id_str: function_ids[i]}

            # Add name if present (for reward/group_reward types)
            if i < len(function_names) and function_names[i] is not None:
                function['name'] = function_names[i]

            # Add weight if present (for reward/group_reward types)
            if i < len(function_weights) and function_weights[i] is not None:
                function['weight'] = function_weights[i]

            # Add reward_metric_weight if present (for reward/group_reward types)
            if i < len(function_metric_weights) and function_metric_weights[i] is not None:
                function['reward_metric_weight'] = function_metric_weights[i]

            # Merge runtime config
            if function_runtimes and i <= len(function_runtimes) - 1:
                runtime_config = function_runtimes[i].copy()
                if 'env' in runtime_config and isinstance(runtime_config['env'], dict):
                    for key, value in runtime_config['env'].items():
                        if isinstance(value, bool):
                            runtime_config['env'][key] = str(value).lower()

                function.update(runtime_config)

            functions.append(function)

        return functions

    def add_function_components(
            self,
            type: FunctionType,
            classpaths: Optional[Union[List[str], str]] = None,
            entity_ids: Optional[Union[List[str], str]] = None, # Prefer entity_ids over classpaths when available
            runtimes: Optional[Union[List[Dict[str, Any]], Dict[str, Any]]] = None,
            names: Optional[Union[List[str], str]] = None,
            weights: Optional[Union[List[float], float]] = None,
            reward_metric_weights: Optional[Union[List[Dict[str, float]], Dict[str, float]]] = None,
            workspace_dir: Optional[str] = './'):

        classpaths = [classpaths] if isinstance(classpaths, str) else classpaths
        entity_ids = [entity_ids] if isinstance(entity_ids, str) else entity_ids
        runtimes = [runtimes] if isinstance(runtimes, Dict) else runtimes
        names = [names] if isinstance(names, str) else names
        weights = [weights] if isinstance(weights, float) else weights
        reward_metric_weights = [reward_metric_weights] if isinstance(reward_metric_weights, Dict) else reward_metric_weights

        len_classpaths = len(classpaths) if classpaths else 0
        len_entity_ids = len(entity_ids) if entity_ids else 0
        len_runtimes = len(runtimes) if runtimes else 0
        len_names = len(names) if names else 0
        len_weights = len(weights) if weights else 0
        len_reward_metric_weights = len(reward_metric_weights) if reward_metric_weights else 0

        if len_classpaths == 0 and len_entity_ids == 0:
            logger.warning("The inputs of classpaths and entity_ids are none.")
            return []

        if len_entity_ids > 0: # Prefer entity_ids over classpaths when available
            for i in range(len_entity_ids):
                self.fcs.append(AgenticRLFunctionComponent(
                    type=type,
                    entity_id=entity_ids[i],
                    runtime=FunctionComponentRuntime(**runtimes[i]) if runtimes and i < len_runtimes else None,
                    name=names[i] if names and i < len_names else None,
                    weight=weights[i] if weights and i < len_weights else None,
                    reward_metric_weight=reward_metric_weights[i] if reward_metric_weights and i < len_reward_metric_weights else None,
                ))
        else:
            for i in range(len_classpaths):
                self.fcs.append(AgenticRLFunctionComponent(
                    type=type,
                    fcmodel=FunctionComponentModel(
                        zipdir=workspace_dir,
                        classpath=classpaths[i]),
                    runtime=FunctionComponentRuntime(**runtimes[i]) if runtimes and i < len_runtimes else None,
                    name=names[i] if names and i < len_names else None,
                    weight=weights[i] if weights and i < len_weights else None,
                    reward_metric_weight=reward_metric_weights[i] if reward_metric_weights and i < len_reward_metric_weights else None,
                ))

        return self.fcs

    def check_function_names(self) -> bool:
        """
        Check for duplicate function component names.

        Returns:
            True if all names are unique, False if duplicates found.
        """
        seen_names = {}
        duplicate_found = False

        for index, fc in enumerate(self.fcs):
            if not hasattr(fc, 'name'):
                logger.error(f"Function component at index {index} is missing a 'name' attribute")
                duplicate_found = True
                continue

            name = fc.name
            if name in seen_names:
                logger.error(
                    f"Duplicate function name '{name}' found: "
                    f"Original at index {seen_names[name]}, duplicate at index {index}"
                )
                duplicate_found = True
            else:
                seen_names[name] = index

        if duplicate_found:
            logger.error("Duplicate function names detected. All function names must be unique.")
            return False

        logger.debug("All function names are unique.")
        return True


class AgenticRLTuning(Models, BaseModel):
    """Main interface class for model tuning operations."""

    tuning_id: Optional[str] = ''
    tuning: TuningModel = TuningModel()
