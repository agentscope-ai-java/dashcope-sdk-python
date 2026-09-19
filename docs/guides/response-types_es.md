# Modelo de Objetos de Respuesta

> [English](response-types.md) | [中文](response-types_zh.md) | [日本語](response-types_ja.md) | **Español** | [한국어](response-types_ko.md)

La sección [Output del README](../../README.md#output) cubre los campos
comunes que comparte cada respuesta. Esto profundiza un nivel más en cómo se
comportan realmente esos objetos.

## Acceso por diccionario y por atributo

Cada objeto de respuesta (y cada objeto anidado `output`/`usage`) es un
`DictMixin` — es una subclase real de `dict` cuyos `__getattr__`/`__setattr__`
delegan a los elementos del diccionario. Esto significa que ambos estilos de
acceso funcionan indistintamente sobre el mismo objeto:

```python
from dashscope import Generation

response = Generation.call(model="qwen-plus", messages=[{"role": "user", "content": "Hi"}])

# Acceso por atributo
print(response.output.choices[0].message.content)
# Acceso equivalente por diccionario
print(response.output["choices"][0]["message"]["content"])
```

## Subclases de respuesta por capacidad

`Generation.call`, `ImageSynthesis.call`, `TextReRank.call`, etc. no
devuelven directamente el tipo base genérico — cada uno envuelve su
`output`/`usage` en una subclase tipada (p. ej. `GenerationResponse` envuelve
`output` en un `GenerationOutput` y `usage` en un `GenerationUsage`;
`ImageSynthesis.call` devuelve `ImageSynthesisResponse`, `TextReRank.call`
devuelve `ReRankResponse`, y así sucesivamente) para que el autocompletado
del IDE y el acceso a atributos funcionen sobre los campos específicos de
esa API, a la vez que se comparten los campos base
`status_code`/`request_id`/`code`/`message`:

```python
from dashscope import TextReRank

resp = TextReRank.call(
    model=TextReRank.Models.gte_rerank,
    query="What is the capital of China?",
    documents=["Beijing is the capital of China.", "Paris is in France."],
)
# resp es un ReRankResponse; resp.output es un ReRankOutput
for r in resp.output.results:
    print(r.index, r.relevance_score)
```

## Roles de Mensaje

El campo `role` usado en todo el parámetro `messages` tiene sus valores
válidos definidos en la clase `Role`:

```python
from dashscope.api_entities.dashscope_response import Role

print(Role.USER, Role.SYSTEM, Role.ASSISTANT, Role.BOT, Role.ATTACHMENT)
# user system assistant bot attachment
```
