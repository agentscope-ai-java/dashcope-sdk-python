# Agentic Reinforcement Learning: User Guide [[中文]](./UserGuide-chn.md)

---

## 1. Introduction

The **Agentic RL SDK/CLI** provides a comprehensive toolchain for building, training, and managing Reinforcement Learning (RL) models for Large Language Models (LLMs). It simplifies the complex workflow of defining agent behaviors, collecting trajectories, and optimizing policies.

The SDK consists of two core modules:
1.  **Functions Module**: Manages custom Python code for **Rollout** (trajectory generation), **Reward** (scoring), and **Group Reward** (batch scoring). It supports automatic registration, testing, and built-in **Observability (Tracing)**.
2.  **Tuning Module**: Handles dataset management, hyperparameter configuration, job submission, and lifecycle management (status, logs, cancellation).

### Module Interaction Diagram
```
+--------------------+       +------------------+
|  Functions Module  |       |  Tuning Module   |
|  - Rollout         | ----> |  - Dataset Mgmt  |
|  - Reward          |       |  - Job Config    |
|  - Group Reward    |       |  - Job Mgmt      |
+--------------------+       +------------------+
```
**Workflow**:
1. First, register functions (Rollout/Reward/Group Reward) in the Functions Module. These can be tested locally or remotely.
2. Then, use the Tuning Module to upload datasets, configure the job, and submit it for training.

---

## 2. Installation & Setup

### 2.1 Install via PyPI
```bash
pip install dashscope
```

### 2.2 Install from Source (For Development)
```bash
git clone https://github.com/dashscope/dashscope-sdk-python.git
cd dashscope-sdk-python
pip install -e .  # Install in editable mode for development
```

### 2.3 Authorization
1.  Obtain your **DashScope API Key**.
2.  Set the environment variable:
    ```bash
    export DASHSCOPE_API_KEY='your-api-key-here'
    ```

### 2.4 Project Structure
A recommended workspace structure ensures smooth deployment and local testing:

```text
workspace/
├── data/                   # Datasets
│   ├── training.jsonl
│   └── validation.jsonl
├── functions/              # Custom Logic
│   ├── reward/
│   │   ├── group_reward.py
│   │   └── reward.py
│   └── rollout/
│       └── rollout.py
├── requirements.txt        # Dependencies for Function Components
└── config.yaml             # Optional: Job configuration
```

### 2.5 Dependency Packages (requirements.txt Guidelines)
This file is **mandatory** for deploying Function Components to the cloud. It must reside in the workspace root.

**requirements.txt:**
```txt
fastapi
uvicorn
rich>=15.0.0
pyyaml>=6.0
protobuf>=4.25.8,<7.0
fsspec
httpx
tenacity
...
```

**Key Notes:**
*   **Default Packages**: `dashscope` are pre-installed in the runtime environment. Do NOT include them in your `requirements.txt`.
*   **Protobuf**: Must be within the specified range to avoid compatibility issues.

#### Dependencies for Observability (Tracing)
To use observability spans (processor / LLM / tool), add the following dependencies to your `requirements.txt` (recommended pinned versions for reproducible deployments):

```txt
opentelemetry-api==1.41.0
opentelemetry-sdk==1.41.0
opentelemetry-exporter-otlp-proto-http==1.41.0
opentelemetry-processor-baggage==0.62b0
loongsuite-util-genai==0.4.0
```

### 2.6 Logging Configuration
Configure logging verbosity via the `LOG_LEVEL` environment variable:

```bash
export LOG_LEVEL="DEBUG"   # Most verbose (masks sensitive info like API keys)
export LOG_LEVEL="INFO"    # Default
export LOG_LEVEL="WARNING"
export LOG_LEVEL="ERROR"
export LOG_LEVEL="CRITICAL"
```

---

## 3. Writing Functions
Reference: workspace/functions directory, output rollout.py, reward.py, etc.

### 3.1 Implementing Functions

Functions must inherit from the abstract base classes provided by the SDK.

#### Rollout Processor
Generates agent trajectories (interactions with the environment/LLM).

```python
from dashscope.finetune.reinforcement import AbstractRolloutProcessor, RolloutInput, RolloutOutput

class DemoRolloutProcessor(AbstractRolloutProcessor):
    async def process(self, input: RolloutInput) -> RolloutOutput:
        # Generate trajectory (supports async/def)
        pass
```

#### Reward Processor
Scores individual steps or final outputs.

```python
from dashscope.finetune.reinforcement import AbstractRewardProcessor, RewardInput, RewardOutput

class DemoRewardProcessor(AbstractRewardProcessor):
    def process(self, input: RewardInput) -> RewardOutput:
        # Calculate reward score
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
        
        total = ...  # Calculate total reward
        return RewardOutput(...)
```

#### Group Reward Processor
Scores a batch of trajectories collectively (e.g., for ranking).

```python
from dashscope.finetune.reinforcement import AbstractGroupRewardProcessor, GroupRewardInput, GroupRewardOutput

class DemoGroupRewardProcessor(AbstractGroupRewardProcessor):
    def setup(self) -> None:
        pass

    async def process(self, input: GroupRewardInput) -> GroupRewardOutput:
        # Calculate group rewards
        pass
```

