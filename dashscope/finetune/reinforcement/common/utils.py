import aiohttp
import ast
import asyncio
import copy
import fnmatch
import json
import os
import requests
import uuid
import zipfile
from aiohttp import FormData
from tenacity import retry, stop_after_attempt, wait_exponential, \
    retry_if_exception_type
from typing import Optional, List, Any, Dict, Union, Tuple

from dashscope.finetune.reinforcement import (
    LOG_LEVEL,
    DASHSCOPE_API_KEY, BAILIAN_FILE_API,
    BAILIAN_FILE_TIMEOUT, HTTP_REQUEST_TIMEOUT,
    FC_FILES_START, FC_PYPI_LIB, FC_PYPI_REPO, FC_LAYER_USED,
    FC_SERVER_CLASSPATH, FC_ZIP_EXCLUDE_PATTERNS, FC_OSS_FILE_SIZE_WARNING,
    LOGGER_FILTER_FIELDS, FC_WORKERS_COUNT)
from dashscope.finetune.reinforcement import logger
from dashscope.finetune.reinforcement.common.errors import (
    InputError, OutputError, ConfigurationError, BasePermissionError,
    RuntimeErrorWithCode, OSSUploadError
)
from dashscope.finetune.reinforcement.common.model_types import FileSpec, \
    FunctionType


def generate_random_id(type: str = '') -> str:
    """Generate a unique identifier with optional prefix."""
    uuid4 = uuid.uuid4()
    return f"{type}-{uuid4}" if type else str(uuid4)


async def async_http_request(
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Union[Dict[str, Any], FormData]] = None,
        timeout: int = 10
) -> Dict[str, Any]:
    """Perform an asynchronous HTTP request with robust error handling."""
    result = {"status": {"code": 200, "message": "Success"}, "output": {}}

    try:
        async with aiohttp.ClientSession(
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=timeout)
        ) as session:
            method = method.upper()

            if method == "GET":
                async with session.get(url, params=data) as response:
                    result = await _handle_response(response)
            elif method == "POST":
                async with session.post(url, json=data) as response:
                    result = await _handle_response(response)
            elif method == "POST-DATA":
                async with session.post(url, data=data) as response:
                    result = await _handle_response(response)
            else:
                raise InputError(f"Unsupported method: {method}",
                                 error_code=4000)

    except aiohttp.ClientError as e:
        result["status"] = {"code": 4001, "message": f"Client error: {str(e)}"}
    except asyncio.TimeoutError:
        result["status"] = {"code": 4002,
                            "message": f"Request timeout: ({timeout}s)"}
    except InputError as e:
        result["status"] = {"code": e.error_code,
                            "message": f"Input error: {str(e)}"}
    except Exception as e:
        result["status"] = {"code": 4003,
                            "message": f"Unexpected error: {str(e)}"}

    return result


async def _handle_response(response) -> Dict[str, Any]:
    """Handle HTTP response and extract JSON data."""
    try:
        content = await response.json()
        content.setdefault("status", {"code": response.status,
                                      "message": response.reason})
        return content
    except json.JSONDecodeError:
        return {
            "status": {
                "code": 4004,
                "message": "Invalid JSON response"
            },
            "output": await response.text()
        }


async def client_fc(
        api_key: str,
        url: str,
        input: dict,
        method: str = 'POST',
        content_type: str = 'application/json'
) -> dict:
    """Client function for Function Compute API requests."""
    return await async_http_request(
        method=method,
        url=url,
        headers={'Content-Type': content_type,
                 'Authorization': 'Bearer ' + api_key},
        data=input,
        timeout=HTTP_REQUEST_TIMEOUT
    )


def check_file(file: str) -> None:
    """Validate file existence and accessibility."""
    if not os.path.exists(file):
        raise InputError(f"File {file} not found", error_code=4100)
    if not os.path.isfile(file):
        raise InputError(f"{file} is not a file", error_code=4101)
    if not os.access(file, os.R_OK):
        raise InputError(f"No read access to file: {file}", error_code=4102)


