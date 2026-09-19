# Agentic Reinforcement Learning: 사용자 가이드 [[English]](./UserGuide.md) [[中文]](./UserGuide-zh.md) [[日本語]](./UserGuide-ja.md) [[Español]](./UserGuide-es.md)

---

## 1. 소개

**Agentic RL SDK/CLI**는 대규모 언어 모델(LLM)을 위한 강화학습(RL) 모델을 구축, 학습, 관리하기 위한 종합적인 툴체인을 제공합니다. 에이전트 행동 정의, 트래젝토리 수집, 정책 최적화라는 복잡한 워크플로를 단순화합니다.

이 SDK는 두 가지 핵심 모듈로 구성됩니다:
1.  **함수 모듈**: **Rollout**(트래젝토리 생성), **Reward**(점수 산정), **Group Reward**(배치 점수 산정)를 위한 커스텀 Python 코드를 관리합니다. 자동 등록, 테스트, 내장 **관측성(Observability, Tracing)**을 지원합니다.
2.  **튜닝 모듈**: 데이터셋 관리, 하이퍼파라미터 설정, 작업 제출, 라이프사이클 관리(상태, 로그, 취소)를 담당합니다.

**워크플로**:
1. 커스텀 함수를 등록합니다. 일반 강화학습에는 Rollout과 최소 1개의
   Reward가 필요합니다. OPD의 경우 Rollout과 Reward는 선택 사항입니다.
2. 튜닝 모듈을 사용해 데이터셋을 업로드하고, 작업을 설정한 뒤 학습을 위해
   제출합니다.

---

## 2. 설치 및 설정

### 2.1 PyPI를 통한 설치
```bash
pip install dashscope>=1.25.19
```

### 2.2 소스에서 설치 (개발용)
```bash
git clone https://github.com/dashscope/dashscope-sdk-python.git
cd dashscope-sdk-python
pip install -e .  # 개발을 위해 editable 모드로 설치
```

### 2.3 인증
1.  **DashScope API 키**를 발급받습니다.
2.  환경 변수를 설정합니다:
    ```bash
    export DASHSCOPE_API_KEY='your-api-key-here'
    ```

### 2.4 프로젝트 구조
권장하는 작업 공간 구조는 원활한 배포와 로컬 테스트를 보장합니다:

```text
workspace/
├── data/                   # 데이터셋
│   ├── training.jsonl
│   └── validation.jsonl
├── functions/              # 커스텀 함수; OPD에서만 선택 사항
│   ├── reward/
│   │   ├── group_reward.py
│   │   └── reward.py
│   └── rollout/
│       └── rollout.py
├── requirements.txt        # 함수 컴포넌트 의존성
├── rl-job.yaml             # 일반 Agentic RL 설정
└── opd-job.yaml            # OPD 설정
```

일반 강화학습에는 커스텀 Rollout과 최소 1개의 Reward가 필요합니다. OPD만
Rollout과 Reward를 생략하거나, 둘 중 하나만 독립적으로 설정할 수 있습니다.

### 2.5 의존성 패키지 (requirements.txt 가이드)
이 파일은 함수 컴포넌트를 클라우드에 배포하기 위해 **필수**입니다. 작업 공간 루트에 있어야 합니다.

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
```

**핵심 참고 사항:**
*   **기본 패키지**: `dashscope`는 런타임 환경에 미리 설치되어 있습니다. `requirements.txt`에 포함하지 **마세요**.
*   **Protobuf**: 호환성 문제를 피하려면 지정된 범위 내에 있어야 합니다.

#### 관측성(Tracing)을 위한 의존성
관측성 스팬(processor / LLM / tool)을 사용하려면, `requirements.txt`에 다음 의존성을 추가하세요(재현 가능한 배포를 위해 버전 고정을 권장합니다):

```txt
opentelemetry-api==1.41.1
opentelemetry-sdk==1.41.1
opentelemetry-exporter-otlp-proto-http==1.41.1
opentelemetry-processor-baggage==0.62b1
loongsuite-util-genai==0.4.0
```

### 2.6 로깅 설정
`LOG_LEVEL` 환경 변수를 통해 로그 상세도를 설정합니다:

```bash
export LOG_LEVEL="DEBUG"   # 가장 상세함 (API 키 등 민감 정보는 마스킹됨)
export LOG_LEVEL="INFO"    # 기본값
export LOG_LEVEL="WARNING"
export LOG_LEVEL="ERROR"
export LOG_LEVEL="CRITICAL"
```

---

## 3. 함수 작성
참고: workspace/functions 디렉터리, 출력물 rollout.py, reward.py 등

### 3.1 함수 구현

함수는 SDK가 제공하는 추상 기본 클래스를 상속해야 합니다.

#### Rollout Processor
에이전트 트래젝토리(환경/LLM과의 상호작용)를 생성합니다.

```python
from dashscope.finetune.reinforcement import AbstractRolloutProcessor, RolloutInput, RolloutOutput

