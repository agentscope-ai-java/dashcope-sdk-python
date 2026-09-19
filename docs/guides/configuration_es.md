# Configuración Avanzada

> [English](configuration.md) | [中文](configuration_zh.md) | [日本語](configuration_ja.md) | **Español** | [한국어](configuration_ko.md)

Esta guía cubre la configuración del SDK más allá de la autenticación y la
selección de región. Para configurar la API key, consulte [Autenticación con API Key](../../README.md#api-key-authentication);
para cambiar de región/endpoint, consulte [Configuración de Región y Endpoint](../../README.md#region-and-endpoint-configuration).

## Tiempo de espera de la solicitud (Request Timeout)

Todo método de tipo `.call()`/`.create()`/`.get()`/`.list()`/`.delete()` acepta
un argumento con nombre `request_timeout` (en segundos). Su valor predeterminado
es 300 segundos (`DEFAULT_REQUEST_TIMEOUT_SECONDS`). Para solicitudes en streaming
es el tiempo de espera inactivo entre fragmentos; para solicitudes no streaming
es el tiempo de espera total de la solicitud.

```python
from dashscope import Generation

response = Generation.call(
    model="qwen-plus",
    messages=[{"role": "user", "content": "Hi"}],
    request_timeout=30,
)
```

## Encabezados de solicitud personalizados

Pase un diccionario `headers` para combinar encabezados HTTP adicionales en la
solicitud (los encabezados propios del SDK, como `Authorization`/workspace,
se siguen aplicando):

```python
from dashscope import Generation

response = Generation.call(
    model="qwen-plus",
    messages=[{"role": "user", "content": "Hi"}],
    headers={"X-Request-Tag": "my-service"},
)
```

La interfaz compatible con OpenAI `Completions.create` tiene un parámetro
dedicado `extra_headers` para el mismo propósito:

```python
from dashscope.aigc.chat_completion import Completions

response = Completions.create(
    model="qwen-max",
    messages=[{"role": "user", "content": "Hi"}],
    api_key="YOUR-DASHSCOPE-API-KEY",
    extra_headers={"X-Request-Tag": "my-service"},
)
```

## Soporte de Proxy

El SDK no implementa su propia configuración de proxy; en su lugar, se basa en
el comportamiento estándar de las bibliotecas HTTP subyacentes. El cliente
asíncrono crea su `aiohttp.ClientSession` con `trust_env=True`, y el
`requests.Session` del cliente síncrono respeta los proxies por defecto —
ambos recogen automáticamente las variables de entorno estándar `HTTP_PROXY`,
`HTTPS_PROXY` y `NO_PROXY`:

```shell
export HTTPS_PROXY="http://proxy.example.com:8080"
```

```python
from dashscope import Generation

# Las solicitudes ahora pasan por el proxy configurado mediante HTTPS_PROXY
response = Generation.call(model="qwen-plus", messages=[{"role": "user", "content": "Hi"}])
```

## Cierre de los pools de conexiones compartidos

El SDK mantiene una `requests.Session` compartida (síncrona) y una
`aiohttp.ClientSession` por bucle de eventos (asíncrona) para el pooling de
conexiones. Los procesos de larga duración pueden cerrarlas explícitamente
para liberar las conexiones agrupadas (se crea una nueva sesión de forma
perezosa en la siguiente solicitud):

```python
import asyncio
from dashscope import close_shared_sync_session, close_shared_aio_session

close_shared_sync_session()
asyncio.run(close_shared_aio_session())
```

## Registro (Logging)

Como se explica en el [README](../../README.md#logging), configurar
`DASHSCOPE_LOGGING_LEVEL` antes de importar adjunta automáticamente un
manejador de consola. Dado que el SDK registra a través del módulo estándar
`logging` bajo el nombre de logger `"dashscope"`, también puede controlarlo
de forma programática sin usar la variable de entorno:

```python
import logging

logging.getLogger("dashscope").setLevel(logging.DEBUG)
```
