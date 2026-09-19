# 模型微调与部署全流程

> [English](fine-tuning.md) | **中文** | [日本語](fine-tuning_ja.md) | [Español](fine-tuning_es.md) | [한국어](fine-tuning_ko.md)

本指南介绍使用 `FineTunes` 微调模型并通过 `Deployments` 部署上线的完整流程。快速开始版本（上传 → 创建 → 等待）请参见[主 README 中的“模型微调”一节](../../README_zh.md#模型微调fine-tuning)。

## 训练文件格式

训练文件为 JSONL 格式——每行一个 JSON 对象。每行使用 `text` 字段承载完整对话内容，并以 `Human:`/`Assistant:` 标记对话轮次：

```jsonl
{"text": "\n\nHuman: I need a picture of someone crying.\n\nAssistant: I'm sorry, but as an AI language model, I do not have the ability to display images."}
```

使用 `Files.upload` 上传（`purpose="fine_tune"` 为默认值）：

```python
from dashscope import Files

file_response = Files.upload(file_path="train.jsonl", purpose="fine_tune")
file_id = file_response.output["uploaded_files"][0]["file_id"]
```

## 创建并监控任务

`FineTunes.call` 创建一个任务；`mode` 用于选择训练方式（`sft` 或 `efficient_sft`）：

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

使用 `FineTunes.get` 查询单个任务的状态：

```python
from dashscope import FineTunes

status = FineTunes.get(job_id="ft-202403261451-d26b")
print(status.output.status)  # 例如 PENDING、RUNNING、SUCCEEDED、FAILED、CANCELED
```

分页列出所有任务：

```python
from dashscope import FineTunes

jobs = FineTunes.list(page_no=1, page_size=10)
for job in jobs.output.jobs:
    print(job.job_id, job.status)
```

如果不想轮询，也可以流式获取正在运行任务的实时事件：

```python
from dashscope import FineTunes

for event in FineTunes.stream_events(job_id="ft-202403261451-d26b"):
    print(event.output)
```

阻塞等待任务完成（每 30 秒轮询一次）——与 README 快速开始中使用的辅助方法相同：

```python
from dashscope import FineTunes

result = FineTunes.wait(job_id="ft-202403261451-d26b")
print(result.output.status)
```

## 取消与删除任务

```python
from dashscope import FineTunes

FineTunes.cancel(job_id="ft-202403261451-d26b")
FineTunes.delete(job_id="ft-202403261451-d26b")
```

## 部署微调后的模型

部署已完成任务产出的模型（上文 `wait()` 调用返回结果中的 `result.output.finetuned_output` 即为训练得到的模型 ID）：

```python
from dashscope import Deployments

deployment = Deployments.call(model=result.output.finetuned_output, capacity=1)
deployed_model = deployment.output.deployed_model
print(deployed_model, deployment.output.status)
```

查看部署状态、列出所有部署、调整容量或删除部署：

```python
from dashscope import Deployments

status = Deployments.get(deployed_model)
print(status.output.status)  # 例如 PENDING、RUNNING

deployments = Deployments.list(page_no=1, page_size=10)
for d in deployments.output.deployments:
    print(d.deployed_model, d.status)

Deployments.scale(deployed_model, capacity=2)

Deployments.delete(deployed_model)
```

部署状态变为 `RUNNING` 后，即可像调用普通模型一样调用它：

```python
from dashscope import Generation

response = Generation.call(model=deployed_model, messages=[{"role": "user", "content": "Hi"}])
print(response.output.choices[0].message.content)
```

## Agentic RL 微调

关于基于自定义 rollout/reward 函数的 Agentic RL 微调（YAML 驱动的训练任务、链路追踪/可观测性），请参见专门的指南 [`dashscope/finetune/reinforcement/examples/workspace/README.md`](../../dashscope/finetune/reinforcement/examples/workspace/README.md)（快速开始）和 [`UserGuide.md`](../../dashscope/finetune/reinforcement/examples/workspace/UserGuide.md)（完整参考）。