class DemoRolloutProcessor(AbstractRolloutProcessor):
    async def process(self, input: RolloutInput) -> RolloutOutput:
        # 트래젝토리 생성 (async/def 모두 지원)
        pass
```

#### Reward Processor
개별 단계 또는 최종 출력에 점수를 매깁니다.

```python
from dashscope.finetune.reinforcement import AbstractRewardProcessor, RewardInput, RewardOutput

class DemoRewardProcessor(AbstractRewardProcessor):
    def process(self, input: RewardInput) -> RewardOutput:
        # reward 점수 계산
        pass
```

#### 데코레이터를 사용한 고급 Reward Processor
```python
from dashscope.finetune.reinforcement import reward_func, sub_reward_func, aggregate_func

@reward_func("SafetyProcessor")
class SafetyProcessor(AbstractRewardProcessor):
    @sub_reward_func("toxicity", sub_weight=0.7)
    def toxicity(self, input: RewardInput) -> RewardOutput: ...

    @sub_reward_func("refusal", sub_weight=0.3)
    async def refusal(self, input: RewardInput) -> RewardOutput: ...

    @aggregate_func
    async def aggregate(self, sub_rewards: dict[str, RewardOutput]) -> RewardOutput: # 커스텀 집계 로직
        weights = self.get_weights()
        scores = self.get_scores(sub_rewards)
        reward_metrics = self.get_reward_metrics(sub_rewards)

        total = ...  # 총 reward 계산
        return RewardOutput(...)
```

#### Group Reward Processor
트래젝토리 배치 전체에 대해 점수를 매깁니다(예: 순위 매기기).

```python
from dashscope.finetune.reinforcement import AbstractGroupRewardProcessor, GroupRewardInput, GroupRewardOutput

class DemoGroupRewardProcessor(AbstractGroupRewardProcessor):
    def setup(self) -> None:
        pass

    async def process(self, input: GroupRewardInput) -> GroupRewardOutput:
        # 그룹 reward 계산
        pass
