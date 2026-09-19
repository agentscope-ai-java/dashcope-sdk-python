# Assistants API（已废弃）

> [English](assistants.md) | **中文** | [日本語](assistants_ja.md) | [Español](assistants_es.md) | [한국어](assistants_ko.md)

> **已废弃。** Assistants API（`dashscope.assistants` 与 `dashscope.threads`）已被废弃，将在未来版本中移除。请迁移到带有 `messages` 参数的 [`Generation`](../../README_zh.md#快速开始) 或 [`MultiModalConversation`](../../README_zh.md#多模态理解视觉)。详情请参见[迁移参考文档](https://help.aliyun.com/zh/model-studio/synchronous-call-api-reference)。

本指南记录了该 API 的现有能力，供维护仍依赖它的代码使用。

## 基本流程

创建一个 assistant，开启一个 thread，运行它并等待完成：

```python
from dashscope import Assistants, Threads, Runs, Messages

assistant = Assistants.create(
    model="qwen-max",
    name="smart helper",
    description="A tool helper.",
    instructions="You are a helpful assistant.",
)

thread = Threads.create(
    messages=[{"role": "user", "content": "How do I make beef stew?"}],
)

run = Runs.create(thread.id, assistant_id=assistant.id)
run_status = Runs.wait(run.id, thread_id=thread.id)
print(run_status.status)

messages = Messages.list(thread.id)
print(messages)
```

## Assistants

```python
from dashscope import Assistants

assistant = Assistants.get(assistant_id=assistant.id)

assistants = Assistants.list(limit=20)
for a in assistants.data:
    print(a.id, a.name)

assistant = Assistants.update(assistant.id, name="renamed helper")

Assistants.delete(assistant.id)
```

## Threads

```python
from dashscope import Threads

thread = Threads.get(thread_id=thread.id)
thread = Threads.update(thread.id, metadata={"topic": "cooking"})
Threads.delete(thread.id)
```

## Messages

```python
from dashscope import Messages

message = Messages.create(thread.id, content="What about a vegetarian version?")
message = Messages.get(message.id, thread_id=thread.id)
messages = Messages.list(thread.id, limit=20)
```

## Runs

```python
from dashscope import Runs

run = Runs.get(run.id, thread_id=thread.id)
run = Runs.wait(run.id, thread_id=thread.id, timeout_seconds=60)
Runs.cancel(run.id, thread_id=thread.id)
```

## Run Steps

列出一次 run 的各个执行步骤（工具调用、消息创建等）：

```python
from dashscope import Steps

steps = Steps.list(run.id, thread_id=thread.id, limit=20)
for step in steps.data:
    print(step.id, step.type, step.status)
```

## 为 Assistant 附加文件

附加文件使用的是 `dashscope.assistants` 下一个单独的 `Files` 类（不同于用于微调上传的顶层 `dashscope.Files`）：

```python
from dashscope.assistants.files import Files

attached = Files.create(assistant_id=assistant.id, file_id="file-id-xxxx")
print(attached)

info = Files.get(file_id="file-id-xxxx", assistant_id=assistant.id)

files = Files.list(assistant.id, limit=10, order="asc")
for f in files.data:
    print(f.id, f.assistant_id)

deleted = Files.delete(file_id="file-id-xxxx", assistant_id=assistant.id)
print(deleted.deleted)
```
