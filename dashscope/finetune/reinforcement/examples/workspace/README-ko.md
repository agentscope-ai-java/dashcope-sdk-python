# Agentic RL SDK/CLI 사용 가이드 [[English]](./README.md) [[中文]](./README-zh.md) [[日本語]](./README-ja.md) [[Español]](./README-es.md)

## 1. SDK 설치

```bash
pip install dashscope>=1.25.19
```

## 2. 환경 설정

### 2.1 환경 변수 설정

```bash
# 필수: API 키 (코드에서도 초기화 가능: AgenticRL(api_key="for your api key") )
export DASHSCOPE_API_KEY="your_api_key_here"

# 선택: 로그 레벨 설정 info/debug/warning/critical (기본값 info)
export LOG_LEVEL="info"
```

### 2.2 의존성 파일 구성

> 참고: `requirements.txt`는 원격 Function Compute 환경(Python >= 3.10)에서 사용됩니다. 로컬 디버깅 시에는 Python 3.10+ 를 사용해야 합니다. `dashscope` SDK 자체는 Python 3.8+ 를 지원합니다.

다음 핵심 의존성을 포함하는 `requirements.txt` 파일을 생성합니다:

```requirements.txt
# 기본 (필수)
dashscope>=1.25.19

# 프레임워크 의존성
fastapi==0.136.0
uvicorn==0.45.0
# ...

# 트래젝토리(trajectory) 함수 의존성
langchain-core==1.3.0
langchain-mcp-adapters==0.2.2
langchain-openai==1.2.0
# ...

# 기타 커스텀 의존성 추가...
```

## 3. 함수 개발 및 데이터 준비

### 3.1 함수 컴포넌트 생성

`functions` 디렉터리 아래에 함수를 개발합니다:

- **Reward 함수 템플릿**:
    - `functions/reward/reward.py` - 기본 구현
    - `functions/reward/reward_decorator.py` - 데코레이터 구현
- **Rollout 함수 템플릿**:
    - `functions/rollout/rollout.py` - 기본 구현

> 참고: `functions/` 디렉터리에는 `__init__.py` 파일이 반드시 포함되어야 합니다

필요한 함수 컴포넌트는 선택한 학습 설정에 따라 달라집니다:

| 설정 | 모드 | 커스텀 Rollout | 커스텀 Reward |
|---|---|---:|---:|
| `rl-job.yaml` | 일반 강화학습 | 필수 | 최소 1개 |
| 함수 블록이 없는 `opd-job.yaml` | Teacher만 | 아니요 | 아니요 |
| Reward만 있는 `opd-job.yaml` | Teacher + Reward | 아니요 | 예 |
| Rollout만 있는 `opd-job.yaml` | Teacher + Rollout | 예 | 아니요 |
| 두 블록 모두 있는 `opd-job.yaml` | Teacher + Rollout + Reward | 예 | 예 |

### 3.2 학습 데이터 준비

`data` 디렉터리 아래에 데이터셋 파일을 추가합니다:

- `data/calc_training_min.jsonl` - 학습 데이터셋 (JSONL 형식)
- `data/calc_validation_min.jsonl` - 검증 데이터셋 (JSONL 형식)

## 4. SDK로 작업 실행

### 4.1 함수 실행 (등록 + 테스트)

일반 강화학습에는 커스텀 Rollout과 최소 1개의 Reward가 필요합니다. OPD의
경우 Rollout과 Reward는 선택 사항입니다.

```bash
python test_functions.py
```

### 4.2 워크플로 실행 (YAML 설정 + 라이프사이클 관리)

일반 강화학습과 OPD는 동일한 SDK 워크플로를 사용합니다. 해당하는 YAML을
선택하세요:

```python
from dashscope.finetune.agentic_rl import AgenticRL

client = AgenticRL()
# 일반 강화학습에는 rl-job.yaml을, OPD에는 opd-job.yaml을 사용합니다
client.init(config_path="rl-job.yaml")
result = await client.run()
```

`opd-job.yaml`은 기본적으로 두 함수 블록을 모두 유지하며, 이는 Teacher +
Rollout + Reward를 의미합니다. Reward 블록을 제거하면 Teacher + Rollout,
Rollout 블록을 제거하면 Teacher + Reward, 둘 다 제거하면 Teacher만 남습니다.

