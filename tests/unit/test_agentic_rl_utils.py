import pytest
import os
from pydantic import BaseModel, SecretStr
from unittest.mock import patch

from dashscope.finetune.reinforcement import InputError, ConfigurationError
from dashscope.finetune.reinforcement import FunctionType
from dashscope.finetune.reinforcement.common.utils import generate_agentic_script, create_deployment_files, \
    get_filepath_classname, deep_mask, set_api_key


class SampleModel(BaseModel):
    api_key: str
    normal_field: str
    nested: dict


@pytest.fixture(autouse=True)
def clean_env():
    """Clean DASHSCOPE_API_KEY environment variable before and after each test."""
    original_key = os.environ.get("DASHSCOPE_API_KEY")
    if "DASHSCOPE_API_KEY" in os.environ:
        del os.environ["DASHSCOPE_API_KEY"]
    yield
    if original_key:
        os.environ["DASHSCOPE_API_KEY"] = original_key


class TestAgenticRLUtils:
    def test_generate_agentic_script(self):
        """Test generating a deployment script with all required components."""
        script = generate_agentic_script(
            fc_pypi_lib="dashscope",
            fc_pypi_repo="https://pypi.org/simple",
            requirements_path="requirements.txt",
            func_type="rollout",
            classpath="module.path.Processor"
        )

        # Validate core configuration
        assert "SERVICE_TYPE=\"rollout\"" in script
        assert "PROCESSOR_CLASS=\"module.path.Processor\"" in script
        assert "SDK_PACKAGE=\"dashscope\"" in script
        assert "REQUIREMENTS_FILE=\"requirements.txt\"" in script

        # Validate key functional blocks
        assert "set -euo pipefail" in script  # Error handling
        assert "install_with_retry" in script  # Retry logic
        assert "python3 -m pip install" in script  # Dependency installation
        assert "python3 -m \"${SERVER_CLASSPATH}\"" in script  # Service startup

    def test_generate_script_with_empty_requirements(self):
        """Test generating a script without a requirements.txt file."""
        script = generate_agentic_script(
            fc_pypi_lib="dashscope",
            fc_pypi_repo="https://pypi.org/simple",
            requirements_path="",
            func_type="reward",
            classpath="rewards.scoring.RewardCalculator"
        )

        # Validate conditional logic for missing requirements
        assert "if [ -f \"${REQUIREMENTS_FILE}\" ]; then" in script
        assert "for pkg in \"${local_packages[@]}\"; do" in script
        assert "local_packages=($SDK_PACKAGE)" in script

    def test_special_characters_in_classpath(self):
        """Test handling of special characters in classpath."""
        script = generate_agentic_script(
            fc_pypi_lib="dashscope",
            fc_pypi_repo="https://pypi.org/simple",
            requirements_path="reqs.txt",
            func_type="group_reward",
            classpath="special.module:Class$With@Chars"
        )

        assert "PROCESSOR_CLASS=\"special.module:Class$With@Chars\"" in script

    def test_create_deployment_files(self, tmp_path):
        """Test creating deployment files with requirements."""
        # Create test environment
        test_dir = tmp_path / "test_project"
        test_dir.mkdir()

        # Create test files
        (test_dir / "processor.py").write_text("class DemoProcessor: pass")
        (test_dir / "requirements.txt").write_text("dashscope==1.0")

        # Execute function
        create_deployment_files(
            type=FunctionType.ROLLOUT,
            zipdir=str(test_dir),
            filepath="processor.py",
            classname="DemoProcessor",
            requirements_path="requirements.txt"
        )

        # Validate generated file
        assert os.path.exists("start.sh")

        # Validate script content
        with open("start.sh", "r") as f:
            content = f.read()
            assert "PROCESSOR_CLASS=\"processor.DemoProcessor\"" in content
            assert "REQUIREMENTS_FILE=\"requirements.txt\"" in content

    def test_create_files_without_requirements(self, tmp_path):
        """Test creating deployment files without requirements."""
        test_dir = tmp_path / "test_project"
        test_dir.mkdir()
        (test_dir / "module").mkdir()
        (test_dir / "module" / "processor.py").write_text("class MyProcessor: pass")

        create_deployment_files(
            type=FunctionType.REWARD,
            zipdir=str(test_dir),
            filepath="module/processor.py",
            classname="MyProcessor",
            requirements_path=""
        )

        # Validate generated file
        assert os.path.exists("start.sh")

        # Validate script content
        with open("start.sh", "r") as f:
            content = f.read()
            assert "PROCESSOR_CLASS=\"module.processor.MyProcessor\"" in content
            assert "local_packages=($SDK_PACKAGE)" in content

    def test_invalid_file_path(self, tmp_path):
        """Test handling of invalid file paths."""
        test_dir = tmp_path / "test_project"
        test_dir.mkdir()

        with pytest.raises(Exception):
            create_deployment_files(
                type=FunctionType.GROUP_REWARD,
                zipdir=str(test_dir),
                filepath="missing.py",
                classname="MissingProcessor"
            )

    def test_get_filepath_classname_colon_format(self):
        """Test colon-separated format parsing."""
        filepath, classname = get_filepath_classname("path/to/file.py:ClassName")
        assert filepath == "path/to/file.py"
        assert classname == "ClassName"

    def test_get_filepath_classname_dot_format(self):
        """Test dot-separated format parsing."""
        filepath, classname = get_filepath_classname("module.submodule.ClassName")
        assert filepath == "module/submodule.py"
        assert classname == "ClassName"

    def test_get_filepath_classname_mixed_format(self):
        """Test mixed format parsing."""
        filepath, classname = get_filepath_classname("path.with.dots/file.py:Class.Name")
        assert filepath == "path.with.dots/file.py"
        assert classname == "Class.Name"

    def test_invalid_formats(self):
        """Test handling of invalid input formats."""
        with pytest.raises(InputError):
            get_filepath_classname("singleword")

        with pytest.raises(InputError):
            get_filepath_classname("path:without:class")

        with pytest.raises(InputError):
            get_filepath_classname("file.py:")  # Missing class name

    def test_deep_mask_dict(self):
        """Test masking sensitive fields in dictionaries."""
        data = {
            "api_key": "secret_value",
            "normal_field": "visible",
            "nested": {
                "password": "123456",
                "info": "public"
            }
        }

        masked = deep_mask(data)
        assert isinstance(masked["api_key"], SecretStr)
        assert masked["normal_field"] == "visible"
        assert isinstance(masked["nested"]["password"], SecretStr)
        assert masked["nested"]["info"] == "public"

    def test_deep_mask_pydantic_model(self):
        """Test masking sensitive fields in Pydantic models."""
        model = SampleModel(
            api_key="model_secret",
            normal_field="model_data",
            nested={"token": "model_token", "data": "model_info"}
        )

        masked = deep_mask(model)

        # Validate sensitive fields are masked
        assert isinstance(masked['api_key'], SecretStr)
        assert masked['normal_field'] == "model_data"
        assert isinstance(masked['nested']["token"], SecretStr) == False
        assert masked['nested']["data"] == "model_info"

    def test_deep_mask_complex_structure(self):
        """Test masking in complex nested structures."""
        data = [
            {"key": "value1", "password": "s1"},
            {"key": "value2", "api_token": "s2"},
            (
                {"key": "value3", "trigger_token": "s3"},
                {"key": "value4", "instance_token": "s4"}
            )
        ]

        masked = deep_mask(data)
        assert isinstance(masked[0]["password"], SecretStr)
        assert isinstance(masked[1]["api_token"], SecretStr)
        assert isinstance(masked[2][0]["trigger_token"], SecretStr)
        assert isinstance(masked[2][1]["instance_token"], SecretStr)

    def test_set_api_key_with_argument(self):
        """Test setting API key via function argument."""
        with patch("os.environ", {}):
            set_api_key("test_key_123")
            assert os.environ["DASHSCOPE_API_KEY"] == "test_key_123"

    def test_set_api_key_with_env_var(self):
        """Test using existing environment variable."""
        with patch("os.environ", {"DASHSCOPE_API_KEY": "env_key_456"}):
            set_api_key(None)
            assert os.environ["DASHSCOPE_API_KEY"] == "env_key_456"

    def test_set_api_key_missing(self):
        """Test handling of missing API key."""
        with patch("os.environ", {}):
            with pytest.raises(ConfigurationError):
                set_api_key(None)