### 3.2 Observability (Tracing)

Enable deep visibility into your agent's execution using OpenTelemetry. Trace data is exported to **ARMS** (Alibaba Cloud Real-Time Monitoring Service) after ARMS authorization is completed in the console. See [ARMS documentation](https://help.aliyun.com/zh/arms/?spm=5176.30275541.J_ZGek9Blx07Hclc3Ddt9dg.3.3ce02f3dmKOpPK&scm=20140722.S_card@@%E4%BA%A7%E5%93%81@@596792.S_new~UND~card.ID_card@@%E4%BA%A7%E5%93%81@@596792-RL_arms-LOC_2024SPSearchCard-OR_ser-PAR1_0bc1409817757870159831522e3953-V_4-RE_new5-P0_0-P1_0).

#### Prerequisites
1.  Add observability dependencies to `requirements.txt` (see Section 2.5, “Dependencies for Observability (Tracing)”).

#### Instrumentation Decorators
Import from `dashscope.finetune.reinforcement.component.observability`.

| Decorator | Usage | Description |
| :--- | :--- | :--- |
| `@observe_processor` | On `process()` method | Auto-traces input/output, latency, and status. Determines span kind (ROLLOUT/REWARD) automatically. |
| `trace_client()` | In `setup()` or before first LLM call | Wraps LLM clients (OpenAI, DashScope, LangChain-like). Auto-traces all downstream calls. **Recommended.** |
| `@observe_llm` | On custom LLM funcs | Use if `trace_client` doesn't support your wrapper. Requires `model` and `messages` as kwargs. |
| `trace_tool()` | In `setup()` (after tools are created) | Wraps tools (LangChain/MCP/LangGraph-like). Auto-traces tool invocations. |
| `@observe_tool` | On plain functions | Use for simple Python functions not wrapped as BaseTools. |

> **Setup:** Called once on server startup; supports both sync and async. Sync setup is offloaded to avoid blocking the event loop.

#### What `trace_client()` supports (duck typing)
`trace_client(client)` is detected by structure (not by class name). It supports:

- **Full OpenAI client** exposing `.chat.completions.create`
- **Completions resource** exposing `.create` and **no** `.chat` (e.g. `ChatOpenAI.client`)
- **LangChain-like wrapper** exposing `.client` and/or `.async_client`
- **DashScope Generation** class (pass the class itself, which has `call` as a classmethod)

#### What `trace_tool()` supports
`trace_tool(tools)` accepts the following shapes:

- A single tool object (e.g. LangChain `BaseTool`)
- A list/tuple of tools
- A dict mapping names to tools
- A LangGraph `ToolNode` (tools are expanded internally)
- MCP tools returned by `langchain-mcp-adapters` (provider is auto-set to `"mcp"`)

> **MCP note:** MCP Server and Client run in separate processes. `@observe_tool` on the Server-side function has no effect on the Client side. Always call `trace_tool(tools)` after `get_tools()` on the Client side.

#### Example: Instrumented Rollout Processor

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
        # 1. Trace LLM Client
        self._client = openai.AsyncOpenAI(base_url="...", api_key="...")
        trace_client(self._client)

        # 2. Trace Tools (e.g., MCP)
        from langchain_mcp_adapters.client import MultiServerMCPClient

        client = MultiServerMCPClient({...})
        self._tools = await client.get_tools()
        trace_tool(self._tools)

    @observe_processor
    async def process(self, input: RolloutInput) -> RolloutOutput:
        messages = input.messages or []
        model = input.model_resource.model_name

        # This call is automatically traced due to trace_client(self._client)
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

---

## 4. SDK & CLI Reference
* [SDK] Interface class: dashscope.finetune.agentic_rl.AgenticRL
* [CLI] Entry point: dashscope rl

### 4.1 Job Configuration
Initialize the client using YAML or code. Code arguments override YAML.

**[SDK] \_\_init\_\_**
```python
def __init__(self, api_key: str = None): ...
```
Initializes the AgenticRL instance.

**Parameters**:
- `api_key`: API key for authentication (uses environment variable if not provided)

**Example**:
```python
from dashscope.finetune.agentic_rl import AgenticRL
rl = AgenticRL(api_key="your_api_key")
```

**[SDK] [init](examples/workspace/demo_sdk_agentic_rl_workflows_yaml.py)**
```python
def init(self, config_path: Optional[str] = None, **kwargs) -> Self: ...
```
Initializes the instance from a YAML configuration file.

**Parameters**:
- `config_path`: Path to YAML configuration file
- `**kwargs`: Configuration overrides

**Returns**: Self instance

**Example**:
```python
from dashscope.finetune.agentic_rl import AgenticRL
rl = AgenticRL().init("config.yaml", job_name="custom_job")
```

### 4.2 Registering Functions

Uploads code and registers Function Components (FCs).

**[SDK] [register_functions](examples/workspace/demo_sdk_agentic_rl_workflows.py)**
```python
def register_functions(self, functions: Optional[Union[List[Union[RolloutFunctionComponent, RewardFunctionComponent]], RolloutFunctionComponent, RewardFunctionComponent]] = None, lazy_load: Optional[bool] = True) -> tuple: ...
```
Registers function components.