def generate_agentic_script(
        fc_pypi_lib: str,
        fc_pypi_repo: str,
        requirements_path: str,
        func_type: str,
        classpath: str,
        function_layer_used: bool = True
) -> str:
    """
    Generate robust deployment script with error handling.

    Args:
        fc_pypi_repo: PyPI repository URL
        requirements_path: Path to requirements.txt
        func_type: Function type (reward/rollout)
        classpath: Full processor class path

    Returns:
        Generated bash script content
    """
    shell_script_header = f'''#!/usr/bin/env bash

set -euo pipefail  # Strict error handling

# ================= Configuration ==================
SERVICE_TYPE="{func_type}"                          # reward|rollout
PROCESSOR_CLASS="{classpath}"  # Full class path
PYPI_REPO="{fc_pypi_repo}"
SDK_PACKAGE="{fc_pypi_lib}"
REQUIREMENTS_FILE="{requirements_path}"
SERVER_CLASSPATH="{FC_SERVER_CLASSPATH}"
WORKERS_COUNT="{FC_WORKERS_COUNT}"
FUNCTION_LAYER="{function_layer_used}"
LOG_DIR="/tmp/log/agentic_rl"
MAX_RETRIES=3
'''

    shell_script_content = r'''
# ================ Helper Functions ================
init_logging() {
    mkdir -p "${LOG_DIR}"
    local log_file="${LOG_DIR}/service_$(date +%Y%m%d).log"
    exec 3>&1 4>&2
    trap 'exec 1>&3 2>&4' EXIT
    exec > >(tee -a "$log_file") 2>&1
    echo -e "\n\n=== Service Start: $(date) ==="
}

log() {
    printf "[%s] %s\n" "$(date +'%Y-%m-%d %H:%M:%S')" "$*"
}

cleanup() {
    log "Cleaning temporary workspace..."
    rm -rf "${TMPDIR:-/tmp}/pip*"
    find . -name "__pycache__" -exec rm -rf {} + 2>/dev/null
}

validate_environment() {
    log "Validating runtime environment..."

    # Python check
    if ! command -v python3 &>/dev/null; then
        log "ERROR: Python3 not found in PATH"
        exit 101
    fi
}

# ============== Dependency Management ==============
install_with_retry() {
    local packages=("$@")
    local retry_count=0

    while [ $retry_count -lt $MAX_RETRIES ]; do
        log "Installing ${packages[*]} (attempt $((retry_count+1))/${MAX_RETRIES})"
        if python3 -m pip install -U "${packages[@]}" \
            --index-url "${PYPI_REPO}" \
            --no-cache-dir \
            --compile; then
            return 0
        fi
        retry_count=$((retry_count+1))
        sleep $((retry_count * 10))
    done

    log "FATAL: Failed to install ${packages[*]} after ${MAX_RETRIES} attempts"
    return 1
}

# ================ Main Execution ===================
main() {
    # Phase 1: Initialization
    init_logging
    trap cleanup EXIT
    validate_environment
    
    if [ "${FUNCTION_LAYER}" = "False" ]; then
        # Phase 2: 
        if ! install_with_retry "virtualenv"; then
            log "Failed to install default package: $pkg"
            exit 202
        fi
        virtualenv dashscope-env
        source dashscope-env/bin/activate
    fi

    # Phase 3: Default dependency Setup
    log "Installing default packages"
    local_packages=($SDK_PACKAGE)
    for pkg in "${local_packages[@]}"; do
        if ! install_with_retry "$pkg"; then
            log "Failed to install default package: $pkg"
            exit 203
        fi
    done
    
    if [ "${FUNCTION_LAYER}" = "False" ]; then
        # Phase 4: User dependency Setup
        log "Starting user dependency installation"
        if [ -f "${REQUIREMENTS_FILE}" ]; then # Check if requirements file exists
            log "Installing additional requirements from ${REQUIREMENTS_FILE}"
            if ! install_with_retry -r "${REQUIREMENTS_FILE}"; then
                log "Failed to install requirements from ${REQUIREMENTS_FILE}"
                exit 204
            fi
        fi
    fi

    # Phase 5: Environment Configuration
    export FUNC_TYPE="${SERVICE_TYPE}"
    export PROCESSOR_CLASS="${PROCESSOR_CLASS}"
    export PYTHONPATH=".:${PYTHONPATH:-}"
    export WORKERS_COUNT="${WORKERS_COUNT}"

    log "Final Environment:"
    env | grep -E 'FUNC_TYPE|PROCESSOR_CLASS|PYTHONPATH'

    # Phase 6: Service Launch
    log "Starting ${SERVICE_TYPE} service"
    exec python3 -m "${SERVER_CLASSPATH}" "$@"
}
'''

    shell_script_main = '''# ==================== Entry ========================
main "$@"
'''

    return shell_script_header + shell_script_content + shell_script_main


