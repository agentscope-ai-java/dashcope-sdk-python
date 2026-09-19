# Basic Chat — Ejemplo mínimo funcional de acli

> [English](README.md) | [中文](README_zh.md) | [日本語](README_ja.md) | **Español** | [한국어](README_ko.md)

Muestra cómo iniciar un agente de chat de propósito general con capacidad de búsqueda web usando una configuración mínima. **Toda la inteligencia reside en la configuración de `.acli/` — no hay código de arranque en Python** — descarga y ejecuta `acli` directamente.

## Estructura de directorios

```
basic-chat/
└── .acli/
    ├── config.toml                   # Provider/modelo/user_name por defecto
    ├── custom-extensions.toml        # Declaración del provider tongyi + plantillas de comentarios de capability/skill/shell_tool
    ├── hooks.toml                    # Plantillas de comentarios de hooks de eventos (before/after_tool_call, on_error, etc.)
    ├── system-prompt.md              # Persona del agente y reglas de comportamiento
    └── skills/
        ├── research-topic.md         # Busca un tema en la web y genera un resumen (llama a web_search)
        ├── explain-code.md           # Explica la lógica del código
        ├── translate.md              # Traducción chino-inglés
        └── write-poem.md             # Escribe una cuarteta de siete caracteres (demuestra una plantilla de prompt pura)
```

## Inicio rápido

```bash
pip install acli
export DASHSCOPE_API_KEY="sk-xxx"

# Fusiona el ejemplo en ./.acli/ (los archivos con el mismo nombre se respaldan automáticamente en .acli/backup/; deshazlo con example restore)
acli example download basic-chat

# Edita .acli/custom-extensions.toml para añadir los providers que necesites
# Edita .acli/system-prompt.md para definir la persona del agente
# Añade tus propias plantillas de skill en .acli/skills/

# Inicia (no hace falta cd; la configuración ya está en el directorio actual)
acli
acli --tui
acli -c "hello"
```

> ¿Quieres usarlo en un directorio nuevo? `mkdir my-agent && cd my-agent && acli example download basic-chat`,
> o usa `acli example download basic-chat --target my-agent`.

## La configuración como programa

### custom-extensions.toml — Declaraciones de providers

Declara qué providers de LLM puede usar acli. Una configuración mínima solo necesita un bloque `[[providers]]`:

```toml
[[providers]]
name = "tongyi"
base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
api_key_env = "DASHSCOPE_API_KEY"      # ← solo guarda el nombre de la variable de entorno; el shell provee el sk-xxx
default_model = "qwen3.8-max"
models = ["qwen3.8-max", "qwen3.7-max", "qwen3.7-plus", "qwen-turbo", "qwen-vl-max"]
vision_models = ["qwen-vl-max"]        # ← le indica a acli que estos modelos aceptan entrada de imagen
protocol = "openai"                     # ← openai / anthropic / dashscope
```

¿Quieres Claude / GPT / un Ollama local? Solo descomenta el bloque `[[providers]]` correspondiente en el toml.

**Tres formas de proporcionar una API key** (en orden decreciente de recomendación):

1. `api_key_env = "FOO_API_KEY"` — `export FOO_API_KEY=sk-xxx` en el shell; el toml se puede subir a git de forma segura
2. Asistente interactivo `/provider` — escribe `api_key = "ENC:..."` (cifrado vinculado a la máquina)
3. Texto plano `api_key = "sk-xxx"` — rechazado por el cargador; solo es un ejemplo ilustrativo

### system-prompt.md — Persona del agente

Define quién "es" el agente. acli carga automáticamente `.acli/system-prompt.md` al iniciar (la configuración del workspace tiene prioridad sobre `~/.acli/system-prompt.md`).

### skills/*.md — Plantillas de prompt

Cada archivo `.md` es un prompt reutilizable con frontmatter YAML:

```yaml
---
name: research-topic
description: Web-search a topic and produce a briefing with source URLs
arguments: [topic]
---

Use the web_search tool to research "{topic}":
...
```

Cómo invocarlo:
- `/skill research-topic quantum computing` — invocación explícita
- Lenguaje natural: "help me research the latest progress in quantum computing" — el LLM decide si usarlo

`research-topic` muestra cómo usar un prompt para guiar al LLM a llamar a la herramienta integrada `web_search` para recopilar información en línea.

### config.toml — Valores por defecto

```toml
user_name = "dashscope"
provider = "tongyi"
model = "qwen3.8-max"
memory_user_id = "acli-basic"
```

## Próximos pasos

- **Añadir más providers**: añade bloques `[[providers]]` en `custom-extensions.toml`
- **Añadir herramientas HTTP**: añade bloques `[[capabilities]]` + `[[capabilities.tools]]` (por ejemplo, generación de imágenes, llamar a un motor de workflows remoto)
- **Añadir capacidad de visión**: añade una herramienta de capability con `type = "vision"` para que el agente de texto pueda llamar a un LLM de visión bajo demanda
- **Añadir herramientas de shell**: añade bloques `[[shell_tools]]` para envolver comandos locales comunes
- **Añadir hooks**: configura hooks pre/post de llamada a herramientas en `.acli/hooks.toml` (por ejemplo, `py_compile` automático tras escribir un archivo `.py`, confirmación antes de `pip install`, bloquear el borrado de archivos). Consulta la plantilla en `.acli/hooks.toml`, que cubre los 5 eventos (`before_tool_call` / `after_tool_call` / `on_error` / `on_message` / `on_response`) × 6 acciones (run/block/confirm/warn/alert/log).
- **Añadir conocimiento persistente**: coloca en `.acli/references/*.md` los documentos que deban aparecer **siempre** en el system prompt (por ejemplo, un índice de API)
- **Cambiar la persona**: edita `system-prompt.md` — por ejemplo, conviértelo en un "revisor de código", "analista de datos" o "agente de atención al cliente"

Consulta el `README.md` de la raíz del proyecto para la documentación completa de funcionalidades.
