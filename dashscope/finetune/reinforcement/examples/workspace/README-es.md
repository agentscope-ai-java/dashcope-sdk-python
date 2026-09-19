# Guía del SDK/CLI de Agentic RL [[English]](./README.md) [[中文]](./README-zh.md) [[日本語]](./README-ja.md) [[한국어]](./README-ko.md)

## 1. Instalar el SDK

```bash
pip install dashscope>=1.25.19
```

## 2. Configuración del entorno

### 2.1 Configurar variables de entorno

```bash
# Obligatorio: clave de API (también se puede inicializar en el código: AgenticRL(api_key="for your api key") )
export DASHSCOPE_API_KEY="your_api_key_here"

# Opcional: nivel de log info/debug/warning/critical (por defecto info)
export LOG_LEVEL="info"
```

### 2.2 Configurar el archivo de dependencias

> Nota: `requirements.txt` se utiliza para el entorno remoto de Function Compute (Python >= 3.10). Para depuración local, asegúrate de usar Python 3.10+. El propio SDK `dashscope` admite Python 3.8+.

Crea un archivo `requirements.txt` con las siguientes dependencias principales:

```requirements.txt
# Base (obligatorio)
dashscope>=1.25.19

# Dependencias del framework
fastapi==0.136.0
uvicorn==0.45.0
# ...

# Dependencias de las funciones de trayectoria
langchain-core==1.3.0
langchain-mcp-adapters==0.2.2
langchain-openai==1.2.0
# ...

# Agrega otras dependencias personalizadas...
```

## 3. Desarrollo de funciones y preparación de datos

### 3.1 Crear componentes de función

Desarrolla las funciones dentro del directorio `functions`:

- **Plantillas de la función Reward**:
    - `functions/reward/reward.py` - Implementación básica
    - `functions/reward/reward_decorator.py` - Implementación con decorador
- **Plantillas de la función Rollout**:
    - `functions/rollout/rollout.py` - Implementación básica

> Nota: el directorio `functions/` debe contener un archivo `__init__.py`

Los componentes de función necesarios dependen de la configuración de entrenamiento elegida:

| Configuración | Modo | Rollout personalizado | Reward personalizado |
|---|---|---:|---:|
| `rl-job.yaml` | Aprendizaje por refuerzo regular | Obligatorio | Al menos uno |
| `opd-job.yaml` sin bloques de función | Solo Teacher | No | No |
| `opd-job.yaml` solo con Reward | Teacher + Reward | No | Sí |
| `opd-job.yaml` solo con Rollout | Teacher + Rollout | Sí | No |
| `opd-job.yaml` con ambos bloques | Teacher + Rollout + Reward | Sí | Sí |

### 3.2 Preparar los datos de entrenamiento

Agrega los archivos del conjunto de datos en el directorio `data`:

- `data/calc_training_min.jsonl` - Conjunto de datos de entrenamiento (formato JSONL)
- `data/calc_validation_min.jsonl` - Conjunto de datos de validación (formato JSONL)

## 4. Ejecutar tareas con el SDK

### 4.1 Ejecución de funciones (registrar + probar)

El entrenamiento por refuerzo regular requiere un Rollout personalizado y al
menos un Reward. Rollout y Reward son opcionales para OPD.

```bash
python test_functions.py
```

### 4.2 Ejecución del flujo de trabajo (configuración YAML + gestión del ciclo de vida)

El entrenamiento por refuerzo regular y OPD usan el mismo flujo de trabajo del
SDK. Selecciona el YAML correspondiente:

```python
from dashscope.finetune.agentic_rl import AgenticRL

client = AgenticRL()
# Usa rl-job.yaml para refuerzo regular u opd-job.yaml para OPD
client.init(config_path="rl-job.yaml")
result = await client.run()
```

`opd-job.yaml` conserva ambos bloques de función por defecto, representando
Teacher + Rollout + Reward. Elimina el bloque Reward para Teacher + Rollout,
elimina el bloque Rollout para Teacher + Reward, o elimina ambos para
solo Teacher.

