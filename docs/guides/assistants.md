# Assistants API (Deprecated)

> **English** | [中文](assistants_zh.md) | [日本語](assistants_ja.md) | [Español](assistants_es.md) | [한국어](assistants_ko.md)

> **Deprecated.** The Assistants API (`dashscope.assistants` and `dashscope.threads`) is deprecated and will be removed in a future release. Please migrate to [`Generation`](../../README.md#quick-start) or [`MultiModalConversation`](../../README.md#multimodal-understanding-vision) with the `messages` parameter. See the [migration reference](https://help.aliyun.com/zh/model-studio/synchronous-call-api-reference) for details.

This guide documents the existing surface for maintaining code that still depends on it.

## Basic Flow

Create an assistant, start a thread, run it, and wait for completion:

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

List the individual execution steps of a run (tool calls, message creations, etc.):

```python
from dashscope import Steps

steps = Steps.list(run.id, thread_id=thread.id, limit=20)
for step in steps.data:
    print(step.id, step.type, step.status)
```

## Attaching Files to an Assistant

Attaching a file uses a separate `Files` class under `dashscope.assistants` (distinct from the top-level `dashscope.Files` used for fine-tuning uploads):

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
