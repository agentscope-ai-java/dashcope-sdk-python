# DashScope Python SDK

> [English](README.md) | [中文](README_zh.md) | [日本語](README_ja.md) | **Español** | [한국어](README_ko.md)

El SDK de Python de DashScope proporciona una interfaz completa a las API de [Alibaba Cloud Model Studio (Bailian)](https://www.alibabacloud.com/help/en/model-studio/), que cubre generación de texto, comprensión multimodal, embeddings, reranking, generación de imágenes/video, síntesis y reconocimiento de voz, y más.

## Novedades

**La v1.27.0 incorpora un asistente de IA interactivo — [DashScope SDK Expert](#asistente-de-ia-dashscope-sdk-expert).** Ejecuta `dashscope` sin argumentos (o pregunta directamente, p. ej. `dashscope "how do I stream Generation output"`) para obtener respuestas sobre el SDK/API, ejemplos ejecutables, uso de la CLI y diagnóstico de errores directamente en tu terminal. Las respuestas se basan en habilidades de referencia rápida por dominio (texto, multimodal, voz, recuperación, fine-tuning, agentes, cli) construidas sobre las interfaces públicas del SDK — parámetros, salidas y códigos de error — para que puedas preguntar en lugar de leer la documentación. Escribe `/help` dentro del asistente para ver los comandos disponibles.

## Instalación
Para instalar el SDK de Python de DashScope, simplemente ejecuta:
```shell
pip install dashscope
```

La instalación base incluye las llamadas a la API del SDK y el comando CLI `dashscope`.
Los grupos de funciones opcionales están disponibles como extras:

| Extra | Proporciona | Instalación |
|-------|----------|---------|
| `acli` | Asistente de IA interactivo (DashScope SDK Expert) | `pip install "dashscope[acli]"` |
| `rl` | Fine-tuning con Agentic RL | `pip install "dashscope[rl]"` |
| `tokenizer` | Tokenizer local sin descargas | `pip install "dashscope[tokenizer]"` |

Si clonas el código desde GitHub, puedes instalarlo desde el código fuente ejecutando:
```shell
pip install -e .
```


## Guía rápida

```python
# pip install dashscope
from http import HTTPStatus
from dashscope import Generation

responses = Generation.call(
    model="qwen-plus",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Who are you?"},
    ],
    result_format="message",
)

if responses.status_code == HTTPStatus.OK:
    print(responses.output.choices[0].message.content)
else:
    print(f"Error: {responses.code} - {responses.message}")
```

### Salida en streaming

Pasa `stream=True` para obtener un generador de respuestas incrementales. Con
`incremental_output=True`, cada fragmento contiene solo los tokens recién
generados (en lugar del texto acumulado hasta el momento):

```python
from dashscope import Generation

responses = Generation.call(
    model="qwen-plus",
    messages=[{"role": "user", "content": "Escribe un haiku sobre el mar."}],
    result_format="message",
    stream=True,
    incremental_output=True,
)
for response in responses:
    print(response.output.choices[0].message.content, end="")
```

### Async / asyncio

Cada clase basada en `call` tiene una contraparte asíncrona con prefijo `Aio`
(`AioGeneration`, `AioImageSynthesis`, `AioMultiModalConversation`,
`AioVideoSynthesis`, `AioMultiModalEmbedding`, `AioTextReRank`, ...) con los
mismos parámetros, usada con `await`:

```python
import asyncio
from dashscope import AioGeneration

async def main():
    response = await AioGeneration.call(
        model="qwen-plus",
        messages=[{"role": "user", "content": "Who are you?"}],
        result_format="message",
    )
    print(response.output.choices[0].message.content)

asyncio.run(main())
```

### Llamadas a funciones

Pasa definiciones de herramientas al estilo OpenAI mediante `tools`; el modelo solicita una llamada a través de `message.tool_calls`, que tu código ejecuta y devuelve:

```python
from dashscope import Generation

tools = [{
    "type": "function",
    "function": {
        "name": "get_current_weather",
        "description": "Obtiene el clima actual de una ciudad.",
        "parameters": {
            "type": "object",
            "properties": {"location": {"type": "string", "description": "El nombre de la ciudad."}},
            "required": ["location"],
        },
    },
}]
response = Generation.call(
    model="qwen-plus",
    messages=[{"role": "user", "content": "¿Qué tiempo hace en Hangzhou?"}],
    tools=tools,
    result_format="message",
)
tool_call = response.output.choices[0].message.tool_calls[0]
print(tool_call.function.name, tool_call.function.arguments)
```

### Modo de razonamiento

Los modelos de razonamiento híbrido pueden exponer su proceso de razonamiento por separado de la respuesta final mediante `enable_thinking` (requiere `stream=True`); el razonamiento aparece en `message.reasoning_content`, la respuesta final en `message.content`:

```python
from dashscope import Generation

responses = Generation.call(
    model="qwen-plus",
    messages=[{"role": "user", "content": "¿Cuál es mayor, 1.1 o 0.9?"}],
    result_format="message",
    enable_thinking=True,
    incremental_output=True,
    stream=True,
)
for response in responses:
    message = response.output.choices[0].message
    print(message.get("reasoning_content") or message.content, end="")
```

### Manejo de errores

Los argumentos requeridos faltantes (p. ej. sin `model`, sin `messages`/`prompt`,
sin API Key) generan de inmediato una subclase de `DashScopeException`; los
fallos a nivel de API (nombre de modelo inválido, límites de tasa, etc.) se
devuelven en la respuesta en lugar de lanzarse, por lo que hay que comprobar
`status_code`:

```python
from http import HTTPStatus
from dashscope import Generation
from dashscope.common.error import DashScopeException

try:
    response = Generation.call(model="qwen-plus", messages=[{"role": "user", "content": "Hi"}])
except DashScopeException as e:
    # Se lanza localmente ante una entrada inválida, p. ej. InputRequired, ModelRequired, AuthenticationError
    print(f"Invalid request: {e}")
else:
    if response.status_code != HTTPStatus.OK:
        # Devuelto por la API, p. ej. modelo inválido, límite de tasa, cuota agotada
        print(f"API error {response.status_code}: {response.code} - {response.message}")
    else:
        print(response.output.choices[0].message.content)
```

Para la lista completa de clases de excepción y cuándo se lanza cada una, consulta la [referencia de manejo de errores](docs/guides/error-handling_es.md).

## Autenticación con API Key

El SDK usa una API Key para la autenticación. Para obtener una API Key, consulta [cómo obtener una API Key](https://help.aliyun.com/en/model-studio/get-api-key). Consulta la [documentación oficial de Alibaba Cloud para China](https://www.alibabacloud.com/help/en/model-studio/) y la [documentación oficial de Alibaba Cloud internacional](https://www.alibabacloud.com/help/en/model-studio/) sobre cómo obtener tu api-key.

### Uso de la API Key

1. Configurar la API Key mediante código
```python
import dashscope

dashscope.api_key = 'YOUR-DASHSCOPE-API-KEY'
# O especifica la ruta del archivo de la API Key mediante código
# dashscope.api_key_file_path='~/.dashscope/api_key'

```

2. Configurar la API Key mediante variables de entorno

```shell
# a. Configura la API Key directamente
export DASHSCOPE_API_KEY='YOUR-DASHSCOPE-API-KEY'

# b. O apunta a un archivo que contenga la clave
export DASHSCOPE_API_KEY_FILE_PATH='~/.dashscope/api_key'
```

Cualquiera de las dos variables hace que `Generation.call(...)` (y cualquier otra llamada del SDK) recoja la clave automáticamente, sin necesidad del argumento `api_key=`:

```python
from dashscope import Generation

# DASHSCOPE_API_KEY (o DASHSCOPE_API_KEY_FILE_PATH) se lee automáticamente
response = Generation.call(model="qwen-plus", messages=[{"role": "user", "content": "Hi"}])
print(response.output.choices[0].message.content)
```

3. Guardar la API Key en un archivo
```python
from dashscope import save_api_key

save_api_key(api_key='YOUR-DASHSCOPE-API-KEY',
             api_key_file_path='api_key_file_location or (None, will save to default location "~/.dashscope/api_key"')

```

## Configuración de región y endpoint

Por defecto, el SDK envía las solicitudes al endpoint público de China (Pekín) `dashscope.aliyuncs.com`. Si tu espacio de trabajo de Model Studio (Bailian) está en otra región, cambia el endpoint antes de realizar las llamadas.

### Uso de `set_region`

`dashscope.set_region(region, workspace_id)` apunta las URL base de HTTP, WebSocket y compatible con OpenAI a la región indicada en una sola llamada. `workspace_id` es obligatorio y se usa como subdominio del endpoint.

```python
import dashscope

# Cambia a la región de Singapur para el workspace "ws-xxx123"
dashscope.set_region(region="ap-southeast-1", workspace_id="ws-xxx123")

# Todas las llamadas posteriores usarán:
#   https://ws-xxx123.ap-southeast-1.maas.aliyuncs.com/api/v1
print(dashscope.base_http_api_url)
```

Regiones compatibles:

| Región | Ubicación |
|--------|----------|
| `cn-beijing` | China (Pekín) |
| `cn-hongkong` | China (Hong Kong) |
| `ap-southeast-1` | Singapur |
| `ap-northeast-1` | Japón (Tokio) |
| `eu-central-1` | Alemania (Fráncfort) |
| `us-east-1` | EE. UU. (Virginia) |

> **Las API Keys son específicas de cada región.** Cada región emite sus propias API Keys (prefijo `sk-`) en su consola de Model Studio, y las claves no se pueden mezclar entre regiones — usar una clave de otra región falla con `401`. Cambia `api_key` junto con la región.

Notas específicas de cada región:

- Los endpoints WebSocket (`wss://.../api-ws/v1/inference`) solo se ofrecen en `cn-beijing` y `ap-southeast-1`. `set_region` sigue configurando `base_websocket_api_url` en todas las regiones, pero las API en tiempo real basadas en WebSocket (reconocimiento/síntesis de voz en tiempo real, diálogo multimodal, etc.) no están disponibles en las demás regiones.
- `eu-central-1` / `ap-northeast-1`: el alcance del despliegue (Global, o UE / Japón) se elige al crear el workspace en la consola, no en cada llamada a la API.
- `us-east-1`: los nombres de modelo con el sufijo `-us` (p. ej. `qwen-plus-us`) restringen la inferencia a EE. UU.; los nombres sin sufijo usan inferencia global por defecto.
- La inferencia por lotes, el fine-tuning de modelos y el desarrollo de aplicaciones actualmente solo están disponibles en `cn-beijing` y `ap-southeast-1`.

> `set_region` actualiza variables globales de todo el proceso, por lo que no es seguro para la concurrencia cuando un mismo proceso habla con varias regiones a la vez. Llámalo una vez al iniciar, o vuelve a llamarlo antes de cada cambio.

### Uso de variables de entorno

También puedes seleccionar la región sin escribir código:

```shell
export DASHSCOPE_API_REGION='ap-southeast-1'   # por defecto: cn-beijing
export DASHSCOPE_WORKSPACE_ID='ws-xxx123'      # se usa para resolver el subdominio del endpoint
```

```python
import dashscope

# Recoge automáticamente DASHSCOPE_API_REGION / DASHSCOPE_WORKSPACE_ID
print(dashscope.base_http_api_url)
# https://ws-xxx123.ap-southeast-1.maas.aliyuncs.com/api/v1
```

Cuando se configura una región MaaS mediante `DASHSCOPE_API_REGION`, el SDK construye los endpoints regionales correspondientes y sustituye `DASHSCOPE_WORKSPACE_ID` en ellos. También puedes sobrescribir cada URL base directamente:

| Variable de entorno | Sobrescribe |
|----------------------|-----------|
| `DASHSCOPE_HTTP_BASE_URL` | Endpoint HTTP (`dashscope.base_http_api_url`) |
| `DASHSCOPE_WEBSOCKET_BASE_URL` | Endpoint WebSocket (`dashscope.base_websocket_api_url`) |
| `DASHSCOPE_COMPATIBLE_BASE_URL` | Endpoint compatible con OpenAI (`dashscope.base_compatible_api_url`) |

`set_region` siempre construye endpoints exclusivos del workspace. Algunas regiones también ofrecen dominios compartidos sin subdominio de workspace — `dashscope.aliyuncs.com` (Pekín), `dashscope-intl.aliyuncs.com` (Singapur) y `dashscope-us.aliyuncs.com` (EE. UU., Virginia); usa las variables de sobrescritura anteriores para apuntar a ellos.

### Chat completions compatibles con OpenAI

El SDK expone una entrada de chat completions compatible con OpenAI que se comunica con `dashscope.base_compatible_api_url` (ruta de solicitud `chat/completions`) — sin necesidad de instalar el paquete `openai` adicional. Sigue la región configurada anteriormente.

```python
import dashscope
from dashscope.aigc.chat_completion import Completions

dashscope.set_region(region="cn-hongkong", workspace_id="ws-hk-789")

response = Completions.create(
    model="qwen-max",
    messages=[{"role": "user", "content": "Hola"}],
    api_key="YOUR-DASHSCOPE-API-KEY",
    stream=False,  # pon True para obtener un generador de ChatCompletionChunk
)
print(response)
```

Un ejemplo completo y ejecutable está disponible en [`samples/set_region_example.py`](samples/set_region_example.py).

Para tiempos de espera de solicitud, cabeceras personalizadas, soporte de proxy y cierre de pools de conexiones compartidos, consulta la [guía de configuración avanzada](docs/guides/configuration_es.md).

## Asistente de IA: DashScope SDK Expert

El SDK incluye un asistente de IA interactivo, **DashScope SDK Expert**, construido sobre el framework Agentic CLI incluido (`dashscope/acli`). Para los usuarios del SDK/CLI de DashScope, es la forma recomendada de obtener asesoría de desarrollo y ayuda de programación con IA — respondiendo preguntas sobre el SDK/API, generando ejemplos ejecutables, mostrando el uso de la CLI y diagnosticando errores, directamente en tu terminal.

- Ejecuta `dashscope` sin argumentos para iniciar el asistente. En la primera ejecución, ofrece instalar el paquete de conocimiento de SDK Expert (habilidades de referencia rápida por dominio: texto, multimodal, voz, recuperación, fine-tuning, agentes, cli), de modo que las respuestas provienen de las interfaces públicas del SDK — parámetros, salidas, códigos de error — sin necesidad de leer el código fuente
- Pregúntale en lugar de leer la documentación — p. ej. `dashscope "how do I stream Generation output"` o `dashscope "CLI command to cancel a fine-tuning job"`. Escribe `/help` dentro del asistente para listar los comandos disponibles (`/setup`, `/skill`, `/stats`, ...); los subcomandos clásicos del SDK siguen funcionando, y los comandos no reconocidos se enrutan automáticamente al asistente
- Guía completa: [guía de DashScope SDK Expert](https://help.aliyun.com/en/model-studio/dashscope-sdk-expert)

## Modelos compatibles

| Categoría | Modelos recomendados | Clase del SDK |
|----------|-------------------|-----------|
| Generación de texto | qwen3.8-max, qwen3.7-max, qwen3.7-plus, qwen3.6-flash | `Generation` |
| Comprensión multimodal | qwen3.5-omni-plus, qwen3.7-plus (visión) | `MultiModalConversation` |
| Embedding de texto | text-embedding-v4, text-embedding-v3 | `TextEmbedding` |
| Embedding multimodal | tongyi-embedding-vision-plus, qwen3-vl-embedding | `MultiModalEmbedding` |
| Reordenamiento de texto | qwen3-rerank, gte-rerank-v2 | `TextReRank` |
| Generación de imágenes | wan2.7-image-pro, qwen-image-2.0-pro | `ImageSynthesis` |
| Generación de video | wan2.7-t2v, wan2.7-i2v, happyhorse-1.0-t2v/i2v | `VideoSynthesis` |
| Síntesis de voz (TTS) | cosyvoice-v3.5-plus, cosyvoice-v1 | `SpeechSynthesizer`, `HttpSpeechSynthesizer` |
| Reconocimiento de voz (ASR) | fun-asr-realtime, fun-asr, paraformer-v1 | `Transcription` |
| Omni (tiempo real) | qwen3.5-omni-plus-realtime | `MultiModalConversation` |

Para la lista de modelos más reciente, visita [Bailian Model Plaza](https://bailian.console.aliyun.com/).

## Ejemplos de uso

Hay más scripts ejecutables disponibles en [`samples/`](samples).

### Comprensión multimodal (visión)

```python
from dashscope import MultiModalConversation

messages = [{
    "role": "user",
    "content": [
        {"image": "https://help-static-aliyun-doc.aliyuncs.com/file-manage-files/zh-CN/20241022/emyrja/dog_and_girl.jpeg"},
        {"text": "¿Qué describe esta imagen?"},
    ],
}]
response = MultiModalConversation.call(model="qwen-vl-max", messages=messages)
print(response.output.choices[0].message.content[0]["text"])
```

Pasa `stream=True` para transmitir la respuesta de forma incremental, igual que con `Generation`:

```python
from dashscope import MultiModalConversation

messages = [{
    "role": "user",
    "content": [
        {"image": "https://help-static-aliyun-doc.aliyuncs.com/file-manage-files/zh-CN/20241022/emyrja/dog_and_girl.jpeg"},
        {"text": "¿Qué describe esta imagen?"},
    ],
}]
responses = MultiModalConversation.call(
    model="qwen-vl-max",
    messages=messages,
    stream=True,
    incremental_output=True,
)
for response in responses:
    print(response.output.choices[0].message.content[0]["text"], end="")
```

Usa `AioMultiModalConversation` para la forma `async`/`await`:

```python
import asyncio
from dashscope import AioMultiModalConversation

async def main():
    messages = [{
        "role": "user",
        "content": [
            {"image": "https://help-static-aliyun-doc.aliyuncs.com/file-manage-files/zh-CN/20241022/emyrja/dog_and_girl.jpeg"},
            {"text": "¿Qué describe esta imagen?"},
        ],
    }]
    response = await AioMultiModalConversation.call(model="qwen-vl-max", messages=messages)
    print(response.output.choices[0].message.content[0]["text"])

asyncio.run(main())
```

El video se pasa como una lista de URLs/rutas de imágenes de fotogramas (no como un único archivo de video):

```python
from dashscope import MultiModalConversation

messages = [{
    "role": "user",
    "content": [
        {"video": ["frame1.jpg", "frame2.jpg", "frame3.jpg", "frame4.jpg"]},
        {"text": "Describe lo que ocurre en este video."},
    ],
}]
response = MultiModalConversation.call(model="qwen-vl-max-latest", messages=messages)
print(response.output.choices[0].message.content[0]["text"])
```

Los modelos `qwen-vl-ocr` aceptan un parámetro `ocr_options` para extracción estructurada (p. ej. rellenar un esquema JSON a partir de la imagen de un documento):

```python
from dashscope import MultiModalConversation

messages = [{
    "role": "user",
    "content": [
        {"image": "https://example.com/invoice.jpg"},
        {"text": "Extrae los campos de este documento según el siguiente esquema JSON: {result_schema}"},
    ],
}]
response = MultiModalConversation.call(
    model="qwen-vl-ocr-latest",
    messages=messages,
    ocr_options={
        "task": "key_information_extraction",
        "task_config": {"result_schema": {"invoice_number": "", "total_amount": ""}},
    },
)
print(response.output.choices[0].message.content[0]["text"])
```

### Uso de archivos locales

Todo campo que acepta una URL (`image`, `audio`, `video` en los mensajes; `images` en `ImageSynthesis`, etc.) también acepta una ruta de archivo local — el SDK lo sube automáticamente a OSS, sin necesidad de configurar cabeceras manualmente:

```python
from dashscope import MultiModalConversation

messages = [{
    "role": "user",
    "content": [
        {"image": "/path/to/local/image.jpg"},
        {"text": "¿Qué hay en esta imagen?"},
    ],
}]
response = MultiModalConversation.call(model="qwen-vl-max", messages=messages)
print(response.output.choices[0].message.content[0]["text"])
```

### Embedding de texto

```python
from dashscope import TextEmbedding

resp = TextEmbedding.call(
    model=TextEmbedding.Models.text_embedding_v3,
    input=["El viento es veloz, el cielo es alto", "Los islotes son claros, la arena es blanca"],
    text_type="document",
)
for e in resp.output["embeddings"]:
    print(e["text_index"], e["embedding"][:3])
```

### Embedding multimodal

```python
from dashscope import MultiModalEmbedding

resp = MultiModalEmbedding.call(
    model="multimodal-embedding-v1",
    input=[{"image": "https://dashscope.oss-cn-beijing.aliyuncs.com/images/256_1.png"}],
)
print(resp.output)
```

Usa las clases de item explícitas para combinar texto/imagen/audio en un único vector fusionado (cada una requiere un peso `factor`, y `enable_fusion` solo está disponible en `qwen3-vl-embedding`):

```python
from dashscope import MultiModalEmbedding
from dashscope.embeddings.multimodal_embedding import (
    MultiModalEmbeddingItemText,
    MultiModalEmbeddingItemImage,
    MultiModalEmbeddingItemAudio,
)

resp = MultiModalEmbedding.call(
    model="qwen3-vl-embedding",
    input=[
        MultiModalEmbeddingItemText(text="un auto deportivo rojo", factor=1.0),
        MultiModalEmbeddingItemImage(image="https://dashscope.oss-cn-beijing.aliyuncs.com/images/256_1.png", factor=1.0),
        MultiModalEmbeddingItemAudio(audio="https://dashscope.oss-cn-beijing.aliyuncs.com/audios/welcome.mp3", factor=1.0),
    ],
    enable_fusion=True,
)
print(resp.output)
```

### Embedding de texto por lotes (offline)

Para grandes volúmenes de texto, envía un archivo (un texto por línea) para el embedding asíncrono por lotes en lugar de llamar a `TextEmbedding.call` por cada elemento:

```python
from dashscope import BatchTextEmbedding

resp = BatchTextEmbedding.call(
    model=BatchTextEmbedding.Models.text_embedding_async_v2,
    url="https://example.com/texts.txt",
)
print(resp.output.task_id, resp.output.task_status)
if resp.output.task_status == "SUCCEEDED":
    print(resp.output.url)  # descarga el archivo de resultados desde aquí
```

Envía la tarea sin bloquear y consulta el estado por separado:

```python
from dashscope import BatchTextEmbedding

task = BatchTextEmbedding.async_call(
    model=BatchTextEmbedding.Models.text_embedding_async_v2,
    url="https://example.com/texts.txt",
)
print(task.output.task_id)

result = BatchTextEmbedding.wait(task)
print(result.output.task_status)
```

### Reordenamiento de texto (ReRank)

```python
from dashscope import TextReRank

resp = TextReRank.call(
    model=TextReRank.Models.gte_rerank,
    query="¿Cuál es la capital de China?",
    documents=[
        "La capital de China es Pekín.",
        "China es un país grande en el este de Asia.",
    ],
    return_documents=True,
    top_n=1,
)
for r in resp.output.results:
    print(r.index, r.relevance_score, r.document)
```

Usa `AioTextReRank` para la forma `async`/`await`:

```python
import asyncio
from dashscope import AioTextReRank

async def main():
    resp = await AioTextReRank.call(
        model=AioTextReRank.Models.gte_rerank,
        query="¿Cuál es la capital de China?",
        documents=["La capital de China es Pekín.", "China es un país grande en el este de Asia."],
        return_documents=True,
        top_n=1,
    )
    for r in resp.output.results:
        print(r.index, r.relevance_score, r.document)

asyncio.run(main())
```

### Generación de código

`CodeGeneration` da soporte a escenarios de programación específicos (`Scenes`): generación de código a partir de lenguaje natural, explicación de código, generación de comentarios, mensajes de commit, pruebas unitarias, preguntas y respuestas sobre código, y generación de SQL a partir de lenguaje natural.

```python
from dashscope import CodeGeneration

response = CodeGeneration.call(
    model=CodeGeneration.Models.tongyi_lingma_v1,
    scene=CodeGeneration.Scenes.nl2code,
    message=[
        {"role": "user", "content": "Calcula el tamaño total de todos los archivos en una ruta dada"},
        {"role": "attachment", "meta": {"language": "python"}},
    ],
)
print(response.output)
```

### Generación de imágenes

```python
from http import HTTPStatus
from dashscope import ImageSynthesis

rsp = ImageSynthesis.call(
    model="wanx2.1-t2i-turbo",
    prompt="una floristería con ventanas delicadas y una puerta de madera",
    n=1,
    size="1024*1024",
)
if rsp.status_code == HTTPStatus.OK:
    for result in rsp.output.results:
        print(result.url)
```

`call` ya bloquea hasta que la tarea se completa; envíala sin bloquear y consulta el estado por separado con `async_call` + `wait`:

```python
from dashscope import ImageSynthesis

task = ImageSynthesis.async_call(
    model="wanx2.1-t2i-turbo",
    prompt="una floristería con ventanas delicadas y una puerta de madera",
    n=1,
    size="1024*1024",
)
print(task.output.task_id)

rsp = ImageSynthesis.wait(task)
for result in rsp.output.results:
    print(result.url)
```

`sync_call` (actualmente solo para `wan2.2-t2i-flash`/`wan2.2-t2i-plus`) devuelve el resultado directamente en lugar de consultar una tarea asíncrona:

```python
from http import HTTPStatus
from dashscope import ImageSynthesis

rsp = ImageSynthesis.sync_call(
    model="wan2.2-t2i-flash",
    prompt="una floristería con ventanas delicadas y una puerta de madera",
    n=1,
    size="1024*1024",
)
if rsp.status_code == HTTPStatus.OK:
    print(rsp.output)
```

Usa `AioImageSynthesis.sync_call` para la forma `async`/`await`:

```python
import asyncio
from dashscope import AioImageSynthesis

async def main():
    rsp = await AioImageSynthesis.sync_call(
        model="wan2.2-t2i-flash",
        prompt="una floristería con ventanas delicadas y una puerta de madera",
        n=1,
        size="1024*1024",
    )
    print(rsp.output)

asyncio.run(main())
```

### De boceto a imagen y edición de imágenes

`ImageSynthesis.call` también acepta un boceto dibujado a mano o una imagen existente para editar, mediante modelos y parámetros dedicados:

```python
from dashscope import ImageSynthesis

# De boceto a imagen
rsp = ImageSynthesis.call(
    model=ImageSynthesis.Models.wanx_sketch_to_image_v1,
    prompt="un gato lindo, estilo acuarela",
    sketch_image_url="https://example.com/sketch.png",
)

# Edita una imagen existente con una instrucción de texto
rsp = ImageSynthesis.call(
    model=ImageSynthesis.Models.wanx_2_1_imageedit,
    prompt="cambia el fondo a una playa",
    function="description_edit",
    base_image_url="https://example.com/photo.png",
)
print(rsp.output)
```

### Generación de video

La generación de video se ejecuta como una tarea asíncrona; `call` bloquea hasta que se completa, o puedes usar `async_call` + `wait`/`fetch` para consultar el estado manualmente.

```python
from http import HTTPStatus
from dashscope import VideoSynthesis

rsp = VideoSynthesis.call(
    model="wan2.7-t2v",
    prompt="un gatito corriendo bajo la luz de la luna",
    audio=True,
    watermark=True,
)
if rsp.status_code == HTTPStatus.OK:
    print(rsp.output.video_url)
```

Envía la tarea sin bloquear y consulta el estado por separado:

```python
from dashscope import VideoSynthesis

task = VideoSynthesis.async_call(model="wan2.7-t2v", prompt="un gatito corriendo bajo la luz de la luna")
print(task.output.task_id)

rsp = VideoSynthesis.wait(task)
print(rsp.output.video_url)
```

### Síntesis de voz (TTS)

Los modelos Qwen-TTS se llaman a través de `MultiModalConversation`, pasando `text`/`voice` en lugar de `messages`:

```python
from dashscope import MultiModalConversation

response = MultiModalConversation.call(
    model="qwen3-tts-flash",
    text="Today is a wonderful day to build something people love!",
    voice="Cherry",
    language_type="English",
)
print(response.output.audio.url)
```

Los modelos CosyVoice usan el `SpeechSynthesizer` dedicado:

```python
from dashscope.audio.tts import SpeechSynthesizer

result = SpeechSynthesizer.call(
    model="cosyvoice-v1",
    text="Hello, Bailian.",
    format=SpeechSynthesizer.AudioFormat.format_wav,
)
with open("output.wav", "wb") as f:
    f.write(result.get_audio_data())
```

`SpeechSynthesisResult` también expone marcas de tiempo por frase y la respuesta bruta de la tarea, útiles p. ej. para sincronizar subtítulos:

```python
print(result.get_timestamps())  # tiempos de inicio/fin de cada frase
print(result.get_response())    # el SpeechSynthesisResponse subyacente (status, request_id, ...)
```

Para streaming en lugar de una única llamada bloqueante, hereda de `ResultCallback` y pásalo como `callback=`; `on_event` recibe cada fragmento de `SpeechSynthesisResult` a medida que se genera el audio:

```python
from dashscope.audio.tts import SpeechSynthesizer, ResultCallback

class Callback(ResultCallback):
    def on_event(self, result) -> None:
        with open("output.wav", "ab") as f:
            f.write(result.get_audio_frame())

SpeechSynthesizer.call(
    model="cosyvoice-v1",
    text="Hello, Bailian.",
    format=SpeechSynthesizer.AudioFormat.format_wav,
    callback=Callback(),
)
```

`HttpSpeechSynthesizer` llama a la síntesis de voz por HTTP simple (sin WebSocket), útil en entornos que no pueden mantener una conexión persistente:

```python
from dashscope.audio.http_tts import HttpSpeechSynthesizer

result = HttpSpeechSynthesizer.call(
    model="cosyvoice-v3-flash",
    text="Hello, Bailian.",
    voice="longxiaochun",
    audio_format="wav",
)
with open("output.wav", "wb") as f:
    f.write(result.audio_data)
```

### Síntesis de voz en streaming (CosyVoice v2)

Envía texto de forma incremental y recibe los bytes de audio a medida que se generan, mediante un callback:

```python
from dashscope.audio.tts_v2 import ResultCallback, SpeechSynthesizer

class Callback(ResultCallback):
    def on_data(self, data: bytes) -> None:
        with open("output.mp3", "ab") as f:
            f.write(data)

synthesizer = SpeechSynthesizer(model="cosyvoice-v2", voice="longxiaochun_v2", callback=Callback())
for text in ["Hola, ", "esto es síntesis de voz ", "en streaming."]:
    synthesizer.streaming_call(text)
synthesizer.streaming_complete()
```

### Reconocimiento de voz (ASR)

`qwen3-asr-flash` y modelos similares de comprensión de audio se llaman a través de `MultiModalConversation`:

```python
from dashscope import MultiModalConversation

messages = [{
    "role": "user",
    "content": [{"audio": "https://dashscope.oss-cn-beijing.aliyuncs.com/audios/welcome.mp3"}],
}]
response = MultiModalConversation.call(
    model="qwen3-asr-flash",
    messages=messages,
    result_format="message",
)
print(response.output.choices[0].message.content)
```

La transcripción por lotes basada en archivos usa `Transcription`:

```python
from dashscope.audio.asr import Transcription

response = Transcription.call(
    model=Transcription.Models.paraformer_v1,
    file_urls=["https://example.com/audio.wav"],
)
if response.output.task_status == "SUCCEEDED":
    print(response.output.results)
```

### Reconocimiento de voz en streaming

Para una fuente de audio en vivo/streaming, envía fotogramas PCM uno a uno y recibe los resultados mediante un callback (aquí se lee un archivo por fragmentos para demostrar el patrón — reemplaza el bucle de lectura del archivo por tu fuente de audio en vivo):

```python
from dashscope.audio.asr import Recognition, RecognitionCallback

class Callback(RecognitionCallback):
    def on_event(self, result) -> None:
        print(result.get_sentence())

recognition = Recognition(
    model="paraformer-realtime-v1",
    format="pcm",
    sample_rate=16000,
    callback=Callback(),
)
recognition.start()
with open("audio.pcm", "rb") as f:
    while chunk := f.read(3200):
        recognition.send_audio_frame(chunk)
recognition.stop()
```

Para clonación de voz, corrección de pronunciación, traducción de voz en tiempo real y palabras clave (hot words) personalizadas para ASR, consulta la [guía de audio avanzado](docs/guides/realtime-audio_es.md).

### Aplicación de Bailian (App de agente)

Llama a una app que hayas creado en el [Centro de Aplicaciones de Bailian](https://bailian.console.aliyun.com/):

```python
from http import HTTPStatus
from dashscope import Application

responses = Application.call(
    app_id="YOUR-APP-ID",
    prompt="Resume este archivo",
    stream=True,
    incremental_output=True,
    file_list=["https://example.com/document.pdf"],
)
for response in responses:
    if response.status_code != HTTPStatus.OK:
        print(f"code={response.code}, message={response.message}")
    else:
        print(response.output.text, end="")
```

### AgentStudio (agentes gestionados)

`dashscope.agentstudio` gestiona agentes construidos en el producto AgentStudio de Bailian — creando agentes/sesiones y recibiendo eventos conversacionales en streaming, o creando "despliegues" programados que ejecutan un agente según un cron:

```python
from dashscope.agentstudio import Client
from dashscope.agentstudio.types import user_message

client = Client(api_key="sk-xxx")
agent = client.agents.create(name="demo", model="qwen-plus")
session = client.sessions.create(agent=agent.id)
client.sessions.events.send(session.id, [user_message("¡Hola!")])
with client.sessions.events.stream(session.id) as stream:
    for event in stream:
        print(event.type, event.to_dict())
        if event.type == "session_status":
            break
```

Nota: `Client()` lee la variable de entorno `DASHSCOPE_WORKSPACE` (sin el sufijo `_ID`) — distinta de `DASHSCOPE_WORKSPACE_ID`, usada en toda la SDK para la [configuración de región](#configuración-de-región-y-endpoint). Un ejemplo completo de despliegue programado está en [`samples/agentstudio_deployments.py`](samples/agentstudio_deployments.py).

### Tokenización local

Cuenta o codifica/decodifica tokens para modelos Qwen localmente, sin una llamada a la API (requiere `pip install "dashscope[tokenizer]"`):

```python
from dashscope.tokenizers.tokenizer import get_tokenizer

tokenizer = get_tokenizer("qwen-turbo")  # funciona con cualquier modelo qwen-*
tokens = tokenizer.encode("这个是千问tokenizer")
print(len(tokens))               # número de tokens
print(tokenizer.decode(tokens))  # vuelve a convertir a texto
```

`Tokenization.call` hace el mismo trabajo pero mediante una llamada a la API remota (útil para modelos no compatibles con el tokenizer local):

```python
from dashscope import Tokenization

resp = Tokenization.call(model=Tokenization.Models.qwen_turbo, prompt="这个是千问tokenizer")
print(resp.output["token_ids"], resp.output["tokens"])
print(resp.usage["input_tokens"])
```

### Listado de modelos disponibles

```python
from dashscope import Models

models = Models.list(page=1, page_size=10)
print(models.output["models"])

model = Models.get("qwen-plus")
print(model.output["model_id"])
```

### Fine-tuning

Sube un archivo de entrenamiento, lanza un trabajo de fine-tuning y espera hasta que se complete (requiere `pip install "dashscope[rl]"` para fine-tuning con Agentic RL; el fine-tuning supervisado clásico no necesita ningún extra):

```python
from dashscope import Files, FineTunes

file_response = Files.upload(file_path="train.jsonl", purpose="fine_tune")
file_id = file_response.output["uploaded_files"][0]["file_id"]

job = FineTunes.call(
    model="qwen-turbo",
    training_file_ids=file_id,
    hyper_parameters={"n_epochs": 10, "learning_rate": 0.001},
)
print(job.output.job_id, job.output.status)

result = FineTunes.wait(job.output.job_id)  # consulta el estado cada 30s hasta terminar
print(result.output.status)
```

Para fine-tuning con Agentic RL basado en funciones personalizadas de rollout/reward (trabajos de entrenamiento definidos en YAML, tracing/observabilidad), consulta la guía dedicada en [`dashscope/finetune/reinforcement/examples/workspace/README-es.md`](dashscope/finetune/reinforcement/examples/workspace/README-es.md) (inicio rápido) y [`UserGuide-es.md`](dashscope/finetune/reinforcement/examples/workspace/UserGuide-es.md) (referencia completa).

### Despliegue de un modelo ajustado

Despliega el modelo producido por un trabajo de fine-tuning para poder llamarlo como a cualquier otro modelo:

```python
from dashscope import Deployments, Generation

deployment = Deployments.call(model=result.output.finetuned_output, capacity=1)
deployed_model = deployment.output.deployed_model

# Consulta el estado hasta que deployment.output.status == "RUNNING", y luego llámalo como a cualquier modelo:
status = Deployments.get(deployed_model).output.status
response = Generation.call(model=deployed_model, messages=[{"role": "user", "content": "Hi"}])
```

Para el ciclo de vida completo de trabajos/despliegues (listado, cancelación, streaming de eventos, escalado), consulta la [guía de fine-tuning y ciclo de vida de despliegues](docs/guides/fine-tuning_es.md).

### API de Assistants (obsoleta)

La API de Assistants heredada (`Assistants`, `Threads`, `Runs`, `Messages`) sigue funcionando pero está obsoleta — consulta la [guía de la API de Assistants](docs/guides/assistants_es.md) para conocer toda su superficie y las notas de migración. El código nuevo debería usar [`Generation`](#guía-rápida) o [`MultiModalConversation`](#comprensión-multimodal-visión) en su lugar.

## Uso de la CLI

Cada capacidad del SDK también está disponible como subcomando de `dashscope` (instalado junto con el paquete base), para scripting o comprobaciones rápidas sin escribir Python:

```shell
# Generación de texto
dashscope generation create -m qwen-plus -p "Who are you?"
dashscope generation create -m qwen-plus -p "Escribe un haiku sobre el mar" --stream

# Listar / inspeccionar los modelos disponibles
dashscope models list
dashscope models get qwen-plus

# Subir, listar, inspeccionar y eliminar archivos
dashscope files upload -f ./train.jsonl -p fine_tune
dashscope files list
dashscope files get <file_id>
dashscope files delete <file_id>

# Subir un archivo directamente a OSS (usado por algunos modelos de CV/visión)
dashscope oss upload -f ./photo.png -m wanx-style-repaint-v1

# Desplegar un modelo ajustado y gestionar ese despliegue
dashscope deployments create -m <finetuned-model-id> --plan mu -c 1
dashscope deployments list
dashscope deployments get <deployed_model>
dashscope deployments scale <deployed_model> -c 2
dashscope deployments delete <deployed_model>

# Gestión de trabajos de Agentic RL (ver la guía de reinforcement learning para `dashscope rl run`)
dashscope rl list
dashscope rl get <job_id>
dashscope rl logs <job_id>
dashscope rl cancel <job_id>
```

Ejecuta `dashscope --help` o `dashscope <command> --help` (p. ej. `dashscope generation --help`) para ver todos los grupos de comandos (`generation`, `ft`, `files`, `deployments`, `models`, `embeddings`, `rerank`, `tokenization`, `application`, `image-synthesis`, `video-synthesis`, `multimodal-conversation`, `transcription`, `speech-synthesis`, `rl`, ...) y sus opciones. Ejecutar `dashscope` sin argumentos, en cambio, inicia el [asistente de IA](#asistente-de-ia-dashscope-sdk-expert) interactivo.

## Autocompletado de shell

Ejecuta el comando correspondiente una vez y luego reinicia tu shell (o vuelve a cargar tu archivo de configuración):

| Shell | Comando de instalación |
|-------|-----------------|
| **bash** | `dashscope --install-completion bash` |
| **zsh** | `dashscope --install-completion zsh` |
| **fish** | `dashscope --install-completion fish` |

Para previsualizar el script de autocompletado sin instalarlo:
```shell
dashscope --show-completion bash
```

## Registro (logging)
Configura `DASHSCOPE_LOGGING_LEVEL` antes de importar `dashscope` para que
adjunte automáticamente un handler de consola (`info` o `debug`):

```shell
export DASHSCOPE_LOGGING_LEVEL='info'
```

```python
from dashscope import Generation

# Ahora los detalles de la solicitud se imprimen automáticamente en la consola, p. ej.:
# 2024-01-01 12:00:00,000 - dashscope - ... - INFO - request: POST https://...
response = Generation.call(model="qwen-plus", messages=[{"role": "user", "content": "Hi"}])
```

## Salida

Cada llamada del SDK devuelve (o produce, en modo streaming) un objeto de respuesta con estos campos:

```python
response = Generation.call(model="qwen-plus", messages=[{"role": "user", "content": "Hi"}])

response.request_id    # str: el ID de la solicitud, útil al reportar problemas
response.status_code   # int: código de estado HTTP; 200 significa éxito
response.code          # str: código de error si falla, vacío en caso contrario
response.message       # str: mensaje de error si falla, vacío en caso contrario
response.output        # Any: la salida de la solicitud (la forma depende de la API llamada)
response.usage         # Any: información de uso de tokens/cuota
```

Para saber cómo `output`/`usage` admiten tanto el acceso estilo diccionario como estilo atributo, y las subclases de respuesta específicas de cada capacidad, consulta la [guía del modelo de objetos de respuesta](docs/guides/response-types_es.md).

## Licencia
Este proyecto está licenciado bajo la Apache License (Versión 2.0).
