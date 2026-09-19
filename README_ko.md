# DashScope Python SDK

> [English](README.md) | [中文](README_zh.md) | [日本語](README_ja.md) | [Español](README_es.md) | **한국어**

DashScope Python SDK는 [Alibaba Cloud Model Studio(Bailian)](https://www.alibabacloud.com/help/en/model-studio/) API에 대한 포괄적인 인터페이스를 제공하며, 텍스트 생성, 멀티모달 이해, 임베딩, 리랭킹, 이미지/영상 생성, 음성 합성 및 인식 등을 다룹니다.

## 새로운 소식

**v1.27.0에 대화형 AI 어시스턴트인 [DashScope SDK Expert](#ai-어시스턴트-dashscope-sdk-expert)가 탑재되었습니다.** 인수 없이 `dashscope`를 실행하거나(또는 `dashscope "how do I stream Generation output"`처럼 직접 질문하면) 터미널에서 바로 SDK/API 답변, 실행 가능한 예제, CLI 사용법, 오류 진단을 받을 수 있습니다. 안내 내용은 SDK의 공개 인터페이스(파라미터, 출력, 오류 코드)를 기반으로 한 도메인별 빠른 참조 스킬(텍스트, 멀티모달, 음성, 검색, 파인튜닝, 에이전트, cli)에서 생성되므로, 문서를 읽는 대신 바로 질문할 수 있습니다. 어시스턴트 안에서 `/help`를 입력하면 사용 가능한 명령어를 확인할 수 있습니다.

## 설치
DashScope Python SDK를 설치하려면 다음을 실행하세요:
```shell
pip install dashscope
```

기본 설치에는 SDK API 호출과 `dashscope` CLI 명령이 포함됩니다.
선택적 기능 그룹은 extras 형태로 제공됩니다:

| Extra | 제공 기능 | 설치 |
|-------|----------|---------|
| `acli` | 대화형 AI 어시스턴트 (DashScope SDK Expert) | `pip install "dashscope[acli]"` |
| `rl` | Agentic RL 파인튜닝 | `pip install "dashscope[rl]"` |
| `tokenizer` | 다운로드가 필요 없는 로컬 tokenizer | `pip install "dashscope[tokenizer]"` |

GitHub에서 코드를 클론했다면 소스에서 설치할 수 있습니다:
```shell
pip install -e .
```


## 빠른 시작

```python
# pip install dashscope
from http import HTTPStatus
from dashscope import Generation

responses = Generation.call(
    model="qwen-plus",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Who are you?"},
    ],
    result_format="message",
)

if responses.status_code == HTTPStatus.OK:
    print(responses.output.choices[0].message.content)
else:
    print(f"Error: {responses.code} - {responses.message}")
```

### 스트리밍 출력

`stream=True`를 전달하면 점진적인 응답을 반환하는 제너레이터를 얻을 수 있습니다.
`incremental_output=True`를 설정하면 각 청크에는 지금까지 누적된 전체 텍스트가
아니라 새로 생성된 토큰만 포함됩니다:

```python
from dashscope import Generation

responses = Generation.call(
    model="qwen-plus",
    messages=[{"role": "user", "content": "바다에 관한 하이쿠를 써줘."}],
    result_format="message",
    stream=True,
    incremental_output=True,
)
for response in responses:
    print(response.output.choices[0].message.content, end="")
```

### 비동기 (asyncio)

`call` 기반 클래스에는 동일한 파라미터를 가진 `Aio` 접두사가 붙은 비동기
버전이 마련되어 있습니다（`AioGeneration`, `AioImageSynthesis`,
`AioMultiModalConversation`, `AioVideoSynthesis`, `AioMultiModalEmbedding`,
`AioTextReRank` 등）. `await`와 함께 사용합니다:

```python
import asyncio
from dashscope import AioGeneration

async def main():
    response = await AioGeneration.call(
        model="qwen-plus",
        messages=[{"role": "user", "content": "Who are you?"}],
        result_format="message",
    )
    print(response.output.choices[0].message.content)

asyncio.run(main())
```

### 함수 호출

`tools`를 통해 OpenAI 스타일의 도구 정의를 전달합니다. 모델은 `message.tool_calls`를 통해 호출을 요청하고, 이를 당신의 코드가 실행한 뒤 결과를 다시 전달합니다:

```python
from dashscope import Generation

tools = [{
    "type": "function",
    "function": {
        "name": "get_current_weather",
        "description": "특정 도시의 현재 날씨를 가져옵니다.",
        "parameters": {
            "type": "object",
            "properties": {"location": {"type": "string", "description": "도시 이름."}},
            "required": ["location"],
        },
    },
}]
response = Generation.call(
    model="qwen-plus",
    messages=[{"role": "user", "content": "항저우 날씨는 어때요?"}],
    tools=tools,
    result_format="message",
)
tool_call = response.output.choices[0].message.tool_calls[0]
print(tool_call.function.name, tool_call.function.arguments)
```

### 사고 모드

하이브리드 사고 모델은 `enable_thinking`(`stream=True` 필요)을 통해 추론 과정을 최종 답변과 별도로 노출할 수 있습니다. 추론 내용은 `message.reasoning_content`에, 최종 답변은 `message.content`에 담깁니다:

```python
from dashscope import Generation

responses = Generation.call(
    model="qwen-plus",
    messages=[{"role": "user", "content": "1.1과 0.9 중 어느 것이 더 큽니까?"}],
    result_format="message",
    enable_thinking=True,
    incremental_output=True,
    stream=True,
)
for response in responses:
    message = response.output.choices[0].message
    print(message.get("reasoning_content") or message.content, end="")
```

### 오류 처리

필수 인자가 누락된 경우（예: `model` 미지정, `messages`/`prompt` 미지정,
API Key 미설정）즉시 `DashScopeException`의 하위 클래스가 발생합니다.
반면 API 수준의 실패（잘못된 모델 이름, 요청 제한 등）는 예외를 발생시키지
않고 응답에 담겨 반환되므로 `status_code`를 확인해야 합니다:

```python
from http import HTTPStatus
from dashscope import Generation
from dashscope.common.error import DashScopeException

try:
    response = Generation.call(model="qwen-plus", messages=[{"role": "user", "content": "Hi"}])
except DashScopeException as e:
    # 잘못된 입력일 때 로컬에서 발생, 예: InputRequired, ModelRequired, AuthenticationError
    print(f"Invalid request: {e}")
else:
    if response.status_code != HTTPStatus.OK:
        # API에서 반환되는 오류, 예: 잘못된 모델, 요청 제한, 할당량 초과
        print(f"API error {response.status_code}: {response.code} - {response.message}")
    else:
        print(response.output.choices[0].message.content)
```

전체 예외 클래스 목록과 각각이 발생하는 조건은 [오류 처리 참조 문서](docs/guides/error-handling_ko.md)를 참고하세요.

## API Key 인증

이 SDK는 인증을 위해 API Key를 사용합니다. API Key를 얻는 방법은 [API Key 발급 방법](https://help.aliyun.com/en/model-studio/get-api-key)을 참고하세요. API Key 발급에 관한 자세한 내용은 [Alibaba Cloud 공식 문서(중국 사이트)](https://www.alibabacloud.com/help/en/model-studio/) 및 [Alibaba Cloud 공식 문서(국제 사이트)](https://www.alibabacloud.com/help/en/model-studio/)를 참고하세요.

### API Key 사용하기

1. 코드에서 API Key 설정하기
```python
import dashscope

dashscope.api_key = 'YOUR-DASHSCOPE-API-KEY'
# 또는 코드에서 API Key 파일 경로를 지정
# dashscope.api_key_file_path='~/.dashscope/api_key'

```

2. 환경 변수로 API Key 설정하기

```shell
# a. API Key를 직접 설정
export DASHSCOPE_API_KEY='YOUR-DASHSCOPE-API-KEY'

# b. 또는 키가 담긴 파일 경로를 지정
export DASHSCOPE_API_KEY_FILE_PATH='~/.dashscope/api_key'
```

두 환경 변수 중 하나만 설정해도 `Generation.call(...)`（및 다른 모든 SDK 호출）이 자동으로 키를 읽어오므로 `api_key=` 인자를 넘길 필요가 없습니다:

```python
from dashscope import Generation

# DASHSCOPE_API_KEY（또는 DASHSCOPE_API_KEY_FILE_PATH）가 자동으로 로드됩니다
response = Generation.call(model="qwen-plus", messages=[{"role": "user", "content": "Hi"}])
print(response.output.choices[0].message.content)
```

3. API Key를 파일에 저장하기
```python
from dashscope import save_api_key

save_api_key(api_key='YOUR-DASHSCOPE-API-KEY',
             api_key_file_path='api_key_file_location or (None, will save to default location "~/.dashscope/api_key"')

```

## 리전 및 엔드포인트 구성

기본적으로 SDK는 중국(베이징) 공개 엔드포인트인 `dashscope.aliyuncs.com`으로 요청을 보냅니다. Model Studio(Bailian) 워크스페이스가 다른 리전에 있다면, 호출 전에 엔드포인트를 전환하세요.

### `set_region` 사용하기

`dashscope.set_region(region, workspace_id)`는 한 번의 호출로 HTTP, WebSocket, OpenAI 호환 base URL을 지정한 리전으로 향하게 합니다. `workspace_id`는 필수이며 엔드포인트의 서브도메인으로 사용됩니다.

```python
import dashscope

# 워크스페이스 "ws-xxx123"에 대해 싱가포르 리전으로 전환
dashscope.set_region(region="ap-southeast-1", workspace_id="ws-xxx123")

# 이후 모든 호출은 다음을 사용합니다:
#   https://ws-xxx123.ap-southeast-1.maas.aliyuncs.com/api/v1
print(dashscope.base_http_api_url)
```

지원되는 리전:

| 리전 | 위치 |
|--------|----------|
| `cn-beijing` | 중국(베이징) |
| `cn-hongkong` | 중국(홍콩) |
| `ap-southeast-1` | 싱가포르 |
| `ap-northeast-1` | 일본(도쿄) |
| `eu-central-1` | 독일(프랑크푸르트) |
| `us-east-1` | 미국(버지니아) |

> **API Key는 리전마다 다릅니다.** 각 리전은 해당 리전의 Model Studio 콘솔에서 발급되는 자체 API Key（`sk-` 접두사）를 가지며, 리전 간에 혼용할 수 없습니다 — 다른 리전의 키를 사용하면 `401` 오류가 발생합니다. 리전을 전환할 때는 `api_key`도 함께 변경하세요.

리전별 참고 사항:

- WebSocket 엔드포인트（`wss://.../api-ws/v1/inference`）는 현재 `cn-beijing`과 `ap-southeast-1`에서만 제공됩니다. `set_region`은 모든 리전에서 `base_websocket_api_url`을 설정하지만, WebSocket 기반 실시간 API（실시간 음성 인식/합성, 멀티모달 대화 등）는 다른 리전에서는 사용할 수 없습니다.
- `eu-central-1` / `ap-northeast-1`: 배포 범위（글로벌 또는 EU / 일본）는 콘솔에서 워크스페이스를 생성할 때 선택하며, API 호출마다 지정하는 것이 아닙니다.
- `us-east-1`: `-us` 접미사가 붙은 모델 이름（예: `qwen-plus-us`）은 추론을 미국 내로 제한합니다. 접미사가 없으면 기본적으로 글로벌 추론을 사용합니다.
- 배치 추론, 모델 파인튜닝, 애플리케이션 개발은 현재 `cn-beijing`과 `ap-southeast-1`에서만 사용할 수 있습니다.

> `set_region`은 프로세스 전역 변수를 수정하므로, 하나의 프로세스가 동시에 여러 리전과 통신하는 경우 동시성에 안전하지 않습니다. 시작 시 한 번만 호출하거나, 전환할 때마다 다시 호출하세요.

### 환경 변수 사용하기

코드를 작성하지 않고도 환경 변수만으로 리전을 선택할 수 있습니다:

```shell
export DASHSCOPE_API_REGION='ap-southeast-1'   # 기본값: cn-beijing
export DASHSCOPE_WORKSPACE_ID='ws-xxx123'      # 엔드포인트 서브도메인 해석에 사용
```

```python
import dashscope

# DASHSCOPE_API_REGION / DASHSCOPE_WORKSPACE_ID를 자동으로 읽어옵니다
print(dashscope.base_http_api_url)
# https://ws-xxx123.ap-southeast-1.maas.aliyuncs.com/api/v1
```

`DASHSCOPE_API_REGION`으로 MaaS 리전이 설정되면, SDK는 해당 리전의 엔드포인트를 구성하고 그 안에 `DASHSCOPE_WORKSPACE_ID`를 대입합니다. 각 base URL을 직접 재정의할 수도 있습니다:

| 환경 변수 | 재정의 대상 |
|----------------------|-----------|
| `DASHSCOPE_HTTP_BASE_URL` | HTTP 엔드포인트（`dashscope.base_http_api_url`） |
| `DASHSCOPE_WEBSOCKET_BASE_URL` | WebSocket 엔드포인트（`dashscope.base_websocket_api_url`） |
| `DASHSCOPE_COMPATIBLE_BASE_URL` | OpenAI 호환 엔드포인트（`dashscope.base_compatible_api_url`） |

`set_region`이 구성하는 것은 항상 워크스페이스 전용 엔드포인트입니다. 일부 리전은 워크스페이스 서브도메인이 없는 공유 도메인도 제공합니다 — 베이징의 `dashscope.aliyuncs.com`, 싱가포르의 `dashscope-intl.aliyuncs.com`, 미국(버지니아)의 `dashscope-us.aliyuncs.com`입니다. 이를 사용하려면 위의 재정의 변수를 통해 직접 지정하세요.

### OpenAI 호환 채팅 완성

SDK는 `dashscope.base_compatible_api_url`（요청 경로 `chat/completions`）에 접근하는 OpenAI 호환 채팅 완성 엔드포인트를 제공합니다 — 추가로 `openai` 패키지를 설치할 필요가 없습니다. 위에서 설정한 리전을 그대로 따릅니다.

```python
import dashscope
from dashscope.aigc.chat_completion import Completions

dashscope.set_region(region="cn-hongkong", workspace_id="ws-hk-789")

response = Completions.create(
    model="qwen-max",
    messages=[{"role": "user", "content": "안녕하세요"}],
    api_key="YOUR-DASHSCOPE-API-KEY",
    stream=False,  # True로 설정하면 ChatCompletionChunk 제너레이터가 반환됩니다
)
print(response)
```

완전히 실행 가능한 예제는 [`samples/set_region_example.py`](samples/set_region_example.py)에서 확인할 수 있습니다.

요청 타임아웃, 커스텀 요청 헤더, 프록시 지원, 공유 커넥션 풀 종료에 대해서는 [고급 구성 가이드](docs/guides/configuration_ko.md)를 참고하세요.

## AI 어시스턴트: DashScope SDK Expert

이 SDK에는 번들로 제공되는 Agentic CLI（`dashscope/acli`） 프레임워크 위에 구축된 대화형 AI 어시스턴트 **DashScope SDK Expert**가 포함되어 있습니다. DashScope SDK/CLI 사용자에게는 개발 상담과 AI 코딩 도움을 받는 데 권장되는 방법으로, 터미널에서 바로 SDK/API 질문에 답하고, 실행 가능한 예제를 생성하고, CLI 사용법을 보여주고, 오류를 진단합니다.

- 인수 없이 `dashscope`를 실행하면 어시스턴트가 시작됩니다. 처음 실행할 때는 SDK Expert 지식 팩（도메인별 빠른 참조 스킬: 텍스트, 멀티모달, 음성, 검색, 파인튜닝, 에이전트, cli）을 설치할지 제안합니다. 이를 통해 소스 코드를 읽지 않아도 SDK의 공개 인터페이스（파라미터, 출력, 오류 코드）를 기반으로 한 안내를 받을 수 있습니다
- 문서를 읽는 대신 질문하세요 — 예: `dashscope "how do I stream Generation output"` 또는 `dashscope "CLI command to cancel a fine-tuning job"`. 어시스턴트 안에서 `/help`를 입력하면 사용 가능한 명령어（`/setup`, `/skill`, `/stats` 등）를 확인할 수 있습니다. 기존 SDK 서브커맨드도 계속 사용할 수 있으며, 인식되지 않는 명령은 자동으로 어시스턴트로 전달됩니다
- 전체 안내: [DashScope SDK Expert 가이드](https://help.aliyun.com/en/model-studio/dashscope-sdk-expert)

## 지원되는 모델

| 카테고리 | 추천 모델 | SDK 클래스 |
|----------|-------------------|-----------|
| 텍스트 생성 | qwen3.8-max, qwen3.7-max, qwen3.7-plus, qwen3.6-flash | `Generation` |
| 멀티모달 이해 | qwen3.5-omni-plus, qwen3.7-plus（비전） | `MultiModalConversation` |
| 텍스트 임베딩 | text-embedding-v4, text-embedding-v3 | `TextEmbedding` |
| 멀티모달 임베딩 | tongyi-embedding-vision-plus, qwen3-vl-embedding | `MultiModalEmbedding` |
| 텍스트 리랭크 | qwen3-rerank, gte-rerank-v2 | `TextReRank` |
| 이미지 생성 | wan2.7-image-pro, qwen-image-2.0-pro | `ImageSynthesis` |
| 영상 생성 | wan2.7-t2v, wan2.7-i2v, happyhorse-1.0-t2v/i2v | `VideoSynthesis` |
| 음성 합성（TTS） | cosyvoice-v3.5-plus, cosyvoice-v1 | `SpeechSynthesizer`, `HttpSpeechSynthesizer` |
| 음성 인식（ASR） | fun-asr-realtime, fun-asr, paraformer-v1 | `Transcription` |
| 옴니（실시간） | qwen3.5-omni-plus-realtime | `MultiModalConversation` |

최신 모델 목록은 [Bailian Model Plaza](https://bailian.console.aliyun.com/)를 참고하세요.

## 사용 예제

더 많은 실행 가능한 스크립트는 [`samples/`](samples)에서 확인할 수 있습니다.

### 멀티모달 이해（비전）

```python
from dashscope import MultiModalConversation

messages = [{
    "role": "user",
    "content": [
        {"image": "https://help-static-aliyun-doc.aliyuncs.com/file-manage-files/zh-CN/20241022/emyrja/dog_and_girl.jpeg"},
        {"text": "이 사진은 무엇을 보여주나요?"},
    ],
}]
response = MultiModalConversation.call(model="qwen-vl-max", messages=messages)
print(response.output.choices[0].message.content[0]["text"])
```

`Generation`과 마찬가지로 `stream=True`를 전달하면 결과를 점진적으로 스트리밍할 수 있습니다:

```python
from dashscope import MultiModalConversation

messages = [{
    "role": "user",
    "content": [
        {"image": "https://help-static-aliyun-doc.aliyuncs.com/file-manage-files/zh-CN/20241022/emyrja/dog_and_girl.jpeg"},
        {"text": "이 사진은 무엇을 보여주나요?"},
    ],
}]
responses = MultiModalConversation.call(
    model="qwen-vl-max",
    messages=messages,
    stream=True,
    incremental_output=True,
)
for response in responses:
    print(response.output.choices[0].message.content[0]["text"], end="")
```

`AioMultiModalConversation`을 사용하면 `async`/`await` 형태로 사용할 수 있습니다:

```python
import asyncio
from dashscope import AioMultiModalConversation

async def main():
    messages = [{
        "role": "user",
        "content": [
            {"image": "https://help-static-aliyun-doc.aliyuncs.com/file-manage-files/zh-CN/20241022/emyrja/dog_and_girl.jpeg"},
            {"text": "이 사진은 무엇을 보여주나요?"},
        ],
    }]
    response = await AioMultiModalConversation.call(model="qwen-vl-max", messages=messages)
    print(response.output.choices[0].message.content[0]["text"])

asyncio.run(main())
```

영상은 단일 영상 파일이 아니라 프레임 이미지의 URL/경로 목록으로 전달합니다:

```python
from dashscope import MultiModalConversation

messages = [{
    "role": "user",
    "content": [
        {"video": ["frame1.jpg", "frame2.jpg", "frame3.jpg", "frame4.jpg"]},
        {"text": "이 영상에서 무슨 일이 일어나는지 설명해줘."},
    ],
}]
response = MultiModalConversation.call(model="qwen-vl-max-latest", messages=messages)
print(response.output.choices[0].message.content[0]["text"])
```

`qwen-vl-ocr` 계열 모델은 구조화된 추출（예: 문서 이미지에서 JSON 스키마의 필드를 채우는 작업）을 위한 `ocr_options` 파라미터를 지원합니다:

```python
from dashscope import MultiModalConversation

messages = [{
    "role": "user",
    "content": [
        {"image": "https://example.com/invoice.jpg"},
        {"text": "이 문서에서 필드를 추출하여 다음 JSON 스키마에 채워줘: {result_schema}"},
    ],
}]
response = MultiModalConversation.call(
    model="qwen-vl-ocr-latest",
    messages=messages,
    ocr_options={
        "task": "key_information_extraction",
        "task_config": {"result_schema": {"invoice_number": "", "total_amount": ""}},
    },
)
print(response.output.choices[0].message.content[0]["text"])
```

### 로컬 파일 사용하기

URL을 받는 모든 필드（messages의 `image`, `audio`, `video`, `ImageSynthesis`의 `images` 등）는 로컬 파일 경로도 그대로 받을 수 있습니다 — SDK가 자동으로 OSS에 업로드하므로 수동으로 헤더를 설정할 필요가 없습니다:

```python
from dashscope import MultiModalConversation

messages = [{
    "role": "user",
    "content": [
        {"image": "/path/to/local/image.jpg"},
        {"text": "이 이미지에는 무엇이 있나요?"},
    ],
}]
response = MultiModalConversation.call(model="qwen-vl-max", messages=messages)
print(response.output.choices[0].message.content[0]["text"])
```

### 텍스트 임베딩

```python
from dashscope import TextEmbedding

resp = TextEmbedding.call(
    model=TextEmbedding.Models.text_embedding_v3,
    input=["바람은 세차고 하늘은 높다", "섬은 맑고 모래는 하얗다"],
    text_type="document",
)
for e in resp.output["embeddings"]:
    print(e["text_index"], e["embedding"][:3])
```

### 멀티모달 임베딩

```python
from dashscope import MultiModalEmbedding

resp = MultiModalEmbedding.call(
    model="multimodal-embedding-v1",
    input=[{"image": "https://dashscope.oss-cn-beijing.aliyuncs.com/images/256_1.png"}],
)
print(resp.output)
```

명시적인 item 클래스를 사용하면 텍스트/이미지/오디오를 하나의 융합 벡터로 결합할 수 있습니다（각 항목에는 `factor` 가중치가 필요하며, `enable_fusion`은 `qwen3-vl-embedding`에서만 사용 가능합니다）:

```python
from dashscope import MultiModalEmbedding
from dashscope.embeddings.multimodal_embedding import (
    MultiModalEmbeddingItemText,
    MultiModalEmbeddingItemImage,
    MultiModalEmbeddingItemAudio,
)

resp = MultiModalEmbedding.call(
    model="qwen3-vl-embedding",
    input=[
        MultiModalEmbeddingItemText(text="빨간 스포츠카", factor=1.0),
        MultiModalEmbeddingItemImage(image="https://dashscope.oss-cn-beijing.aliyuncs.com/images/256_1.png", factor=1.0),
        MultiModalEmbeddingItemAudio(audio="https://dashscope.oss-cn-beijing.aliyuncs.com/audios/welcome.mp3", factor=1.0),
    ],
    enable_fusion=True,
)
print(resp.output)
```

### 배치（오프라인） 텍스트 임베딩

대량의 텍스트를 처리할 때는 `TextEmbedding.call`을 하나씩 호출하는 대신, 파일（한 줄에 텍스트 하나）을 제출하여 비동기 배치 임베딩을 수행할 수 있습니다:

```python
from dashscope import BatchTextEmbedding

resp = BatchTextEmbedding.call(
    model=BatchTextEmbedding.Models.text_embedding_async_v2,
    url="https://example.com/texts.txt",
)
print(resp.output.task_id, resp.output.task_status)
if resp.output.task_status == "SUCCEEDED":
    print(resp.output.url)  # 여기서 결과 파일을 다운로드
```

블로킹 없이 작업을 제출한 뒤 별도로 폴링합니다:

```python
from dashscope import BatchTextEmbedding

task = BatchTextEmbedding.async_call(
    model=BatchTextEmbedding.Models.text_embedding_async_v2,
    url="https://example.com/texts.txt",
)
print(task.output.task_id)

result = BatchTextEmbedding.wait(task)
print(result.output.task_status)
```

### 텍스트 리랭크（ReRank）

```python
from dashscope import TextReRank

resp = TextReRank.call(
    model=TextReRank.Models.gte_rerank,
    query="중국의 수도는 어디입니까?",
    documents=[
        "중국의 수도는 베이징입니다.",
        "중국은 동아시아에 있는 큰 나라입니다.",
    ],
    return_documents=True,
    top_n=1,
)
for r in resp.output.results:
    print(r.index, r.relevance_score, r.document)
```

`AioTextReRank`를 사용하면 `async`/`await` 형태로 사용할 수 있습니다:

```python
import asyncio
from dashscope import AioTextReRank

async def main():
    resp = await AioTextReRank.call(
        model=AioTextReRank.Models.gte_rerank,
        query="중국의 수도는 어디입니까?",
        documents=["중국의 수도는 베이징입니다.", "중국은 동아시아에 있는 큰 나라입니다."],
        return_documents=True,
        top_n=1,
    )
    for r in resp.output.results:
        print(r.index, r.relevance_score, r.document)

asyncio.run(main())
```

### 텍스트 이해（NLU）

`Understanding`은 커스텀 모델을 학습시키지 않고도 고정된 레이블 집합에 대해 제로샷 정보 추출 또는 분류를 수행합니다:

```python
from dashscope import Understanding

response = Understanding.call(
    model=Understanding.Models.opennlu_v1,
    sentence="老师今天表扬我了",
    labels="积极，消极",
    task="classification",
)
print(response.output["text"])
```

`task`를 `"extraction"`（기본값）으로 설정하면 `sentence`를 분류하는 대신 `labels`와 일치하는 부분을 추출합니다.

### 코드 생성

`CodeGeneration`은 특정 코딩 시나리오（`Scenes`）를 지원합니다: 자연어를 코드로 변환, 코드 설명, 주석 생성, 커밋 메시지 생성, 단위 테스트 생성, 코드 질의응답, 자연어를 SQL로 변환.

```python
from dashscope import CodeGeneration

response = CodeGeneration.call(
    model=CodeGeneration.Models.tongyi_lingma_v1,
    scene=CodeGeneration.Scenes.nl2code,
    message=[
        {"role": "user", "content": "주어진 경로 아래 모든 파일의 총 크기를 계산해줘"},
        {"role": "attachment", "meta": {"language": "python"}},
    ],
)
print(response.output)
```

### 이미지 생성

```python
from http import HTTPStatus
from dashscope import ImageSynthesis

rsp = ImageSynthesis.call(
    model="wanx2.1-t2i-turbo",
    prompt="섬세한 창문과 나무 문이 있는 꽃집",
    n=1,
    size="1024*1024",
)
if rsp.status_code == HTTPStatus.OK:
    for result in rsp.output.results:
        print(result.url)
```

`call` 자체가 작업이 완료될 때까지 블로킹됩니다. 블로킹 없이 제출한 뒤 `async_call` + `wait`로 별도로 폴링할 수도 있습니다:

```python
from dashscope import ImageSynthesis

task = ImageSynthesis.async_call(
    model="wanx2.1-t2i-turbo",
    prompt="섬세한 창문과 나무 문이 있는 꽃집",
    n=1,
    size="1024*1024",
)
print(task.output.task_id)

rsp = ImageSynthesis.wait(task)
for result in rsp.output.results:
    print(result.url)
```

`sync_call`（현재는 `wan2.2-t2i-flash`/`wan2.2-t2i-plus`에서만 지원）은 비동기 작업을 폴링하는 대신 결과를 직접 반환합니다:

```python
from http import HTTPStatus
from dashscope import ImageSynthesis

rsp = ImageSynthesis.sync_call(
    model="wan2.2-t2i-flash",
    prompt="섬세한 창문과 나무 문이 있는 꽃집",
    n=1,
    size="1024*1024",
)
if rsp.status_code == HTTPStatus.OK:
    print(rsp.output)
```

`AioImageSynthesis.sync_call`을 사용하면 `async`/`await` 형태로 사용할 수 있습니다:

```python
import asyncio
from dashscope import AioImageSynthesis

async def main():
    rsp = await AioImageSynthesis.sync_call(
        model="wan2.2-t2i-flash",
        prompt="섬세한 창문과 나무 문이 있는 꽃집",
        n=1,
        size="1024*1024",
    )
    print(rsp.output)

asyncio.run(main())
```

### 스케치를 이미지로 변환 및 이미지 편집

`ImageSynthesis.call`은 손으로 그린 스케치나 기존 이미지 편집도 전용 모델과 파라미터를 통해 지원합니다:

```python
from dashscope import ImageSynthesis

# 스케치를 이미지로 변환
rsp = ImageSynthesis.call(
    model=ImageSynthesis.Models.wanx_sketch_to_image_v1,
    prompt="귀여운 고양이, 수채화 스타일",
    sketch_image_url="https://example.com/sketch.png",
)

# 텍스트 지시로 기존 이미지 편집
rsp = ImageSynthesis.call(
    model=ImageSynthesis.Models.wanx_2_1_imageedit,
    prompt="배경을 해변으로 바꿔줘",
    function="description_edit",
    base_image_url="https://example.com/photo.png",
)
print(rsp.output)
```

### 영상 생성

영상 생성은 비동기 작업으로 실행됩니다. `call`은 작업이 완료될 때까지 블로킹되며, 수동으로 폴링하려면 `async_call` + `wait`/`fetch`를 사용하세요.

```python
from http import HTTPStatus
from dashscope import VideoSynthesis

rsp = VideoSynthesis.call(
    model="wan2.7-t2v",
    prompt="달빛 아래를 달리는 새끼 고양이",
    audio=True,
    watermark=True,
)
if rsp.status_code == HTTPStatus.OK:
    print(rsp.output.video_url)
```

블로킹 없이 작업을 제출한 뒤 별도로 폴링합니다:

```python
from dashscope import VideoSynthesis

task = VideoSynthesis.async_call(model="wan2.7-t2v", prompt="달빛 아래를 달리는 새끼 고양이")
print(task.output.task_id)

rsp = VideoSynthesis.wait(task)
print(rsp.output.video_url)
```

### 음성 합성（TTS）

Qwen-TTS 계열 모델은 `MultiModalConversation`을 통해 호출하며, `messages` 대신 `text`/`voice`를 전달합니다:

```python
from dashscope import MultiModalConversation

response = MultiModalConversation.call(
    model="qwen3-tts-flash",
    text="Today is a wonderful day to build something people love!",
    voice="Cherry",
    language_type="English",
)
print(response.output.audio.url)
```

CosyVoice 계열 모델은 전용 `SpeechSynthesizer`를 사용합니다:

```python
from dashscope.audio.tts import SpeechSynthesizer

result = SpeechSynthesizer.call(
    model="cosyvoice-v1",
    text="Hello, Bailian.",
    format=SpeechSynthesizer.AudioFormat.format_wav,
)
with open("output.wav", "wb") as f:
    f.write(result.get_audio_data())
```

`SpeechSynthesisResult`는 문장 단위 타임스탬프와 원본 작업 응답도 제공하며, 예를 들어 자막 동기화 등에 활용할 수 있습니다:

```python
print(result.get_timestamps())  # 각 문장의 시작/종료 시간
print(result.get_response())    # 내부의 SpeechSynthesisResponse（status, request_id 등）
```

한 번의 블로킹 호출 대신 스트리밍을 원한다면 `ResultCallback`을 상속하여 `callback=`으로 전달하세요. 오디오가 생성될 때마다 `on_event`가 각 `SpeechSynthesisResult` 청크를 받습니다:

```python
from dashscope.audio.tts import SpeechSynthesizer, ResultCallback

class Callback(ResultCallback):
    def on_event(self, result) -> None:
        with open("output.wav", "ab") as f:
            f.write(result.get_audio_frame())

SpeechSynthesizer.call(
    model="cosyvoice-v1",
    text="Hello, Bailian.",
    format=SpeechSynthesizer.AudioFormat.format_wav,
    callback=Callback(),
)
```

`HttpSpeechSynthesizer`는 WebSocket 없이 일반 HTTP로 음성 합성을 호출하며, 지속적인 연결을 유지할 수 없는 환경에서 유용합니다:

```python
from dashscope.audio.http_tts import HttpSpeechSynthesizer

result = HttpSpeechSynthesizer.call(
    model="cosyvoice-v3-flash",
    text="Hello, Bailian.",
    voice="longxiaochun",
    audio_format="wav",
)
with open("output.wav", "wb") as f:
    f.write(result.audio_data)
```

### 스트리밍 음성 합성（CosyVoice v2）

텍스트를 점진적으로 스트리밍하여 전송하고, 생성되는 오디오 바이트를 콜백을 통해 실시간으로 받습니다:

```python
from dashscope.audio.tts_v2 import ResultCallback, SpeechSynthesizer

class Callback(ResultCallback):
    def on_data(self, data: bytes) -> None:
        with open("output.mp3", "ab") as f:
            f.write(data)

synthesizer = SpeechSynthesizer(model="cosyvoice-v2", voice="longxiaochun_v2", callback=Callback())
for text in ["안녕하세요, ", "이것은 스트리밍 ", "음성 합성입니다."]:
    synthesizer.streaming_call(text)
synthesizer.streaming_complete()
```

### 음성 인식（ASR）

`qwen3-asr-flash` 등 음성 이해 모델은 `MultiModalConversation`을 통해 호출합니다:

```python
from dashscope import MultiModalConversation

messages = [{
    "role": "user",
    "content": [{"audio": "https://dashscope.oss-cn-beijing.aliyuncs.com/audios/welcome.mp3"}],
}]
response = MultiModalConversation.call(
    model="qwen3-asr-flash",
    messages=messages,
    result_format="message",
)
print(response.output.choices[0].message.content)
```

파일 기반 배치 음성 인식에는 `Transcription`을 사용합니다:

```python
from dashscope.audio.asr import Transcription

response = Transcription.call(
    model=Transcription.Models.paraformer_v1,
    file_urls=["https://example.com/audio.wav"],
)
if response.output.task_status == "SUCCEEDED":
    print(response.output.results)
```

### 스트리밍 음성 인식

라이브/스트리밍 오디오 소스의 경우, PCM 프레임을 하나씩 전송하고 콜백을 통해 결과를 받습니다（여기서는 패턴을 보여주기 위해 파일을 청크 단위로 읽지만, 실제로는 파일 읽기 루프를 라이브 오디오 소스로 교체하세요）:

```python
from dashscope.audio.asr import Recognition, RecognitionCallback

class Callback(RecognitionCallback):
    def on_event(self, result) -> None:
        print(result.get_sentence())

recognition = Recognition(
    model="paraformer-realtime-v1",
    format="pcm",
    sample_rate=16000,
    callback=Callback(),
)
recognition.start()
with open("audio.pcm", "rb") as f:
    while chunk := f.read(3200):
        recognition.send_audio_frame(chunk)
recognition.stop()
```

음성 클로닝, 발음 교정, 실시간 음성 번역, 커스텀 ASR 핫워드에 대해서는 [고급 음성 기능 가이드](docs/guides/realtime-audio_ko.md)를 참고하세요.

### TingWu（회의 및 산업용 오디오 분석）

`TingWu`는 파일 URL을 대상으로 도메인 특화 오디오 분석 작업（산업 점검, 자동차 서비스 통화 등）을 수행합니다:

```python
from dashscope.multimodal.tingwu.tingwu import TingWu

response = TingWu.call(
    model="tingwu-automotive-service-inspection",
    user_defined_input={
        "fileUrl": "http://example.com/call-recording.mp3",
        "appid": "your-app-id",
    },
)
print(response)
```

실시간 오디오 소스를 대상으로 하는 스트리밍/실시간 TingWu 세션에 대해서는 [TingWu 가이드](docs/guides/tingwu_ko.md)를 참고하세요.

### Bailian 애플리케이션（에이전트 앱）

[Bailian 애플리케이션 센터](https://bailian.console.aliyun.com/)에서 만든 앱을 호출합니다:

```python
from http import HTTPStatus
from dashscope import Application

responses = Application.call(
    app_id="YOUR-APP-ID",
    prompt="이 파일을 요약해줘",
    stream=True,
    incremental_output=True,
    file_list=["https://example.com/document.pdf"],
)
for response in responses:
    if response.status_code != HTTPStatus.OK:
        print(f"code={response.code}, message={response.message}")
    else:
        print(response.output.text, end="")
```

### AgentStudio（관리형 에이전트）

`dashscope.agentstudio`는 Bailian AgentStudio 제품에서 구축한 에이전트를 관리합니다 — 에이전트/세션을 생성하고 대화 이벤트를 스트리밍으로 받거나, cron 일정에 따라 에이전트를 실행하는 "배포（deployment）"를 생성할 수 있습니다:

```python
from dashscope.agentstudio import Client
from dashscope.agentstudio.types import user_message

client = Client(api_key="sk-xxx")
agent = client.agents.create(name="demo", model="qwen-plus")
session = client.sessions.create(agent=agent.id)
client.sessions.events.send(session.id, [user_message("안녕하세요!")])
with client.sessions.events.stream(session.id) as stream:
    for event in stream:
        print(event.type, event.to_dict())
        if event.type == "session_status":
            break
```

참고: `Client()`는 환경 변수 `DASHSCOPE_WORKSPACE`（`_ID` 접미사 없음）를 읽습니다 — 이는 [리전 설정](#리전-및-엔드포인트-구성)에서 사용하는 `DASHSCOPE_WORKSPACE_ID`와는 다른 변수입니다. 정기 배포의 전체 예제는 [`samples/agentstudio_deployments.py`](samples/agentstudio_deployments.py)에서 확인할 수 있습니다.

### 로컬 토크나이즈

API를 호출하지 않고 로컬에서 Qwen 계열 모델의 토큰 수를 세거나 인코딩/디코딩할 수 있습니다（`pip install "dashscope[tokenizer]"` 필요）:

```python
from dashscope.tokenizers.tokenizer import get_tokenizer, list_tokenizers

print(list_tokenizers())  # 로컬 tokenizer가 지원하는 모델 계열

tokenizer = get_tokenizer("qwen-turbo")  # 모든 qwen-* 모델에서 사용 가능
tokens = tokenizer.encode("这个是千问tokenizer")
print(len(tokens))               # 토큰 수
print(tokenizer.decode(tokens))  # 토큰을 다시 텍스트로 복원
```

`Tokenization.call`은 원격 API 호출을 통해 동일한 작업을 수행합니다（로컬 tokenizer가 지원하지 않는 모델에 유용합니다）:

```python
from dashscope import Tokenization

resp = Tokenization.call(model=Tokenization.Models.qwen_turbo, prompt="这个是千问tokenizer")
print(resp.output["token_ids"], resp.output["tokens"])
print(resp.usage["input_tokens"])
```

### 사용 가능한 모델 목록 조회

```python
from dashscope import Models

models = Models.list(page=1, page_size=10)
print(models.output["models"])

model = Models.get("qwen-plus")
print(model.output["model_id"])
```

### 파인튜닝

학습용 파일을 업로드하고 파인튜닝 작업을 생성한 뒤 완료될 때까지 폴링합니다（Agentic RL 파인튜닝에는 `pip install "dashscope[rl]"`이 필요합니다. 기존의 지도 학습 파인튜닝에는 추가 설치가 필요 없습니다）:

```python
from dashscope import Files, FineTunes

file_response = Files.upload(file_path="train.jsonl", purpose="fine_tune")
file_id = file_response.output["uploaded_files"][0]["file_id"]

job = FineTunes.call(
    model="qwen-turbo",
    training_file_ids=file_id,
    hyper_parameters={"n_epochs": 10, "learning_rate": 0.001},
)
print(job.output.job_id, job.output.status)

result = FineTunes.wait(job.output.job_id)  # 완료될 때까지 30초마다 폴링
print(result.output.status)
```

커스텀 rollout/reward 함수를 사용하는 Agentic RL 파인튜닝（YAML 기반 학습 작업, 트레이싱/관찰 가능성）에 대해서는 [`dashscope/finetune/reinforcement/examples/workspace/README-ko.md`](dashscope/finetune/reinforcement/examples/workspace/README-ko.md)（빠른 시작）와 [`UserGuide-ko.md`](dashscope/finetune/reinforcement/examples/workspace/UserGuide-ko.md)（전체 참조）의 전용 가이드를 참고하세요.

### 파인튜닝된 모델 배포하기

파인튜닝 작업에서 생성된 모델을 배포하여 다른 모델과 동일하게 호출할 수 있도록 합니다:

```python
from dashscope import Deployments, Generation

deployment = Deployments.call(model=result.output.finetuned_output, capacity=1)
deployed_model = deployment.output.deployed_model

# deployment.output.status가 "RUNNING"이 될 때까지 폴링한 뒤, 일반 모델과 동일하게 호출할 수 있습니다:
status = Deployments.get(deployed_model).output.status
response = Generation.call(model=deployed_model, messages=[{"role": "user", "content": "Hi"}])
```

작업/배포의 전체 라이프사이클 관리（목록 조회, 취소, 이벤트 스트리밍, 스케일링）에 대해서는 [파인튜닝 및 배포 라이프사이클 가이드](docs/guides/fine-tuning_ko.md)를 참고하세요.

### Assistants API（지원 종료 예정）

레거시 Assistants API（`Assistants`, `Threads`, `Runs`, `Messages`）는 계속 동작하지만 지원 종료 예정입니다 — 전체 기능과 마이그레이션 방법은 [Assistants API 가이드](docs/guides/assistants_ko.md)를 참고하세요. 새로운 코드는 대신 [`Generation`](#빠른-시작) 또는 [`MultiModalConversation`](#멀티모달-이해비전)을 사용해야 합니다.

## CLI 사용법

모든 SDK 기능은 `dashscope` 서브커맨드로도 사용할 수 있습니다（기본 패키지와 함께 설치됨）. Python 코드를 작성하지 않고도 스크립팅이나 빠른 확인에 사용할 수 있습니다:

```shell
# 텍스트 생성
dashscope generation create -m qwen-plus -p "Who are you?"
dashscope generation create -m qwen-plus -p "바다에 관한 하이쿠를 써줘" --stream

# 사용 가능한 모델 목록 조회 / 상세 확인
dashscope models list
dashscope models get qwen-plus

# 파일 업로드, 목록 조회, 상세 확인, 삭제
dashscope files upload -f ./train.jsonl -p fine_tune
dashscope files list
dashscope files get <file_id>
dashscope files delete <file_id>

# OSS에 파일을 직접 업로드（일부 CV/비전 모델에서 사용）
dashscope oss upload -f ./photo.png -m wanx-style-repaint-v1

# 파인튜닝된 모델을 배포하고 해당 배포를 관리
dashscope deployments create -m <finetuned-model-id> --plan mu -c 1
dashscope deployments list
dashscope deployments get <deployed_model>
dashscope deployments scale <deployed_model> -c 2
dashscope deployments delete <deployed_model>

# Agentic RL 작업 관리（`dashscope rl run`의 사용법은 강화학습 가이드를 참고）
dashscope rl list
dashscope rl get <job_id>
dashscope rl logs <job_id>
dashscope rl cancel <job_id>
```

`dashscope --help` 또는 `dashscope <command> --help`（예: `dashscope generation --help`）를 실행하면 모든 명령 그룹（`generation`, `ft`, `files`, `deployments`, `models`, `embeddings`, `rerank`, `tokenization`, `application`, `image-synthesis`, `video-synthesis`, `multimodal-conversation`, `transcription`, `speech-synthesis`, `rl` 등）과 해당 옵션을 확인할 수 있습니다. 인수 없이 `dashscope`를 실행하면 대화형 [AI 어시스턴트](#ai-어시스턴트-dashscope-sdk-expert)가 대신 실행됩니다.

## 셸 자동완성

해당 명령을 한 번 실행한 뒤 셸을 재시작하세요（또는 설정 파일을 다시 불러오세요）:

| 셸 | 설치 명령 |
|-------|-----------------|
| **bash** | `dashscope --install-completion bash` |
| **zsh** | `dashscope --install-completion zsh` |
| **fish** | `dashscope --install-completion fish` |

설치하지 않고 자동완성 스크립트를 미리 보려면:
```shell
dashscope --show-completion bash
```

## 로깅
`dashscope`를 import하기 전에 `DASHSCOPE_LOGGING_LEVEL`（`info` 또는 `debug`）을
설정하면 콘솔 핸들러가 자동으로 추가됩니다:

```shell
export DASHSCOPE_LOGGING_LEVEL='info'
```

```python
from dashscope import Generation

# 이제 요청 세부 정보가 콘솔에 자동으로 출력됩니다. 예:
# 2024-01-01 12:00:00,000 - dashscope - ... - INFO - request: POST https://...
response = Generation.call(model="qwen-plus", messages=[{"role": "user", "content": "Hi"}])
```

## 출력

모든 SDK 호출은（스트리밍의 경우 각 청크마다）다음 필드를 가진 응답 객체를 반환합니다:

```python
response = Generation.call(model="qwen-plus", messages=[{"role": "user", "content": "Hi"}])

response.request_id    # str: 요청 ID로, 문제를 보고할 때 유용합니다
response.status_code   # int: HTTP 상태 코드. 200은 성공을 의미합니다
response.code          # str: 실패 시 오류 코드, 성공 시 빈 문자열
response.message       # str: 실패 시 오류 메시지, 성공 시 빈 문자열
response.output        # Any: 요청의 출력（호출한 API에 따라 형태가 다름）
response.usage         # Any: 토큰/할당량 사용 정보
```

`output`/`usage`가 딕셔너리 방식과 속성 방식 접근을 모두 지원하는 방법과, 각 기능 전용 응답 서브클래스에 대해서는 [응답 객체 모델 가이드](docs/guides/response-types_ko.md)를 참고하세요.

## 라이선스
이 프로젝트는 Apache License（버전 2.0）에 따라 라이선스가 부여됩니다.
