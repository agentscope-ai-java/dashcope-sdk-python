# Agentic Reinforcement Learning: Guía del usuario [[English]](./UserGuide.md) [[中文]](./UserGuide-zh.md) [[日本語]](./UserGuide-ja.md) [[한국어]](./UserGuide-ko.md)

---

## 1. Introducción

El **SDK/CLI de Agentic RL** ofrece una cadena de herramientas completa para construir, entrenar y gestionar modelos de aprendizaje por refuerzo (RL) para modelos de lenguaje de gran tamaño (LLMs). Simplifica el complejo flujo de trabajo de definir comportamientos de agentes, recopilar trayectorias y optimizar políticas.

El SDK consta de dos módulos principales:
1.  **Módulo de funciones**: gestiona el código Python personalizado para **Rollout** (generación de trayectorias), **Reward** (puntuación) y **Group Reward** (puntuación por lotes). Admite registro y pruebas automáticos, además de **observabilidad (Tracing)** integrada.
2.  **Módulo de ajuste (Tuning)**: gestiona los conjuntos de datos, la configuración de hiperparámetros, el envío de trabajos y la gestión del ciclo de vida (estado, logs, cancelación).

**Flujo de trabajo**:
1. Registra funciones personalizadas. El entrenamiento por refuerzo regular
   requiere un Rollout y al menos un Reward; Rollout y Reward son opcionales para OPD.
2. Usa el módulo de ajuste para subir los conjuntos de datos, configurar el
   trabajo y enviarlo para su entrenamiento.

---

## 2. Instalación y configuración

### 2.1 Instalar mediante PyPI
```bash
pip install dashscope>=1.25.19
```

### 2.2 Instalar desde el código fuente (para desarrollo)
```bash
git clone https://github.com/dashscope/dashscope-sdk-python.git
cd dashscope-sdk-python
pip install -e .  # Instalar en modo editable para desarrollo
```

### 2.3 Autorización
1.  Obtén tu **clave de API de DashScope**.
2.  Configura la variable de entorno:
    ```bash
    export DASHSCOPE_API_KEY='your-api-key-here'
    ```

### 2.4 Estructura del proyecto
Una estructura de espacio de trabajo recomendada garantiza una implementación y pruebas locales sin problemas:

```text
workspace/
├── data/                   # Conjuntos de datos
│   ├── training.jsonl
│   └── validation.jsonl
├── functions/              # Funciones personalizadas; opcional solo para OPD
│   ├── reward/
│   │   ├── group_reward.py
│   │   └── reward.py
│   └── rollout/
│       └── rollout.py
├── requirements.txt        # Dependencias de los componentes de función
├── rl-job.yaml             # Configuración de Agentic RL regular
└── opd-job.yaml            # Configuración de OPD
```

El entrenamiento por refuerzo regular requiere un Rollout personalizado y al
menos un Reward. Solo OPD puede omitir Rollout y Reward, o configurar
cualquiera de los dos de forma independiente.

### 2.5 Paquetes de dependencias (guía de requirements.txt)
Este archivo es **obligatorio** para implementar componentes de función en la nube. Debe estar en la raíz del espacio de trabajo.

**requirements.txt:**
```txt
fastapi==0.136.0
uvicorn==0.45.0
typer==0.24.1
rich==15.0.0
pyyaml==6.0.3
protobuf>=4.25.8,<7.0 #6.33.6
fsspec==2026.3.0
httpx==0.28.1
tenacity==9.1.4
```

**Notas clave:**
*   **Paquetes por defecto**: `dashscope` viene preinstalado en el entorno de ejecución. NO lo incluyas en tu `requirements.txt`.
*   **Protobuf**: debe mantenerse dentro del rango especificado para evitar problemas de compatibilidad.

#### Dependencias para observabilidad (Tracing)
Para usar los spans de observabilidad (processor / LLM / tool), agrega las siguientes dependencias a tu `requirements.txt` (versiones fijadas recomendadas para implementaciones reproducibles):

