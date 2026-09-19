# DashScope Python SDK

> **English** | [中文](README_zh.md) | [日本語](README_ja.md)

The DashScope Python SDK provides a comprehensive interface to [Alibaba Cloud Model Studio (Bailian)](https://www.alibabacloud.com/help/en/model-studio/) APIs, covering text generation, multi-modal understanding, embeddings, reranking, image/video generation, speech synthesis & recognition, and more.

## What is New

**v1.27.0 ships an interactive AI assistant — [DashScope SDK Expert](#ai-assistant-dashscope-sdk-expert).** Run `dashscope` with no arguments (or ask directly, e.g. `dashscope "how do I stream Generation output"`) to get SDK/API answers, runnable examples, CLI usage, and error diagnosis right in your terminal. Guidance is drawn from per-domain quick-reference skills (text, multimodal, speech, retrieval, fine-tuning, agent, cli) built on the SDK's public interfaces — parameters, outputs, and error codes — so you can ask instead of reading the docs. Type `/help` inside the assistant to view available commands.

## Installation
To install the DashScope Python SDK, simply run:
```shell
pip install dashscope
```

The base install covers SDK API calls and the `dashscope` CLI command.
Optional feature groups are available as extras:

| Extra | Provides | Install |
|-------|----------|---------|
| `acli` | Interactive AI assistant (DashScope SDK Expert) | `pip install "dashscope[acli]"` |
| `rl` | Agentic RL fine-tuning | `pip install "dashscope[rl]"` |
| `tokenizer` | Local tokenizer without downloads | `pip install "dashscope[tokenizer]"` |

If you clone the code from github, you can install from  source by running:
```shell
pip install -e .
```


## Quick Start

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

### Streaming Output

Pass `stream=True` to get a generator of incremental responses. With
`incremental_output=True`, each chunk carries only the newly generated
tokens (instead of the cumulative text so far):

```python
from dashscope import Generation

responses = Generation.call(
    model="qwen-plus",
    messages=[{"role": "user", "content": "Write a haiku about the sea."}],
    result_format="message",
    stream=True,
    incremental_output=True,
)
for response in responses:
    print(response.output.choices[0].message.content, end="")
```

### Async / asyncio

Every `call`-based class has an `Aio`-prefixed async counterpart
(`AioGeneration`, `AioImageSynthesis`, `AioMultiModalConversation`,
`AioVideoSynthesis`, `AioMultiModalEmbedding`, `AioTextReRank`, ...) with the
same parameters, used with `await`:

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

### Error Handling

Missing required arguments (e.g. no `model`, no `messages`/`prompt`, no API
key) raise a `DashScopeException` subclass immediately; API-level failures
(bad model name, rate limits, etc.) are returned in the response instead of
raised, so check `status_code`:

```python
from http import HTTPStatus
from dashscope import Generation
from dashscope.common.error import DashScopeException

try:
    response = Generation.call(model="qwen-plus", messages=[{"role": "user", "content": "Hi"}])
except DashScopeException as e:
    # Raised locally for invalid input, e.g. InputRequired, ModelRequired, AuthenticationError
    print(f"Invalid request: {e}")
else:
    if response.status_code != HTTPStatus.OK:
        # Returned by the API, e.g. invalid model, rate limiting, quota exceeded
        print(f"API error {response.status_code}: {response.code} - {response.message}")
    else:
        print(response.output.choices[0].message.content)
```

For the full list of exception classes and when each is raised, see the [Error Handling Reference](docs/guides/error-handling.md).

## API Key Authentication

The SDK uses API key for authentication. To obtain an API Key, see [How to get an API Key](https://help.aliyun.com/en/model-studio/get-api-key). Please refer to [official documentation for alibabacloud china](https://www.alibabacloud.com/help/en/model-studio/) and [official documentation for alibabacloud international](https://www.alibabacloud.com/help/en/model-studio/) regarding how to obtain your api-key.

### Using the API Key

1. Set the API key via code
```python
import dashscope

dashscope.api_key = 'YOUR-DASHSCOPE-API-KEY'
# Or specify the API key file path via code
# dashscope.api_key_file_path='~/.dashscope/api_key'

```

2. Set the API key via environment variables

```shell
# a. Set the API key directly
export DASHSCOPE_API_KEY='YOUR-DASHSCOPE-API-KEY'

# b. Or point to a file containing the key instead
export DASHSCOPE_API_KEY_FILE_PATH='~/.dashscope/api_key'
```

Either variable makes `Generation.call(...)` (and every other SDK call) pick up the key automatically, with no `api_key=` argument needed:

```python
from dashscope import Generation

# DASHSCOPE_API_KEY (or DASHSCOPE_API_KEY_FILE_PATH) is read automatically
response = Generation.call(model="qwen-plus", messages=[{"role": "user", "content": "Hi"}])
print(response.output.choices[0].message.content)
```

3. Save the API key to a file
```python
from dashscope import save_api_key

save_api_key(api_key='YOUR-DASHSCOPE-API-KEY',
             api_key_file_path='api_key_file_location or (None, will save to default location "~/.dashscope/api_key"')

```

## Region and Endpoint Configuration

By default the SDK sends requests to the China (Beijing) public endpoint `dashscope.aliyuncs.com`. If your Model Studio (Bailian) workspace lives in another region, switch the endpoint before making calls.

### Using `set_region`

`dashscope.set_region(region, workspace_id)` points the HTTP, WebSocket and OpenAI-compatible base URLs at the given region in a single call. `workspace_id` is required and is used as the endpoint subdomain.

```python
import dashscope

# Switch to the Singapore region for workspace "ws-xxx123"
dashscope.set_region(region="ap-southeast-1", workspace_id="ws-xxx123")

# All subsequent calls use:
#   https://ws-xxx123.ap-southeast-1.maas.aliyuncs.com/api/v1
print(dashscope.base_http_api_url)
```

Supported regions:

| Region | Location |
|--------|----------|
| `cn-beijing` | China (Beijing) |
| `cn-hongkong` | China (Hong Kong) |
| `ap-southeast-1` | Singapore |
| `ap-northeast-1` | Japan (Tokyo) |
| `eu-central-1` | Germany (Frankfurt) |
| `us-east-1` | US (Virginia) |

> **API keys are region-specific.** Each region issues its own API keys (`sk-` prefix) in its Model Studio console, and keys cannot be mixed across regions — using a key from another region fails with `401`. Switch `api_key` together with the region.

Region-specific notes:

- WebSocket endpoints (`wss://.../api-ws/v1/inference`) are only served in `cn-beijing` and `ap-southeast-1`. `set_region` still sets `base_websocket_api_url` for every region, but WebSocket-based realtime APIs (realtime speech recognition/synthesis, multimodal dialog, etc.) are not available in the other regions.
- `eu-central-1` / `ap-northeast-1`: the deployment scope (Global, or EU / Japan) is chosen when the workspace is created in the console, not per API call.
- `us-east-1`: model names with the `-us` suffix (e.g. `qwen-plus-us`) restrict inference to the US; names without the suffix default to global inference.
- Batch inference, model fine-tuning and application development are currently only available in `cn-beijing` and `ap-southeast-1`.

> `set_region` updates process-wide globals, so it is not concurrency-safe when a single process talks to multiple regions at the same time. Call it once at startup, or re-call it before each switch.

### Using environment variables

You can also select the region without code:

```shell
export DASHSCOPE_API_REGION='ap-southeast-1'   # default: cn-beijing
export DASHSCOPE_WORKSPACE_ID='ws-xxx123'      # used to resolve the endpoint subdomain
```

```python
import dashscope

# Picks up DASHSCOPE_API_REGION / DASHSCOPE_WORKSPACE_ID automatically
print(dashscope.base_http_api_url)
# https://ws-xxx123.ap-southeast-1.maas.aliyuncs.com/api/v1
```

When a MaaS region is set via `DASHSCOPE_API_REGION`, the SDK builds the regional endpoints and substitutes `DASHSCOPE_WORKSPACE_ID` into them. You can also override each base URL directly:

| Environment variable | Overrides |
|----------------------|-----------|
| `DASHSCOPE_HTTP_BASE_URL` | HTTP endpoint (`dashscope.base_http_api_url`) |
| `DASHSCOPE_WEBSOCKET_BASE_URL` | WebSocket endpoint (`dashscope.base_websocket_api_url`) |
| `DASHSCOPE_COMPATIBLE_BASE_URL` | OpenAI-compatible endpoint (`dashscope.base_compatible_api_url`) |

`set_region` always builds workspace-exclusive endpoints. Some regions also offer shared domains without a workspace subdomain — `dashscope.aliyuncs.com` (Beijing), `dashscope-intl.aliyuncs.com` (Singapore) and `dashscope-us.aliyuncs.com` (US Virginia); use the override variables above to point at them.

### OpenAI-compatible chat completions

The SDK exposes an OpenAI-compatible chat completions entry that talks to `dashscope.base_compatible_api_url` (request path `chat/completions`) — no extra `openai` package required. It follows the region configured above.

```python
import dashscope
from dashscope.aigc.chat_completion import Completions

dashscope.set_region(region="cn-hongkong", workspace_id="ws-hk-789")

response = Completions.create(
    model="qwen-max",
    messages=[{"role": "user", "content": "Hello"}],
    api_key="YOUR-DASHSCOPE-API-KEY",
    stream=False,  # set True to get a generator of ChatCompletionChunk
)
print(response)
```

A complete runnable example is available in [`samples/set_region_example.py`](samples/set_region_example.py).

For request timeouts, custom headers, proxy support, and closing shared connection pools, see the [Advanced Configuration guide](docs/guides/configuration.md).

## AI Assistant: DashScope SDK Expert

The SDK ships with an interactive AI assistant, **DashScope SDK Expert**, built on the bundled Agentic CLI (`dashscope/acli`) framework. For DashScope SDK/CLI users it is the recommended way to get development consultation and AI coding help — answering SDK/API questions, generating runnable examples, showing CLI usage, and diagnosing errors, right in your terminal.

- Run `dashscope` with no arguments to start the assistant. On first run it offers to install the SDK Expert knowledge pack (per-domain quick-reference skills: text, multimodal, speech, retrieval, fine-tuning, agent, cli), so guidance comes from the SDK's public interfaces — parameters, outputs, error codes — without reading the source
- Ask it instead of reading docs — e.g. `dashscope "how do I stream Generation output"` or `dashscope "CLI command to cancel a fine-tuning job"`. Type `/help` inside the assistant to list available commands (`/setup`, `/skill`, `/stats`, ...); classic SDK subcommands still work, and unrecognized commands are routed to the assistant
- Full walkthrough: [DashScope SDK Expert guide](https://help.aliyun.com/en/model-studio/dashscope-sdk-expert)

## Supported Models

| Category | Recommended Models | SDK Class |
|----------|-------------------|-----------|
| Text Generation | qwen3.8-max, qwen3.7-max, qwen3.7-plus, qwen3.6-flash | `Generation` |
| Multi-Modal Understanding | qwen3.5-omni-plus, qwen3.7-plus (vision) | `MultiModalConversation` |
| Text Embedding | text-embedding-v4, text-embedding-v3 | `TextEmbedding` |
| Multi-Modal Embedding | tongyi-embedding-vision-plus, qwen3-vl-embedding | `MultiModalEmbedding` |
| Text ReRank | qwen3-rerank, gte-rerank-v2 | `TextReRank` |
| Image Generation | wan2.7-image-pro, qwen-image-2.0-pro | `ImageSynthesis` |
| Video Generation | wan2.7-t2v, wan2.7-i2v, happyhorse-1.0-t2v/i2v | `VideoSynthesis` |
| Speech Synthesis (TTS) | cosyvoice-v3.5-plus, cosyvoice-v1 | `SpeechSynthesizer`, `HttpSpeechSynthesizer` |
| Speech Recognition (ASR) | fun-asr-realtime, fun-asr, paraformer-v1 | `Transcription` |
| Omni (Real-time) | qwen3.5-omni-plus-realtime | `MultiModalConversation` |

For the latest model list, visit [Bailian Model Plaza](https://bailian.console.aliyun.com/).

## Usage Examples

More runnable scripts are available under [`samples/`](samples).

### Multimodal Understanding (Vision)

```python
from dashscope import MultiModalConversation

messages = [{
    "role": "user",
    "content": [
        {"image": "https://help-static-aliyun-doc.aliyuncs.com/file-manage-files/zh-CN/20241022/emyrja/dog_and_girl.jpeg"},
        {"text": "What does this picture describe?"},
    ],
}]
response = MultiModalConversation.call(model="qwen-vl-max", messages=messages)
print(response.output.choices[0].message.content[0]["text"])
```

Use `AioMultiModalConversation` for the `async`/`await` form:

```python
import asyncio
from dashscope import AioMultiModalConversation

async def main():
    messages = [{
        "role": "user",
        "content": [
            {"image": "https://help-static-aliyun-doc.aliyuncs.com/file-manage-files/zh-CN/20241022/emyrja/dog_and_girl.jpeg"},
            {"text": "What does this picture describe?"},
        ],
    }]
    response = await AioMultiModalConversation.call(model="qwen-vl-max", messages=messages)
    print(response.output.choices[0].message.content[0]["text"])

asyncio.run(main())
```

### Using Local Files

Every field that accepts a URL (`image`, `audio`, `video` in messages; `images` on `ImageSynthesis`, etc.) also accepts a local file path — the SDK uploads it to OSS automatically, no manual header needed:

```python
from dashscope import MultiModalConversation

messages = [{
    "role": "user",
    "content": [
        {"image": "/path/to/local/image.jpg"},
        {"text": "What is in this image?"},
    ],
}]
response = MultiModalConversation.call(model="qwen-vl-max", messages=messages)
print(response.output.choices[0].message.content[0]["text"])
```

### Text Embedding

```python
from dashscope import TextEmbedding

resp = TextEmbedding.call(
    model=TextEmbedding.Models.text_embedding_v3,
    input=["The wind is swift, the sky is high", "The islets are clear, the sand is white"],
    text_type="document",
)
for e in resp.output["embeddings"]:
    print(e["text_index"], e["embedding"][:3])
```

### Multimodal Embedding

```python
from dashscope import MultiModalEmbedding

resp = MultiModalEmbedding.call(
    model="multimodal-embedding-v1",
    input=[{"image": "https://dashscope.oss-cn-beijing.aliyuncs.com/images/256_1.png"}],
)
print(resp.output)
```

### Batch (Offline) Text Embedding

For large volumes of text, submit a file (one text per line) for asynchronous batch embedding instead of calling `TextEmbedding.call` per item:

```python
from dashscope import BatchTextEmbedding

resp = BatchTextEmbedding.call(
    model=BatchTextEmbedding.Models.text_embedding_async_v2,
    url="https://example.com/texts.txt",
)
print(resp.output.task_id, resp.output.task_status)
if resp.output.task_status == "SUCCEEDED":
    print(resp.output.url)  # download the result file from here
```

### Text ReRank

```python
from dashscope import TextReRank

resp = TextReRank.call(
    model=TextReRank.Models.gte_rerank,
    query="What is the capital of China?",
    documents=[
        "The capital of China is Beijing.",
        "China is a large country in East Asia.",
    ],
    return_documents=True,
    top_n=1,
)
for r in resp.output.results:
    print(r.index, r.relevance_score, r.document)
```

Use `AioTextReRank` for the `async`/`await` form:

```python
import asyncio
from dashscope import AioTextReRank

async def main():
    resp = await AioTextReRank.call(
        model=AioTextReRank.Models.gte_rerank,
        query="What is the capital of China?",
        documents=["The capital of China is Beijing.", "China is a large country in East Asia."],
        return_documents=True,
        top_n=1,
    )
    for r in resp.output.results:
        print(r.index, r.relevance_score, r.document)

asyncio.run(main())
```

### Code Generation

`CodeGeneration` powers task-specific coding scenarios (`Scenes`): natural-language-to-code, code explanation, comment generation, commit messages, unit tests, code Q&A, and natural-language-to-SQL.

```python
from dashscope import CodeGeneration

response = CodeGeneration.call(
    model=CodeGeneration.Models.tongyi_lingma_v1,
    scene=CodeGeneration.Scenes.nl2code,
    message=[
        {"role": "user", "content": "Compute the total size of all files under a given path"},
        {"role": "attachment", "meta": {"language": "python"}},
    ],
)
print(response.output)
```

### Image Generation

```python
from http import HTTPStatus
from dashscope import ImageSynthesis

rsp = ImageSynthesis.call(
    model="wanx2.1-t2i-turbo",
    prompt="a flower shop with delicate windows and a wooden door",
    n=1,
    size="1024*1024",
)
if rsp.status_code == HTTPStatus.OK:
    for result in rsp.output.results:
        print(result.url)
```

### Video Generation

Video generation runs as an async task; `call` blocks until it completes, or use `async_call` + `wait`/`fetch` to poll manually.

```python
from http import HTTPStatus
from dashscope import VideoSynthesis

rsp = VideoSynthesis.call(
    model="wan2.7-t2v",
    prompt="a kitten running under the moonlight",
    audio=True,
    watermark=True,
)
if rsp.status_code == HTTPStatus.OK:
    print(rsp.output.video_url)
```

### Speech Synthesis (TTS)

Qwen-TTS models are called through `MultiModalConversation`, passing `text`/`voice` instead of `messages`:

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

CosyVoice models use the dedicated `SpeechSynthesizer`:

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

`HttpSpeechSynthesizer` calls TTS over plain HTTP (no WebSocket), useful in environments that can't hold a persistent connection:

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

### Streaming Speech Synthesis (CosyVoice v2)

Stream text in incrementally and receive audio bytes as they're generated, via a callback:

```python
from dashscope.audio.tts_v2 import ResultCallback, SpeechSynthesizer

class Callback(ResultCallback):
    def on_data(self, data: bytes) -> None:
        with open("output.mp3", "ab") as f:
            f.write(data)

synthesizer = SpeechSynthesizer(model="cosyvoice-v2", voice="longxiaochun_v2", callback=Callback())
for text in ["Hello, ", "this is streaming ", "text-to-speech."]:
    synthesizer.streaming_call(text)
synthesizer.streaming_complete()
```

### Speech Recognition (ASR)

`qwen3-asr-flash` and similar audio-understanding models are called through `MultiModalConversation`:

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

File-based batch transcription uses `Transcription`:

```python
from dashscope.audio.asr import Transcription

response = Transcription.call(
    model=Transcription.Models.paraformer_v1,
    file_urls=["https://example.com/audio.wav"],
)
if response.output.task_status == "SUCCEEDED":
    print(response.output.results)
```

### Streaming Speech Recognition

For a live/streaming audio source, feed PCM frames one at a time and receive results through a callback (here reading a file in chunks to demonstrate the pattern — replace the file loop with your live audio source):

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

### Bailian Application (Agent App)

Call an app you built in [Bailian's Application Center](https://bailian.console.aliyun.com/):

```python
from http import HTTPStatus
from dashscope import Application

responses = Application.call(
    app_id="YOUR-APP-ID",
    prompt="Summarize this file",
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

### AgentStudio (Managed Agents)

`dashscope.agentstudio` manages agents built in Bailian's AgentStudio product — creating agents/sessions and streaming conversational events, or creating scheduled "deployments" that run an agent on a cron schedule:

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

Note: `Client()` reads the `DASHSCOPE_WORKSPACE` environment variable (no `_ID` suffix) — different from the SDK-wide `DASHSCOPE_WORKSPACE_ID` used for [region configuration](#region-and-endpoint-configuration). A complete scheduled-deployment example is in [`samples/agentstudio_deployments.py`](samples/agentstudio_deployments.py).

### Local Tokenization

Count or encode/decode tokens for Qwen models locally, without an API call (requires `pip install "dashscope[tokenizer]"`):

```python
from dashscope.tokenizers.tokenizer import get_tokenizer

tokenizer = get_tokenizer("qwen-turbo")  # works for any qwen-* model
tokens = tokenizer.encode("这个是千问tokenizer")
print(len(tokens))               # token count
print(tokenizer.decode(tokens))  # round-trip back to text
```

### Fine-tuning

Upload a training file, launch a fine-tune job, and poll it to completion (requires `pip install "dashscope[rl]"` for agentic RL fine-tuning; classic supervised fine-tuning needs no extra):

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

result = FineTunes.wait(job.output.job_id)  # polls every 30s until done
print(result.output.status)
```

For custom rollout/reward-function-driven Agentic RL fine-tuning (YAML-driven training jobs, tracing/observability), see the dedicated guide in [`dashscope/finetune/reinforcement/examples/workspace/README.md`](dashscope/finetune/reinforcement/examples/workspace/README.md) (quick start) and [`UserGuide.md`](dashscope/finetune/reinforcement/examples/workspace/UserGuide.md) (full reference).

### Deploying a Fine-tuned Model

Deploy the model produced by a fine-tune job so it can be called like any other model:

```python
from dashscope import Deployments, Generation

deployment = Deployments.call(model=result.output.finetuned_output, capacity=1)
deployed_model = deployment.output.deployed_model

# Poll until deployment.output.status == "RUNNING", then call it like any model:
status = Deployments.get(deployed_model).output.status
response = Generation.call(model=deployed_model, messages=[{"role": "user", "content": "Hi"}])
```

For the full job/deployment lifecycle (listing, canceling, streaming events, scaling), see the [Fine-tuning & Deployment Lifecycle guide](docs/guides/fine-tuning.md).

### Assistants API (Deprecated)

The legacy Assistants API (`Assistants`, `Threads`, `Runs`, `Messages`) still works but is deprecated — see the [Assistants API guide](docs/guides/assistants.md) for the full surface and migration notes. New code should use [`Generation`](#quick-start) or [`MultiModalConversation`](#multimodal-understanding-vision) instead.

## CLI Usage

Every SDK capability is also available as a `dashscope` sub-command (installed with the base package), for scripting or quick checks without writing Python:

```shell
# Text generation
dashscope generation create -m qwen-plus -p "Who are you?"
dashscope generation create -m qwen-plus -p "Write a haiku about the sea" --stream

# List / inspect available models
dashscope models list
dashscope models get qwen-plus

# Upload a file for fine-tuning
dashscope files upload -f ./train.jsonl -p fine_tune
```

Run `dashscope --help` or `dashscope <command> --help` (e.g. `dashscope generation --help`) to see every command group (`generation`, `ft`, `files`, `deployments`, `models`, `embeddings`, `rerank`, `tokenization`, `application`, `image-synthesis`, `video-synthesis`, `multimodal-conversation`, `transcription`, `speech-synthesis`, `rl`, ...) and their options. Running `dashscope` with no arguments instead launches the interactive [AI Assistant](#ai-assistant-dashscope-sdk-expert).

## Shell Completion

Run the appropriate command once, then restart your shell (or re-source your config file):

| Shell | Install command |
|-------|-----------------|
| **bash** | `dashscope --install-completion bash` |
| **zsh** | `dashscope --install-completion zsh` |
| **fish** | `dashscope --install-completion fish` |

To preview the completion script without installing:
```shell
dashscope --show-completion bash
```

## Logging
Set `DASHSCOPE_LOGGING_LEVEL` before importing `dashscope` to have it attach a
console handler automatically (`info` or `debug`):

```shell
export DASHSCOPE_LOGGING_LEVEL='info'
```

```python
from dashscope import Generation

# Request details are now printed to the console automatically, e.g.:
# 2024-01-01 12:00:00,000 - dashscope - ... - INFO - request: POST https://...
response = Generation.call(model="qwen-plus", messages=[{"role": "user", "content": "Hi"}])
```

## Output

Every SDK call returns (or yields, when streaming) a response object with these fields:

```python
response = Generation.call(model="qwen-plus", messages=[{"role": "user", "content": "Hi"}])

response.request_id    # str: the request id, useful when reporting issues
response.status_code   # int: HTTP status code; 200 means success
response.code          # str: error code on failure, otherwise ""
response.message       # str: error message on failure, otherwise ""
response.output        # Any: the request output (shape depends on the API called)
response.usage         # Any: token/quota usage information
```

For how `output`/`usage` support both dict-style and attribute-style access, and the per-capability response subclasses, see the [Response Object Model guide](docs/guides/response-types.md).

## License
This project is licensed under the Apache License (Version 2.0).
