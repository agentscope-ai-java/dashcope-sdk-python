# Referencia de Manejo de Errores

> [English](error-handling.md) | [中文](error-handling_zh.md) | [日本語](error-handling_ja.md) | **Español** | [한국어](error-handling_ko.md)

Esta guía va más allá del patrón básico descrito en la [sección de Manejo de Errores del README](../../README.md#error-handling)
(capturar `DashScopeException` y luego comprobar `status_code`).

## Clases de excepción

Todas las excepciones lanzadas por el SDK (`dashscope/common/error.py`) heredan de
`DashScopeException`, por lo que un único `except DashScopeException` captura
cualquiera de ellas. Las más comunes y cuándo se lanzan realmente:

| Excepción | Se lanza cuando |
|---|---|
| `InputRequired` | Falta una entrada obligatoria, p. ej. no se proporcionó `prompt`/`messages` |
| `ModelRequired` | El argumento `model` está vacío |
| `AuthenticationError` | No hay ninguna API key configurada en ningún lugar (código, variable de entorno o archivo) |
| `InvalidInput` | Una combinación de argumentos no es válida, p. ej. parámetros en conflicto |
| `InvalidFileFormat` | Un archivo a subir no coincide con el formato esperado (p. ej. no es JSONL para fine-tuning) |
| `UnsupportedModel` | El modelo solicitado no es compatible con la operación (p. ej. un modelo no soportado para la tokenización local) |
| `UploadFileException` | Falló la subida de un archivo local (p. ej. para una solicitud de visión/imagen) a OSS |
| `UnsupportedDataType` | No se reconoce un tipo de dato de entrada/salida |
| `TimeoutException` | Una espera bloqueante (p. ej. `Runs.wait`) superó su tiempo límite |

```python
from dashscope import Generation
from dashscope.common.error import (
    DashScopeException,
    InputRequired,
    ModelRequired,
    AuthenticationError,
)

try:
    Generation.call(model="", messages=[{"role": "user", "content": "Hi"}])
except ModelRequired as e:
    print(f"Model missing: {e}")
except (InputRequired, AuthenticationError) as e:
    print(f"Invalid setup: {e}")
except DashScopeException as e:
    print(f"Other SDK-side error: {e}")
```

## Obtener el request_id para soporte técnico

Toda respuesta —éxito o fallo— incluye un `request_id`. Inclúyalo al
reportar un problema o contactar con soporte:

```python
from http import HTTPStatus
from dashscope import Generation

response = Generation.call(model="qwen-plus", messages=[{"role": "user", "content": "Hi"}])
if response.status_code != HTTPStatus.OK:
    print(f"request_id={response.request_id} code={response.code} message={response.message}")
```

## Reintentos automáticos de conexión

El SDK reintenta automáticamente una solicitud **una vez** si una conexión
keep-alive del pool fue cerrada silenciosamente por el servidor o por un
balanceador de carga intermedio (detectado como un error de conexión antes de
que lleguen bytes de respuesta) — tanto el cliente síncrono (basado en
`requests`) como el asíncrono (basado en `aiohttp`) lo hacen internamente.
Esto no es configurable y no requiere código de su parte; solo cubre
conexiones cerradas antes de que comience una respuesta, no fallos a nivel de
aplicación como límites de tasa o entradas inválidas, que se devuelven como
respuestas de error normales (vea el patrón en la sección de Manejo de
Errores del README).

## Reintentos y backoff para límites de tasa

A diferencia del reintento a nivel de conexión anterior, el SDK **no**
reintenta automáticamente fallos a nivel de aplicación como límites de tasa
o errores transitorios del servidor — estos se devuelven como una respuesta
normal con un `status_code` distinto de 200, y depende de su código decidir
si reintentar. Un backoff exponencial simple basado en `status_code`:

```python
import time
from http import HTTPStatus
from dashscope import Generation

def call_with_backoff(max_retries=5, base_delay=1.0, **kwargs):
    for attempt in range(max_retries):
        response = Generation.call(**kwargs)
        if response.status_code == HTTPStatus.OK:
            return response
        if response.status_code in (429, 500, 502, 503, 504) and attempt < max_retries - 1:
            time.sleep(base_delay * (2 ** attempt))
            continue
        return response  # se rinde: el llamador revisa status_code/code/message

response = call_with_backoff(model="qwen-plus", messages=[{"role": "user", "content": "Hi"}])
```
