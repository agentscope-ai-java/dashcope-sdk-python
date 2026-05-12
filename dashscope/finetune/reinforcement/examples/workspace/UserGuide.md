# Agentic Reinforcement Learning: User Guide [[中文]](./UserGuide-zh.md)

---

## 1. Introduction

The **Agentic RL SDK/CLI** provides a complete toolchain for building, training, and managing reinforcement learning (RL) models for large language models (LLMs). It simplifies the complex workflows of defining agent behavior, collecting trajectories, and optimizing policies.

The SDK consists of two core modules:
1.  **Functions Module**: Manages custom Python code for **Rollout** (trajectory generation), **Reward** (scoring), and **Group Reward** (batch scoring). Supports automatic registration, testing, and built-in **Observability (Tracing)**.
2.  **Tuning Module**: Handles dataset management, hyperparameter configuration, job submission, and lifecycle management (status, logs, cancellation).

**Workflow**:
1.  First, register functions (Rollout/Reward/Group Reward) in the Functions module. These functions can be tested locally or remotely.
2.  Then, use the Tuning module to upload datasets, configure jobs, and submit training.

---

## 2. Installation and Setup

### 2.1 Install via PyPI
```bash
pip install dashscope>=1.25.18 # If the dashscope version is not released, you can install via a local whl package
```

### 2.2 Install from Source (Development Environment)
```bash
git clone https://github.com/dashscope/dashscope-sdk-python.git
cd dashscope-sdk-python
pip install -e .  # Install in editable mode for development
```

### 2.3 Authentication
1.  Obtain your **DashScope API Key**.
2.  Set the environment variable:
    ```bash
    export DASHSCOPE_API_KEY='your-api-key-here'
    ```

### 2.4 Project Structure
A recommended workspace structure to ensure smooth deployment and local testing:

```text
workspace/
├── data/                   # Datasets
│   ├── calc_train_min.jsonl
│   └── calc_validation_min.jsonl
├── functions/              # Custom logic
│   ├── reward/
│   │   ├── group_reward_.py
│   │   ├── reward.py
│   │   └── reward_decorator.py
│   └── rollout/
│       ├── rollout_only.py
│       └── rollout.py
├── requirements.txt        # Function component dependencies
└── config.yaml             # Optional: job configuration
```

### 2.5 Dependencies (requirements.txt Guide)
This file is **required** for deploying function components to the cloud and must be placed in the workspace root.

**requirements.txt:**
```txt
fastapi==0.136.0
uvicorn==0.45.0
typer==0.24.1
rich==15.0.0
pyyaml==6.0.3
protobuf>=4.25.8,<7.0 #6.33.6
fsspec==2026.3.0
httpx==0.28.1
tenacity==9.1.4
...
```

**Key Notes:**
*   **Default Package**: `dashscope` is pre-installed in the runtime environment; **do not** include it in your `requirements.txt`.
*   **Protobuf**: Must be within the specified version range to avoid compatibility issues.

#### Observability (Tracing) Dependencies
To use **Tracing** capabilities (processor/LLM/tool call traces), add the following dependencies to your `requirements.txt` (pinning versions is recommended for reproducible deployments):

```txt
opentelemetry-api==1.41.1
opentelemetry-sdk==1.41.1
opentelemetry-exporter-otlp-proto-http==1.41.1
opentelemetry-processor-baggage==0.62b1
loongsuite-util-genai==0.4.0
```

#### Tracing Toggle (`ENABLE_TRAJECTORY`)

The SDK uses the environment variable `ENABLE_TRAJECTORY` to control whether OpenTelemetry **Tracing** is enabled; tracing data is generated only when enabled.

- **Enabled by default**: If the variable is not set (or set to `true`), tracing is enabled.
- **Disable explicitly**: Set to `false` to disable.

### 2.6 Logging Configuration
Configure the logging verbosity via the `LOG_LEVEL` environment variable:

```bash
export LOG_LEVEL="DEBUG"   # Most verbose (sensitive information like API keys will be masked)
export LOG_LEVEL="INFO"    # Default
export LOG_LEVEL="WARNING"
export LOG_LEVEL="ERROR"
export LOG_LEVEL="CRITICAL"
```

---

## 3. Writing Functions
Reference: workspace/functions directory, output files like rollout.py, reward.py, etc.

### 3.1 Implementing Functions

Functions must inherit the abstract base classes provided by the SDK.

#### Rollout Processor
Generates agent trajectories (interactions with environment/LLM).

```python
from dashscope.finetune.reinforcement import AbstractRolloutProcessor, RolloutInput, RolloutOutput

class DemoRolloutProcessor(AbstractRolloutProcessor):
    async def process(self, input: RolloutInput) -> RolloutOutput:
        # Generate trajectories (supports async/def)
        pass
```

#### Reward Processor
Scores individual steps or final outputs.

```python
from dashscope.finetune.reinforcement import AbstractRewardProcessor, RewardInput, RewardOutput

class DemoRewardProcessor(AbstractRewardProcessor):
    def process(self, input: RewardInput) -> RewardOutput:
        # Compute reward score
        pass
```

#### Advanced Reward Processor with Decorators
```python
from dashscope.finetune.reinforcement import reward_func, sub_reward_func, aggregate_func

@reward_func("SafetyProcessor")
class SafetyProcessor(AbstractRewardProcessor):
    @sub_reward_func("toxicity", sub_weight=0.7)
    def toxicity(self, input: RewardInput) -> RewardOutput: ...
    
    @sub_reward_func("refusal", sub_weight=0.3)
    async def refusal(self, input: RewardInput) -> RewardOutput: ...

    @aggregate_func
    async def aggregate(self, sub_rewards: dict[str, RewardOutput]) -> RewardOutput: # Custom aggregation logic
        weights = self.get_weights()
        scores = self.get_scores(sub_rewards)
        reward_metrics = self.get_reward_metrics(sub_rewards)
        
        total = ...  # Compute total reward
        return RewardOutput(...)
```

#### Group Reward Processor
Scores trajectories in batches (e.g., for ranking).

```python
from dashscope.finetune.reinforcement import AbstractGroupRewardProcessor, GroupRewardInput, GroupRewardOutput

class DemoGroupRewardProcessor(AbstractGroupRewardProcessor):
    def setup(self) -> None:
        pass

    async def process(self, input: GroupRewardInput) -> GroupRewardOutput:
        # Compute group reward
        pass
```

### 3.2 Observability (Tracing)