**Parameters**:
- `functions`: Function components to register
- `lazy_load`: Defer loading until execution

**Returns**: Tuple of entity/instance IDs

**Example**:
```python
from dashscope.finetune.agentic_rl import AgenticRL, AgenticRLFunctionComponent, FunctionType, FunctionComponentModel

rl=AgenticRL()
rollout_eids, reward_eids, group_eids, \
rollout_iids, reward_iids, group_iids = await rl.register_functions(
    functions=[
        AgenticRLFunctionComponent(
            type=FunctionType.ROLLOUT,
            fcmodel=FunctionComponentModel(
                zipdir='./',
                classpath="functions.rollout.demo_rollout.DemoRolloutProcessor"),
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
    lazy_load=False  # Set False to get instance IDs immediately for testing
)
```

**[CLI] [register_functions](examples/workspace/demo_cli_agentic_rl_functions.sh)**

**Usage: dashscope register_functions [OPTIONS]**                                                                                                                                                             
```bash                                                                                                                                                                                                                       
 🧩 Register Rollout/Reward function components, returns entity_id & instance_id                                                                                                                                        
                                                                                                                                                                                                                        
 Requires at least one of:                                                                                                                                                                                              
 - rollout_classpath                                                                                                                                                                                                    
 - reward_classpaths                                                                                                                                                                                                    
                                                                                                                                                                                                                        
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --rollout-classpaths                             TEXT  List for rollout class path (file.py:ClassName)                                                                                                               │
│ --reward-classpaths                              TEXT  List for reward class path (file.py:ClassName)                                                                                                                │
│ --group-reward-classpaths                        TEXT  List for group-reward class path (file.py:ClassName)                                                                                                          │
│ --workspace-dir                                  TEXT  Local workspace directory [default: ./]                                                                                                                       │
│ --lazy-load                    --no-lazy-load          Delay instance loading (set False for debugging) [default: lazy-load]                                                                                         │
│ --api-key                                        TEXT  DashScope API Key (uses DASHSCOPE_API_KEY env var if omitted) [env var: DASHSCOPE_API_KEY]                                                                    │
│ --output-format            -o                    TEXT  Output format: table|json|yaml [default: json]                                                                                                                │
│ --help                                                 Show this message and exit.                                                                                                                                   │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```
**Example**:
```bash
dashscope rl register_functions \
  --rollout-classpath "functions.rollout.demo_rollout.DemoRolloutProcessor" \
  --group-reward-classpaths "functions.reward.demo_group_reward.DemoGroupRewardProcessor" \
  --workspace-dir "./" \
  --output-format json
```

### 4.3 Testing Functions

#### 4.3.1 Remote Testing
**[SDK] [test_functions](examples/workspace/demo_sdk_agentic_rl_functions.py)**

Test registered instances with sample data.

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
    input_data="resouces/rollout_input.json" # path to JSON file
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

**[CLI] [test_functions](examples/workspace/demo_cli_agentic_rl_functions.sh)**

**Usage: dashscope test_functions [OPTIONS] INSTANCE_ID**
```bash   
 🧪 Test a registered Rollout/Reward function instance with custom input data.                                                                                                                                          
                                                                                                                                                                                                                        
╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    instance_id      TEXT  Target function instance ID (e.g., ro-ins-xxx or rw-ins-xxx) [required]                                                                                                                  │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *  --type           -t      TEXT  Function type: ROLLOUT or REWARD [required]                                                                                                                                        │
│ *  --input          -i      TEXT  JSON string or file path containing test payload [required]                                                                                                                        │
│    --api-key                TEXT  DashScope API Key (uses DASHSCOPE_API_KEY env var if omitted) [env var: DASHSCOPE_API_KEY]                                                                                         │
│    --output-format  -o      TEXT  Output format: table|json|yaml [default: json]                                                                                                                                     │
│    --help                         Show this message and exit.                                                                                                                                                        │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

**Example**:
```bash
dashscope rl test_functions "ins-xxx" \
  --type rollout \
  --input "resources/rollout_input.json"
```

#### 4.3.2 Local Testing
Use provided scripts to debug locally before uploading.
```bash
./scripts/start_local_rollout.sh
./scripts/query_local_rollout.sh
```

### 4.4 Dataset Upload
**[SDK] upload_datasets**
```python
def upload_datasets(self, training_files: Optional[List[str]] = None, validation_files: Optional[List[str]] = None) -> tuple: ...
```
Uploads datasets to the platform.

**Parameters**:
- `training_files`: List of training file paths
- `validation_files`: List of validation file paths

**Returns**: Tuple of uploaded file IDs

**Example**:
```python
from dashscope.finetune.agentic_rl import AgenticRL