```txt
opentelemetry-api==1.41.1
opentelemetry-sdk==1.41.1
opentelemetry-exporter-otlp-proto-http==1.41.1
opentelemetry-processor-baggage==0.62b1
loongsuite-util-genai==0.4.0
```

### 2.6 Configuración de logs
Configura la verbosidad de los logs mediante la variable de entorno `LOG_LEVEL`:

```bash
export LOG_LEVEL="DEBUG"   # Más detallado (enmascara información sensible como las claves de API)
export LOG_LEVEL="INFO"    # Por defecto
export LOG_LEVEL="WARNING"
export LOG_LEVEL="ERROR"
export LOG_LEVEL="CRITICAL"
```

---

## 3. Escribir funciones
Referencia: directorio workspace/functions, con salida rollout.py, reward.py, etc.

### 3.1 Implementar funciones

Las funciones deben heredar de las clases base abstractas proporcionadas por el SDK.

#### Rollout Processor
Genera las trayectorias del agente (interacciones con el entorno/LLM).

```python
from dashscope.finetune.reinforcement import AbstractRolloutProcessor, RolloutInput, RolloutOutput

class DemoRolloutProcessor(AbstractRolloutProcessor):
    async def process(self, input: RolloutInput) -> RolloutOutput:
        # Generar la trayectoria (admite async/def)
        pass
```

#### Reward Processor
Puntúa pasos individuales o resultados finales.

```python
from dashscope.finetune.reinforcement import AbstractRewardProcessor, RewardInput, RewardOutput

class DemoRewardProcessor(AbstractRewardProcessor):
    def process(self, input: RewardInput) -> RewardOutput:
        # Calcular la puntuación de reward
        pass
```

#### Reward Processor avanzado con decoradores
```python
from dashscope.finetune.reinforcement import reward_func, sub_reward_func, aggregate_func

@reward_func("SafetyProcessor")
class SafetyProcessor(AbstractRewardProcessor):
    @sub_reward_func("toxicity", sub_weight=0.7)
    def toxicity(self, input: RewardInput) -> RewardOutput: ...

    @sub_reward_func("refusal", sub_weight=0.3)
    async def refusal(self, input: RewardInput) -> RewardOutput: ...

    @aggregate_func
    async def aggregate(self, sub_rewards: dict[str, RewardOutput]) -> RewardOutput: # Lógica de agregación personalizada
        weights = self.get_weights()
        scores = self.get_scores(sub_rewards)
        reward_metrics = self.get_reward_metrics(sub_rewards)

        total = ...  # Calcular el reward total
        return RewardOutput(...)
```

#### Group Reward Processor
Puntúa un lote de trayectorias en conjunto (por ejemplo, para hacer un ranking).

```python
from dashscope.finetune.reinforcement import AbstractGroupRewardProcessor, GroupRewardInput, GroupRewardOutput

class DemoGroupRewardProcessor(AbstractGroupRewardProcessor):
    def setup(self) -> None:
        pass

    async def process(self, input: GroupRewardInput) -> GroupRewardOutput:
        # Calcular los rewards del grupo
        pass
```

### 3.2 Observabilidad (Tracing)