def create_deployment_files(
        type: FunctionType,
        dirpath: str,
        filepath: str,
        classname: str,
        requirements_path: str = '',
) -> None:
    """Create startup script and requirements file for deployment."""
    try:
        # Validate main Python file
        path = os.path.join(dirpath, filepath)
        check_file(path)
        logger.debug(f"Found code file: {path}")

        # Validate requirements file if provided
        if requirements_path and requirements_path.strip():
            req_path = os.path.join(dirpath, requirements_path)
            check_file(req_path)
            logger.debug(f"Found requirements file: {req_path}")

        # Create startup script
        classpath = \
        os.path.normpath(filepath).replace('/', '.').rsplit('.py', 1)[
            0] + '.' + classname
        content = generate_agentic_script(
            fc_pypi_lib=FC_PYPI_LIB,
            fc_pypi_repo=FC_PYPI_REPO,
            requirements_path=requirements_path,
            func_type=str(type),
            classpath=classpath,
            function_layer_used=FC_LAYER_USED,
        )

        with open(FC_FILES_START, 'w', encoding='utf-8') as f:
            f.write(content)

        # Add execute permission on Unix systems
        if os.name == 'posix':
            os.chmod(FC_FILES_START, 0o755)

        logger.debug(f"Generated startup script: {FC_FILES_START}")
    except Exception as e:
        logger.error(f"Deployment file creation failed: {str(e)}",
                     exc_info=True)
        raise RuntimeErrorWithCode("Deployment file creation error",
                                   error_code=4200) from e


def zip_files(files: List[str], output_zip: str) -> None:
    """Zip multiple files into a single archive."""
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file in files:
            zipf.write(file)


def zip_dir(
        dirpath: str,
        output_zip: str,
        extra_files: Optional[List[str]] = None,
        rw_type: str = "w",
        exclude_patterns: Optional[List[str]] = None,
) -> None:
    """
    Compress a directory and optional extra files, with exclusion support.

    Args:
        dirpath: Main directory path to compress
        output_zip: Output zip file path
        extra_files: List of additional files to add
        rw_type: Zip file write mode ('w', 'a', etc.)
        exclude_patterns: List of patterns to exclude (e.g. ["*.log", "__pycache__"])
    """
    if exclude_patterns is None:
        env_exclude = FC_ZIP_EXCLUDE_PATTERNS
        exclude_patterns = [p.strip() for p in env_exclude.split(",") if
                            p.strip()]

    all_excludes = exclude_patterns
    logger.debug(f"Zip exclusion patterns: {all_excludes}")

    try:
        with zipfile.ZipFile(output_zip, rw_type,
                             zipfile.ZIP_DEFLATED) as zipf:
            # Compress main directory
            if os.path.exists(dirpath):
                for root, dirs, files in os.walk(dirpath, topdown=True):
                    the_dirs = []
                    for d in dirs:
                        full_rel_path = os.path.join(
                            os.path.relpath(root, start=dirpath), d)
                        normalized_path = full_rel_path.replace('\\', '/')

                        matched_pattern = None
                        for pattern in all_excludes:
                            if fnmatch.fnmatch(d, pattern) or fnmatch.fnmatch(
                                    normalized_path, pattern):
                                matched_pattern = pattern
                                break

                        if not matched_pattern:
                            the_dirs.append(d)
                        else:
                            logger.debug(
                                f"Excluding directory: {normalized_path} (matched pattern: '{matched_pattern}')")
                    dirs[:] = the_dirs

                    for file in files:
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, start=dirpath)

                        if any(
                                fnmatch.fnmatch(os.path.basename(file),
                                                pattern) or
                                fnmatch.fnmatch(file, pattern)
                                for pattern in all_excludes
                        ):
                            logger.debug(f"Excluding file: {rel_path}")
                            continue

                        zipf.write(file_path, rel_path)
            else:
                logger.warning(f"Directory not found: {dirpath}")

            # Add extra files to zip root directory
            if extra_files:
                for file in extra_files:
                    if os.path.exists(file):
                        if any(
                                fnmatch.fnmatch(os.path.basename(file),
                                                pattern)
                                for pattern in all_excludes
                        ):
                            logger.debug(f"Excluding extra file: {file}")
                            continue

                        zipf.write(file, os.path.basename(file))
                    else:
                        logger.warning(f"Extra file not found: {file}")

    except Exception as e:
        logger.error(f"Directory compression failed: {str(e)}", exc_info=True)
        raise RuntimeErrorWithCode("Directory compression error",
                                   error_code=4300) from e


