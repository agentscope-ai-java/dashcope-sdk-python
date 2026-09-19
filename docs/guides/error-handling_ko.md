# 오류 처리 참고 문서

> [English](error-handling.md) | [中文](error-handling_zh.md) | [日本語](error-handling_ja.md) | [Español](error-handling_es.md) | **한국어**

이 문서는 [README의 오류 처리 섹션](../../README.md#error-handling)에 나온
기본 패턴(`DashScopeException`을 잡은 뒤 `status_code`를 확인하는 방식)보다
더 깊이 다룹니다.

## 예외 클래스

SDK가 발생시키는 모든 예외(`dashscope/common/error.py`)는 `DashScopeException`을
상속하므로, `except DashScopeException` 하나로 모두 잡을 수 있습니다. 가장
흔한 예외와 실제로 발생하는 시점은 다음과 같습니다:

| 예외 | 발생 조건 |
|---|---|
| `InputRequired` | 필수 입력이 누락됨, 예: `prompt`/`messages`가 없음 |
| `ModelRequired` | `model` 인자가 비어 있음 |
| `AuthenticationError` | 코드, 환경 변수, 파일 어디에도 API 키가 설정되어 있지 않음 |
| `InvalidInput` | 인자 조합이 유효하지 않음, 예: 매개변수 간 충돌 |
| `InvalidFileFormat` | 업로드할 파일이 예상 형식과 다름(예: 파인튜닝용 파일이 JSONL이 아님) |
| `UnsupportedModel` | 요청한 모델이 해당 작업에서 지원되지 않음(예: 로컬 토큰화에서 지원하지 않는 모델) |
| `UploadFileException` | 로컬 파일(예: 비전/이미지 요청용)을 OSS에 업로드하는 데 실패함 |
| `UnsupportedDataType` | 입력/출력 데이터 유형을 인식할 수 없음 |
| `TimeoutException` | 블로킹 대기(예: `Runs.wait`)가 제한 시간을 초과함 |

```python
from dashscope import Generation
from dashscope.common.error import (
    DashScopeException,
    InputRequired,
    ModelRequired,
    AuthenticationError,
)

try:
    Generation.call(model="", messages=[{"role": "user", "content": "Hi"}])
except ModelRequired as e:
    print(f"Model missing: {e}")
except (InputRequired, AuthenticationError) as e:
    print(f"Invalid setup: {e}")
except DashScopeException as e:
    print(f"Other SDK-side error: {e}")
```

## 지원 요청을 위한 request_id 확인

성공이든 실패든 모든 응답에는 `request_id`가 포함됩니다. 문제를 보고하거나
기술 지원에 문의할 때 이를 함께 알려주세요:

```python
from http import HTTPStatus
from dashscope import Generation

response = Generation.call(model="qwen-plus", messages=[{"role": "user", "content": "Hi"}])
if response.status_code != HTTPStatus.OK:
    print(f"request_id={response.request_id} code={response.code} message={response.message}")
```

## 자동 연결 재시도

풀링된 keep-alive 연결이 서버 또는 중간의 로드 밸런서에 의해 조용히 끊어진
경우(응답 바이트가 도착하기 전에 연결 오류로 감지됨), SDK는 해당 요청을
내부적으로 **한 번만** 자동으로 재시도합니다 — 동기(`requests` 기반)와
비동기(`aiohttp` 기반) 클라이언트 모두 내부적으로 이렇게 동작합니다. 이
동작은 설정할 수 없으며 별도의 코드가 필요하지 않습니다. 응답이 시작되기
전에 연결이 끊긴 경우만 해당하며, 속도 제한이나 잘못된 입력과 같은
애플리케이션 수준의 실패(README의 오류 처리 섹션에서 설명한 패턴대로 일반
오류 응답으로 반환됨)는 포함하지 않습니다.

## 속도 제한에 대한 재시도와 백오프

위의 연결 수준 재시도와 달리, SDK는 속도 제한이나 일시적인 서버 오류와 같은
애플리케이션 수준의 실패를 자동으로 재시도하지 **않습니다** — 이런 경우
200이 아닌 `status_code`를 가진 일반 응답으로 반환되며, 재시도 여부는
사용자의 코드가 결정해야 합니다. `status_code`를 기반으로 한 간단한 지수
백오프 예시:

```python
import time
from http import HTTPStatus
from dashscope import Generation

def call_with_backoff(max_retries=5, base_delay=1.0, **kwargs):
    for attempt in range(max_retries):
        response = Generation.call(**kwargs)
        if response.status_code == HTTPStatus.OK:
            return response
        if response.status_code in (429, 500, 502, 503, 504) and attempt < max_retries - 1:
            time.sleep(base_delay * (2 ** attempt))
            continue
        return response  # 재시도 포기: 호출자가 status_code/code/message를 확인

response = call_with_backoff(model="qwen-plus", messages=[{"role": "user", "content": "Hi"}])
```