Habilita una visibilidad profunda sobre la ejecución de tu agente usando OpenTelemetry. Los datos de trazas se exportan a **ARMS** (Alibaba Cloud Real-Time Monitoring Service) después de completar la autorización de ARMS en la consola. Consulta la [documentación de ARMS](https://help.aliyun.com/zh/arms/?spm=5176.30275541.J_ZGek9Blx07Hclc3Ddt9dg.3.3ce02f3dmKOpPK&scm=20140722.S_card@@%E4%BA%A7%E5%93%81@@596792.S_new~UND~card.ID_card@@%E4%BA%A7%E5%93%81@@596792-RL_arms-LOC_2024SPSearchCard-OR_ser-PAR1_0bc1409817757870159831522e3953-V_4-RE_new5-P0_0-P1_0).

#### Requisitos previos
1.  Agrega las dependencias de observabilidad a `requirements.txt` (ver Sección 2.5, "Dependencias para observabilidad (Tracing)").

#### Decoradores de instrumentación
Impórtalos desde `dashscope.finetune.reinforcement.component.observability`.

| Decorador | Uso | Descripción |
| :--- | :--- | :--- |
| `@observe_processor` | En el método `process()` | Traza automáticamente la entrada/salida, la latencia y el estado. Determina el tipo de span (ROLLOUT/REWARD) automáticamente. |
| `trace_client()` | En `setup()` o antes de la primera llamada al LLM | Envuelve clientes LLM (OpenAI, DashScope, tipo LangChain). Traza automáticamente todas las llamadas posteriores. **Recomendado.** |
| `@observe_llm` | En funciones LLM personalizadas | Úsalo si `trace_client` no admite tu wrapper. Requiere `model` y `messages` como kwargs. |
| `trace_tool()` | En `setup()` (después de crear las herramientas) | Envuelve herramientas (tipo LangChain/MCP/LangGraph). Traza automáticamente las invocaciones de herramientas. |
| `@observe_tool` | En funciones simples | Úsalo para funciones Python simples que no están envueltas como BaseTools. |

> **Configuración:** se llama una vez al iniciar el servidor; admite tanto síncrono como asíncrono. La configuración síncrona se descarga para evitar bloquear el bucle de eventos.

#### Qué admite `trace_client()` (duck typing)
`trace_client(client)` se detecta por estructura (no por nombre de clase). Admite:

- **Cliente completo de OpenAI** que expone `.chat.completions.create`
- **Recurso Completions** que expone `.create` y **no** `.chat` (por ejemplo, `ChatOpenAI.client`)
- **Wrapper tipo LangChain** que expone `.client` y/o `.async_client`
- **Clase DashScope Generation** (pasa la clase en sí, que tiene `call` como classmethod)

#### Qué admite `trace_tool()`
`trace_tool(tools)` acepta las siguientes formas:

- Un único objeto de herramienta (por ejemplo, `BaseTool` de LangChain)
- Una lista/tupla de herramientas
- Un diccionario que asigna nombres a herramientas
- Un `ToolNode` de LangGraph (las herramientas se expanden internamente)
- Herramientas MCP devueltas por `langchain-mcp-adapters` (el proveedor se establece automáticamente en `"mcp"`)

> **Nota sobre MCP:** el servidor y el cliente MCP se ejecutan en procesos separados. `@observe_tool` en la función del lado del servidor no tiene efecto en el lado del cliente. Llama siempre a `trace_tool(tools)` después de `get_tools()` en el lado del cliente.

#### Ejemplo: Rollout Processor instrumentado

```python
import openai
from dashscope.finetune.reinforcement import AbstractRolloutProcessor, RolloutInput, RolloutOutput
from dashscope.finetune.reinforcement.component.data.base_data_model import AgentOutput, TaskStatus
from dashscope.finetune.reinforcement.component.observability import (
    observe_processor,
    trace_client,
    trace_tool,
)

class MyRolloutProcessor(AbstractRolloutProcessor):

    async def setup(self) -> None:
        # 1. Trazar el cliente LLM
        self._client = openai.AsyncOpenAI(base_url="...", api_key="...")
        trace_client(self._client)

        # 2. Trazar herramientas (por ejemplo, MCP)
        from langchain_mcp_adapters.client import MultiServerMCPClient

        client = MultiServerMCPClient({...})
        self._tools = await client.get_tools()
        trace_tool(self._tools)

    @observe_processor
    async def process(self, input: RolloutInput) -> RolloutOutput:
        messages = input.messages or []
        model = input.model_resource.model_name

        # Esta llamada se traza automáticamente gracias a trace_client(self._client)
        response = await self._client.chat.completions.create(
            model=model,
            messages=messages,
        )

        content = response.choices[0].message.content if response.choices else ""

        return RolloutOutput(
            agent_output=AgentOutput(messages=messages, reward_score=0.0),
            status=TaskStatus.SUCCESS,
        )
```

---

## 4. Referencia del SDK y la CLI
* [SDK] Clase de interfaz: dashscope.finetune.agentic_rl.AgenticRL
* [CLI] Punto de entrada: dashscope rl

### 4.1 Configuración del trabajo

El entrenamiento por refuerzo regular y OPD usan el mismo flujo de trabajo de
SDK/CLI. Selecciona la configuración YAML correspondiente; los argumentos del
código sobrescriben los valores del YAML.

| Tipo de entrenamiento | Configuración | Funciones personalizadas |
|---|---|---|
| Refuerzo regular | `rl-job.yaml` | Rollout es obligatorio, con al menos un Reward |
| OPD | `opd-job.yaml` | Rollout y Reward son opcionales de forma independiente y pueden omitirse ambos |

**[SDK] \_\_init\_\_**
```python
def __init__(self, api_key: str = None): ...
```
Inicializa la instancia de AgenticRL.

**Parámetros**:
- `api_key`: clave de API para autenticación (usa la variable de entorno si no se proporciona)

**Ejemplo**:
```python
from dashscope.finetune.agentic_rl import AgenticRL
rl = AgenticRL(api_key="your_api_key")
```

**[SDK] [init](submit_job.py)**
```python
def init(self, config_path: Optional[str] = None, **kwargs) -> Self: ...
```
Inicializa la instancia a partir de un archivo de configuración YAML.

**Parámetros**:
- `config_path`: ruta al archivo de configuración YAML
- `**kwargs`: sobrescrituras de configuración

**Devuelve**: la propia instancia (Self)

**Ejemplo**:
```python
from dashscope.finetune.agentic_rl import AgenticRL
config_path = "opd-job.yaml"  # Usa "rl-job.yaml" para refuerzo regular
rl = AgenticRL().init(config_path, job_name="custom_job")
result = await rl.run()
```

Al seleccionar `opd-job.yaml`, conserva o elimina los bloques Rollout y Reward
para elegir las capacidades requeridas:

| Bloques de función conservados | Modo OPD | Origen de la trayectoria | Reward de la tarea |
|---|---|---|---|
| Ninguno | Solo Teacher | Plataforma | Deshabilitado |
| Solo Reward | Teacher + Reward | Plataforma | Reward personalizado |
| Solo Rollout | Teacher + Rollout | Rollout personalizado | Deshabilitado |
| Rollout y Reward | Teacher + Rollout + Reward | Rollout personalizado | Reward personalizado |

El `opd-job.yaml` incluido conserva ambos bloques. Elimina uno de los bloques,
o ambos, para seleccionar otra combinación de OPD:

```yaml
teacher_model: qwen3.5-397b-a17b

functions:
# Elimina este bloque para usar la generación de la plataforma.
- type: rollout
  # ...
# Elimina este bloque para deshabilitar los rewards de tarea personalizados.
- type: reward
  # ...

training:
  type: pg_opd
```

```bash
# Refuerzo regular
dashscope rl run -c rl-job.yaml

# OPD
dashscope rl run -c opd-job.yaml
```

### 4.2 Registrar funciones

Sube el código y registra los componentes de función (functions).

**[SDK] [register_functions](submit_job.py)**
```python
def register_functions(self, functions: Optional[Union[List[Union[RolloutFunctionComponent, RewardFunctionComponent]], RolloutFunctionComponent, RewardFunctionComponent]] = None, lazy_load: Optional[bool] = True) -> tuple: ...
```
Registra los componentes de función.

**Parámetros**:
- `functions`: componentes de función a registrar
- `lazy_load`: retrasa la carga hasta la ejecución

**Devuelve**: tupla de IDs de entidad/instancia

**Ejemplo**:
```python
from dashscope.finetune.agentic_rl import AgenticRL, AgenticRLFunctionComponent, FunctionType, FunctionComponentModel

rl=AgenticRL()
rollout_eids, reward_eids, group_eids, \
rollout_iids, reward_iids, group_iids = await rl.register_functions(
    functions=[
        AgenticRLFunctionComponent(
            type=FunctionType.ROLLOUT,
            fcmodel=FunctionComponentModel(
                zipdir='./',
                classpath="functions.rollout.rollout2.DemoRolloutProcessor"),
        ),

        AgenticRLFunctionComponent(
            type=FunctionType.REWARD,
            fcmodel=FunctionComponentModel(
                classpath="functions/reward/reward.py:DemoRewardProcessor"),
        ),

        AgenticRLFunctionComponent(
            type=FunctionType.GROUP_REWARD,
            fcmodel=FunctionComponentModel(
                classpath="functions.reward.group_reward.DemoGroupRewardProcessor"),
        ),
    ],
    lazy_load=False  # Establece False para obtener los IDs de instancia inmediatamente para pruebas
)
```

**[CLI] register_functions**

**Uso: dashscope register_functions [OPTIONS]**
```bash
 🧩 Register Rollout/Reward function components, returns entity_id & instance_id

 Requires at least one of:
 - rollout_classpath
 - reward_classpaths

╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --rollout-classpaths                             TEXT  List for rollout class path (file.py:ClassName)                                                                                                               │
│ --reward-classpaths                              TEXT  List for reward class path (file.py:ClassName)                                                                                                                │
│ --group-reward-classpaths                        TEXT  List for group-reward class path (file.py:ClassName)                                                                                                          │
│ --workspace-dir                                  TEXT  Local workspace directory [default: ./]                                                                                                                       │
│ --lazy-load                    --no-lazy-load          Delay instance loading (set False for debugging) [default: lazy-load]                                                                                         │
│ --api-key                                        TEXT  DashScope API Key (uses DASHSCOPE_API_KEY env var if omitted) [env var: DASHSCOPE_API_KEY]                                                                    │
│ --output-format            -o                    TEXT  Output format: table|json|yaml [default: json]                                                                                                                │
│ --help                                                 Show this message and exit.                                                                                                                                   │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```
**Ejemplo**:
```bash
dashscope rl register_functions \
  --rollout-classpath "functions.rollout.rollout2.DemoRolloutProcessor" \
  --group-reward-classpaths "functions.reward.group_reward.DemoGroupRewardProcessor" \
  --workspace-dir "./" \
  --output-format json
```

### 4.3 Probar funciones

#### 4.3.1 Pruebas remotas
**[SDK] [test_functions](test_functions.py)**

Prueba las instancias registradas con datos de muestra.

```python
def test_functions(cls, instance_id: str, type: FunctionType, input_data: Dict[str, Any], api_key: str = None): ...
```

**Parámetros**:
- `instance_id`: ID de la instancia de función
- `type`: tipo de función (ROLLOUT/REWARD/GROUP_REWARD)
- `input_data`: datos de entrada de prueba
- `api_key`: clave de API para autenticación

**Ejemplo**:
```python
from dashscope.finetune.agentic_rl import AgenticRL, FunctionType

# Probar Rollout
result = await AgenticRL.test_functions(
    instance_id=rollout_iids[0],
    functype=FunctionType.ROLLOUT,
    input_data="resouces/rollout_input.json" # ruta al archivo JSON
)

# Probar Reward
reward_input = {
    "func_type": "reward",
    "agent_output": {
        "messages": [{"role": "user", "content": "Test"}],
        "reward_score": null
    }
}
result = await AgenticRL.test_functions(
    instance_id=reward_iids[0],
    functype=FunctionType.REWARD,
    input_data=reward_input
)
```

**[CLI] test_functions**

**Uso: dashscope test_functions [OPTIONS] INSTANCE_ID**
```bash
 🧪 Test a registered Rollout/Reward function instance with custom input data.

╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    instance_id      TEXT  Target function instance ID (e.g., ro-ins-xxx or rw-ins-xxx) [required]                                                                                                                  │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *  --type           -t      TEXT  Function type: ROLLOUT or REWARD [required]                                                                                                                                        │
│ *  --input          -i      TEXT  JSON string or file path containing test payload [required]                                                                                                                        │
│    --api-key                TEXT  DashScope API Key (uses DASHSCOPE_API_KEY env var if omitted) [env var: DASHSCOPE_API_KEY]                                                                                         │
│    --output-format  -o      TEXT  Output format: table|json|yaml [default: json]                                                                                                                                     │
│    --help                         Show this message and exit.                                                                                                                                                        │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

**Ejemplo**:
```bash
dashscope rl test_functions "ro-ins-xxx" \
  --type rollout \
  --input "resources/rollout_input.json"
```

### 4.4 Flujo de trabajo de un solo paso
Registra automáticamente las funciones, sube los datos y envía el trabajo.

**[SDK] [run](submit_job.py)**
```python
async def run(
    self,
    model: Optional[str] = None,
    training_datasets: Optional[List[TrainingDataset]] = None,
    validation_datasets: Optional[List[ValidationDataset]] = None,
    functions: Optional[
        Union[List[AgenticRLFunctionComponent], AgenticRLFunctionComponent]
    ] = None,
    hyper_parameters: Optional[Dict[str, str]] = None,
    resources: Optional[Dict[str, str]] = None,
    job_name: Optional[str] = None,
    teacher_model: Optional[str] = None,
    **kwargs,
) -> FineTune: ...
```
Ejecución completa del flujo de trabajo (registro + subida + envío).

**Parámetros**:
- `model`: nombre del modelo base
- `training_datasets`: objetos de conjunto de datos de entrenamiento
- `validation_datasets`: objetos de conjunto de datos de validación
- `functions`: componentes de función
- `hyper_parameters`: hiperparámetros de entrenamiento
- `resources`: configuración de recursos de entrenamiento
- `job_name`: nombre personalizado del trabajo
- `teacher_model`: modelo Teacher; habilita OPD mientras Rollout y Reward siguen siendo opcionales

**Devuelve**: objeto de trabajo `FineTune`

**Ejemplo**:
```python
from dashscope.finetune.agentic_rl import AgenticRL, AgenticRLFunctionComponent, FunctionType, FunctionComponentModel

rl=AgenticRL()
rollout_runtime = {"cpu": 2, "memory_size": 4096, "disk_size": 20960, "concurrency": 2,
                    "env": {}, "capacity": 5}
reward_runtimes = [
    {"cpu": 2, "memory_size": 4096, "disk_size": 20960, "concurrency": 10, "env": {},
     "capacity": 8},
    {"cpu": 2, "memory_size": 4096, "disk_size": 20960, "concurrency": 5, "env": {},
     "capacity": 6}
]
functions=[
    RolloutFunctionComponent(
        type=FunctionType.ROLLOUT,
        name="rollout-1",
        fcmodel=FunctionComponentModel(
            classpath="functions.rollout.rollout_only.DemoRolloutProcessor"),
        runtime=FunctionComponentRuntime(**rollout_runtime)),
    AgenticRLFunctionComponent(
        type=FunctionType.REWARD,
        name="reward-1",
        weight=1.0,
        fcmodel=FunctionComponentModel(
            classpath="functions.reward.reward.DemoRewardProcessor"),
        runtime=FunctionComponentRuntime(**reward_runtimes[0])),
]
training_datasets=[
    TrainingDataset(
        data_source_type=DataSourceType.FILE_ID,
        file_name="./data/calc_train_min.jsonl",
    ),
]
validation_datasets=[
    ValidationDataset(
        data_source_type=DataSourceType.FILE_ID,
        file_name="./data/calc_validation_min.jsonl",
    ),
]
job = await rl.run(
    model="qwen3.5-9b",
    training_datasets=training_datasets,
    validation_datasets=validation_datasets,
    functions=functions,
    hyper_parameters={'batch_size': '128'}
)
```

**[CLI] run**

**Uso: dashscope rl run [OPTIONS]**
```bash
 🚀 Launch the complete RL tuning workflow (function registration → dataset upload → job submission)

 Execution modes:
 1. Configuration-driven: Use -c/--config to specify a YAML file
 2. Direct parameter: Provide all required arguments via CLI options

 Required parameters:
 - training_files (at least one)
 - Rollout and Reward are required for reinforcement learning, but optional for OPD.

╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --config                   -c      PATH   Path to YAML configuration file                                                                                                                                            │
│ --model                            TEXT   Base model identifier                                                                                                                                                      │
│ --teacher-model                    TEXT   Enable OPD and override the Teacher model in YAML; Rollout and Reward are optional                                                                                          │
│ --training-files                   TEXT   Paths to training dataset files                                                                                                                                            │
│ --validation-files                 TEXT   Paths to validation dataset files                                                                                                                                          │
│ --rollout-classpath                TEXT   Python import path to rollout class (module:Class)                                                                                                                         │
│ --reward-classpaths                TEXT   List for reward class path (file.py:ClassName)                                                                                                                             │
│ --group-reward-classpaths          TEXT   List for group-reward class path (file.py:ClassName)                                                                                                                       │
│ --rollout-name                     TEXT   Pre-registered Rollout entity_name                                                                                                                                         │
│ --reward-names                     TEXT   Comma-separated list of reward entity_names                                                                                                                                │
│ --group-reward-names               TEXT   Comma-separated list of group-reward entity_names                                                                                                                          │
│ --rollout-weight                   TEXT   Pre-registered Rollout entity_weight                                                                                                                                       │
│ --reward-weights                   FLOAT  Comma-separated list of reward entity_weights                                                                                                                              │
│ --group-reward-weights             FLOAT  Comma-separated list of group-reward entity_weights                                                                                                                        │
│ --reward-metric-weights            TEXT   Reward metric weights as JSON string (list of dicts)                                                                                                                       │
│ --rollout-runtime                  TEXT   Rollout runtime as JSON string                                                                                                                                             │
│ --reward-runtimes                  TEXT   Reward runtimes as JSON string                                                                                                                                             │
│ --group-reward-runtimes            TEXT   Group-reward runtimes as JSON string                                                                                                                                       │
│ --hyper-parameters                 TEXT   JSON string of hyper_parameters                                                                                                                                             │
│ --job-name                         TEXT   Custom name for the tuning job                                                                                                                                             │
│ --api-key                          TEXT   DashScope API Key (uses DASHSCOPE_API_KEY env var if omitted) [env var: DASHSCOPE_API_KEY]                                                                                 │
│ --workspace-dir                    TEXT   Workspace directory for job artifacts [default: ./]                                                                                                                        │
│ --output-format            -o      TEXT   Output format: table|json|yaml [default: table]                                                                                                                            │
│ --verbose                  -v             Enable detailed error traces                                                                                                                                               │
│ --help                                    Show this message and exit.                                                                                                                                                │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

**Ejemplo**: Ejecutar el flujo de trabajo completo (automático)
```bash
dashscope rl run \
  --config "rl-job.yaml" \
  --verbose
```

### 4.5 Gestión de trabajos

**[SDK] get**
```python
def get(cls, job_id: str, api_key: str = None, workspace: str = None, **kwargs) -> FineTune: ...
```
Obtiene información del trabajo.

**Parámetros**:
- `job_id`: ID del trabajo a consultar
- `api_key`: clave de API para autenticación
- `workspace`: identificador del espacio de trabajo

**Ejemplo**:
```python
from dashscope.finetune.agentic_rl import AgenticRL
job = AgenticRL.get("job-12345")
```

**[CLI] get**

**Uso: dashscope get [OPTIONS] JOB_ID**
```bash
 📊 Query the current status and metadata of a specific job

╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    job_id      TEXT  Target job ID [required]                                                                                                                                                                      │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --api-key                TEXT  DashScope API Key (uses DASHSCOPE_API_KEY env var if omitted) [env var: DASHSCOPE_API_KEY]                                                                                            │
│ --output-format  -o      TEXT  [default: table]                                                                                                                                                                      │
│ --help                         Show this message and exit.                                                                                                                                                           │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

**Ejemplo**:
```bash
dashscope rl get "$JOB_ID" -o json
```

**[SDK] cancel**
```python
def cancel(cls, job_id: str, api_key: str = None, workspace: str = None, **kwargs) -> FineTuneCancel: ...
```
Cancela un trabajo en ejecución.

**Parámetros**:
- `job_id`: ID del trabajo a cancelar
- `api_key`: clave de API para autenticación
- `workspace`: identificador del espacio de trabajo

**Ejemplo**:
```python
from dashscope.finetune.agentic_rl import AgenticRL
AgenticRL.cancel("job-12345")
```

**[CLI] cancel**

**Uso: dashscope cancel [OPTIONS] JOB_ID**
```bash
 🛑 Cancel a running job

╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    job_id      TEXT  Target job ID [required]                                                                                                                                                                      │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --api-key        TEXT  DashScope API Key (uses DASHSCOPE_API_KEY env var if omitted) [env var: DASHSCOPE_API_KEY]                                                                                                    │
│ --help                 Show this message and exit.                                                                                                                                                                   │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

**Ejemplo**:
```bash
dashscope rl cancel "$JOB_ID"
```

---

## 5. Referencia de la CLI

La CLI refleja la funcionalidad del SDK. Usa `dashscope rl --help` para más detalles.

### Uso: dashscope [OPTIONS] COMMAND [ARGS]...
```bash

 🚀 Agentic RL Fine-Tuning CLI

╭─ Options ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                                                                                                                                                     │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ register_functions  🧩 Register Rollout/Reward function components, returns entity_id & instance_id                                                                                                             │
│ test_functions      🧪 Test a registered Rollout/Reward function instance with custom input data.                                                                                                               │
│ upload_data         📦 Upload training/validation datasets to the platform, returns file IDs                                                                                                                    │
│ submit              📤 Submit fine-tuning job (requires pre-registered functions & uploaded datasets)                                                                                                                 │
│ run                 🚀 Launch the complete RL tuning workflow (function registration → dataset upload → job submission)                                                                                         │
│ status              📊 Query the current status and metadata of a specific job                                                                                                                                  │
│ list                📋 List historical fine-tuning jobs with pagination                                                                                                                                         │
│ cancel              🛑 Cancel a running job                                                                                                                                                                     │
│ delete              🗑️ Delete a job record (releases metadata)                                                                                                                                                  │
│ logs                📜 Fetch job execution logs (supports pagination)                                                                                                                                           │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

---

## 6. Preguntas frecuentes y solución de problemas

**P: El registro de funciones falla.**
*   **Comprueba**: ¿es correcto el classpath (`module.path:ClassName`)?
*   **Comprueba**: ¿existe `requirements.txt` en la raíz del espacio de trabajo?
*   **Comprueba**: ¿están todas las dependencias listadas en `requirements.txt`?

**P: El envío del trabajo falla.**
*   **Comprueba**: ¿son válidos los Entity IDs y File IDs?
*   **Comprueba**: ¿está disponible el modelo base en tu región?
*   **Comprueba**: ¿coincide la longitud de la lista `reward_runtimes` con la de `reward_ids`?

**P: ¿Cómo optimizar el rendimiento?**
*   Usa `async def process` para tareas limitadas por E/S.
*   Aumenta `concurrency` en la configuración de runtime si la CPU/memoria lo permiten.
*   Mantén acotados los payloads de observabilidad (evita capturar entradas/salidas excesivas) para reducir la sobrecarga.

**P: ¿Dónde están mis trazas?**
*   Las trazas se envían a **ARMS** después de completar la autorización de ARMS en la Consola de Bailian. Asegúrate de que tu `requirements.txt` incluya las dependencias de observabilidad y de que estés usando las API de observabilidad (`observe_processor`, `trace_client`, `trace_tool`, etc.).
