# Error Handling Reference

> **English** | [中文](error-handling_zh.md) | [日本語](error-handling_ja.md) | [Español](error-handling_es.md) | [한국어](error-handling_ko.md)

This goes beyond the basic pattern in the [README's Error Handling section](../../README.md#error-handling)
(catch `DashScopeException`, then check `status_code`).

## Exception Classes

All SDK-raised exceptions (`dashscope/common/error.py`) subclass
`DashScopeException`, so a single `except DashScopeException` catches any of
them. The most common ones and when they're actually raised:

| Exception | Raised when |
|---|---|
| `InputRequired` | A required input is missing, e.g. no `prompt`/`messages` |
| `ModelRequired` | The `model` argument is empty |
| `AuthenticationError` | No API key is configured anywhere (code, env var, or file) |
| `InvalidInput` | An argument combination is invalid, e.g. conflicting parameters |
| `InvalidFileFormat` | A file to upload doesn't match the expected format (e.g. non-JSONL for fine-tuning) |
| `UnsupportedModel` | The requested model isn't supported by the operation (e.g. an unsupported model for local tokenization) |
| `UploadFileException` | Uploading a local file (e.g. for a vision/image request) to OSS failed |
| `UnsupportedDataType` | An input/output data type isn't recognized |
| `TimeoutException` | A blocking wait (e.g. `Runs.wait`) exceeded its timeout |

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

## Getting the Request ID for Support

Every response — success or failure — carries a `request_id`. Include it
when reporting an issue or contacting support:

```python
from http import HTTPStatus
from dashscope import Generation

response = Generation.call(model="qwen-plus", messages=[{"role": "user", "content": "Hi"}])
if response.status_code != HTTPStatus.OK:
    print(f"request_id={response.request_id} code={response.code} message={response.message}")
```

## Automatic Connection Retries

The SDK automatically retries a request **once** if a pooled keep-alive
connection was silently dropped by the server or an intermediate load
balancer (detected as a connection error before any response bytes
arrive) — both the sync (`requests`-based) and async (`aiohttp`-based)
clients do this internally. This is not configurable and requires no code
on your part; it only covers connections dropped before a response starts,
not application-level failures like rate limiting or invalid input, which
are returned as normal error responses (see the README's Error Handling
section for that pattern).

## Retry and Backoff for Rate Limits

Unlike the connection-level retry above, the SDK does **not** automatically
retry application-level failures such as rate limiting or transient server
errors — these come back as a normal response with a non-200 `status_code`,
and it's up to your code to decide whether to retry. A simple exponential
backoff around `status_code`:

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
        return response  # give up: caller checks status_code/code/message

response = call_with_backoff(model="qwen-plus", messages=[{"role": "user", "content": "Hi"}])
```
