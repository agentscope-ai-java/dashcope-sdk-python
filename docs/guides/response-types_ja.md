# レスポンスオブジェクトモデル

> [English](response-types.md) | [中文](response-types_zh.md) | **日本語**

README の [出力](../../README.md#output) の節では、すべてのレスポンスが
共有する共通フィールドについて説明しています。本ガイドでは、これらの
オブジェクトが実際にどのように振る舞うかをさらに掘り下げます。

## 辞書アクセスと属性アクセス

すべてのレスポンスオブジェクト（および入れ子になっている `output`/`usage`
オブジェクト）は `DictMixin` です——これは実体としては本物の `dict` の
サブクラスであり、その `__getattr__`/`__setattr__` は辞書の要素に対して
プロキシとして働きます。つまり、同じオブジェクトに対して両方のアクセス方法を
相互に使うことができます：

```python
from dashscope import Generation

response = Generation.call(model="qwen-plus", messages=[{"role": "user", "content": "Hi"}])

# 属性アクセス
print(response.output.choices[0].message.content)
# 同等の辞書スタイルのアクセス
print(response.output["choices"][0]["message"]["content"])
```

## 機能ごとのレスポンスサブクラス

`Generation.call`、`ImageSynthesis.call`、`TextReRank.call` などは、汎用的な
基底型をそのまま返すのではなく、それぞれ `output`/`usage` を専用の型で
ラップします（例えば `GenerationResponse` は `output` を `GenerationOutput`
に、`usage` を `GenerationUsage` にラップします。`ImageSynthesis.call` は
`ImageSynthesisResponse` を、`TextReRank.call` は `ReRankResponse` を返す、
といった具合です）。これにより、その API 固有のフィールドに対して IDE の
自動補完や属性アクセスが機能する一方で、`status_code`/`request_id`/`code`/
`message` といった基本フィールドは引き続き共有されます：

```python
from dashscope import TextReRank

resp = TextReRank.call(
    model=TextReRank.Models.gte_rerank,
    query="What is the capital of China?",
    documents=["Beijing is the capital of China.", "Paris is in France."],
)
# resp は ReRankResponse であり、resp.output は ReRankOutput です
for r in resp.output.results:
    print(r.index, r.relevance_score)
```

## メッセージのロール

`messages` パラメータ全体で使用される `role` フィールドの有効な値は、
`Role` クラスで定義されています：

```python
from dashscope.api_entities.dashscope_response import Role

print(Role.USER, Role.SYSTEM, Role.ASSISTANT, Role.BOT, Role.ATTACHMENT)
# user system assistant bot attachment
```
