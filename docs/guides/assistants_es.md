# API de Assistants (Obsoleta)

> [English](assistants.md) | [中文](assistants_zh.md) | [日本語](assistants_ja.md) | **Español** | [한국어](assistants_ko.md)

> **Obsoleta.** La API de Assistants (`dashscope.assistants` y `dashscope.threads`) está obsoleta y se eliminará en una versión futura. Migre a [`Generation`](../../README_es.md#inicio-rápido) o [`MultiModalConversation`](../../README_es.md#comprensión-multimodal-visión) con el parámetro `messages`. Consulte la [referencia de migración](https://help.aliyun.com/zh/model-studio/synchronous-call-api-reference) para más detalles.

Esta guía documenta la superficie existente para mantener código que aún depende de ella.

## Flujo básico

Crea un asistente, inicia un hilo, ejecútalo y espera a que finalice:

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

## Pasos de ejecución (Run Steps)

Lista los pasos de ejecución individuales de un run (llamadas a herramientas, creación de mensajes, etc.):

```python
from dashscope import Steps

steps = Steps.list(run.id, thread_id=thread.id, limit=20)
for step in steps.data:
    print(step.id, step.type, step.status)
```

## Adjuntar archivos a un asistente

Para adjuntar un archivo se usa una clase `Files` independiente dentro de `dashscope.assistants` (distinta de la clase `dashscope.Files` de nivel superior usada para las cargas de fine-tuning):

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