```

### 3.2 관측성 (Tracing)

OpenTelemetry를 사용해 에이전트 실행에 대한 깊이 있는 가시성을 확보하세요. 트레이스 데이터는 콘솔에서 ARMS 인증을 완료한 후 **ARMS**(Alibaba Cloud Real-Time Monitoring Service)로 내보내집니다. 자세한 내용은 [ARMS 문서](https://help.aliyun.com/zh/arms/?spm=5176.30275541.J_ZGek9Blx07Hclc3Ddt9dg.3.3ce02f3dmKOpPK&scm=20140722.S_card@@%E4%BA%A7%E5%93%81@@596792.S_new~UND~card.ID_card@@%E4%BA%A7%E5%93%81@@596792-RL_arms-LOC_2024SPSearchCard-OR_ser-PAR1_0bc1409817757870159831522e3953-V_4-RE_new5-P0_0-P1_0)를 참고하세요.

#### 사전 요구 사항
1.  `requirements.txt`에 관측성 의존성을 추가합니다(섹션 2.5 "관측성(Tracing)을 위한 의존성" 참조).

#### 계측(Instrumentation) 데코레이터
`dashscope.finetune.reinforcement.component.observability`에서 임포트합니다.

| 데코레이터 | 사용 위치 | 설명 |
| :--- | :--- | :--- |
| `@observe_processor` | `process()` 메서드에 사용 | 입력/출력, 지연 시간, 상태를 자동으로 트레이싱합니다. span 종류(ROLLOUT/REWARD)를 자동으로 판별합니다. |
| `trace_client()` | `setup()` 안이나 첫 LLM 호출 이전에 사용 | LLM 클라이언트(OpenAI, DashScope, LangChain 유사 클라이언트)를 감쌉니다. 이후의 모든 호출을 자동으로 트레이싱합니다. **권장.** |
| `@observe_llm` | 커스텀 LLM 함수에 사용 | `trace_client`가 해당 래퍼를 지원하지 않을 때 사용합니다. kwargs로 `model`과 `messages`가 필요합니다. |
| `trace_tool()` | `setup()`(도구 생성 이후)에 사용 | 도구(LangChain/MCP/LangGraph 유사)를 감쌉니다. 도구 호출을 자동으로 트레이싱합니다. |
| `@observe_tool` | 일반 함수에 사용 | BaseTools로 감싸지 않은 단순한 Python 함수에 사용합니다. |

> **설정(Setup):** 서버 시작 시 한 번 호출되며, 동기와 비동기를 모두 지원합니다. 동기 setup은 이벤트 루프를 막지 않도록 오프로드됩니다.

#### `trace_client()`가 지원하는 형태 (덕 타이핑)
`trace_client(client)`는 클래스 이름이 아니라 구조로 감지됩니다. 다음을 지원합니다:

- `.chat.completions.create`를 노출하는 **완전한 OpenAI 클라이언트**
- `.create`는 노출하지만 `.chat`은 **없는** Completions 리소스(예: `ChatOpenAI.client`)
- `.client` 및/또는 `.async_client`를 노출하는 **LangChain 유사 래퍼**
- **DashScope Generation** 클래스(classmethod인 `call`을 가진 클래스 자체를 전달)

#### `trace_tool()`이 지원하는 형태
`trace_tool(tools)`는 다음 형태를 받습니다:

- 단일 도구 객체(예: LangChain `BaseTool`)
- 도구의 리스트/튜플
- 이름을 도구에 매핑하는 딕셔너리
- LangGraph `ToolNode`(내부적으로 도구가 펼쳐짐)
- `langchain-mcp-adapters`가 반환하는 MCP 도구(provider가 자동으로 `"mcp"`로 설정됨)

> **MCP 참고:** MCP 서버와 클라이언트는 서로 다른 프로세스에서 실행됩니다. 서버 측 함수에 붙인 `@observe_tool`은 클라이언트 측에는 영향을 주지 않습니다. 클라이언트 측에서는 항상 `get_tools()` 이후에 `trace_tool(tools)`를 호출하세요.

#### 예제: 계측된 Rollout Processor

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
        # 1. LLM 클라이언트 트레이싱
        self._client = openai.AsyncOpenAI(base_url="...", api_key="...")
        trace_client(self._client)

        # 2. 도구 트레이싱 (예: MCP)
        from langchain_mcp_adapters.client import MultiServerMCPClient

        client = MultiServerMCPClient({...})
        self._tools = await client.get_tools()
        trace_tool(self._tools)

    @observe_processor
    async def process(self, input: RolloutInput) -> RolloutOutput:
        messages = input.messages or []
        model = input.model_resource.model_name

        # trace_client(self._client) 덕분에 이 호출은 자동으로 트레이싱됩니다
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

## 4. SDK & CLI 레퍼런스
* [SDK] 인터페이스 클래스: dashscope.finetune.agentic_rl.AgenticRL
* [CLI] 진입점: dashscope rl

### 4.1 작업 설정

일반 강화학습과 OPD는 동일한 SDK/CLI 워크플로를 사용합니다. 해당하는 YAML
설정을 선택하세요. 코드의 인자는 YAML 값을 재정의합니다.

| 학습 유형 | 설정 | 커스텀 함수 |
|---|---|---|
| 일반 강화학습 | `rl-job.yaml` | Rollout이 필수이며, 최소 1개의 Reward가 필요 |
| OPD | `opd-job.yaml` | Rollout과 Reward는 독립적으로 선택 사항이며 둘 다 생략 가능 |

**[SDK] \_\_init\_\_**
```python
def __init__(self, api_key: str = None): ...
```
AgenticRL 인스턴스를 초기화합니다.

**매개변수**:
- `api_key`: 인증용 API 키(제공하지 않으면 환경 변수 사용)

**예제**:
```python
from dashscope.finetune.agentic_rl import AgenticRL
rl = AgenticRL(api_key="your_api_key")
```

**[SDK] [init](submit_job.py)**
```python
def init(self, config_path: Optional[str] = None, **kwargs) -> Self: ...
```
YAML 설정 파일로부터 인스턴스를 초기화합니다.

**매개변수**:
- `config_path`: YAML 설정 파일 경로
- `**kwargs`: 설정 재정의 값

**반환값**: Self 인스턴스

**예제**:
```python
from dashscope.finetune.agentic_rl import AgenticRL
config_path = "opd-job.yaml"  # 일반 강화학습에는 "rl-job.yaml" 사용
rl = AgenticRL().init(config_path, job_name="custom_job")
result = await rl.run()
```

`opd-job.yaml`을 선택했을 때, 필요한 기능을 선택하려면 Rollout과 Reward
블록을 유지하거나 제거하세요:

| 유지된 함수 블록 | OPD 모드 | 트래젝토리 출처 | 작업 Reward |
|---|---|---|---|
| 없음 | Teacher만 | 플랫폼 | 비활성화 |
| Reward만 | Teacher + Reward | 플랫폼 | 커스텀 Reward |
| Rollout만 | Teacher + Rollout | 커스텀 Rollout | 비활성화 |
| Rollout과 Reward | Teacher + Rollout + Reward | 커스텀 Rollout | 커스텀 Reward |

기본으로 커밋된 `opd-job.yaml`은 두 블록을 모두 유지합니다. 다른 OPD 조합을
선택하려면 블록 중 하나 또는 둘 다 삭제하세요:

```yaml
teacher_model: qwen3.5-397b-a17b

