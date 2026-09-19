# Assistants API（非推奨）

> [English](assistants.md) | [中文](assistants_zh.md) | **日本語** | [Español](assistants_es.md) | [한국어](assistants_ko.md)

> **非推奨。** Assistants API（`dashscope.assistants` および `dashscope.threads`）は非推奨であり、将来のリリースで削除される予定です。`messages` パラメータを使用する [`Generation`](../../README_ja.md#クイックスタート) または [`MultiModalConversation`](../../README_ja.md#マルチモーダル理解ビジョン) への移行をお願いします。詳細は[移行リファレンス](https://help.aliyun.com/zh/model-studio/synchronous-call-api-reference)を参照してください。

このガイドは、このAPIに依存するコードを保守するために、既存のインターフェースをまとめたものです。

## 基本的な流れ

アシスタントを作成し、スレッドを開始して実行し、完了を待ちます：

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

run の個々の実行ステップ（ツール呼び出し、メッセージ作成など）を一覧表示します：

```python
from dashscope import Steps

steps = Steps.list(run.id, thread_id=thread.id, limit=20)
for step in steps.data:
    print(step.id, step.type, step.status)
```

## アシスタントへのファイルの添付

ファイルの添付には、`dashscope.assistants` 配下の専用の `Files` クラスを使用します（微調整のアップロードに使うトップレベルの `dashscope.Files` とは別のものです）：

```python
from dashscope.assistants.files import Files

attached = Files.create(assistant_id=assistant.id, file_id="file-id-xxxx")
print(attached)

info = Files.get(assistant_id=assistant.id, file_id="file-id-xxxx")
```