rl=AgenticRL()
train_ids, val_ids = await rl.upload_datasets(["data/training.jsonl"], ["validation.jsonl"])
```
*   Supports local JSONL files.
*   Returns list of File IDs for job submission.

**[CLI] upload_data**

**Usage: dashscope upload_data [OPTIONS]**                                                                                                                                                                             
```bash                                                                                                                                                                                                                
 📦 Upload training/validation datasets to the platform, returns file IDs                                                                                                                                               
                                                                                                                                                                                                                        
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *  --training-files            TEXT  List of training dataset file paths [required]                                                                                                                                  │
│    --validation-files          TEXT  List of validation dataset file paths                                                                                                                                           │
│    --api-key                   TEXT  DashScope API Key (uses DASHSCOPE_API_KEY env var if omitted) [env var: DASHSCOPE_API_KEY]                                                                                      │
│    --output-format     -o      TEXT  Output format: table|json|yaml [default: json]                                                                                                                                  │
│    --help                            Show this message and exit.                                                                                                                                                     │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

**Example**:
```bash
dashscope rl upload_data \
  --training-files "./data/train.jsonl" \
  --validation-files "./data/validation.jsonl" \
  --output-format json
```

### 4.5 Submitting Jobs
Use pre-registered IDs for finer control.

#### 4.5.1 Runtime Configuration
Define compute resources for Rollout and Reward components.

```python
rollout_runtime = {
    "cpu": 2.0,                 # vCPUs (min: 0.05, max: 16)
    "memory_size": 4096,        # MB (1:1 to 1:4 CPU-memory(GB) ratio)
    "disk_size": 20480,         # MB (options: 512, 10240)
    "concurrency": 10,          # Concurrent requests
    "capacity": 5,              # Initial instances
    "max_capacity": 50,         # Max scaling
    "env": {}
}
```

**Runtime Fields (`FunctionComponentRuntime`):**
| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `cpu` | int | 1 | vCPUs per instance. |
| `memory_size` | int | 4096 | Memory in MB. |
| `disk_size` | int | 20480 | Disk in MB. |
| `concurrency` | int | 2 | Max concurrent requests per instance. |
| `capacity` | int | 10 | Target number of replicas. |
| `max_capacity` | int | 50 | Max replicas for auto-scaling. |
| `env` | dict | {} | Environment variables. |

#### 4.5.2 Submitting Jobs

**[SDK] [submit_job](examples/workspace/demo_sdk_agentic_rl_tuning.py)**
```python
def submit_job(self, model: Optional[str] = None, training_file_ids: Optional[Union[List[str], str]] = None, validation_file_ids: Optional[Union[List[str], str]] = None, functions: Optional[Union[List[Union[RolloutFunctionComponent, RewardFunctionComponent, AgenticRLFunctionComponent]], RolloutFunctionComponent, RewardFunctionComponent, AgenticRLFunctionComponent]] = None, hyper_parameters: Optional[Dict[str, str]] = None, job_name: Optional[str] = None, **kwargs) -> FineTune: ...
```
Submits RL tuning job to the platform.

**Parameters**:
- `model`: Base model name
- `training_file_ids`: IDs of uploaded training files
- `validation_file_ids`: IDs of uploaded validation files
- `functions`: Function components
- `hyper_parameters`: Training hyperparameters
- `job_name`: Custom job name

**Returns**: `FineTune` job object

**Example**:
```python
from dashscope.finetune.agentic_rl import AgenticRL, AgenticRLFunctionComponent, FunctionType, FunctionComponentModel

rl=AgenticRL()

rollout_id = 'ro-de54dc89-7aae-4e17-b9b6-c2f0def6a586'
reward_ids = ['rw-8feba7fc-3b2e-4ceb-a336-ba03d5f351cd']
rollout_runtime = {"cpu": 2, "memory_size": 4096, "disk_size": 10240, "concurrency": 2,
                   "env": {}, "capacity": 5}
hyper_parameters = {'batch_size': '256'}
functions = [
    AgenticRLFunctionComponent(
        type=FunctionType.ROLLOUT,
        name="rollout-1",
        entity_id=rollout_id,
        runtime=FunctionComponentRuntime(**rollout_runtime)),
    AgenticRLFunctionComponent(
        type=FunctionType.REWARD,
        weight=1.0,
        entity_id=reward_ids[0]),
]

result = rl.submit_job(
    job_name="agentic-rl-0423",
    model="qwen3-32b",
    training_file_ids=training_file_ids,
    validation_file_ids=validation_file_ids,
    functions=functions,
    hyper_parameters=hyper_parameters)
```

**[CLI] [submit](examples/workspace/demo_cli_agentic_rl_tuning.sh)**