functions:
# 플랫폼 생성을 사용하려면 이 블록을 삭제하세요.
- type: rollout
  # ...
# 커스텀 작업 reward를 비활성화하려면 이 블록을 삭제하세요.
- type: reward
  # ...

training:
  type: pg_opd
```

```bash
# 일반 강화학습
dashscope rl run -c rl-job.yaml

# OPD
dashscope rl run -c opd-job.yaml
```

### 4.2 함수 등록

코드를 업로드하고 함수 컴포넌트(functions)를 등록합니다.

**[SDK] [register_functions](submit_job.py)**
```python
def register_functions(self, functions: Optional[Union[List[Union[RolloutFunctionComponent, RewardFunctionComponent]], RolloutFunctionComponent, RewardFunctionComponent]] = None, lazy_load: Optional[bool] = True) -> tuple: ...
```
함수 컴포넌트를 등록합니다.

**매개변수**:
- `functions`: 등록할 함수 컴포넌트
- `lazy_load`: 실행 시점까지 로딩을 지연

**반환값**: entity/instance ID의 튜플

**예제**:
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
                classpath="functions.rollout.rollout2.DemoRolloutProcessor"),
        ),

        AgenticRLFunctionComponent(
            type=FunctionType.REWARD,
            fcmodel=FunctionComponentModel(
                classpath="functions/reward/reward.py:DemoRewardProcessor"),
        ),

        AgenticRLFunctionComponent(
            type=FunctionType.GROUP_REWARD,
            fcmodel=FunctionComponentModel(
                classpath="functions.reward.group_reward.DemoGroupRewardProcessor"),
        ),
    ],
    lazy_load=False  # 테스트를 위해 즉시 인스턴스 ID를 받으려면 False로 설정
)
```

**[CLI] register_functions**

**사용법: dashscope register_functions [OPTIONS]**
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
**예제**:
```bash
dashscope rl register_functions \
  --rollout-classpath "functions.rollout.rollout2.DemoRolloutProcessor" \
  --group-reward-classpaths "functions.reward.group_reward.DemoGroupRewardProcessor" \
  --workspace-dir "./" \
  --output-format json
```

### 4.3 함수 테스트

#### 4.3.1 원격 테스트
**[SDK] [test_functions](test_functions.py)**

등록된 인스턴스를 샘플 데이터로 테스트합니다.

```python
def test_functions(cls, instance_id: str, type: FunctionType, input_data: Dict[str, Any], api_key: str = None): ...
```

**매개변수**:
- `instance_id`: 함수 인스턴스 ID
- `type`: 함수 유형 (ROLLOUT/REWARD/GROUP_REWARD)
- `input_data`: 테스트 입력 데이터
- `api_key`: 인증용 API 키

