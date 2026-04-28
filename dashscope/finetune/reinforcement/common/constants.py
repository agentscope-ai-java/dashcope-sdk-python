from typing import Any
import os
import logging

from dashscope.version import __version__

# --------------------------
# Environment Configuration
# --------------------------

def get_bool_env(env_var: str, default: bool) -> bool:
    """Safely parse boolean environment variable."""
    value = os.getenv(env_var, str(default)).strip().lower()
    return value in ('true', '1', 'yes')

def get_int_env(env_var: str, default: int) -> int:
    """Safely parse integer environment variable."""
    try:
        return int(os.getenv(env_var, str(default)))
    except ValueError:
        return default

# Debug mode configuration
DEBUG_AGENTIC_RL = get_bool_env('DEBUG_AGENTIC_RL', False)

# Base URL configuration
DASHSCOPE_HTTP_BASE_URL = os.environ.get(
    'DASHSCOPE_HTTP_BASE_URL',
    'https://dashscope.aliyuncs.com/api/v1'
)

# API Key configuration
DASHSCOPE_API_KEY = os.environ.get('DASHSCOPE_API_KEY', '')
FC_API_KEY = os.environ.get('FC_API_KEY', DASHSCOPE_API_KEY)

# --------------------------
# Logging Configuration
# --------------------------
LOGGER_NAME = os.environ.get('LOGGER_NAME', 'dashscope')
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'info').upper()
LOGGER_FILTER_FIELDS = {
    'trigger_token', 'instance_token', 'api_token',
    'api_key', 'password', 'access_key', 'secret_key'
}  # Case-sensitive field names to filter

# Initialize logger
logger = logging.getLogger(LOGGER_NAME)
logger.setLevel(LOG_LEVEL)

# --------------------------
# Service Configuration
# --------------------------
HTTP_REQUEST_TIMEOUT = get_int_env('HTTP_REQUEST_TIMEOUT', 600)

# Bailian File Service
BAILIAN_FILE_API = os.environ.get(
    'BAILIAN_FILE_API',
    f'{DASHSCOPE_HTTP_BASE_URL}/files'
)
BAILIAN_FILE_TIMEOUT = get_int_env('BAILIAN_FILE_TIMEOUT', 600)

# Function Compute Endpoints
FC_BASE_ENDPOINT = f'{DASHSCOPE_HTTP_BASE_URL}/fine-tunes'
FC_UPLOAD_OSS_API = os.environ.get(
    'FC_UPLOAD_OSS_API',
    f'{FC_BASE_ENDPOINT}/generate/faas/upload/url'
)
FC_REGISTER_ROLLOUT_API = os.environ.get(
    'FC_REGISTER_ROLLOUT_API',
    f'{FC_BASE_ENDPOINT}/create/rollout'
)
FC_REGISTER_REWARD_API = os.environ.get(
    'FC_REGISTER_REWARD_API',
    f'{FC_BASE_ENDPOINT}/create/reward'
)
FC_REGISTER_GROUP_REWARD_API = os.environ.get(
    'FC_REGISTER_GROUP_REWARD_API',
    f'{FC_BASE_ENDPOINT}/create/group-reward'
)
FC_LOAD_API = os.environ.get(
    'FC_LOAD_API',
    f'{FC_BASE_ENDPOINT}/online/faas'
)
FC_QUERY_API = os.environ.get(
    'FC_QUERY_API',
    f'{FC_BASE_ENDPOINT}/query/faas'
)
FC_LAYER_CREATE_API = os.environ.get( # POST
    'FC_LAYER_CREATE_API',
    f'{FC_BASE_ENDPOINT}/create/faas/layer'
)
FC_LAYER_QUERY_API = os.environ.get( # GET
    'FC_LAYER_QUERY_API',
    f'{FC_BASE_ENDPOINT}/query/faas/layer/status'
)


# --------------------------
# Function Compute Runtime
# --------------------------
FC_FILES_START = 'start.sh'
FC_PYPI_LIB = os.environ.get(
    'FC_PYPI_LIB',
    f'dashscope-{__version__}-py3-none-any.whl' if DEBUG_AGENTIC_RL
    else 'dashscope'
)
FC_PYPI_REPO = os.environ.get(
    'FC_PYPI_REPO',
    'https://mirrors.aliyun.com/pypi/simple/'
)
FC_SERVER_CLASSPATH = os.environ.get(
    'FC_SERVER_CLASSPATH',
    'dashscope.finetune.reinforcement.component.server.server'
)
FC_WORKERS_COUNT = get_int_env('FC_WORKERS_COUNT', 2)
FC_OFFLINE_INSTALLATION = get_bool_env('FC_OFFLINE_INSTALLATION', True)
FC_LAYER_NAME = "fc_layer"
FC_REQUIREMENTS_FILE = "./requirements.txt"

# --------------------------
# Tuning Configuration
# --------------------------
TUNING_MODE_NAME = 'reinforcement'
ENABLE_TRAJECTORY = get_bool_env('ENABLE_TRAJECTORY', True)

# --------------------------
# Configuration Validation
# --------------------------
# if DEBUG_AGENTIC_RL:
#     logger.debug(f"Debug mode enabled. Using base URL: {DASHSCOPE_HTTP_BASE_URL}")
#     logger.debug(f"FC_PYPI_LIB: {FC_PYPI_LIB}")
