# Advanced Configuration

> **English** | [中文](configuration_zh.md) | [日本語](configuration_ja.md) | [Español](configuration_es.md) | [한국어](configuration_ko.md)

This guide covers SDK-wide configuration beyond authentication and region
selection. For API key setup, see [API Key Authentication](../../README.md#api-key-authentication);
for switching regions/endpoints, see [Region and Endpoint Configuration](../../README.md#region-and-endpoint-configuration).

## Request Timeout

Every `.call()`/`.create()`/`.get()`/`.list()`/`.delete()`-style method accepts
a `request_timeout` keyword argument (in seconds). It defaults to 300 seconds
(`DEFAULT_REQUEST_TIMEOUT_SECONDS`). For streaming requests this is the idle
timeout between chunks; for non-streaming requests it's the total request
timeout.

```python
from dashscope import Generation

response = Generation.call(
    model="qwen-plus",
    messages=[{"role": "user", "content": "Hi"}],
    request_timeout=30,
)
```

## Custom Request Headers

Pass a `headers` dict to merge additional HTTP headers into the request
(the SDK's own `Authorization`/workspace headers are still applied):

```python
from dashscope import Generation

response = Generation.call(
    model="qwen-plus",
    messages=[{"role": "user", "content": "Hi"}],
    headers={"X-Request-Tag": "my-service"},
)
```

The OpenAI-compatible `Completions.create` has a dedicated `extra_headers`
parameter for the same purpose:

```python
from dashscope.aigc.chat_completion import Completions

response = Completions.create(
    model="qwen-max",
    messages=[{"role": "user", "content": "Hi"}],
    api_key="YOUR-DASHSCOPE-API-KEY",
    extra_headers={"X-Request-Tag": "my-service"},
)
```

## Proxy Support

The SDK doesn't implement its own proxy configuration; instead it relies on
the underlying HTTP libraries' standard behavior. The async client creates
its `aiohttp.ClientSession` with `trust_env=True`, and the sync client's
`requests.Session` honors proxies by default — both automatically pick up
the standard `HTTP_PROXY`, `HTTPS_PROXY`, and `NO_PROXY` environment
variables:

```shell
export HTTPS_PROXY="http://proxy.example.com:8080"
```

```python
from dashscope import Generation

# Requests now go through the proxy configured via HTTPS_PROXY
response = Generation.call(model="qwen-plus", messages=[{"role": "user", "content": "Hi"}])
```

## Closing Shared Connection Pools

The SDK maintains a shared `requests.Session` (sync) and one
`aiohttp.ClientSession` per event loop (async) for connection pooling.
Long-running processes can close them explicitly to release pooled
connections (a fresh session is created lazily on the next request):

```python
import asyncio
from dashscope import close_shared_sync_session, close_shared_aio_session

close_shared_sync_session()
asyncio.run(close_shared_aio_session())
```

## Logging

As covered in the [README](../../README.md#logging), setting
`DASHSCOPE_LOGGING_LEVEL` before import attaches a console handler
automatically. Since the SDK logs through the standard `logging` module
under the `"dashscope"` logger name, you can also control it
programmatically without the environment variable:

```python
import logging

logging.getLogger("dashscope").setLevel(logging.DEBUG)
```