```bash
# submit_job.py usa por defecto el rl-job.yaml de refuerzo regular
python submit_job.py
```

## 5. Ejecutar tareas con la CLI
Código de ejemplo: cli.sh

`cli.sh` muestra el flujo de trabajo de refuerzo regular. Para OPD, omite el
registro y las pruebas de los bloques de función eliminados de `opd-job.yaml`;
el envío de datos, `rl run` y los comandos del ciclo de vida de la tarea
permanecen sin cambios.

La CLI utiliza los mismos archivos YAML que el SDK:

```bash
# Refuerzo regular
dashscope rl run -c rl-job.yaml

# OPD
dashscope rl run -c opd-job.yaml

# Sobrescribir el Teacher configurado en opd-job.yaml
dashscope rl run -c opd-job.yaml \
  --teacher-model qwen3.5-397b-a17b
```

```bash
dashscope rl --help  # Ver la ayuda completa de los comandos

 Usage: dashscope [OPTIONS] COMMAND [ARGS]...

 🚀 Agentic RL Fine-Tuning CLI

╭─ Options ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                                                                                                                                                     │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ register_functions  🧩 Register Rollout/Reward function components, returns entity_id & instance_id                                                                                                             │
│ test_functions      🧪 Test a registered Rollout/Reward function instance with custom input data.                                                                                                               │
│ upload_data         📦 Upload training/validation datasets to the platform, returns file IDs                                                                                                                    │
│ run                 🚀 Launch the complete RL tuning workflow (function registration → dataset upload → job submission)                                                                                         │
│ get                 📊 Query the current status and metadata of a specific job                                                                                                                                  │
│ list                📋 List historical fine-tuning jobs with pagination                                                                                                                                         │
│ cancel              🛑 Cancel a running job                                                                                                                                                                     │
│ delete              🗑️ Delete a job record (releases metadata)                                                                                                                                                  │
│ logs                📜 Fetch job execution logs (supports pagination)                                                                                                                                           │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

## Consejos de buenas prácticas

1. **Desarrollo y pruebas**: usa el comando `test_functions` para verificar la lógica de las funciones antes de enviarlas
2. **Desarrollo incremental**: simplemente vuelve a registrar las funciones después de modificarlas, sin necesidad de reconstruir todo el entorno
3. **Solución de problemas con logs**: configura `LOG_LEVEL=debug` para obtener información de depuración detallada
4. **Gestión de recursos**: usa el comando `delete` para liberar recursos después de completar la tarea

> Nota: todas las rutas y parámetros deben ajustarse según el proyecto real; los scripts de ejemplo se encuentran en el
> directorio `workspace/` del proyecto
>
> Nota: todos los archivos del directorio `workspace/` del proyecto se empaquetarán y subirán a la nube para el
> cómputo en línea; ten en cuenta la seguridad de los datos
>
> Nota: para configurar los subdirectorios y archivos excluidos de la subida en el directorio `workspace/` del
> proyecto, consulta la variable de entorno: `FC_ZIP_EXCLUDE_PATTERNS`
>
> Nota: el límite de tamaño total para empaquetar y subir todos los archivos del directorio `workspace/` del proyecto
> es de 200M; esto se puede modificar mediante la variable de entorno `FC_OSS_FILE_SIZE_WARNING`
>
> Nota: el tamaño máximo por defecto para un único archivo de conjunto de datos (por ejemplo, JSONL de
> entrenamiento/validación) es de 1G; esto se puede modificar mediante la variable de entorno `DATASETS_FILE_SIZE_WARNING`
>
> Nota: si deseas usar un paquete whl de dashscope compilado localmente (generado mediante el script scripts/build.sh), puedes configurar:
> export FC_PYPI_LIB="dashscope-1.25.19-py3-none-any.whl"
> y colocarlo en el directorio workspace/workspace/ bajo la raíz del proyecto. También elimina la dependencia de dashscope de `requirements.txt`.
