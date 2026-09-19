# DashScope SDK Expert — Ejemplo de acli basado en configuración

> [English](README.md) | [中文](README_zh.md) | [日本語](README_ja.md) | **Español** | [한국어](README_ko.md)

**Guía en línea**: https://help.aliyun.com/en/model-studio/dashscope-sdk-expert

Este ejemplo muestra cómo construir un agente experto en IA para un escenario específico usando los mecanismos de configuración nativos de **AgenticCLI (acli)**.

**Idea central: impulsado por configuración, sin código pegamento en Python.** La identidad, capacidades, skills e índice de conocimiento del agente se definen todos mediante archivos bajo `.acli/`; descarga el ejemplo y ejecuta `acli` directamente para iniciar.

## Estructura de directorios

```
dashscope-sdk-expert/
└── .acli/                      # Directorio de configuración del agente
    ├── config.toml              # Configuración de modelo y usuario
    ├── custom-extensions.toml   # Declaración del provider (tongyi)
    ├── hooks.toml               # Hooks de eventos
    ├── system-prompt.md         # System prompt (persona del agente y reglas de comportamiento)
    └── skills/                  # Plantillas de skill (cargadas por el modelo bajo demanda vía use_skill)
        ├── text-generation.md   # Generación de texto (Generation / compatible con OpenAI, Python+Java)
        ├── multimodal.md        # Multimodal (MultiModalConversation/ImageSynthesis/VideoSynthesis)
        ├── speech.md            # Voz (SpeechSynthesizer/Transcription)
        ├── retrieval.md         # Recuperación (Embedding/TextReRank/RAG)
        ├── fine-tuning.md       # Fine-tuning y despliegue (SFT/CPT/DPO/Deployments)
        ├── agent.md             # Agente (Application/Assistants/plugins y MCP)
        ├── cli.md               # Referencia de comandos de la CLI de dashscope
        ├── sdk-example.md       # Genera ejemplos de código del SDK
        ├── api-doc.md           # Consulta la documentación de parámetros de la API
        ├── diagnose.md          # Diagnostica errores de llamadas al SDK
        ├── error-code.md        # Explica los códigos de error
        ├── explain-code.md      # Explica la lógica del código
        └── translate.md         # Traducción chino-inglés
```

## Inicio rápido

```bash
pip install acli
export DASHSCOPE_API_KEY="sk-xxx"

# Fusiona el ejemplo en ./.acli/ (los archivos con el mismo nombre se respaldan automáticamente en .acli/backup/; deshazlo con example restore)
acli example download dashscope-sdk-expert

# Inicia — sin cd, sin script de arranque en Python
acli
acli --tui
acli -c "How do I use Generation.call?"
```

## El enfoque impulsado por configuración

### 1. system-prompt.md — Persona del agente

Define la identidad del agente, el alcance de su conocimiento y las reglas de comportamiento. Es el núcleo de quién "es" el agente:

```markdown
You are DashScope SDK Expert, an intelligent assistant for the DashScope Python SDK...

## Grounded Knowledge First
Before answering, ALWAYS verify against the actual installed SDK...
```

### 2. skills/ — Base de conocimiento de dominio (cargada bajo demanda)

El conocimiento de la interfaz pública del SDK/CLI vive directamente en skills de dominio: un archivo por dominio, con listas de modelos, firmas del SDK en Python y Java, estructuras de entrada/salida y códigos de error. Al responder preguntas sobre la API, el modelo carga el skill correspondiente bajo demanda mediante `use_skill` — **nada permanece de forma permanente en el system prompt** — reduciendo los tokens de entrada del primer turno en unos 16k caracteres; los detalles no cubiertos por un skill recurren a `inspect.signature` / `help()` sobre el paquete instalado.

### 3. skills/ — Plantillas de tareas

Cada archivo `.md` es una plantilla de prompt reutilizable con metadatos en el frontmatter:

```yaml
---
name: sdk-example
description: Generate runnable DashScope SDK code examples
arguments: [api_name]
---

Before generating code, first verify the user's installed SDK version and API signature:
1. `run_command("python -c 'import dashscope; ...'")`
...
```

- **name**: identificador del skill, invocado mediante el comando `/skill`
- **description**: descripción breve; el agente la usa para decidir cuándo aplicar el skill
- **arguments**: variables de la plantilla, reemplazadas por valores reales al invocarla

### 4. config.toml — Configuración en tiempo de ejecución

```toml
user_name = "dashscope"
provider = "tongyi"
model = "qwen3.8-max"
memory_user_id = "acli-dashscope"
```

## Reutiliza este patrón

Para crear un experto en IA para tu propio escenario:

1. `acli example download dashscope-sdk-expert` (se fusiona en el `./.acli/` de tu proyecto)
2. Edita `.acli/system-prompt.md` — define la persona de tu agente
3. Edita `.acli/skills/` — añade tu conocimiento de dominio y plantillas de skill (cargadas por el modelo bajo demanda)
4. Edita `.acli/config.toml` — elige un modelo adecuado
5. Ejecuta `acli`

## Puntos clave del diseño

| Enfoque tradicional | Enfoque de configuración de acli |
|---------|---------------|
| Prompts codificados directamente en el código | Archivo `system-prompt.md` |
| Ramas if-else para distintos escenarios | Biblioteca de plantillas `skills/*.md` |
| Documentos enteros y extensos metidos en el prompt | Conocimiento de dominio en `skills/` cargado bajo demanda |
| Se requieren cambios de código para ajustar el comportamiento | Basta con editar Markdown |
| Difícil de compartir y reutilizar | Todo el directorio `.acli/` es portable |