def _sync_upload_to_oss(signed_url: str, zip_path: str) -> int:
    """Synchronously upload a file to OSS with progress tracking."""
    try:
        file_size = os.path.getsize(zip_path)
        size_mb = file_size / (1024 * 1024)
        if file_size > FC_OSS_FILE_SIZE_WARNING:
            logger.warning(
                f"Uploading large file: {zip_path} ({size_mb:.2f}MB) to OSS")
            raise OSSUploadError(
                f"Uploading large file: {zip_path} ({size_mb:.2f}MB) to OSS")
        else:
            logger.debug(
                f"Uploading file: {zip_path} ({size_mb:.2f}MB) to OSS")

        with open(zip_path, 'rb') as file:
            response = requests.put(
                signed_url,
                data=file,
                headers={},
                timeout=BAILIAN_FILE_TIMEOUT
            )

            if response.status_code != 200:
                error_msg = response.text
                raise OSError(
                    f"OSS upload failed ({response.status_code}): {error_msg}")

            return response.status_code
    except Exception as e:
        logger.error(f"OSS upload failed: {str(e)}", exc_info=True)
        raise RuntimeErrorWithCode("OSS upload error", error_code=4400) from e


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            requests.exceptions.ChunkedEncodingError
    )),
    reraise=True
)
async def upload_zip_to_oss_and_by_signed_url(signed_url: str,
                                              zipfile: str) -> int:
    """Asynchronously upload ZIP file to OSS with retry mechanism."""
    try:
        return await asyncio.to_thread(_sync_upload_to_oss, signed_url,
                                       zipfile)
    except BasePermissionError:
        raise  # Re-raise permission errors directly
    except Exception as e:
        if "403" in str(e):
            raise BasePermissionError("OSS access denied (403)",
                                  error_code=4401) from e
        raise


async def to_bailian_data(files: List[FileSpec]) -> List[str]:
    """
    Upload files to Bailian file storage service.

    Returns:
        List of uploaded file IDs

    Raises:
        OutputError: If file upload fails
    """
    headers = {"Authorization": f"Bearer {DASHSCOPE_API_KEY}"}
    form_data = FormData()
    uploaded_files = []

    try:
        valid_file_count = 0
        for file_spec in files:
            file_path = file_spec.path
            descriptions = file_spec.descriptions

            # Validate file
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                continue
            if not os.path.isfile(file_path):
                logger.error(f"Not a file: {file_path}")
                continue
            if os.path.getsize(file_path) == 0:
                logger.error(f"Empty file: {file_path}")
                continue

            # Add file to form data
            with open(file_path, "rb") as f:
                form_data.add_field(
                    name="files",
                    value=f.read(),
                    filename=os.path.basename(file_path),
                    content_type="application/octet-stream"
                )

            form_data.add_field("purpose", "fine-tune")
            if descriptions:
                form_data.add_field("descriptions", descriptions)

            valid_file_count += 1

        # Check if there are any valid files to upload
        if valid_file_count == 0:
            raise InputError(
                "No valid files found to upload. All files failed validation.",
                error_code=4600)

        # Execute upload request
        result = await async_http_request(
            method="POST-DATA",
            url=BAILIAN_FILE_API,
            headers=headers,
            data=form_data,
            timeout=BAILIAN_FILE_TIMEOUT
        )

        # Handle errors
        if result.get('status', {}).get('code', 200) != 200:
            raise OutputError(f"File upload failed: {result}", error_code=4500)

        data = result.get('data', {})
        if 'failed_uploads' in data and data['failed_uploads']:
            failed_files = ', '.join(
                [f['name'] for f in data['failed_uploads']])
            raise OutputError(f"Partial upload failed: {failed_files}",
                              error_code=4501)

        # Collect uploaded file IDs
        for f in data.get('uploaded_files', []):
            if file_id := f.get('file_id'):
                uploaded_files.append(file_id)

        logger.debug(f"Uploaded {len(uploaded_files)} files")
        return uploaded_files

    except Exception as e:
        logger.error(f"File upload failed: {str(e)}", exc_info=True)
        raise OutputError("File upload error", error_code=4502) from e


