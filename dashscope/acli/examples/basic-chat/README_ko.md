# Basic Chat — 최소한으로 동작하는 acli 예제

> [English](README.md) | [中文](README_zh.md) | [日本語](README_ja.md) | [Español](README_es.md) | **한국어**

최소한의 설정으로 웹 검색 기능을 갖춘 범용 채팅 에이전트를 시작하는 방법을 보여줍니다. **모든 지능은 `.acli/` 설정에 담겨 있으며, Python 시작 코드는 전혀 없습니다** — `acli`를 다운로드해서 바로 실행하면 됩니다.

## 디렉터리 구조

```
basic-chat/
└── .acli/
    ├── config.toml                   # 기본 provider/model/user_name
    ├── custom-extensions.toml        # tongyi provider 선언 + capability/skill/shell_tool 주석 템플릿
    ├── hooks.toml                    # 이벤트 훅(before/after_tool_call, on_error 등) 주석 템플릿
    ├── system-prompt.md              # 에이전트 페르소나와 행동 규칙
    └── skills/
        ├── research-topic.md         # 주제를 웹 검색하여 브리핑 작성(web_search 호출)
        ├── explain-code.md           # 코드 로직 설명
        ├── translate.md              # 중국어-영어 번역
        └── write-poem.md             # 칠언절구 작성(순수 프롬프트 템플릿 예시)
```

## 빠른 시작

```bash
pip install acli
export DASHSCOPE_API_KEY="sk-xxx"

# 예제를 ./.acli/ 에 병합합니다(동일한 이름의 파일은 .acli/backup/ 에 자동 백업되며, example restore로 되돌릴 수 있습니다)
acli example download basic-chat

# 필요한 provider를 추가하려면 .acli/custom-extensions.toml을 수정하세요
# 에이전트 페르소나를 정의하려면 .acli/system-prompt.md를 수정하세요
# .acli/skills/ 아래에 자신만의 skill 템플릿을 추가하세요

# 시작(cd 불필요, 설정이 이미 현재 디렉터리에 있습니다)
acli
acli --tui
acli -c "hello"
```

> 새 디렉터리에서 사용하고 싶다면? `mkdir my-agent && cd my-agent && acli example download basic-chat`를 실행하거나,
> `acli example download basic-chat --target my-agent`를 사용하세요.

## 프로그램으로서의 설정

### custom-extensions.toml — Provider 선언

acli가 사용할 수 있는 LLM provider를 선언합니다. 최소 설정은 `[[providers]]` 블록 하나만 있으면 됩니다:

```toml
[[providers]]
name = "tongyi"
base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
api_key_env = "DASHSCOPE_API_KEY"      # ← 환경 변수 이름만 저장하며, sk-xxx는 셸에서 제공됩니다
default_model = "qwen3.8-max"
models = ["qwen3.8-max", "qwen3.7-max", "qwen3.7-plus", "qwen-turbo", "qwen-vl-max"]
vision_models = ["qwen-vl-max"]        # ← 이 모델들이 이미지 입력을 받을 수 있음을 acli에 알려줍니다
protocol = "openai"                     # ← openai / anthropic / dashscope
```

Claude / GPT / 로컬 Ollama를 사용하고 싶다면, toml에서 해당 `[[providers]]` 블록의 주석을 해제하면 됩니다.

**API Key를 제공하는 세 가지 방법**(권장 순서대로):

1. `api_key_env = "FOO_API_KEY"` — 셸에서 `export FOO_API_KEY=sk-xxx` 실행; toml을 git에 안전하게 커밋할 수 있습니다
2. `/provider` 대화형 마법사 — `api_key = "ENC:..."`(기기에 종속된 암호화)를 기록합니다
3. 평문 `api_key = "sk-xxx"` — 로더에 의해 거부됩니다; 자리 표시용 예시일 뿐입니다

### system-prompt.md — 에이전트 페르소나

에이전트가 "누구인지"를 정의합니다. acli는 시작 시 `.acli/system-prompt.md`를 자동으로 로드합니다(워크스페이스 설정이 `~/.acli/system-prompt.md`보다 우선합니다).

### skills/*.md — 프롬프트 템플릿

각 `.md` 파일은 YAML frontmatter가 포함된 재사용 가능한 프롬프트입니다:

```yaml
---
name: research-topic
description: Web-search a topic and produce a briefing with source URLs
arguments: [topic]
---

Use the web_search tool to research "{topic}":
...
```

호출 방법:
- `/skill research-topic quantum computing` — 명시적 호출
- 자연어: "help me research the latest progress in quantum computing" — LLM이 사용 여부를 판단합니다

`research-topic`은 프롬프트를 사용하여 LLM이 내장된 `web_search` 도구를 호출해 온라인 정보를 수집하도록 유도하는 방법을 보여줍니다.

### config.toml — 기본값

```toml
user_name = "dashscope"
provider = "tongyi"
model = "qwen3.8-max"
memory_user_id = "acli-basic"
```

## 다음 단계

- **더 많은 provider 추가**: `custom-extensions.toml`에 `[[providers]]` 블록을 추가하세요
- **HTTP 도구 추가**: `[[capabilities]]` + `[[capabilities.tools]]` 블록을 추가하세요(예: 이미지 생성, 원격 워크플로 엔진 호출)
- **비전 기능 추가**: `type = "vision"`인 capability 도구를 추가하여 텍스트 에이전트가 필요할 때 비전 LLM을 호출할 수 있게 하세요
- **셸 도구 추가**: 자주 쓰는 로컬 명령을 감싸는 `[[shell_tools]]` 블록을 추가하세요
- **훅 추가**: `.acli/hooks.toml`에서 도구 호출 전/후 훅을 설정하세요(예: `.py` 파일 작성 후 자동 `py_compile`, `pip install` 전 확인, 파일 삭제 차단). `.acli/hooks.toml`의 템플릿을 참고하세요. 5가지 이벤트(`before_tool_call` / `after_tool_call` / `on_error` / `on_message` / `on_response`) × 6가지 액션(run/block/confirm/warn/alert/log)을 모두 다룹니다.
- **영구 지식 추가**: system prompt에 **항상** 표시되어야 하는 문서(예: API 색인)를 `.acli/references/*.md`에 두세요
- **페르소나 변경**: `system-prompt.md`를 수정하세요 — 예를 들어 "코드 리뷰어", "데이터 분석가", "고객 지원 담당자"로 바꿀 수 있습니다

전체 기능 문서는 프로젝트 루트의 `README.md`를 참고하세요.