**Usage: dashscope submit [OPTIONS]**
```bash
 📤 Submit fine-tuning job (requires pre-registered FCs & uploaded datasets)                                                                                                                                            
                                                                                                                                                                                                                        
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *  --model                          TEXT   Base model name [required]                                                                                                                                                │
│ *  --training-file-ids              TEXT   Comma-separated list of training file_ids [required]                                                                                                                      │
│ *  --rollout-id                     TEXT   Pre-registered Rollout entity_id [required]                                                                                                                               │
│    --reward-ids                     TEXT   Comma-separated list of reward entity_ids                                                                                                                                 │
│    --group-reward-ids               TEXT   Comma-separated list of group-reward entity_ids                                                                                                                           │
│    --rollout-runtime                TEXT   Rollout runtime as JSON string                                                                                                                                            │
│    --reward-runtimes                TEXT   Reward runtimes as JSON string                                                                                                                                            │
│    --group-reward-runtimes          TEXT   Group-reward runtimes as JSON string                                                                                                                                      │
│    --rollout-name                   TEXT   Pre-registered Rollout entity_name                                                                                                                                        │
│    --reward-names                   TEXT   Comma-separated list of reward entity_names                                                                                                                               │
│    --group-reward-names             TEXT   Comma-separated list of group-reward entity_names                                                                                                                         │
│    --rollout-weight                 FLOAT  Pre-registered Rollout entity_weight                                                                                                                                      │
│    --reward-weights                 FLOAT  Comma-separated list of reward entity_weights                                                                                                                             │
│    --group-reward-weights           FLOAT  Comma-separated list of group-reward entity_weights                                                                                                                       │
│    --reward-metric-weights          TEXT   Reward metric weights as JSON string (list of dicts)                                                                                                                      │
│    --validation-file-ids            TEXT   Comma-separated list of validation file_ids                                                                                                                               │
│    --hyper-parameters               TEXT   Hyperparameters as JSON string                                                                                                                                            │
│    --job-name                       TEXT   Job name                                                                                                                                                                  │
│    --api-key                        TEXT   DashScope API Key (uses DASHSCOPE_API_KEY env var if omitted) [env var: DASHSCOPE_API_KEY]                                                                                │
│    --output-format          -o      TEXT   Output format: table|json|yaml [default: table]                                                                                                                           │
│    --help                                  Show this message and exit.                                                                                                                                               │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

**Example**:
```bash
dashscope rl submit \
  --model "qwen3-32b" \
  --rollout-id "ro-entity-xxx" \
  --group-reward-ids "grw-entity-yyy" \
  --training-file-ids "file-zzz" \
  --rollout-name "rollout-1" \
  --rollout-runtime '{"cpu": 2, "memory_size": 4096}' \
  --reward-runtimes '[{"cpu": 2, "memory_size": 4096}]' \
  --group-reward-runtimes '[{"cpu": 2, "memory_size": 4096}]' \
  --hyper-parameters '{"batch_size": "256"}'
```
*Note: `--rollout-runtime` is a JSON string. `--reward-runtimes` / `--group-reward-runtimes` is a JSON array of strings/objects.*


### 4.6 One-Step Workflow
Automatically registers functions, uploads data, and submits the job.

**[SDK] [run](examples/workspace/demo_sdk_agentic_rl_workflows.py)**
```python
def run(self, model: Optional[str] = None, training_files: Optional[Union[List[str], str]] = None, validation_files: Optional[Union[List[str], str]] = None, functions: Optional[Union[List[Union[RolloutFunctionComponent, RewardFunctionComponent, AgenticRLFunctionComponent]], RolloutFunctionComponent, RewardFunctionComponent, AgenticRLFunctionComponent]] = None, hyper_parameters: Optional[Dict[str, str]] = None, job_name: Optional[str] = None, workspace_dir: str = "./", **kwargs) -> FineTune: ...
```
Full workflow execution (registration + upload + submission).

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

rl=AgenticRL()
rollout_runtime = {"cpu": 2, "memory_size": 4096, "disk_size": 20960, "concurrency": 2,
                    "env": {}, "capacity": 5}
reward_runtimes = [
    {"cpu": 2, "memory_size": 4096, "disk_size": 20960, "concurrency": 10, "env": {},
     "capacity": 8},
    {"cpu": 2, "memory_size": 4096, "disk_size": 20960, "concurrency": 5, "env": {},
     "capacity": 6}
]
functions=[
    AgenticRLFunctionComponent(
        type=FunctionType.ROLLOUT,
        name="rollout-1",
        fcmodel=FunctionComponentModel(
            classpath="functions.rollout.demo_rollout.DemoRolloutProcessor"),
        runtime=FunctionComponentRuntime(**rollout_runtime)),
    AgenticRLFunctionComponent(
        type=FunctionType.REWARD,
        name="reward-1",
        weight=1.1,
        fcmodel=FunctionComponentModel(
            classpath="functions.reward.demo_reward.DemoRewardProcessor"),
        runtime=FunctionComponentRuntime(**reward_runtimes[0])),
]
job = await rl.run(
    model="qwen3-32b",
    training_files=["./data/train.jsonl"],
    validation_files=["./data/validation.jsonl"],
    functions=functions,
    hyper_parameters={'batch_size': '128'}
)
```

**[CLI] [run](examples/workspace/demo_cli_agentic_rl_workflows.sh)**