**예제**:
```python
from dashscope.finetune.agentic_rl import AgenticRL, FunctionType

# Rollout 테스트
result = await AgenticRL.test_functions(
    instance_id=rollout_iids[0],
    functype=FunctionType.ROLLOUT,
    input_data="resouces/rollout_input.json" # JSON 파일 경로
)

# Reward 테스트
reward_input = {
    "func_type": "reward",
    "agent_output": {
        "messages": [{"role": "user", "content": "Test"}],
        "reward_score": null
    }
}
result = await AgenticRL.test_functions(
    instance_id=reward_iids[0],
    functype=FunctionType.REWARD,
    input_data=reward_input
)
```

**[CLI] test_functions**

**사용법: dashscope test_functions [OPTIONS] INSTANCE_ID**
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

**예제**:
```bash
dashscope rl test_functions "ro-ins-xxx" \
  --type rollout \
  --input "resources/rollout_input.json"
```

### 4.4 원스텝 워크플로
함수 등록, 데이터 업로드, 작업 제출을 자동으로 수행합니다.

**[SDK] [run](submit_job.py)**
```python
async def run(
    self,
    model: Optional[str] = None,
    training_datasets: Optional[List[TrainingDataset]] = None,
    validation_datasets: Optional[List[ValidationDataset]] = None,
    functions: Optional[
        Union[List[AgenticRLFunctionComponent], AgenticRLFunctionComponent]
    ] = None,
    hyper_parameters: Optional[Dict[str, str]] = None,
    resources: Optional[Dict[str, str]] = None,
    job_name: Optional[str] = None,
    teacher_model: Optional[str] = None,
    **kwargs,
) -> FineTune: ...
```
전체 워크플로 실행(등록 + 업로드 + 제출).

**매개변수**:
- `model`: 베이스 모델 이름
- `training_datasets`: 학습 데이터셋 객체
- `validation_datasets`: 검증 데이터셋 객체
- `functions`: 함수 컴포넌트
- `hyper_parameters`: 학습 하이퍼파라미터
- `resources`: 학습 리소스 설정
- `job_name`: 커스텀 작업 이름
- `teacher_model`: Teacher 모델; OPD를 활성화하며 Rollout과 Reward는 선택 사항으로 유지됨

**반환값**: `FineTune` 작업 객체

