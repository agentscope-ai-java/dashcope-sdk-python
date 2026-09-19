# DashScope Python SDK

> [English](README.md) | **中文** | [日本語](README_ja.md)

DashScope Python SDK 提供了访问[阿里云百炼（Model Studio）](https://help.aliyun.com/zh/model-studio/) API 的完整接口，覆盖文本生成、多模态理解、向量（Embedding）、重排（Rerank）、图像/视频生成、语音合成与识别等能力。

## 最新动态

**v1.27.0 内置交互式 AI 助手 —— [DashScope SDK Expert](#ai-助手dashscope-sdk-expert)。** 直接运行 `dashscope`（不带任何参数），或直接提问（如 `dashscope "如何流式输出 Generation 结果"`），即可在终端中获得 SDK/API 答疑、可运行示例、CLI 用法和错误诊断。助手基于按领域划分的速查技能（文本、多模态、语音、检索、微调、Agent、CLI），这些技能构建在 SDK 的公开接口——参数、输出、错误码——之上，让你直接提问，无需翻文档。在助手内输入 `/help` 可查看可用命令。

## 安装

安装 DashScope Python SDK，只需运行：
```shell
pip install dashscope
```

基础安装包含 SDK API 调用和 `dashscope` CLI 命令。可选功能组通过 extras 安装：

| Extra | 提供的能力 | 安装命令 |
|-------|----------|---------|
| `acli` | 交互式 AI 助手（DashScope SDK Expert) | `pip install "dashscope[acli]"` |
| `rl` | Agentic RL 微调 | `pip install "dashscope[rl]"` |
| `tokenizer` | 本地 tokenizer（无需下载） | `pip install "dashscope[tokenizer]"` |

如果从 GitHub 克隆了源码，可以通过源码安装：
```shell
pip install -e .
```

## 快速开始

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

### 流式输出

传入 `stream=True` 即可获得一个增量响应的生成器。设置 `incremental_output=True` 后，每个分片只携带新生成的内容（而不是从开头累计的全部文本）：

```python
from dashscope import Generation

responses = Generation.call(
    model="qwen-plus",
    messages=[{"role": "user", "content": "写一首关于大海的诗"}],
    result_format="message",
    stream=True,
    incremental_output=True,
)
for response in responses:
    print(response.output.choices[0].message.content, end="")
```

### 异步（asyncio）

每一个基于 `call` 的类都有一个 `Aio` 前缀的异步版本（`AioGeneration`、`AioImageSynthesis`、`AioMultiModalConversation`、`AioVideoSynthesis`、`AioMultiModalEmbedding`、`AioTextReRank` 等），参数完全一致，配合 `await` 使用：

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

### 错误处理

缺少必填参数（如未传 `model`、`messages`/`prompt`，或没有配置 API Key）会立即抛出 `DashScopeException` 的子类；而 API 层面的失败（模型名不合法、限流等）不会抛异常，而是体现在返回结果里，因此需要检查 `status_code`：

```python
from http import HTTPStatus
from dashscope import Generation
from dashscope.common.error import DashScopeException

try:
    response = Generation.call(model="qwen-plus", messages=[{"role": "user", "content": "Hi"}])
except DashScopeException as e:
    # 本地校验失败时抛出，例如 InputRequired、ModelRequired、AuthenticationError
    print(f"请求参数有误: {e}")
else:
    if response.status_code != HTTPStatus.OK:
        # 服务端返回的错误，例如模型名不合法、触发限流、余额不足
        print(f"接口报错 {response.status_code}: {response.code} - {response.message}")
    else:
        print(response.output.choices[0].message.content)
```

## API Key 鉴权

SDK 使用 API Key 进行鉴权。获取 API Key 请参见[如何获取 API Key](https://help.aliyun.com/zh/model-studio/get-api-key)，或参考[阿里云百炼官方文档（国内站）](https://help.aliyun.com/zh/model-studio/)和[阿里云百炼官方文档（国际站）](https://www.alibabacloud.com/help/en/model-studio/)。

### 使用 API Key

1. 通过代码设置 API Key
```python
import dashscope

dashscope.api_key = 'YOUR-DASHSCOPE-API-KEY'
# 或者通过代码指定 API Key 文件路径
# dashscope.api_key_file_path='~/.dashscope/api_key'

```

2. 通过环境变量设置 API Key

```shell
# a. 直接设置 API Key
export DASHSCOPE_API_KEY='YOUR-DASHSCOPE-API-KEY'

# b. 或者改为指定 API Key 所在的文件路径
export DASHSCOPE_API_KEY_FILE_PATH='~/.dashscope/api_key'
```

设置以上任一环境变量后，`Generation.call(...)`（以及其他所有 SDK 调用）都会自动读取，无需再传 `api_key=` 参数：

```python
from dashscope import Generation

# 自动读取 DASHSCOPE_API_KEY（或 DASHSCOPE_API_KEY_FILE_PATH）
response = Generation.call(model="qwen-plus", messages=[{"role": "user", "content": "Hi"}])
print(response.output.choices[0].message.content)
```

3. 将 API Key 保存到文件
```python
from dashscope import save_api_key

save_api_key(api_key='YOUR-DASHSCOPE-API-KEY',
             api_key_file_path='api_key_file_location or (None, will save to default location "~/.dashscope/api_key"')

```

## 区域与端点配置

默认情况下，SDK 将请求发往华北2（北京）公共端点 `dashscope.aliyuncs.com`。如果你的百炼（Model Studio）业务空间位于其他区域，请在调用前先切换端点。

### 使用 `set_region`

`dashscope.set_region(region, workspace_id)` 会一次性把 HTTP、WebSocket 和 OpenAI-compatible 三个 base URL 指向指定区域。`workspace_id` 为必填项，会作为端点的子域名。

```python
import dashscope

# 切换到新加坡区域，业务空间为 "ws-xxx123"
dashscope.set_region(region="ap-southeast-1", workspace_id="ws-xxx123")

# 之后所有调用都会使用：
#   https://ws-xxx123.ap-southeast-1.maas.aliyuncs.com/api/v1
print(dashscope.base_http_api_url)
```

支持的区域：

| 区域 | 地理位置 |
|--------|----------|
| `cn-beijing` | 华北2（北京） |
| `cn-hongkong` | 中国（香港） |
| `ap-southeast-1` | 新加坡 |
| `ap-northeast-1` | 日本（东京） |
| `eu-central-1` | 德国（法兰克福） |
| `us-east-1` | 美国（弗吉尼亚） |

> **各地域 API Key 相互独立。**每个地域的 API Key（`sk-` 前缀）需在对应地域的百炼控制台创建，不可跨地域混用——使用其他地域的 Key 会返回 `401`。切换地域时请同步更换 `api_key`。

地域特殊说明：

- WebSocket 端点（`wss://.../api-ws/v1/inference`）目前仅 `cn-beijing` 与 `ap-southeast-1` 提供。`set_region` 对所有地域都会设置 `base_websocket_api_url`，但实时语音识别/合成、多模态对话等基于 WebSocket 的实时 API 在其他地域不可用。
- `eu-central-1` / `ap-northeast-1`：部署范围（全球，或欧盟 / 日本）在控制台创建业务空间时选择，不在 API 调用层配置。
- `us-east-1`：模型名带 `-us` 后缀（如 `qwen-plus-us`）限定美国境内推理；不带后缀默认全球推理。
- 批量推理、模型调优、应用开发等高级功能目前仅 `cn-beijing` 与 `ap-southeast-1` 支持。

> `set_region` 修改的是进程级全局变量，因此在单进程同时访问多个区域时并非并发安全。建议在启动时调用一次，或在每次切换前重新调用。

### 使用环境变量

也可以不写代码，直接通过环境变量选择区域：

```shell
export DASHSCOPE_API_REGION='ap-southeast-1'   # 默认：cn-beijing
export DASHSCOPE_WORKSPACE_ID='ws-xxx123'      # 用于解析端点子域名
```

```python
import dashscope

# 自动读取 DASHSCOPE_API_REGION / DASHSCOPE_WORKSPACE_ID
print(dashscope.base_http_api_url)
# https://ws-xxx123.ap-southeast-1.maas.aliyuncs.com/api/v1
```

当通过 `DASHSCOPE_API_REGION` 设置了 MaaS 区域时，SDK 会构造对应的区域端点，并把 `DASHSCOPE_WORKSPACE_ID` 代入其中。你也可以直接覆盖每一个 base URL：

| 环境变量 | 覆盖的对象 |
|----------------------|-----------|
| `DASHSCOPE_HTTP_BASE_URL` | HTTP 端点（`dashscope.base_http_api_url`） |
| `DASHSCOPE_WEBSOCKET_BASE_URL` | WebSocket 端点（`dashscope.base_websocket_api_url`） |
| `DASHSCOPE_COMPATIBLE_BASE_URL` | OpenAI-compatible 端点（`dashscope.base_compatible_api_url`） |

`set_region` 构造的始终是业务空间专属域名。部分地域还提供不含 workspace 子域名的共享域名——北京 `dashscope.aliyuncs.com`、新加坡 `dashscope-intl.aliyuncs.com`、美国 `dashscope-us.aliyuncs.com`，如需使用可通过上面的环境变量直接覆盖。

### OpenAI-compatible 对话补全

SDK 提供了 OpenAI-compatible 的对话补全入口，它会请求 `dashscope.base_compatible_api_url`（请求路径 `chat/completions`）——无需额外安装 `openai` 库，并自动跟随上面配置的区域。

```python
import dashscope
from dashscope.aigc.chat_completion import Completions

dashscope.set_region(region="cn-hongkong", workspace_id="ws-hk-789")

response = Completions.create(
    model="qwen-max",
    messages=[{"role": "user", "content": "你好"}],
    api_key="YOUR-DASHSCOPE-API-KEY",
    stream=False,  # 设为 True 则返回 ChatCompletionChunk 生成器
)
print(response)
```

完整可运行示例见 [`samples/set_region_example.py`](samples/set_region_example.py)。

## AI 助手：DashScope SDK Expert

SDK 内置了交互式 AI 助手 **DashScope SDK Expert**，基于随包提供的 Agentic CLI（`dashscope/acli`）框架构建。对于 DashScope SDK/CLI 用户，它是获取开发咨询和 AI 编码帮助的推荐方式——直接在终端中解答 SDK/API 问题、生成可运行示例、展示 CLI 用法、诊断错误。

- 直接运行 `dashscope`（不带参数）即可启动助手。首次运行时会提示安装 SDK Expert 知识包（按领域划分的速查技能：文本、多模态、语音、检索、微调、Agent、CLI），使助手的指导来自 SDK 的公开接口——参数、输出、错误码——而无需阅读源码
- 直接提问代替翻文档——如 `dashscope "如何流式输出 Generation 结果"` 或 `dashscope "取消微调任务的 CLI 命令"`。在助手内输入 `/help` 可列出可用命令（`/setup`、`/skill`、`/stats` 等）；经典 SDK 子命令依然可用，无法识别的命令会自动转给助手处理
- 完整使用指南：[DashScope SDK Expert 文档](https://help.aliyun.com/zh/model-studio/dashscope-sdk-expert)

## 支持的模型

| 类别 | 推荐模型 | SDK 类 |
|----------|-------------------|-----------|
| 文本生成 | qwen3.8-max、qwen3.7-max、qwen3.7-plus、qwen3.6-flash | `Generation` |
| 多模态理解 | qwen3.5-omni-plus、qwen3.7-plus（视觉） | `MultiModalConversation` |
| 文本向量 | text-embedding-v4、text-embedding-v3 | `TextEmbedding` |
| 多模态向量 | tongyi-embedding-vision-plus、qwen3-vl-embedding | `MultiModalEmbedding` |
| 文本重排 | qwen3-rerank、gte-rerank-v2 | `TextReRank` |
| 图像生成 | wan2.7-image-pro、qwen-image-2.0-pro | `ImageSynthesis` |
| 视频生成 | wan2.7-t2v、wan2.7-i2v、happyhorse-1.0-t2v/i2v | `VideoSynthesis` |
| 语音合成（TTS） | cosyvoice-v3.5-plus、cosyvoice-v1 | `SpeechSynthesizer`、`HttpSpeechSynthesizer` |
| 语音识别（ASR） | fun-asr-realtime、fun-asr、paraformer-v1 | `Transcription` |
| 全模态（实时） | qwen3.5-omni-plus-realtime | `MultiModalConversation` |

最新模型列表请访问[百炼模型广场](https://bailian.console.aliyun.com/)。

## 使用示例

更多可运行脚本见 [`samples/`](samples)。

### 多模态理解（视觉）

```python
from dashscope import MultiModalConversation

messages = [{
    "role": "user",
    "content": [
        {"image": "https://help-static-aliyun-doc.aliyuncs.com/file-manage-files/zh-CN/20241022/emyrja/dog_and_girl.jpeg"},
        {"text": "图中描绘的是什么景象?"},
    ],
}]
response = MultiModalConversation.call(model="qwen-vl-max", messages=messages)
print(response.output.choices[0].message.content[0]["text"])
```

使用 `AioMultiModalConversation` 可获得 `async`/`await` 形式：

```python
import asyncio
from dashscope import AioMultiModalConversation

async def main():
    messages = [{
        "role": "user",
        "content": [
            {"image": "https://help-static-aliyun-doc.aliyuncs.com/file-manage-files/zh-CN/20241022/emyrja/dog_and_girl.jpeg"},
            {"text": "图中描绘的是什么景象?"},
        ],
    }]
    response = await AioMultiModalConversation.call(model="qwen-vl-max", messages=messages)
    print(response.output.choices[0].message.content[0]["text"])

asyncio.run(main())
```

### 使用本地文件

任何接受 URL 的字段（messages 中的 `image`、`audio`、`video`，`ImageSynthesis` 的 `images` 等）同样支持本地文件路径——SDK 会自动上传到 OSS，无需手动设置请求头：

```python
from dashscope import MultiModalConversation

messages = [{
    "role": "user",
    "content": [
        {"image": "/path/to/local/image.jpg"},
        {"text": "图中是什么内容？"},
    ],
}]
response = MultiModalConversation.call(model="qwen-vl-max", messages=messages)
print(response.output.choices[0].message.content[0]["text"])
```

### 文本向量（Embedding）

```python
from dashscope import TextEmbedding

resp = TextEmbedding.call(
    model=TextEmbedding.Models.text_embedding_v3,
    input=["风急天高猿啸哀", "渚清沙白鸟飞回"],
    text_type="document",
)
for e in resp.output["embeddings"]:
    print(e["text_index"], e["embedding"][:3])
```

### 多模态向量（Embedding）

```python
from dashscope import MultiModalEmbedding

resp = MultiModalEmbedding.call(
    model="multimodal-embedding-v1",
    input=[{"image": "https://dashscope.oss-cn-beijing.aliyuncs.com/images/256_1.png"}],
)
print(resp.output)
```

### 批量（离线）文本向量

对于大批量文本，可以提交一个文件（每行一条文本）进行异步批量向量化，而不必逐条调用 `TextEmbedding.call`：

```python
from dashscope import BatchTextEmbedding

resp = BatchTextEmbedding.call(
    model=BatchTextEmbedding.Models.text_embedding_async_v2,
    url="https://example.com/texts.txt",
)
print(resp.output.task_id, resp.output.task_status)
if resp.output.task_status == "SUCCEEDED":
    print(resp.output.url)  # 从这里下载结果文件
```

### 文本重排（ReRank）

```python
from dashscope import TextReRank

resp = TextReRank.call(
    model=TextReRank.Models.gte_rerank,
    query="哈尔滨在哪？",
    documents=[
        "黑龙江离俄罗斯很近",
        "哈尔滨是中国黑龙江省的省会，位于中国东北",
    ],
    return_documents=True,
    top_n=1,
)
for r in resp.output.results:
    print(r.index, r.relevance_score, r.document)
```

使用 `AioTextReRank` 可获得 `async`/`await` 形式：

```python
import asyncio
from dashscope import AioTextReRank

async def main():
    resp = await AioTextReRank.call(
        model=AioTextReRank.Models.gte_rerank,
        query="哈尔滨在哪？",
        documents=["黑龙江离俄罗斯很近", "哈尔滨是中国黑龙江省的省会，位于中国东北"],
        return_documents=True,
        top_n=1,
    )
    for r in resp.output.results:
        print(r.index, r.relevance_score, r.document)

asyncio.run(main())
```

### 代码生成

`CodeGeneration` 面向特定编程场景（`Scenes`）：自然语言生成代码、代码解释、生成注释、生成 commit message、生成单元测试、代码问答、自然语言生成 SQL。

```python
from dashscope import CodeGeneration

response = CodeGeneration.call(
    model=CodeGeneration.Models.tongyi_lingma_v1,
    scene=CodeGeneration.Scenes.nl2code,
    message=[
        {"role": "user", "content": "计算给定路径下所有文件的总大小"},
        {"role": "attachment", "meta": {"language": "python"}},
    ],
)
print(response.output)
```

### 图像生成

```python
from http import HTTPStatus
from dashscope import ImageSynthesis

rsp = ImageSynthesis.call(
    model="wanx2.1-t2i-turbo",
    prompt="一间有着精致窗户的花店，漂亮的木质门，摆放着花朵",
    n=1,
    size="1024*1024",
)
if rsp.status_code == HTTPStatus.OK:
    for result in rsp.output.results:
        print(result.url)
```

### 视频生成

视频生成是异步任务；`call` 会阻塞直到任务完成，也可以用 `async_call` + `wait`/`fetch` 手动轮询。

```python
from http import HTTPStatus
from dashscope import VideoSynthesis

rsp = VideoSynthesis.call(
    model="wan2.7-t2v",
    prompt="一只小猫在月光下奔跑",
    audio=True,
    watermark=True,
)
if rsp.status_code == HTTPStatus.OK:
    print(rsp.output.video_url)
```

### 语音合成（TTS）

Qwen-TTS 系列模型通过 `MultiModalConversation` 调用，传入 `text`/`voice` 而非 `messages`：

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

CosyVoice 系列模型使用专门的 `SpeechSynthesizer`：

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

`HttpSpeechSynthesizer` 通过普通 HTTP（无需 WebSocket）调用语音合成，适用于无法保持持久连接的环境：

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

### 流式语音合成（CosyVoice v2）

流式传入文本，并通过回调实时接收生成中的音频数据：

```python
from dashscope.audio.tts_v2 import ResultCallback, SpeechSynthesizer

class Callback(ResultCallback):
    def on_data(self, data: bytes) -> None:
        with open("output.mp3", "ab") as f:
            f.write(data)

synthesizer = SpeechSynthesizer(model="cosyvoice-v2", voice="longxiaochun_v2", callback=Callback())
for text in ["你好，", "这是流式", "语音合成。"]:
    synthesizer.streaming_call(text)
synthesizer.streaming_complete()
```

### 语音识别（ASR）

`qwen3-asr-flash` 等语音理解模型通过 `MultiModalConversation` 调用：

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

基于文件的批量语音识别使用 `Transcription`：

```python
from dashscope.audio.asr import Transcription

response = Transcription.call(
    model=Transcription.Models.paraformer_v1,
    file_urls=["https://example.com/audio.wav"],
)
if response.output.task_status == "SUCCEEDED":
    print(response.output.results)
```

### 流式语音识别

对于实时/流式音频源，逐帧发送 PCM 数据，并通过回调接收识别结果（这里以分块读取文件来演示该模式——请将文件读取循环替换为你的实时音频源）：

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

### 百炼应用（Agent 应用）

调用你在[百炼应用中心](https://bailian.console.aliyun.com/)搭建的应用：

```python
from http import HTTPStatus
from dashscope import Application

responses = Application.call(
    app_id="YOUR-APP-ID",
    prompt="总结文件内容",
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

### AgentStudio（托管 Agent）

`dashscope.agentstudio` 用于管理在百炼 AgentStudio 中搭建的 Agent——创建 Agent/会话并流式接收对话事件，或创建按 cron 计划定时运行 Agent 的"部署（deployment）"：

```python
from dashscope.agentstudio import Client
from dashscope.agentstudio.types import user_message

client = Client(api_key="sk-xxx")
agent = client.agents.create(name="demo", model="qwen-plus")
session = client.sessions.create(agent=agent.id)
client.sessions.events.send(session.id, [user_message("Hello!")])
with client.sessions.events.stream(session.id) as stream:
    for event in stream:
        print(event.type, event.to_dict())
        if event.type == "session_status":
            break
```

注意：`Client()` 读取的是环境变量 `DASHSCOPE_WORKSPACE`（不带 `_ID` 后缀）——与[区域配置](#区域与端点配置)中使用的 `DASHSCOPE_WORKSPACE_ID` 是两个不同的变量。完整的定时部署示例见 [`samples/agentstudio_deployments.py`](samples/agentstudio_deployments.py)。

### 本地分词（Tokenization）

无需调用接口，即可在本地对 Qwen 系列模型进行分词计数或编解码（需要 `pip install "dashscope[tokenizer]"`）：

```python
from dashscope.tokenizers.tokenizer import get_tokenizer

tokenizer = get_tokenizer("qwen-turbo")  # 适用于任意 qwen-* 模型
tokens = tokenizer.encode("这个是千问tokenizer")
print(len(tokens))               # token 数量
print(tokenizer.decode(tokens))  # 解码还原文本
```

### 模型微调（Fine-tuning）

上传训练文件、创建微调任务，并轮询直至完成（Agentic RL 微调需要 `pip install "dashscope[rl]"`；经典有监督微调无需额外安装）：

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

result = FineTunes.wait(job.output.job_id)  # 每 30 秒轮询一次，直至完成
print(result.output.status)
```

关于基于自定义 rollout/reward 函数的 Agentic RL 微调（YAML 驱动的训练任务、链路追踪/可观测性），请参见 [`dashscope/finetune/reinforcement/examples/workspace/README-zh.md`](dashscope/finetune/reinforcement/examples/workspace/README-zh.md)（快速开始）和 [`UserGuide-zh.md`](dashscope/finetune/reinforcement/examples/workspace/UserGuide-zh.md)（完整参考）。

### 部署微调模型

将微调任务产出的模型部署上线，之后即可像调用普通模型一样调用它：

```python
from dashscope import Deployments, Generation

deployment = Deployments.call(model=result.output.finetuned_output, capacity=1)
deployed_model = deployment.output.deployed_model

# 轮询直至 deployment.output.status == "RUNNING"，之后即可像调用普通模型一样调用：
status = Deployments.get(deployed_model).output.status
response = Generation.call(model=deployed_model, messages=[{"role": "user", "content": "Hi"}])
```

## CLI 用法

每一项 SDK 能力都可以通过 `dashscope` 子命令直接使用（随基础包一起安装），便于脚本化或快速验证，无需编写 Python 代码：

```shell
# 文本生成
dashscope generation create -m qwen-plus -p "Who are you?"
dashscope generation create -m qwen-plus -p "写一首关于大海的诗" --stream

# 查看 / 检索可用模型
dashscope models list
dashscope models get qwen-plus

# 上传用于微调的文件
dashscope files upload -f ./train.jsonl -p fine_tune
```

运行 `dashscope --help` 或 `dashscope <command> --help`（如 `dashscope generation --help`）可查看全部命令组（`generation`、`ft`、`files`、`deployments`、`models`、`embeddings`、`rerank`、`tokenization`、`application`、`image-synthesis`、`video-synthesis`、`multimodal-conversation`、`transcription`、`speech-synthesis`、`rl` 等）及其参数。不带任何参数运行 `dashscope` 则会启动交互式 [AI 助手](#ai-助手dashscope-sdk-expert)。

## Shell 命令补全

运行对应命令一次，然后重启 Shell（或重新 source 配置文件）：

| Shell | 安装命令 |
|-------|-----------------|
| **bash** | `dashscope --install-completion bash` |
| **zsh** | `dashscope --install-completion zsh` |
| **fish** | `dashscope --install-completion fish` |

如需预览补全脚本而不安装：
```shell
dashscope --show-completion bash
```

## 日志

在导入 `dashscope` 之前设置 `DASHSCOPE_LOGGING_LEVEL`（`info` 或 `debug`），SDK 会自动附加一个控制台日志 handler：

```shell
export DASHSCOPE_LOGGING_LEVEL='info'
```

```python
from dashscope import Generation

# 请求详情会自动打印到控制台，例如：
# 2024-01-01 12:00:00,000 - dashscope - ... - INFO - request: POST https://...
response = Generation.call(model="qwen-plus", messages=[{"role": "user", "content": "Hi"}])
```

## 输出

每一次 SDK 调用（流式场景下为每一个分片）都会返回一个包含以下字段的响应对象：

```python
response = Generation.call(model="qwen-plus", messages=[{"role": "user", "content": "Hi"}])

response.request_id    # str: 请求 ID，反馈问题时会用到
response.status_code   # int: HTTP 状态码，200 表示成功
response.code          # str: 失败时的错误码，成功时为空字符串
response.message       # str: 失败时的错误信息，成功时为空字符串
response.output        # Any: 请求输出，具体结构取决于调用的接口
response.usage         # Any: Token / 用量信息
```

## 许可证

本项目采用 Apache License (Version 2.0) 许可证。