```bash
# submit_job.py는 기본적으로 일반 강화학습용 rl-job.yaml을 사용합니다
python submit_job.py
```

## 5. CLI로 작업 실행
예제 코드: cli.sh

`cli.sh`는 일반 강화학습 워크플로를 보여줍니다. OPD의 경우 `opd-job.yaml`에서
제거된 함수 블록에 대한 등록과 테스트는 건너뛰며, 데이터셋 제출, `rl run`,
작업 라이프사이클 명령은 변경되지 않습니다.

CLI는 SDK와 동일한 YAML 파일을 사용합니다:

```bash
# 일반 강화학습
dashscope rl run -c rl-job.yaml

# OPD
dashscope rl run -c opd-job.yaml

# opd-job.yaml에 설정된 Teacher를 재정의
dashscope rl run -c opd-job.yaml \
  --teacher-model qwen3.5-397b-a17b
```

```bash
dashscope rl --help  # 전체 명령어 도움말 보기

 Usage: dashscope [OPTIONS] COMMAND [ARGS]...

 🚀 Agentic RL Fine-Tuning CLI

╭─ Options ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                                                                                                                                                     │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ register_functions  🧩 Register Rollout/Reward function components, returns entity_id & instance_id                                                                                                             │
│ test_functions      🧪 Test a registered Rollout/Reward function instance with custom input data.                                                                                                               │
│ upload_data         📦 Upload training/validation datasets to the platform, returns file IDs                                                                                                                    │
│ run                 🚀 Launch the complete RL tuning workflow (function registration → dataset upload → job submission)                                                                                         │
│ get                 📊 Query the current status and metadata of a specific job                                                                                                                                  │
│ list                📋 List historical fine-tuning jobs with pagination                                                                                                                                         │
│ cancel              🛑 Cancel a running job                                                                                                                                                                     │
│ delete              🗑️ Delete a job record (releases metadata)                                                                                                                                                  │
│ logs                📜 Fetch job execution logs (supports pagination)                                                                                                                                           │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

## 모범 사례 팁

1. **개발 및 테스트**: 제출 전 `test_functions` 명령으로 함수 로직을 검증하세요
2. **점진적 개발**: 수정 후 함수를 다시 등록하기만 하면 되며, 전체 환경을 재구축할 필요가 없습니다
3. **로그를 통한 문제 해결**: 자세한 디버그 정보를 얻으려면 `LOG_LEVEL=debug`로 설정하세요
4. **리소스 관리**: 작업 완료 후 `delete` 명령으로 리소스를 해제하세요

> 참고: 모든 경로와 매개변수는 실제 프로젝트에 맞게 조정해야 하며, 예제 스크립트는 프로젝트의 `workspace/`
> 디렉터리에 있습니다
>
> 참고: 프로젝트의 `workspace/` 디렉터리 아래의 모든 파일은 패키징되어 온라인 연산을 위해 클라우드에
> 업로드됩니다. 데이터 보안에 유의하세요
>
> 참고: 프로젝트의 `workspace/` 디렉터리에서 업로드 시 제외할 하위 디렉터리와 파일을 설정하려면 환경 변수를
> 참고하세요: `FC_ZIP_EXCLUDE_PATTERNS`
>
> 참고: 프로젝트의 `workspace/` 디렉터리 아래 모든 파일을 패키징하여 업로드할 때의 전체 크기 제한은 200M이며,
> 환경 변수 `FC_OSS_FILE_SIZE_WARNING`으로 수정할 수 있습니다
>
> 참고: 단일 데이터셋 파일(예: 학습/검증 JSONL)의 기본 최대 크기는 1G이며, 환경 변수
> `DATASETS_FILE_SIZE_WARNING`으로 수정할 수 있습니다
>
> 참고: 로컬에서 빌드한 dashscope whl 패키지(scripts/build.sh 스크립트로 생성)를 사용하려면 다음과 같이 설정하세요:
> export FC_PYPI_LIB="dashscope-1.25.19-py3-none-any.whl"
> 그리고 프로젝트 루트의 workspace/workspace/ 디렉터리에 배치하세요. 또한 `requirements.txt`에서 dashscope 의존성을 제거하세요.
