# 高级配置

> [English](configuration.md) | **中文** | [日本語](configuration_ja.md) | [Español](configuration_es.md) | [한국어](configuration_ko.md)

本指南介绍身份验证和区域选择之外的 SDK 全局配置。API Key 的设置请参见 [API Key 鉴权](../../README.md#api-key-authentication)；切换区域/端点请参见 [区域与端点配置](../../README.md#region-and-endpoint-configuration)。

## 请求超时

所有 `.call()`/`.create()`/`.get()`/`.list()`/`.delete()` 风格的方法都接受
`request_timeout` 关键字参数（单位为秒）。默认值为 300 秒
（`DEFAULT_REQUEST_TIMEOUT_SECONDS`）。对于流式请求，这是分片之间的空闲超时；
对于非流式请求，这是整个请求的总超时时间。

```python
from dashscope import Generation

response = Generation.call(
    model="qwen-plus",
    messages=[{"role": "user", "content": "Hi"}],
    request_timeout=30,
)
```

## 自定义请求头

传入 `headers` 字典，可以将额外的 HTTP 请求头合并到请求中
（SDK 自身的 `Authorization`/业务空间请求头仍会一并附加）：

```python
from dashscope import Generation

response = Generation.call(
    model="qwen-plus",
    messages=[{"role": "user", "content": "Hi"}],
    headers={"X-Request-Tag": "my-service"},
)
```

OpenAI-compatible 的 `Completions.create` 提供了专门的 `extra_headers`
参数，作用相同：

```python
from dashscope.aigc.chat_completion import Completions

response = Completions.create(
    model="qwen-max",
    messages=[{"role": "user", "content": "Hi"}],
    api_key="YOUR-DASHSCOPE-API-KEY",
    extra_headers={"X-Request-Tag": "my-service"},
)
```

## 代理支持

SDK 本身没有实现专门的代理配置；而是依赖底层 HTTP 库的标准行为。
异步客户端创建 `aiohttp.ClientSession` 时使用了 `trust_env=True`，
同步客户端的 `requests.Session` 默认也支持代理——两者都会自动读取标准的
`HTTP_PROXY`、`HTTPS_PROXY` 和 `NO_PROXY` 环境变量：

```shell
export HTTPS_PROXY="http://proxy.example.com:8080"
```

```python
from dashscope import Generation

# 请求现在会通过 HTTPS_PROXY 配置的代理发出
response = Generation.call(model="qwen-plus", messages=[{"role": "user", "content": "Hi"}])
```

## 关闭共享连接池

SDK 维护着一个共享的 `requests.Session`（同步）以及每个事件循环一个
`aiohttp.ClientSession`（异步），用于连接池复用。长时间运行的进程可以
显式关闭它们以释放连接池中的连接（下次请求时会自动惰性创建新的会话）：

```python
import asyncio
from dashscope import close_shared_sync_session, close_shared_aio_session

close_shared_sync_session()
asyncio.run(close_shared_aio_session())
```

## 日志

正如 [README](../../README.md#logging) 中所述，在导入前设置
`DASHSCOPE_LOGGING_LEVEL` 会自动附加一个控制台日志 handler。由于 SDK 通过
标准 `logging` 模块、以 `"dashscope"` 作为 logger 名称输出日志，你也可以
不依赖环境变量、直接以编程方式控制日志级别：

```python
import logging

logging.getLogger("dashscope").setLevel(logging.DEBUG)
```
