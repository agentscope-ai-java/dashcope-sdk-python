# 响应对象模型

> [English](response-types.md) | **中文** | [日本語](response-types_ja.md)

README 的 [输出](../../README.md#output) 部分介绍了所有响应共有的通用字段。
本指南将进一步说明这些对象的实际行为方式。

## 字典与属性访问

每一个响应对象（以及每一个嵌套的 `output`/`usage` 对象）都是一个
`DictMixin`——它本质上是一个真正的 `dict` 子类，其 `__getattr__`/`__setattr__`
会代理到对应的字典项上。这意味着在同一个对象上，两种访问方式可以互换使用：

```python
from dashscope import Generation

response = Generation.call(model="qwen-plus", messages=[{"role": "user", "content": "Hi"}])

# 属性访问
print(response.output.choices[0].message.content)
# 等价的字典风格访问
print(response.output["choices"][0]["message"]["content"])
```

## 各能力专属的响应子类

`Generation.call`、`ImageSynthesis.call`、`TextReRank.call` 等方法并不直接
返回通用的基础类型——每一个都会将其 `output`/`usage` 包装为专属的子类
（例如 `GenerationResponse` 将 `output` 包装为 `GenerationOutput`、将
`usage` 包装为 `GenerationUsage`；`ImageSynthesis.call` 返回
`ImageSynthesisResponse`，`TextReRank.call` 返回 `ReRankResponse`，以此类推），
这样 IDE 的自动补全和属性访问就能作用于该接口专属的字段，同时仍然共享
`status_code`/`request_id`/`code`/`message` 这些基础字段：

```python
from dashscope import TextReRank

resp = TextReRank.call(
    model=TextReRank.Models.gte_rerank,
    query="What is the capital of China?",
    documents=["Beijing is the capital of China.", "Paris is in France."],
)
# resp 是一个 ReRankResponse；resp.output 是一个 ReRankOutput
for r in resp.output.results:
    print(r.index, r.relevance_score)
```

## 消息角色（Role）

`messages` 参数中使用的 `role` 字段，其合法取值定义在 `Role` 类上：

```python
from dashscope.api_entities.dashscope_response import Role

print(Role.USER, Role.SYSTEM, Role.ASSISTANT, Role.BOT, Role.ATTACHMENT)
# user system assistant bot attachment
```