Use OpenTelemetry to gain deep visibility into agent execution. After authorizing ARMS in the console, tracing data is automatically exported to **ARMS** (Alibaba Cloud Real-time Monitoring Service); you can view nodes such as LLM and tool calls within a single Rollout in the traces. See [ARMS Documentation](https://help.aliyun.com/zh/arms/?spm=5176.30275541.J_ZGek9Blx07Hclc3Ddt9dg.3.3ce02f3dmKOpPK&scm=20140722.S_card@@%E4%BA%A7%E5%93%81@@596792.S_new~UND~card.ID_card@@%E4%BA%A7%E5%93%81@@596792-RL_arms-LOC_2024SPSearchCard-OR_ser-PAR1_0bc1409817757870159831522e3953-V_4-RE_new5-P0_0-P1_0).

#### Prerequisites
1.  Add observability dependencies to `requirements.txt` (see Section 2.5 "Observability (Tracing) Dependencies").
2.  Ensure tracing is not explicitly disabled (`ENABLE_TRAJECTORY=false` would disable it).

#### Instrumentation Decorators
Import from `dashscope.finetune.reinforcement.component.observability`.

| Decorator | Usage | Description |
| :--- | :--- | :--- |
| `@observe_processor` | On `process()` method | Automatically traces input/output, latency, and status. Automatically determines span type (ROLLOUT/REWARD). |
| `trace_client()` | In `setup()` or before the first LLM call | Wraps the LLM client (OpenAI, DashScope, LangChain classes). Automatically traces all downstream calls. **Recommended**. |
| `@observe_llm` | On a custom LLM function | Use if `trace_client` does not support your wrapper. Requires `model` and `messages` as keyword arguments. |
| `trace_tool()` | In `setup()` (after tool creation) | Wraps tools (LangChain/MCP/LangGraph classes). Automatically traces tool calls. |
| `@observe_tool` | On plain functions | For simple Python functions not wrapped as BaseTools. |

> **Setup:** Called once when the server starts; supports both synchronous and asynchronous. Synchronous setup is offloaded to avoid blocking the event loop.

> **Quick Tip:** `@observe_llm` is suitable for custom functions: `@observe_llm async def call_llm(*, model, messages, **kwargs): ...`; `@observe_tool` is suitable for plain function tools: `@observe_tool def my_tool(x: str) -> str: ...`.

#### What `trace_client()` Supports (Duck Typing)
`trace_client(client)` works via structural detection (not class name). It supports:

- **Full OpenAI clients** that expose `.chat.completions.create`
- **Completions resources** that expose `.create` but **without** `.chat` (e.g., `ChatOpenAI.client`)
- **LangChain class wrappers** that expose `.client` and/or `.async_client`
- **DashScope Generation** class (pass the class itself, which has a `call` classmethod)

> **Note:** If no tracing data is generated, the client type might not be in the supported set; tracing is skipped without affecting business execution.
> **DashScope Minimal Usage:** Call `trace_client(Generation)` on the `Generation` class (pass the class, not an instance).

#### What `trace_tool()` Supports
`trace_tool(tools)` accepts the following forms:

- A single tool object (e.g., LangChain `BaseTool`)
- A list/tuple of tools
- A dictionary mapping names to tools
- A LangGraph `ToolNode` (tools are expanded internally)
- MCP tools returned by `langchain-mcp-adapters` (provider set to `"mcp"` automatically)

> **MCP Note:** MCP servers and clients run in separate processes. Using `@observe_tool` on server-side functions has no effect on the client. Always call `trace_tool(tools)` after calling `get_tools()` on the client.

#### Example: Instrumented Rollout Processor

> The following example primarily demonstrates how to integrate Tracing, not a complete dialog state machine or business logic example.

```python
import openai
from dashscope.finetune.reinforcement import AbstractRolloutProcessor, RolloutInput, RolloutOutput
from dashscope.finetune.reinforcement.component.data.base_data_model import AgentOutput, TaskStatus
from dashscope.finetune.reinforcement.component.observability import (
    observe_processor,
    trace_client,
    trace_tool,
)

class MyRolloutProcessor(AbstractRolloutProcessor):

    async def setup(self) -> None:
        # 1. Trace the LLM client
        self._client = openai.AsyncOpenAI(base_url="...", api_key="...")
        trace_client(self._client)

        # 2. Trace tools (e.g., MCP)
        from langchain_mcp_adapters.client import MultiServerMCPClient

        client = MultiServerMCPClient({...})
        self._tools = await client.get_tools()
        trace_tool(self._tools)

    @observe_processor
    async def process(self, input: RolloutInput) -> RolloutOutput:
        messages = input.messages or []
        model = input.model_resource.model_name

        # Due to trace_client(self._client), this call is automatically traced
        response = await self._client.chat.completions.create(
            model=model,
            messages=messages,
        )
        
        content = response.choices[0].message.content if response.choices else ""

        return RolloutOutput(
            agent_output=AgentOutput(messages=messages, reward_score=0.0),
            status=TaskStatus.SUCCESS,
        )
```

> **Tip:** Some streaming (`stream`) scenarios with DashScope may not generate tracing data; for troubleshooting, first switch to non-streaming to verify.

---

## 4. SDK & CLI Reference
* [SDK] Interface class: `dashscope.finetune.agentic_rl.AgenticRL`
* [CLI] Entry point: `dashscope rl`

### 4.1 Job Configuration
Use YAML or code to initialize the client. Code parameters override YAML configuration.

**[SDK] \_\_init\_\_**
```python
def __init__(self, api_key: str = None): ...
```
Initialize an AgenticRL instance.

**Parameters**:
- `api_key`: API key for authentication (uses environment variable if not provided)

**Example**:
```python
from dashscope.finetune.agentic_rl import AgenticRL
rl = AgenticRL(api_key="your_api_key")
```

**[SDK] [init](examples/workspace/demo_sdk_agentic_rl_workflows.py)**
```python
def init(self, config_path: Optional[str] = None, **kwargs) -> Self: ...
```
Initialize instance from a YAML configuration file.

**Parameters**:
- `config_path`: Path to the YAML configuration file
- `**kwargs`: Configuration overrides

**Returns**: Self instance

**Example**:
```python
from dashscope.finetune.agentic_rl import AgenticRL
rl = AgenticRL().init("config.yaml", job_name="custom_job")
```

### 4.2 Register Functions

Upload code and register function components (FCs).

**[SDK] [register_functions](examples/workspace/demo_sdk_agentic_rl_workflows.py)**
```python
def register_functions(self, functions: Optional[Union[List[Union[RolloutFunctionComponent, RewardFunctionComponent]], RolloutFunctionComponent, RewardFunctionComponent]] = None, lazy_load: Optional[bool] = True) -> tuple: ...
```
Register function components.

**Parameters**:
- `functions`: Function components to register
- `lazy_load`: Lazy load until execution

**Returns**: Tuple of entity/instance IDs

**Example**:
```python
from dashscope.finetune.agentic_rl import AgenticRL, AgenticRLFunctionComponent, FunctionType, FunctionComponentModel

rl = AgenticRL()
rollout_eids, reward_eids, group_eids, \
rollout_iids, reward_iids, group_iids = await rl.register_functions(
    functions=[
        AgenticRLFunctionComponent(
            type=FunctionType.ROLLOUT,
            fcmodel=FunctionComponentModel(
                zipdir='./',
                classpath="functions.rollout.demo_rollout2.DemoRolloutProcessor"),
        ),

        AgenticRLFunctionComponent(
            type=FunctionType.REWARD,
            fcmodel=FunctionComponentModel(
                classpath="functions/reward/demo_reward.py:DemoRewardProcessor"),
        ),

        AgenticRLFunctionComponent(
            type=FunctionType.GROUP_REWARD,
            fcmodel=FunctionComponentModel(
                classpath="functions.reward.demo_group_reward.DemoGroupRewardProcessor"),
        ),
    ],
    lazy_load=False  # Set to False to get instance IDs immediately for testing
)
```

**[CLI] [register_functions](examples/workspace/demo_cli_agentic_rl_functions_and_tuning.sh)**

**Usage: dashscope register_functions [OPTIONS]**
```bash                                                                                                                                                                                                                       
 🧩 Register Rollout/Reward function components, returns entity_id & instance_id                                                                                                                                        
                                                                                                                                                                                                                        
 At least one of the following is required:                                                                                                                                                                                              
 - rollout_classpath                                                                                                                                                                                                    
 - reward_classpaths                                                                                                                                                                                                    
                                                                                                                                                                                                                        
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --rollout-classpaths                             TEXT  List of Rollout class paths (file.py:ClassName)                                                                                                               │
│ --reward-classpaths                              TEXT  List of Reward class paths (file.py:ClassName)                                                                                                                │
│ --group-reward-classpaths                        TEXT  List of Group-reward class paths (file.py:ClassName)                                                                                                          │
│ --workspace-dir                                  TEXT  Local workspace directory [default: ./]                                                                                                                       │
│ --lazy-load                    --no-lazy-load          Lazy instance loading (set to False for debugging) [default: lazy-load]                                                                                         │
│ --api-key                                        TEXT  DashScope API Key (uses DASHSCOPE_API_KEY env var if omitted) [env var: DASHSCOPE_API_KEY]                                                                    │
│ --output-format            -o                    TEXT  Output format: table|json|yaml [default: json]                                                                                                                │
│ --help                                                  Show this message and exit                                                                                                                                   │
╰───────────────────────────────────────────────────────────────────────────────────────────���──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```
**Example**:
```bash
dashscope rl register_functions \
  --rollout-classpath "functions.rollout.rollout_only.DemoRolloutProcessor" \
  --group-reward-classpaths "functions.reward.group_reward.DemoGroupRewardProcessor" \
  --workspace-dir "./" \
  --output-format json
```

### 4.3 Test Functions

#### 4.3.1 Remote Testing
**[SDK] [test_functions](examples/workspace/demo_sdk_agentic_rl_functions_and_tuning.py)**

Test a registered instance with sample data.

```python
def test_functions(cls, instance_id: str, type: FunctionType, input_data: Dict[str, Any], api_key: str = None): ...
```

**Parameters**:
- `instance_id`: Function instance ID
- `type`: Function type (ROLLOUT/REWARD/GROUP_REWARD)
- `input_data`: Test input data
- `api_key`: API key for authentication

**Example**:
```python
from dashscope.finetune.agentic_rl import AgenticRL, FunctionType

# Test Rollout
result = await AgenticRL.test_functions(
    instance_id=rollout_iids[0],
    type=FunctionType.ROLLOUT,
    input_data="resouces/rollout_input.json" # JSON file path
)

# Test Reward
reward_input = {
    "func_type": "reward",
    "agent_output": {
        "messages": [{"role": "user", "content": "Test"}],
        "reward_score": null
    }
}
result = await AgenticRL.test_functions(
    instance_id=reward_iids[0],
    type=FunctionType.REWARD,
    input_data=reward_input
)
```

**[CLI] [test_functions](examples/workspace/demo_cli_agentic_rl_functions_and_tuning.sh)**

**Usage: dashscope test_functions [OPTIONS] INSTANCE_ID**
```bash   
 🧪 Test a registered Rollout/Reward function instance with custom input data                                                                                                                                          
                                                                                                                                                                                                                        
╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    instance_id      TEXT  Target function instance ID (e.g., ro-ins-xxx or rw-ins-xxx) [required]                                                                                                                  │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *  --type           -t      TEXT  Function type: ROLLOUT or REWARD [required]                                                                                                                                        │
│ *  --input          -i      TEXT  JSON string or file path containing the test payload [required]                                                                                                                        │
│    --api-key                TEXT  DashScope API Key (uses DASHSCOPE_API_KEY env var if omitted) [env var: DASHSCOPE_API_KEY]                                                                                         │
│    --output-format  -o      TEXT  Output format: table|json|yaml [default: json]                                                                                                                                     │
│    --help                          Show this message and exit                                                                                                                                                        │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

**Example**:
```bash
dashscope rl test_functions "ro-ins--xxx" \
  --type rollout \
  --input "resources/rollout_input.json"
```

### 4.4 One-Click Workflow
Automatically registers functions, uploads data, and submits a job.

**[SDK] [run](examples/workspace/demo_sdk_agentic_rl_workflows.py)**
```python
def run(self, model: Optional[str] = None, training_files: Optional[Union[List[str], str]] = None, validation_files: Optional[Union[List[str], str]] = None, functions: Optional[Union[List[Union[RolloutFunctionComponent, RewardFunctionComponent, AgenticRLFunctionComponent]], RolloutFunctionComponent, RewardFunctionComponent, AgenticRLFunctionComponent]] = None, hyper_parameters: Optional[Dict[str, str]] = None, job_name: Optional[str] = None, workspace_dir: str = "./", **kwargs) -> FineTune: ...
```
Full workflow execution (register + upload + submit).

**Parameters**:
- `model`: Base model name
- `training_files`: Training dataset files
- `validation_files`: Validation dataset files
- `functions`: Function components
- `hyper_parameters`: Training hyperparameters
- `job_name`: Custom job name
- `workspace_dir`: Working directory

**Returns**: `FineTune` job object

**Example**:
```python
from dashscope.finetune.agentic_rl import AgenticRL, AgenticRLFunctionComponent, FunctionType, FunctionComponentModel

rl = AgenticRL()
rollout_runtime = {"cpu": 2, "memory_size": 4, "disk_size": 20960, "concurrency": 2,
                    "env": {}, "capacity": 5}
reward_runtimes = [
    {"cpu": 2, "memory_size": 4, "disk_size": 20960, "concurrency": 10, "env": {},
     "capacity": 8},
    {"cpu": 2, "memory_size": 4, "disk_size": 20960, "concurrency": 5, "env": {},
     "capacity": 6}
]
functions=[
    AgenticRLFunctionComponent(
        type=FunctionType.ROLLOUT,
        name="rollout-1",
        fcmodel=FunctionComponentModel(
            classpath="functions.rollout.rollout_only.DemoRolloutProcessor"),
        runtime=FunctionComponentRuntime(**rollout_runtime)),
    AgenticRLFunctionComponent(
        type=FunctionType.REWARD,
        name="reward-1",
        weight=1.0,
        fcmodel=FunctionComponentModel(
            classpath="functions.reward.reward.DemoRewardProcessor"),
        runtime=FunctionComponentRuntime(**reward_runtimes[0])),
]
job = await rl.run(
    model="qwen3.5-9b",
    training_files=["./data/calc_train_min.jsonl"],
    validation_files=["./data/calc_validation_min.jsonl"],
    functions=functions,
    hyper_parameters={'batch_size': '128'}
)
```

**[CLI] [run](examples/workspace/demo_cli_agentic_rl_workflows.sh)**

**Usage: dashscope run [OPTIONS]**                                                                                                                                                                                   
```bash                                                                                                                                                                                                                   
 🚀 Start a complete RL tuning workflow (function registration → dataset upload → job submission)                                                                                                                    
                                                                                                                                                                                                                        
 Execution modes:                                                                                                                                                                                                       
 1. Configuration-driven: Use -c/--config to specify a YAML file                                                                                                                                                        
 2. Direct parameters: Provide all required parameters via CLI options                                                                                                                                                    
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --config                   -c      PATH   YAML configuration file path                                                                                                                                               │
│ --job-name                         TEXT   Custom name for the tuning job                                                                                                                                             │
│ --api-key                          TEXT   DashScope API Key (uses DASHSCOPE_API_KEY env var if omitted) [env var: DASHSCOPE_API_KEY]                                                                                 │
│ --output-format            -o      TEXT   Output format: table|json|yaml [default: table]                                                                                                                            │
│ --verbose                  -v             Enable detailed error traces                                                                                                                                               │
│ --help                                    Show this message and exit                                                                                                                                                 │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

**Example**: Run full workflow (automatic)
```bash
dashscope rl run \
  --config "config.yaml" \
  --verbose
```

### 4.7 Job Management

**[SDK] get**
```python
def get(cls, job_id: str, api_key: str = None, workspace: str = None, **kwargs) -> FineTune: ...
```
Get job information.

**Parameters**:
- `job_id`: Job ID to retrieve
- `api_key`: API key for authentication
- `workspace`: Workspace identifier

**Example**:
```python
from dashscope.finetune.agentic_rl import AgenticRL
job = AgenticRL.get("ft-12345")
```

**[CLI] get**

**Usage: dashscope get [OPTIONS] JOB_ID**
```bash 
 📊 Query the current status and metadata of a specific job                                                                                                                                                             
                                                                                                                                                                                                                        
╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    job_id      TEXT  Target job ID [required]                                                                                                                                                                      │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --api-key                TEXT  DashScope API Key (uses DASHSCOPE_API_KEY env var if omitted) [env var: DASHSCOPE_API_KEY]                                                                                            │
│ --output-format  -o      TEXT  [default: table]                                                                                                                                                                      │
│ --help                          Show this message and exit                                                                                                                                                           │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

**Example**:
```bash
dashscope rl get "$JOB_ID" -o json
```

**[SDK] cancel**
```python
def cancel(cls, job_id: str, api_key: str = None, workspace: str = None, **kwargs) -> FineTuneCancel: ...
```
Cancel a running job.

**Parameters**:
- `job_id`: Job ID to cancel
- `api_key`: API key for authentication
- `workspace`: Workspace identifier

**Example**:
```python
from dashscope.finetune.agentic_rl import AgenticRL
AgenticRL.cancel("ft-12345")
```

**[CLI] cancel**

**Usage: dashscope cancel [OPTIONS] JOB_ID**                                                                                                                                                                     
```bash                                                                                                                                                                                                                    
 🛑 Cancel a running job                                                                                                                                                                                                
                                                                                                                                                                                                                        
╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    job_id      TEXT  Target job ID [required]                                                                                                                                                                      │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --api-key        TEXT  DashScope API Key (uses DASHSCOPE_API_KEY env var if omitted) [env var: DASHSCOPE_API_KEY]                                                                                                    │
│ --help                  Show this message and exit                                                                                                                                                                   │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

**Example**:
```bash
dashscope rl cancel "$JOB_ID"
```

---

## 6. CLI Reference

The CLI mirrors the SDK functionality. Use `dashscope rl --help` for details.

### Usage: dashscope [OPTIONS] COMMAND [ARGS]...  
```bash
                                                                                                                                                                                                                                                                                                                                                                             
 🚀 Agentic RL Fine-Tuning CLI        
                                                                                                                                                                                                                                                                                                                                                                                           
╭─ Options ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit                                                                                                                                                                     │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ register_functions  🧩 Register Rollout/Reward function components, returns entity_id & instance_id                                                                                                             │
│ test_functions      🧪 Test a registered Rollout/Reward function instance with custom input data                                                                                                               │
│ upload_data         📦 Upload training/validation datasets to the platform, returns file ID                                                                                                                    │                                                                                                               │
│ run                 🚀 Start a complete RL tuning workflow (function registration → dataset upload → job submission)                                                                                         │
│ status              📊 Query the current status and metadata of a specific job                                                                                                                                  │
│ list                📋 List historical fine-tuning jobs with pagination                                                                                                                                         │
│ cancel              🛑 Cancel a running job                                                                                                                                     │
│ delete              🗑️ Delete job records (release metadata)                                                                                                                                                  │
│ logs                📜 Get job execution logs (supports pagination)                                                                                                                                           │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

---

## 7. Common Issues and Troubleshooting

**Q: Function registration fails**
*   **Check**: Is the class path correct (`module.path:ClassName`)?
*   **Check**: Does a `requirements.txt` exist in the workspace root?
*   **Check**: Are all dependencies listed in `requirements.txt`?

**Q: Job submission fails**
*   **Check**: Are the entity IDs and file IDs valid?
*   **Check**: Is the base model available in your region?
*   **Check**: Does the length of the `reward_runtimes` list match the length of the `reward_ids` list?

**Q: How to optimize performance?**
*   Use `async def process` for I/O-intensive tasks.
*   Increase `concurrency` in the runtime configuration if CPU/memory allows.
*   Control the volume of observable payloads (avoid excessive input/output capture) to reduce overhead.

**Q: Where can I view tracing data?**
*   After authorizing ARMS in the Bailian console, tracing data is exported to **ARMS**. Ensure that the observability dependencies are included in `requirements.txt` and that observability interfaces (such as `observe_processor`, `trace_client`, `trace_tool`, etc.) are used.
*   **Still no data?**: Confirm that `ENABLE_TRAJECTORY` is not set to `false` (this value disables tracing).