def secret_part_str(value: str):
    return value[:4] + '*' * 4 + value[-4:] if len(value) > 8 else '****'


def deep_mask(data: Any) -> Any:
    """
    Recursively mask sensitive fields in data structures.

    Args:
        data: Input data to process

    Returns:
        Deep copy with sensitive fields masked
    """
    if hasattr(data, 'model_dump'):
        try:
            data = data.model_dump(mode='json')
        except AttributeError:
            data = data.dict()

    if isinstance(data, dict):
        return {
            key: secret_part_str(
                val) if key.lower() in LOGGER_FILTER_FIELDS else deep_mask(val)
            for key, val in data.items()
        }
    elif isinstance(data, list):
        return [deep_mask(item) for item in data]
    elif isinstance(data, tuple):
        return tuple(deep_mask(item) for item in data)
    elif isinstance(data, set):
        return {deep_mask(item) for item in data}
    else:
        return copy.deepcopy(data)


def set_api_key(api_key: Optional[str] = None) -> None:
    """
    Sets the DashScope API key as an environment variable.

    Args:
        api_key: The API key to set. If None, it attempts to use the
                 existing DASHSCOPE_API_KEY environment variable.

    Raises:
        ConfigurationError: If api_key is not provided and DASHSCOPE_API_KEY
                    environment variable is not set.
    """
    # 1. If api_key is provided, set it and log
    if api_key:
        os.environ['DASHSCOPE_API_KEY'] = api_key
        logger.debug(
            f"Set environ DASHSCOPE_API_KEY: {api_key if LOG_LEVEL == 'DEBUG' else deep_mask(api_key)}"
        )
        return

    # 2. If api_key is NOT provided, check if env var exists
    if not os.environ.get('DASHSCOPE_API_KEY'):
        raise ConfigurationError(
            "DashScope API key is missing. "
            "Please provide 'api_key' argument or set the 'DASHSCOPE_API_KEY' environment variable.",
            error_code=4600
        )

    # 3. If env var exists, just log that we are using it (optional)
    logger.debug("Using existing DASHSCOPE_API_KEY from environment.")


def get_filepath_classname(full_path: str) -> Tuple[str, str]:
    """
    Extract file path and class name from a path string.

    Args:
        full_path: Path in either format:
            - 'module.path.ClassName'
            - 'path/to/file.py:ClassName'

    Returns:
        Tuple (filepath, classname)

    Raises:
        InputError: For invalid formats
    """
    full_path = full_path.strip()

    if ':' in full_path:
        # Format: 'path/to/file.py:ClassName'
        parts = full_path.split(':', 1)
        if len(parts) != 2 or not parts[0].strip() or not parts[1].strip():
            raise InputError(
                f"Invalid format '{full_path}'. Expected 'path/to/file.py:ClassName'",
                error_code=4700
            )
        if ':' in parts[1]:
            raise InputError(
                f"Invalid class name format '{parts[1]}'. Class name cannot contain colon.",
                error_code=4701
            )

        filepath, classname = parts[0].strip(), parts[1].strip()
        if not filepath.endswith('.py'):
            filepath += '.py'
    else:
        # Format: 'module.path.ClassName'
        parts = full_path.split('.')
        if len(parts) < 2:
            raise InputError(
                f"Invalid format '{full_path}'. Expected 'module.path.ClassName' or 'path/to/file.py:ClassName'",
                error_code=4702
            )
        classname = parts[-1]
        module_path = '.'.join(parts[:-1])
        filepath = module_path.replace('.', '/') + '.py'

    return filepath.replace('\\', '/'), classname


def get_func_type_id(func_type: FunctionType):
    return str(func_type).lower() + '_id'


def deep_remove_none(obj):
    """Recursively remove items with value None from dicts and lists (including nested structures)"""
    if isinstance(obj, dict):
        # Process dict: filter keys with non-None values and recursively process values
        return {
            k: deep_remove_none(v)
            for k, v in obj.items()
            if v is not None
        }
    elif isinstance(obj, list):
        # Process list: filter non-None elements and recursively process each element
        return [
            deep_remove_none(elem)
            for elem in obj
            if elem is not None
        ]
    else:
        # Other types are returned as-is
        return obj


