# DashScope SDK Expert — 설정 기반 acli 예제

> [English](README.md) | [中文](README_zh.md) | [日本語](README_ja.md) | [Español](README_es.md) | **한국어**

**온라인 가이드**: https://help.aliyun.com/en/model-studio/dashscope-sdk-expert

이 예제는 **AgenticCLI(acli)**의 네이티브 설정 메커니즘을 사용하여 특정 시나리오에 특화된 AI 전문가 에이전트를 만드는 방법을 보여줍니다.

**핵심 아이디어: 설정 기반, Python 접착 코드 불필요.** 에이전트의 정체성, 능력, skill, 지식 색인은 모두 `.acli/` 아래의 파일로 정의됩니다. 예제를 다운로드하고 `acli`를 바로 실행하면 시작됩니다.

## 디렉터리 구조

```
dashscope-sdk-expert/
└── .acli/                      # 에이전트 설정 디렉터리
    ├── config.toml              # 모델 및 사용자 설정
    ├── custom-extensions.toml   # Provider 선언(tongyi)
    ├── hooks.toml               # 이벤트 훅
    ├── system-prompt.md         # System prompt(에이전트 페르소나와 행동 규칙)
    └── skills/                  # skill 템플릿(use_skill을 통해 모델이 필요 시 로드)
        ├── text-generation.md   # 텍스트 생성(Generation / OpenAI 호환, Python+Java)
        ├── multimodal.md        # 멀티모달(MultiModalConversation/ImageSynthesis/VideoSynthesis)
        ├── speech.md            # 음성(SpeechSynthesizer/Transcription)
        ├── retrieval.md         # 검색(Embedding/TextReRank/RAG)
        ├── fine-tuning.md       # 파인튜닝과 배포(SFT/CPT/DPO/Deployments)
        ├── agent.md             # 에이전트(Application/Assistants/플러그인과 MCP)
        ├── cli.md               # dashscope CLI 명령어 참고
        ├── sdk-example.md       # SDK 코드 예제 생성
        ├── api-doc.md           # API 파라미터 문서 조회
        ├── diagnose.md          # SDK 호출 오류 진단
        ├── error-code.md        # 오류 코드 설명
        ├── explain-code.md      # 코드 로직 설명
        └── translate.md         # 중국어-영어 번역
```

## 빠른 시작

```bash
pip install acli
export DASHSCOPE_API_KEY="sk-xxx"

# 예제를 ./.acli/ 에 병합합니다(동일한 이름의 파일은 .acli/backup/ 에 자동 백업되며, example restore로 되돌릴 수 있습니다)
acli example download dashscope-sdk-expert

# 시작 — cd도, Python 실행 스크립트도 필요 없습니다
acli
acli --tui
acli -c "How do I use Generation.call?"
```

## 설정 기반 접근 방식의 작동 원리

### 1. system-prompt.md — 에이전트 페르소나

에이전트의 정체성, 지식 범위, 행동 규칙을 정의합니다. 에이전트가 "누구인지"의 핵심입니다:

```markdown
You are DashScope SDK Expert, an intelligent assistant for the DashScope Python SDK...

## Grounded Knowledge First
Before answering, ALWAYS verify against the actual installed SDK...
```

### 2. skills/ — 필요 시 로드되는 도메인 지식 베이스

SDK/CLI의 공개 인터페이스 지식은 도메인별 skill에 직접 저장됩니다: 도메인마다 파일이 하나씩 있으며, 모델 목록, Python 및 Java SDK 시그니처, 입출력 구조, 오류 코드를 담고 있습니다. API 관련 질문에 답할 때 모델은 `use_skill`을 통해 해당 skill을 필요 시 로드합니다 — **system prompt에 상주하는 내용은 전혀 없습니다** — 이를 통해 첫 턴의 입력 토큰을 약 16,000자 줄입니다. skill로 다루지 않는 세부 사항은 설치된 패키지에 대한 `inspect.signature` / `help()`로 대체됩니다.

### 3. skills/ — 작업 템플릿

각 `.md` 파일은 frontmatter 메타데이터가 포함된 재사용 가능한 프롬프트 템플릿입니다:

```yaml
---
name: sdk-example
description: Generate runnable DashScope SDK code examples
arguments: [api_name]
---

Before generating code, first verify the user's installed SDK version and API signature:
1. `run_command("python -c 'import dashscope; ...'")`
...
```

- **name**: skill 식별자, `/skill` 명령으로 호출됩니다
- **description**: 짧은 설명; 에이전트가 이를 보고 이 skill을 언제 적용할지 판단합니다
- **arguments**: 템플릿 변수, 호출 시 실제 값으로 대체됩니다

### 4. config.toml — 런타임 설정

```toml
user_name = "dashscope"
provider = "tongyi"
model = "qwen3.8-max"
memory_user_id = "acli-dashscope"
```

## 이 패턴 재사용하기

자신의 시나리오를 위한 AI 전문가를 만들려면:

1. `acli example download dashscope-sdk-expert`(프로젝트의 `./.acli/`에 병합됩니다)
2. `.acli/system-prompt.md`를 수정 — 자신의 에이전트 페르소나를 정의합니다
3. `.acli/skills/`를 수정 — 자신의 도메인 지식과 skill 템플릿을 추가합니다(모델이 필요 시 로드)
4. `.acli/config.toml`을 수정 — 적절한 모델을 선택합니다
5. `acli`를 실행합니다

## 설계 요점

| 전통적인 방식 | acli의 설정 기반 방식 |
|---------|---------------|
| 코드에 하드코딩된 prompt | `system-prompt.md` 파일 |
| 시나리오별 if-else 분기 | `skills/*.md` 템플릿 라이브러리 |
| 거대한 문서 전체를 prompt에 밀어넣음 | `skills/`의 도메인 지식을 필요 시 로드 |
| 동작을 바꾸려면 코드 수정 필요 | Markdown만 수정하면 됨 |
| 공유와 재사용이 어려움 | `.acli/` 디렉터리 전체가 이식 가능 |