**Usage: dashscope run [OPTIONS]**                                                                                                                                                                                   
```bash                                                                                                                                                                                                                   
 🚀 Launch the complete RL tuning workflow (function registration → dataset upload → job submission)                                                                                                                    
                                                                                                                                                                                                                        
 Execution modes:                                                                                                                                                                                                       
 1. Configuration-driven: Use -c/--config to specify a YAML file                                                                                                                                                        
 2. Direct parameter: Provide all required arguments via CLI options                                                                                                                                                    
                                                                                                                                                                                                                        
 Required parameters:                                                                                                                                                                                                   
 - rollout_classpath                                                                                                                                                                                                    
 - reward_classpaths (at least one)                                                                                                                                                                                     
 - training_files (at least one)                                                                                                                                                                                        
                                                                                                                                                                                                                        
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --config                   -c      PATH   Path to YAML configuration file                                                                                                                                            │
│ --model                            TEXT   Base model identifier                                                                                                                                                      │
│ --training-files                   TEXT   Paths to training dataset files                                                                                                                                            │
│ --validation-files                 TEXT   Paths to validation dataset files                                                                                                                                          │
│ --rollout-classpath                TEXT   Python import path to rollout class (module:Class)                                                                                                                         │
│ --reward-classpaths                TEXT   List for reward class path (file.py:ClassName)                                                                                                                             │
│ --group-reward-classpaths          TEXT   List for group-reward class path (file.py:ClassName)                                                                                                                       │
│ --rollout-name                     TEXT   Pre-registered Rollout entity_name                                                                                                                                         │
│ --reward-names                     TEXT   Comma-separated list of reward entity_names                                                                                                                                │
│ --group-reward-names               TEXT   Comma-separated list of group-reward entity_names                                                                                                                          │
│ --rollout-weight                   TEXT   Pre-registered Rollout entity_weight                                                                                                                                       │
│ --reward-weights                   FLOAT  Comma-separated list of reward entity_weights                                                                                                                              │
│ --group-reward-weights             FLOAT  Comma-separated list of group-reward entity_weights                                                                                                                        │
│ --reward-metric-weights            TEXT   Reward metric weights as JSON string (list of dicts)                                                                                                                       │
│ --rollout-runtime                  TEXT   Rollout runtime as JSON string                                                                                                                                             │
│ --reward-runtimes                  TEXT   Reward runtimes as JSON string                                                                                                                                             │
│ --group-reward-runtimes            TEXT   Group-reward runtimes as JSON string                                                                                                                                       │
│ --hyper-parameters                 TEXT   JSON string of hyperparameters                                                                                                                                             │
│ --job-name                         TEXT   Custom name for the tuning job                                                                                                                                             │
│ --api-key                          TEXT   DashScope API Key (uses DASHSCOPE_API_KEY env var if omitted) [env var: DASHSCOPE_API_KEY]                                                                                 │
│ --workspace-dir                    TEXT   Workspace directory for job artifacts [default: ./]                                                                                                                        │
│ --output-format            -o      TEXT   Output format: table|json|yaml [default: table]                                                                                                                            │
│ --verbose                  -v             Enable detailed error traces                                                                                                                                               │
│ --help                                    Show this message and exit.                                                                                                                                                │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

**Example**: [Run Full Workflow (Auto) ](examples/workspace/demo_cli_agentic_rl_workflows.sh)
```bash
dashscope rl run \
  --config "resources/agentic_rl_config.yaml" \
  --model "qwen3-32b" \
  --rollout-classpath "functions.rollout.demo_rollout.DemoRolloutProcessor" \
  --group-reward-classpaths "functions.reward.demo_group_reward.DemoGroupRewardProcessor" \
  --rollout-name "rollout-1" \
  --training-files "./data/train.jsonl" \
  --validation-files "./data/validation.jsonl" \
  --verbose
```

### 4.7 Job Management

**[SDK] get**
```python
def get(cls, job_id: str, api_key: str = None, workspace: str = None, **kwargs) -> FineTune: ...
```
Gets job information.

**Parameters**:
- `job_id`: ID of job to retrieve
- `api_key`: API key for authentication
- `workspace`: Workspace identifier

**Example**:
```python
from dashscope.finetune.agentic_rl import AgenticRL
job = AgenticRL.get("job-12345")
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
│ --help                         Show this message and exit.                                                                                                                                                           │
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
Cancels a running job.

**Parameters**:
- `job_id`: ID of job to cancel
- `api_key`: API key for authentication
- `workspace`: Workspace identifier

**Example**:
```python
from dashscope.finetune.agentic_rl import AgenticRL
AgenticRL.cancel("job-12345")
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
│ --help                 Show this message and exit.                                                                                                                                                                   │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

**Example**:
```bash
dashscope rl cancel "$JOB_ID"
```

**[SDK] delete**
```python
def delete(cls, job_id: str, api_key: str = None, workspace: str = None, **kwargs) -> FineTuneDelete: ...
```
Deletes a job.

**Parameters**:
- `job_id`: ID of job to delete
- `api_key`: API key for authentication
- `workspace`: Workspace identifier

**Example**:
```python
from dashscope.finetune.agentic_rl import AgenticRL
AgenticRL.delete("job-12345")
```

**[CLI] delete**

**Usage: dashscope delete [OPTIONS] JOB_ID**                                                                                                                                                                     
```bash 
 🗑️ Delete a job record (releases metadata)                                                                                                                                                                             
                                                                                                                                                                                                                        
╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    job_id      TEXT  Target job ID [required]                                                                                                                                                                      │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --api-key        TEXT  DashScope API Key (uses DASHSCOPE_API_KEY env var if omitted) [env var: DASHSCOPE_API_KEY]                                                                                                    │
│ --help                 Show this message and exit.                                                                                                                                                                   │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

**Example**:
```bash
dashscope rl delete "$JOB_ID"
```

