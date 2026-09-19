# 고급 설정

> [English](configuration.md) | [中文](configuration_zh.md) | [日本語](configuration_ja.md) | [Español](configuration_es.md) | **한국어**

이 가이드는 인증 및 리전 선택 이외의 SDK 전역 설정을 다룹니다. API 키 설정은
[API Key 인증](../../README.md#api-key-authentication)을, 리전/엔드포인트
전환은 [리전 및 엔드포인트 설정](../../README.md#region-and-endpoint-configuration)을
참고하세요.

## 요청 타임아웃 (Request Timeout)

`.call()`/`.create()`/`.get()`/`.list()`/`.delete()` 형태의 모든 메서드는
`request_timeout` 키워드 인자(초 단위)를 받습니다. 기본값은 300초
(`DEFAULT_REQUEST_TIMEOUT_SECONDS`)입니다. 스트리밍 요청의 경우 청크 간의
유휴 타임아웃이며, 비스트리밍 요청의 경우 전체 요청 타임아웃입니다.

```python
from dashscope import Generation

response = Generation.call(
    model="qwen-plus",
    messages=[{"role": "user", "content": "Hi"}],
    request_timeout=30,
)
```

## 사용자 지정 요청 헤더

`headers` 딕셔너리를 전달하여 추가 HTTP 헤더를 요청에 병합할 수 있습니다
(SDK 자체의 `Authorization`/워크스페이스 헤더는 그대로 적용됩니다):

```python
from dashscope import Generation

response = Generation.call(
    model="qwen-plus",
    messages=[{"role": "user", "content": "Hi"}],
    headers={"X-Request-Tag": "my-service"},
)
```

OpenAI 호환 `Completions.create`에는 동일한 목적의 전용 `extra_headers`
매개변수가 있습니다:

```python
from dashscope.aigc.chat_completion import Completions

response = Completions.create(
    model="qwen-max",
    messages=[{"role": "user", "content": "Hi"}],
    api_key="YOUR-DASHSCOPE-API-KEY",
    extra_headers={"X-Request-Tag": "my-service"},
)
```

## 프록시 지원

SDK는 자체 프록시 설정을 구현하지 않으며, 대신 기본 HTTP 라이브러리의 표준
동작에 의존합니다. 비동기 클라이언트는 `trust_env=True`로 `aiohttp.ClientSession`을
생성하고, 동기 클라이언트의 `requests.Session`은 기본적으로 프록시를 준수합니다 —
둘 다 표준 환경 변수 `HTTP_PROXY`, `HTTPS_PROXY`, `NO_PROXY`를 자동으로 인식합니다:

```shell
export HTTPS_PROXY="http://proxy.example.com:8080"
```

```python
from dashscope import Generation

# 이제 요청은 HTTPS_PROXY로 설정된 프록시를 통해 전송됩니다
response = Generation.call(model="qwen-plus", messages=[{"role": "user", "content": "Hi"}])
```

## 공유 커넥션 풀 닫기

SDK는 커넥션 풀링을 위해 공유 `requests.Session`(동기) 하나와 이벤트 루프당
`aiohttp.ClientSession`(비동기) 하나를 유지합니다. 장시간 실행되는 프로세스는
이를 명시적으로 닫아 풀링된 커넥션을 해제할 수 있습니다(다음 요청 시 새 세션이
지연 생성됩니다):

```python
import asyncio
from dashscope import close_shared_sync_session, close_shared_aio_session

close_shared_sync_session()
asyncio.run(close_shared_aio_session())
```

## 로깅

[README](../../README.md#logging)에서 설명한 대로, import 전에
`DASHSCOPE_LOGGING_LEVEL`을 설정하면 콘솔 핸들러가 자동으로 연결됩니다.
SDK는 `"dashscope"`라는 로거 이름으로 표준 `logging` 모듈을 통해 로그를
남기므로, 환경 변수 없이도 프로그래밍 방식으로 제어할 수 있습니다:

```python
import logging

logging.getLogger("dashscope").setLevel(logging.DEBUG)
```