def get_weights_from_file(filepath: str, classname: str = "") -> Dict[
    str, float]:
    """
    Extract reward weights from a Python file

    Args:
        filepath: Path to the Python file
        classname: Optional class name to filter by

    Returns:
        Dictionary mapping reward function names to their weights
    """
    # Check if file exists
    if not filepath or not os.path.exists(filepath):
        logger.error(f"File not found or empty filepath: {filepath}")
        return {}

    # Read file content
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source_code = f.read()
    except Exception as e:
        logger.error(f"Error reading file {filepath}: {str(e)}")
        return {}

    # Try AST method first
    return extract_reward_weights(source_code, classname)


def extract_reward_weights(source_code: str, classname: str) -> Dict[
    str, float]:
    """
    Static analyzer to extract reward weights from decorated functions.

    Args:
        source_code: Python source code containing decorated reward functions
        classname: Name of the class to scan

    Returns:
        Dictionary of {function_name: weight} pairs
    """
    weights = {}

    # Parse the AST
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return weights

    # Find the class definition
    for node in tree.body:
        if not isinstance(node, ast.ClassDef) or node.name != classname:
            continue

        for item in node.body:
            # Check for both synchronous and asynchronous functions
            if not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            for decorator in item.decorator_list:
                decorator_name = ""
                decorator_args = {}

                # Get decorator name
                if isinstance(decorator, ast.Call):
                    if isinstance(decorator.func, ast.Name):
                        decorator_name = decorator.func.id
                    elif isinstance(decorator.func, ast.Attribute):
                        decorator_name = decorator.func.attr
                elif isinstance(decorator, ast.Name):
                    decorator_name = decorator.id

                if decorator_name != "sub_reward_func":
                    continue

                # Process decorator arguments
                if isinstance(decorator, ast.Call):
                    # Positional arguments
                    for i, arg in enumerate(decorator.args):
                        if i == 0:
                            # Handle string values
                            if isinstance(arg, ast.Str):
                                decorator_args["name"] = arg.s
                            elif isinstance(arg, ast.Constant) and isinstance(
                                    arg.value, str):
                                decorator_args["name"] = arg.value
                            elif isinstance(arg,
                                            ast.Num):  # Deprecated but still in some versions
                                decorator_args["name"] = str(arg.n)

                        if i == 1:
                            # Handle numeric values
                            if isinstance(arg, ast.Num):
                                decorator_args["sub_weight"] = arg.n
                            elif isinstance(arg, ast.Constant) and isinstance(
                                    arg.value, (int, float)):
                                decorator_args["sub_weight"] = arg.value

                    # Keyword arguments
                    for kw in decorator.keywords:
                        key = kw.arg
                        value = kw.value

                        if key == "name":
                            if isinstance(value, ast.Str):
                                decorator_args["name"] = value.s
                            elif isinstance(value,
                                            ast.Constant) and isinstance(
                                    value.value, str):
                                decorator_args["name"] = value.value
                            elif isinstance(value, ast.Num):
                                decorator_args["name"] = str(value.n)

                        elif key == "sub_weight":
                            if isinstance(value, ast.Num):
                                decorator_args["sub_weight"] = value.n
                            elif isinstance(value,
                                            ast.Constant) and isinstance(
                                    value.value, (int, float)):
                                decorator_args["sub_weight"] = value.value

                # Extract values with fallbacks
                name = decorator_args.get("name", item.name)
                weight = decorator_args.get("sub_weight", 1.0)

                if name:
                    weights[name] = weight

    return weights


def serialize_for_output(data: Any) -> Any:
    """
    Safely serialize various data types for output formatting.

    This function recursively processes data to ensure it can be serialized to formats like JSON.
    It handles:
    - Pydantic V2 models using model_dump()
    - Pydantic V1 models using dict()
    - Regular objects via their __dict__ attribute
    - Lists, tuples, and dictionaries recursively
    - Other basic types as-is

    Args:
        data: Input data to serialize (any type)

    Returns:
        Serialized data in a format suitable for output (dict, list, or primitive)
    """
    # Handle Pydantic models (version detection)
    if hasattr(data, "model_dump"):  # Pydantic V2
        return data.model_dump()
    elif hasattr(data, "dict"):  # Pydantic V1
        return data.dict()

    # Handle regular objects via their attribute dictionary
    if hasattr(data, "__dict__"):
        data = data.__dict__

    # Recursively process container types
    if isinstance(data, dict):
        return {k: serialize_for_output(v) for k, v in data.items()}
    elif isinstance(data, (list, tuple, set)):
        return [serialize_for_output(item) for item in data]

    # Return basic types directly
    return data