**[SDK] list**
```python
def list(cls, page_no=1, page_size=10, api_key: str = None, workspace: str = None, **kwargs) -> FineTuneList: ...
```
Lists fine-tune jobs.

**Parameters**:
- `page_no`: Page number
- `page_size`: Items per page
- `api_key`: API key for authentication
- `workspace`: Workspace identifier

**Example**:
```python
from dashscope.finetune.agentic_rl import AgenticRL
jobs = AgenticRL.list(page_no=1, page_size=20)
```

**[CLI] list**

**Usage: dashscope list [OPTIONS]**                                                                                                                                                                          
```bash                                                                                                                                                                                                            
 📋 List historical fine-tuning jobs with pagination                                                                                                                                                                    
                                                                                                                                                                                                                        
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --page           -p      INTEGER  Page number [default: 1]                                                                                                                                                           │
│ --size           -s      INTEGER  Items per page [default: 10]                                                                                                                                                       │
│ --api-key                TEXT     DashScope API Key (uses DASHSCOPE_API_KEY env var if omitted) [env var: DASHSCOPE_API_KEY]                                                                                         │
│ --output-format  -o      TEXT     [default: table]                                                                                                                                                                   │
│ --help                            Show this message and exit.                                                                                                                                                        │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```
**Example**:
```bash
dashscope rl list --page 1 --size 10
```

**[SDK] logs**
```python
def logs(cls, job_id: str, offset: int = 1, lines: int = 1000, api_key: str = None, workspace: str = None, **kwargs) -> FineTune: ...
```
Gets job logs.

**Parameters**:
- `job_id`: ID of job to retrieve logs for
- `offset`: Log line offset
- `lines`: Number of lines to retrieve
- `api_key`: API key for authentication
- `workspace`: Workspace identifier

**Example**:
```python
from dashscope.finetune.agentic_rl import AgenticRL
logs = AgenticRL.logs("job-12345", lines=500)
```

**[CLI] logs**

**Usage: dashscope logs [OPTIONS] JOB_ID**                                                                                                                                                                           
```bash
 📜 Fetch job execution logs (supports pagination)                                                                                                                                                                      
                                                                                                                                                                                                                        
╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    job_id      TEXT  Target job ID [required]                                                                                                                                                                      │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --offset                 INTEGER  Starting line number [default: 1]                                                                                                                                                  │
│ --lines                  INTEGER  Number of log lines to return [default: 1000]                                                                                                                                      │
│ --api-key                TEXT     DashScope API Key (uses DASHSCOPE_API_KEY env var if omitted) [env var: DASHSCOPE_API_KEY]                                                                                         │
│ --output-format  -o      TEXT     [default: table]                                                                                                                                                                   │
│ --help                            Show this message and exit.                                                                                                                                                        │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

**Example**:
```bash
dashscope rl logs "$JOB_ID" --offset 1 --lines 50
```

**[SDK] stream_events**
```python
def stream_events(cls, job_id: str, api_key: str = None, workspace: str = None, **kwargs) -> Iterator[FineTuneEvent]: ...
```
Streams job events.

**Parameters**:
- `job_id`: ID of job to monitor
- `api_key`: API key for authentication
- `workspace`: Workspace identifier

**Example**:
```python
from dashscope.finetune.agentic_rl import AgenticRL
for event in AgenticRL.stream_events("job-12345"):
    print(event)
```

---

## 5. The hierarchical structure of the core classes and their members：
```text
AgenticRLTuning (Root)
├── tuning_id: str                          # System-generated tuning job ID
└── tuning: TuningModel                     # Core configuration container
    ├── name: str = "agentic-rl"            # Job name (1-256 chars)
    ├── fcs: List[AgenticRLFunctionComponent]  # Function components
    ├── datasets: Datasets                  # Training data management
    │   ├── name: str                       # Dataset collection name
    │   ├── training_files: List[FileSpec]  # Training files metadata
    │   ├── validation_files: List[FileSpec] # Validation files metadata
    │   ├── uploaded_training_ids: List[str] # OSS IDs for uploaded training data
    │   └── uploaded_validation_ids: List[str] # OSS IDs for validation data
    ├── model: FoundationModel              # Base model configuration
    │   └── name: str                       # Foundation model name
    ├── training: Training                  # Training parameters
    │   ├── type: TrainingType              # Training methodology
    │   └── hyperparameters: Dict[str, str] # Tuning parameters
    └── observability: Observability        # Monitoring config

