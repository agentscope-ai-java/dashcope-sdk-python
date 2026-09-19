# 응답 객체 모델

> [English](response-types.md) | [中文](response-types_zh.md) | [日本語](response-types_ja.md) | [Español](response-types_es.md) | **한국어**

README의 [Output](../../README.md#output) 섹션은 모든 응답이 공유하는 공통
필드를 다룹니다. 여기서는 이러한 객체가 실제로 어떻게 동작하는지 한 단계
더 깊이 살펴봅니다.

## 딕셔너리 및 속성 접근

모든 응답 객체(그리고 중첩된 모든 `output`/`usage` 객체)는 `DictMixin`입니다
— `__getattr__`/`__setattr__`가 딕셔너리 항목으로 위임되는 실제 `dict`
서브클래스입니다. 즉, 같은 객체에서 두 가지 접근 방식을 서로 바꿔가며 사용할
수 있습니다:

```python
from dashscope import Generation

response = Generation.call(model="qwen-plus", messages=[{"role": "user", "content": "Hi"}])

# 속성 접근
print(response.output.choices[0].message.content)
# 동일한 딕셔너리 방식 접근
print(response.output["choices"][0]["message"]["content"])
```

## 기능별 응답 서브클래스

`Generation.call`, `ImageSynthesis.call`, `TextReRank.call` 등은 일반적인
기본 타입을 그대로 반환하지 않습니다 — 각각 자신의 `output`/`usage`를
타입이 지정된 서브클래스로 감쌉니다(예: `GenerationResponse`는 `output`을
`GenerationOutput`으로, `usage`를 `GenerationUsage`로 감쌉니다;
`ImageSynthesis.call`은 `ImageSynthesisResponse`를, `TextReRank.call`은
`ReRankResponse`를 반환하는 식입니다). 이를 통해 IDE 자동완성과 속성 접근이
해당 API 전용 필드에서 동작하면서도, 공통 `status_code`/`request_id`/`code`/`message`
필드는 그대로 공유됩니다:

```python
from dashscope import TextReRank

resp = TextReRank.call(
    model=TextReRank.Models.gte_rerank,
    query="What is the capital of China?",
    documents=["Beijing is the capital of China.", "Paris is in France."],
)
# resp는 ReRankResponse이며, resp.output은 ReRankOutput입니다
for r in resp.output.results:
    print(r.index, r.relevance_score)
```

## 메시지 역할 (Role)

`messages` 매개변수 전반에서 사용되는 `role` 필드의 유효한 값은 `Role`
클래스에 정의되어 있습니다:

```python
from dashscope.api_entities.dashscope_response import Role

print(Role.USER, Role.SYSTEM, Role.ASSISTANT, Role.BOT, Role.ATTACHMENT)
# user system assistant bot attachment
```
