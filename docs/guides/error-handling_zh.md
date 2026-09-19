# 错误处理参考

> [English](error-handling.md) | **中文** | [日本語](error-handling_ja.md) | [Español](error-handling_es.md) | [한국어](error-handling_ko.md)

本指南在 [README 的错误处理部分](../../README.md#error-handling)
（捕获 `DashScopeException`，再检查 `status_code`）基础上做进一步说明。

## 异常类

所有 SDK 抛出的异常（`dashscope/common/error.py`）都继承自
`DashScopeException`，因此用一个 `except DashScopeException` 即可捕获其中任意一种。
以下是最常见的几种，以及它们实际的触发条件：

| 异常 | 触发条件 |
|---|---|
| `InputRequired` | 缺少必需的输入，例如未提供 `prompt`/`messages` |
| `ModelRequired` | `model` 参数为空 |
| `AuthenticationError` | 任何地方（代码、环境变量、文件）都未配置 API Key |
| `InvalidInput` | 参数组合无效，例如参数之间相互冲突 |
| `InvalidFileFormat` | 待上传的文件不符合预期格式（例如用于微调的文件不是 JSONL 格式） |
| `UnsupportedModel` | 该操作不支持所请求的模型（例如本地分词不支持该模型） |
| `UploadFileException` | 将本地文件（例如用于视觉/图像请求）上传到 OSS 失败 |
| `UnsupportedDataType` | 无法识别的输入/输出数据类型 |
| `TimeoutException` | 阻塞等待（例如 `Runs.wait`）超过了超时时间 |

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

## 获取用于报障的 request_id

无论成功还是失败，每个响应都携带一个 `request_id`。在反馈问题或联系
技术支持时请附上它：

```python
from http import HTTPStatus
from dashscope import Generation

response = Generation.call(model="qwen-plus", messages=[{"role": "user", "content": "Hi"}])
if response.status_code != HTTPStatus.OK:
    print(f"request_id={response.request_id} code={response.code} message={response.message}")
```

## 自动连接重试

如果某个复用中的长连接被服务端或中间的负载均衡器悄悄断开（在收到任何响应字节
之前就检测到连接错误），SDK 会自动**重试一次**该请求——同步（基于
`requests`）和异步（基于 `aiohttp`）客户端内部都会这样做。这一行为不可配置，
也无需你编写任何代码；它仅覆盖"响应尚未开始前连接就被断开"这一种情况，
不包括限流、参数错误等应用层失败——这些会作为正常的错误响应返回（相关处理方式
见 README 的错误处理部分）。

## 限流的重试与退避

与上面的连接级重试不同，SDK **不会**自动重试限流或临时性服务端错误这类
应用层失败——这些会以非 200 的 `status_code` 正常返回，是否重试由你的代码
决定。一个基于 `status_code` 的简单指数退避实现：

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
        return response  # 放弃重试：由调用方检查 status_code/code/message

response = call_with_backoff(model="qwen-plus", messages=[{"role": "user", "content": "Hi"}])
```