**예제**:
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
    RolloutFunctionComponent(
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
training_datasets=[
    TrainingDataset(
        data_source_type=DataSourceType.FILE_ID,
        file_name="./data/calc_train_min.jsonl",
    ),
]
validation_datasets=[
    ValidationDataset(
        data_source_type=DataSourceType.FILE_ID,
        file_name="./data/calc_validation_min.jsonl",
    ),
]
job = await rl.run(
    model="qwen3.5-9b",
    training_datasets=training_datasets,
    validation_datasets=validation_datasets,
    functions=functions,
    hyper_parameters={'batch_size': '128'}
)
```

**[CLI] run**

**사용법: dashscope rl run [OPTIONS]**
```bash
 🚀 Launch the complete RL tuning workflow (function registration → dataset upload → job submission)

 Execution modes:
 1. Configuration-driven: Use -c/--config to specify a YAML file
 2. Direct parameter: Provide all required arguments via CLI options

 Required parameters:
 - training_files (at least one)
 - Rollout and Reward are required for reinforcement learning, but optional for OPD.

╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --config                   -c      PATH   Path to YAML configuration file                                                                                                                                            │
│ --model                            TEXT   Base model identifier                                                                                                                                                      │
│ --teacher-model                    TEXT   Enable OPD and override the Teacher model in YAML; Rollout and Reward are optional                                                                                          │
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
│ --hyper-parameters                 TEXT   JSON string of hyper_parameters                                                                                                                                             │
│ --job-name                         TEXT   Custom name for the tuning job                                                                                                                                             │
│ --api-key                          TEXT   DashScope API Key (uses DASHSCOPE_API_KEY env var if omitted) [env var: DASHSCOPE_API_KEY]                                                                                 │
│ --workspace-dir                    TEXT   Workspace directory for job artifacts [default: ./]                                                                                                                        │
│ --output-format            -o      TEXT   Output format: table|json|yaml [default: table]                                                                                                                            │
│ --verbose                  -v             Enable detailed error traces                                                                                                                                               │
│ --help                                    Show this message and exit.                                                                                                                                                │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

**예제**: 전체 워크플로 실행 (자동)
```bash
dashscope rl run \
  --config "rl-job.yaml" \
  --verbose
```

### 4.5 작업 관리

**[SDK] get**
```python
def get(cls, job_id: str, api_key: str = None, workspace: str = None, **kwargs) -> FineTune: ...
```
작업 정보를 가져옵니다.

**매개변수**:
- `job_id`: 조회할 작업 ID
- `api_key`: 인증용 API 키
- `workspace`: 작업 공간 식별자

**예제**:
```python
from dashscope.finetune.agentic_rl import AgenticRL
job = AgenticRL.get("job-12345")
```

**[CLI] get**

**사용법: dashscope get [OPTIONS] JOB_ID**
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

**예제**:
```bash
dashscope rl get "$JOB_ID" -o json
```

**[SDK] cancel**
```python
def cancel(cls, job_id: str, api_key: str = None, workspace: str = None, **kwargs) -> FineTuneCancel: ...
```
실행 중인 작업을 취소합니다.

**매개변수**:
- `job_id`: 취소할 작업 ID
- `api_key`: 인증용 API 키
- `workspace`: 작업 공간 식별자

**예제**:
```python
from dashscope.finetune.agentic_rl import AgenticRL
AgenticRL.cancel("job-12345")
```

**[CLI] cancel**

**사용법: dashscope cancel [OPTIONS] JOB_ID**
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

**예제**:
```bash
dashscope rl cancel "$JOB_ID"
```

---

## 5. CLI 레퍼런스

CLI는 SDK 기능을 그대로 반영합니다. 자세한 내용은 `dashscope rl --help`를 사용하세요.

### 사용법: dashscope [OPTIONS] COMMAND [ARGS]...
```bash

 🚀 Agentic RL Fine-Tuning CLI

╭─ Options ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                                                                                                                                                     │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ register_functions  🧩 Register Rollout/Reward function components, returns entity_id & instance_id                                                                                                             │
│ test_functions      🧪 Test a registered Rollout/Reward function instance with custom input data.                                                                                                               │
│ upload_data         📦 Upload training/validation datasets to the platform, returns file IDs                                                                                                                    │
│ submit              📤 Submit fine-tuning job (requires pre-registered functions & uploaded datasets)                                                                                                                 │
│ run                 🚀 Launch the complete RL tuning workflow (function registration → dataset upload → job submission)                                                                                         │
│ status              📊 Query the current status and metadata of a specific job                                                                                                                                  │
│ list                📋 List historical fine-tuning jobs with pagination                                                                                                                                         │
│ cancel              🛑 Cancel a running job                                                                                                                                                                     │
│ delete              🗑️ Delete a job record (releases metadata)                                                                                                                                                  │
│ logs                📜 Fetch job execution logs (supports pagination)                                                                                                                                           │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

---

## 6. FAQ 및 문제 해결

**질문: 함수 등록이 실패합니다.**
*   **확인**: classpath(`module.path:ClassName`)가 올바른가요?
*   **확인**: 작업 공간 루트에 `requirements.txt`가 존재하나요?
*   **확인**: 모든 의존성이 `requirements.txt`에 나열되어 있나요?

**질문: 작업 제출이 실패합니다.**
*   **확인**: Entity ID와 File ID가 유효한가요?
*   **확인**: 베이스 모델이 해당 리전에서 사용 가능한가요?
*   **확인**: `reward_runtimes` 리스트 길이가 `reward_ids` 리스트 길이와 일치하나요?

**질문: 성능을 최적화하려면 어떻게 해야 하나요?**
*   I/O 바운드 작업에는 `async def process`를 사용하세요.
*   CPU/메모리 여유가 있다면 런타임 설정의 `concurrency`를 늘리세요.
*   관측성 페이로드를 적절한 범위로 유지하세요(과도한 입출력 캡처를 피해 오버헤드를 줄이세요).

**질문: 트레이스는 어디에서 확인할 수 있나요?**
*   Bailian(百炼) 콘솔에서 ARMS 인증을 완료하면 트레이스가 **ARMS**로 전송됩니다. `requirements.txt`에 관측성 의존성이 포함되어 있고, 관측성 API(`observe_processor`, `trace_client`, `trace_tool` 등)를 사용하고 있는지 확인하세요.
