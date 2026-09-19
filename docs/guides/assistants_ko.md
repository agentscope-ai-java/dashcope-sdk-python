# Assistants API (사용 중단됨)

> [English](assistants.md) | [中文](assistants_zh.md) | [日本語](assistants_ja.md) | [Español](assistants_es.md) | **한국어**

> **사용 중단됨(Deprecated).** Assistants API(`dashscope.assistants` 및 `dashscope.threads`)는 사용이 중단되었으며 향후 릴리스에서 제거될 예정입니다. `messages` 매개변수를 사용하는 [`Generation`](../../README_ko.md#빠른-시작) 또는 [`MultiModalConversation`](../../README_ko.md#멀티모달-이해-비전)으로 마이그레이션하세요. 자세한 내용은 [마이그레이션 참고 문서](https://help.aliyun.com/zh/model-studio/synchronous-call-api-reference)를 참고하세요.

이 가이드는 이 API에 여전히 의존하는 코드를 유지 관리하기 위해 기존 기능을 문서화합니다.

## 기본 흐름

어시스턴트를 생성하고, 스레드를 시작하고, 실행한 뒤 완료를 기다립니다:

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

## 실행 단계 (Run Steps)

실행의 개별 단계(도구 호출, 메시지 생성 등)를 나열합니다:

```python
from dashscope import Steps

steps = Steps.list(run.id, thread_id=thread.id, limit=20)
for step in steps.data:
    print(step.id, step.type, step.status)
```

## 어시스턴트에 파일 첨부하기

파일을 첨부할 때는 `dashscope.assistants` 아래의 별도 `Files` 클래스를 사용합니다(파인튜닝 업로드에 사용되는 최상위 `dashscope.Files`와는 다른 클래스입니다):

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