AgenticRLFunctionComponent                  # Function component definition
├── type: FunctionType                      # Component type (ROLLOUT/REWARD/GROUP_REWARD)
├── name: Optional[str]                     # Component identifier
├── weight: Optional[float]                 # Execution priority (0.0-1.0) only for reward/group-reward
├── fcmodel: FunctionComponentModel         # Deployment package config
│   ├── zipdir: str                         # Source code directory
│   ├── classpath: Optional[str]            # Entrypoint class path
│   ├── filepath: str                       # Main Python file
│   ├── classname: str                      # Entrypoint class name
│   ├── requirements_path: str              # Dependencies
│   ├── extra_files: List[str]              # Additional deployment files
│   ├── oss_id: Optional[str]               # OSS storage ID
│   └── oss_signed_url: Optional[str]       # OSS access URL
├── runtime: FunctionComponentRuntime       # Resource allocation
│   ├── cpu: Optional[int]                  # vCPUs per instance
│   ├── memory_size: Optional[int]          # Memory (MB)
│   ├── disk_size: Optional[int]            # Disk space (MB)
│   ├── concurrency: Optional[int]          # Concurrent requests
│   ├── capacity: Optional[int]             # Initial instances
│   ├── max_capacity: Optional[int]         # Max auto-scaling
│   ├── min_capacity: Optional[int]         # Min auto-scaling
│   ├── memory_scale_threshold: Optional[float] # Memory scaling trigger
│   ├── concurrency_scale_threshold: Optional[float] # Concurrency scaling
│   ├── enable_vpc_config: Optional[bool]   # VPC network toggle
│   ├── security_group_id: Optional[str]    # Security group ID
│   ├── switch_ids: Optional[List[str]]     # Network switch IDs
│   ├── vpc_id: Optional[str]              # VPC identifier
│   ├── vpc_role: Optional[str]            # IAM role for VPC
│   ├── enable_log: Optional[bool]         # Logging toggle
│   └── env: Optional[Dict[str, Any]]      # Environment variables
├── entity_id: Optional[str]               # System registration ID
├── instance_id: Optional[str]             # Runtime instance ID
├── instance_status: int = -1              # -1=Unknown, 0=Init, 1=Deploying, 2=Active
├── instance_url: Optional[str]            # Service endpoint
└── instance_token: Optional[str]          # Access credential

FileSpec                                   # Dataset file metadata
├── path: str                             # Local file path
├── name: Optional[str]                   # Display name
├── description: Optional[str]            # File purpose description
└── oss_id: Optional[str]                 # Uploaded OSS ID

FunctionComponentRuntime                  # Hardware resource config
├── cpu: Optional[int]                    # vCPU cores
├── memory_size: Optional[int]            # RAM in MB
├── disk_size: Optional[int]              # Storage in MB
├── concurrency: Optional[int]            # Concurrent requests
├── capacity: Optional[int]               # Initial instances
├── max_capacity: Optional[int]           # Max scaling limit
├── min_capacity: Optional[int]           # Min scaling limit
├── memory_scale_threshold: Optional[float] # RAM usage scaling trigger
├── concurrency_scale_threshold: Optional[float] # Request rate scaling
├── enable_vpc_config: Optional[bool]     # VPC network toggle
├── security_group_id: Optional[str]      # Security group ID
├── switch_ids: Optional[List[str]]       # Network switches
├── vpc_id: Optional[str]                 # VPC identifier
├── vpc_role: Optional[str]               # IAM role for VPC
├── enable_log: Optional[bool]            # Log collection toggle
└── env: Optional[Dict[str, Any]]         # Environment variables
```

---

## 6. CLI Reference

The CLI mirrors the SDK functionality. Use `dashscope rl --help` for details.

### Usage: dashscope [OPTIONS] COMMAND [ARGS]...  
```bash
                                                                                                                                                                                                                                                                                                                                                                             
 🚀 Agentic RL Fine-Tuning CLI        
                                                                                                                                                                                                                                                                                                                                                                                           
╭─ Options ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                                                                                                                                                     │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ register_functions  🧩 Register Rollout/Reward function components, returns entity_id & instance_id                                                                                                             │
│ test_functions      🧪 Test a registered Rollout/Reward function instance with custom input data.                                                                                                               │
│ upload_data         📦 Upload training/validation datasets to the platform, returns file IDs                                                                                                                    │
│ submit              📤 Submit fine-tuning job (requires pre-registered FCs & uploaded datasets)                                                                                                                 │
│ run                 🚀 Launch the complete RL tuning workflow (function registration → dataset upload → job submission)                                                                                         │
│ status              📊 Query the current status and metadata of a specific job                                                                                                                                  │
│ list                📋 List historical fine-tuning jobs with pagination                                                                                                                                         │
│ cancel              🛑 Cancel a running job                                                                                                                                                                     │
│ delete              🗑️ Delete a job record (releases metadata)                                                                                                                                                  │
│ logs                📜 Fetch job execution logs (supports pagination)                                                                                                                                           │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

---

## 7. FAQ & Troubleshooting

**Q: Function registration fails.**
*   **Check**: Is the classpath correct (`module.path:ClassName`)?
*   **Check**: Does `requirements.txt` exist in the workspace root?
*   **Check**: Are all dependencies listed in `requirements.txt`?

**Q: Job submission fails.**
*   **Check**: Are the Entity IDs and File IDs valid?
*   **Check**: Is the base model available in your region?
*   **Check**: Do `reward_runtimes` list length match `reward_ids` list length?

**Q: How to optimize performance?**
*   Use `async def process` for I/O bound tasks.
*   Increase `concurrency` in runtime config if CPU/Memory allows.
*   Keep observability payloads bounded (avoid excessive input/output capture) to reduce overhead.

**Q: Where are my traces?**
*   Traces are sent to **ARMS** after ARMS authorization is completed in the Bailian Console. Ensure your `requirements.txt` includes the observability dependencies and that you are using the observability APIs (`observe_processor`, `trace_client`, `trace_tool`, etc.).
