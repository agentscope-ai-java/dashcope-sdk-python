# Response Object Model

> **English** | [中文](response-types_zh.md) | [日本語](response-types_ja.md) | [Español](response-types_es.md) | [한국어](response-types_ko.md)

The README's [Output](../../README.md#output) section covers the common
fields every response shares. This goes one level deeper into how those
objects actually behave.

## Dict and Attribute Access

Every response object (and every nested `output`/`usage` object) is a
`DictMixin` — it's a real `dict` subclass whose `__getattr__`/`__setattr__`
proxy to dict items. That means both access styles work interchangeably on
the same object:

```python
from dashscope import Generation

response = Generation.call(model="qwen-plus", messages=[{"role": "user", "content": "Hi"}])

# Attribute access
print(response.output.choices[0].message.content)
# Equivalent dict-style access
print(response.output["choices"][0]["message"]["content"])
```

## Per-Capability Response Subclasses

`Generation.call`, `ImageSynthesis.call`, `TextReRank.call`, etc. don't
return the generic base type directly — each wraps its `output`/`usage`
in a typed subclass (e.g. `GenerationResponse` wraps `output` in a
`GenerationOutput` and `usage` in a `GenerationUsage`; `ImageSynthesis.call`
returns `ImageSynthesisResponse`, `TextReRank.call` returns
`ReRankResponse`, and so on) so IDE autocomplete and attribute access work
on the fields specific to that API, while still sharing the base
`status_code`/`request_id`/`code`/`message` fields:

```python
from dashscope import TextReRank

resp = TextReRank.call(
    model=TextReRank.Models.gte_rerank,
    query="What is the capital of China?",
    documents=["Beijing is the capital of China.", "Paris is in France."],
)
# resp is a ReRankResponse; resp.output is a ReRankOutput
for r in resp.output.results:
    print(r.index, r.relevance_score)
```

## Message Roles

The `role` field used throughout the `messages` parameter has its valid
values defined on the `Role` class:

```python
from dashscope.api_entities.dashscope_response import Role

print(Role.USER, Role.SYSTEM, Role.ASSISTANT, Role.BOT, Role.ATTACHMENT)
# user system assistant bot attachment
```
