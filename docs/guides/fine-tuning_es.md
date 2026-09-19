# Ciclo de Vida de Fine-tuning y Despliegue

> [English](fine-tuning.md) | [中文](fine-tuning_zh.md) | [日本語](fine-tuning_ja.md) | **Español** | [한국어](fine-tuning_ko.md)

Esta guía cubre el ciclo de vida completo de hacer fine-tuning a un modelo con `FineTunes` y servirlo con `Deployments`. Para la versión de inicio rápido (subir → crear → esperar), consulte la ["sección de Fine-tuning en el README principal"](../../README_es.md#ajuste-fino-fine-tuning).

## Formato del archivo de entrenamiento

Los archivos de entrenamiento son JSONL — un objeto JSON por línea. Cada línea usa un campo `text` que contiene la conversación completa, con marcadores de turno `Human:`/`Assistant:`:

```jsonl
{"text": "\n\nHuman: I need a picture of someone crying.\n\nAssistant: I'm sorry, but as an AI language model, I do not have the ability to display images."}
```

Súbalo con `Files.upload` (`purpose="fine_tune"` es el valor por defecto):

```python
from dashscope import Files

file_response = Files.upload(file_path="train.jsonl", purpose="fine_tune")
file_id = file_response.output["uploaded_files"][0]["file_id"]
```

## Creación y monitoreo de un job

`FineTunes.call` crea un job; `mode` selecciona el método de entrenamiento (`sft` o `efficient_sft`):

```python
from dashscope import FineTunes

job = FineTunes.call(
    model="qwen-turbo",
    training_file_ids=file_id,
    mode="sft",
    hyper_parameters={"n_epochs": 10, "learning_rate": 0.001},
)
print(job.output.job_id, job.output.status)
```

Compruebe el estado de un job individual con `FineTunes.get`:

```python
from dashscope import FineTunes

status = FineTunes.get(job_id="ft-202403261451-d26b")
print(status.output.status)  # p. ej. PENDING, RUNNING, SUCCEEDED, FAILED, CANCELED
```

Liste todos los jobs (paginado):

```python
from dashscope import FineTunes

jobs = FineTunes.list(page_no=1, page_size=10)
for job in jobs.output.jobs:
    print(job.job_id, job.status)
```

Transmita eventos en vivo de un job en ejecución en lugar de sondear:

```python
from dashscope import FineTunes

for event in FineTunes.stream_events(job_id="ft-202403261451-d26b"):
    print(event.output)
```

Bloquee hasta que un job termine (sondea cada 30s) — el mismo helper usado en el inicio rápido del README:

```python
from dashscope import FineTunes

result = FineTunes.wait(job_id="ft-202403261451-d26b")
print(result.output.status)
```

## Cancelar y eliminar jobs

```python
from dashscope import FineTunes

FineTunes.cancel(job_id="ft-202403261451-d26b")
FineTunes.delete(job_id="ft-202403261451-d26b")
```

## Desplegar un modelo con fine-tuning

Despliegue el modelo producido por un job completado (`result.output.finetuned_output` de la llamada `wait()` anterior contiene el id del modelo entrenado):

```python
from dashscope import Deployments

deployment = Deployments.call(model=result.output.finetuned_output, capacity=1)
deployed_model = deployment.output.deployed_model
print(deployed_model, deployment.output.status)
```

Compruebe el estado de un despliegue, liste todos los despliegues, escale la capacidad o elimínelo:

```python
from dashscope import Deployments

status = Deployments.get(deployed_model)
print(status.output.status)  # p. ej. PENDING, RUNNING

deployments = Deployments.list(page_no=1, page_size=10)
for d in deployments.output.deployments:
    print(d.deployed_model, d.status)

Deployments.scale(deployed_model, capacity=2)

Deployments.delete(deployed_model)
```

Una vez que el estado de un despliegue sea `RUNNING`, llámelo como a cualquier otro modelo:

```python
from dashscope import Generation

response = Generation.call(model=deployed_model, messages=[{"role": "user", "content": "Hi"}])
print(response.output.choices[0].message.content)
```

## Fine-tuning de Agentic RL

Para fine-tuning de Agentic RL basado en funciones personalizadas de rollout/reward (jobs de entrenamiento dirigidos por YAML, tracing/observabilidad), consulte la guía dedicada en [`dashscope/finetune/reinforcement/examples/workspace/README.md`](../../dashscope/finetune/reinforcement/examples/workspace/README.md) (inicio rápido) y [`UserGuide.md`](../../dashscope/finetune/reinforcement/examples/workspace/UserGuide.md) (referencia completa).
