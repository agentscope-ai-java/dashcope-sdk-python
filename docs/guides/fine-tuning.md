# Fine-tuning & Deployment Lifecycle

> **English** | [中文](fine-tuning_zh.md) | [日本語](fine-tuning_ja.md)

This guide covers the full lifecycle of fine-tuning a model with `FineTunes` and serving it with `Deployments`. For the quick-start version (upload → create → wait), see the ["Fine-tuning" section in the main README](../../README.md#fine-tuning).

## Training File Format

Training files are JSONL — one JSON object per line. Each line uses a `text` field containing the full conversation, with `Human:`/`Assistant:` turn markers:

```jsonl
{"text": "\n\nHuman: I need a picture of someone crying.\n\nAssistant: I'm sorry, but as an AI language model, I do not have the ability to display images."}
```

Upload it with `Files.upload` (`purpose="fine_tune"` is the default):

```python
from dashscope import Files

file_response = Files.upload(file_path="train.jsonl", purpose="fine_tune")
file_id = file_response.output["uploaded_files"][0]["file_id"]
```

## Creating and Monitoring a Job

`FineTunes.call` creates a job; `mode` selects the training method (`sft` or `efficient_sft`):

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

Check the status of a single job with `FineTunes.get`:

```python
from dashscope import FineTunes

status = FineTunes.get(job_id="ft-202403261451-d26b")
print(status.output.status)  # e.g. PENDING, RUNNING, SUCCEEDED, FAILED, CANCELED
```

List all jobs (paginated):

```python
from dashscope import FineTunes

jobs = FineTunes.list(page_no=1, page_size=10)
for job in jobs.output.jobs:
    print(job.job_id, job.status)
```

Stream live events from a running job instead of polling:

```python
from dashscope import FineTunes

for event in FineTunes.stream_events(job_id="ft-202403261451-d26b"):
    print(event.output)
```

Block until a job finishes (polls every 30s) — the same helper used in the README quick-start:

```python
from dashscope import FineTunes

result = FineTunes.wait(job_id="ft-202403261451-d26b")
print(result.output.status)
```

## Canceling and Deleting Jobs

```python
from dashscope import FineTunes

FineTunes.cancel(job_id="ft-202403261451-d26b")
FineTunes.delete(job_id="ft-202403261451-d26b")
```

## Deploying a Fine-tuned Model

Deploy the model produced by a completed job (`result.output.finetuned_output` from the `wait()` call above holds the trained model id):

```python
from dashscope import Deployments

deployment = Deployments.call(model=result.output.finetuned_output, capacity=1)
deployed_model = deployment.output.deployed_model
print(deployed_model, deployment.output.status)
```

Check a deployment's status, list all deployments, scale capacity, or delete it:

```python
from dashscope import Deployments

status = Deployments.get(deployed_model)
print(status.output.status)  # e.g. PENDING, RUNNING

deployments = Deployments.list(page_no=1, page_size=10)
for d in deployments.output.deployments:
    print(d.deployed_model, d.status)

Deployments.scale(deployed_model, capacity=2)

Deployments.delete(deployed_model)
```

Once a deployment's status is `RUNNING`, call it like any other model:

```python
from dashscope import Generation

response = Generation.call(model=deployed_model, messages=[{"role": "user", "content": "Hi"}])
print(response.output.choices[0].message.content)
```

## Agentic RL Fine-tuning

For custom rollout/reward-function-driven Agentic RL fine-tuning (YAML-driven training jobs, tracing/observability), see the dedicated guide in [`dashscope/finetune/reinforcement/examples/workspace/README.md`](../../dashscope/finetune/reinforcement/examples/workspace/README.md) (quick start) and [`UserGuide.md`](../../dashscope/finetune/reinforcement/examples/workspace/UserGuide.md) (full reference).
