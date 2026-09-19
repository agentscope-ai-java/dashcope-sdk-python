# ファインチューニングとデプロイのライフサイクル

> [English](fine-tuning.md) | [中文](fine-tuning_zh.md) | **日本語** | [Español](fine-tuning_es.md) | [한국어](fine-tuning_ko.md)

このガイドでは、`FineTunes` を使ったモデルのファインチューニングと、`Deployments` を使ったデプロイの全ライフサイクルを説明します。クイックスタート版（アップロード → 作成 → 待機）については、[メイン README の「ファインチューニング」セクション](../../README_ja.md#ファインチューニング)を参照してください。

## 学習用ファイルの形式

学習用ファイルは JSONL 形式です——1 行につき 1 つの JSON オブジェクトを記述します。各行は完全な会話を格納する `text` フィールドを持ち、`Human:`/`Assistant:` のターンマーカーを使用します：

```jsonl
{"text": "\n\nHuman: I need a picture of someone crying.\n\nAssistant: I'm sorry, but as an AI language model, I do not have the ability to display images."}
```

`Files.upload` でアップロードします（`purpose="fine_tune"` がデフォルトです）：

```python
from dashscope import Files

file_response = Files.upload(file_path="train.jsonl", purpose="fine_tune")
file_id = file_response.output["uploaded_files"][0]["file_id"]
```

## ジョブの作成と監視

`FineTunes.call` はジョブを作成します。`mode` で学習方式（`sft` または `efficient_sft`）を選択します：

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

`FineTunes.get` で単一ジョブのステータスを確認します：

```python
from dashscope import FineTunes

status = FineTunes.get(job_id="ft-202403261451-d26b")
print(status.output.status)  # 例：PENDING、RUNNING、SUCCEEDED、FAILED、CANCELED
```

すべてのジョブをページ分割で一覧表示します：

```python
from dashscope import FineTunes

jobs = FineTunes.list(page_no=1, page_size=10)
for job in jobs.output.jobs:
    print(job.job_id, job.status)
```

ポーリングの代わりに、実行中のジョブからライブイベントをストリーミングで受け取ることもできます：

```python
from dashscope import FineTunes

for event in FineTunes.stream_events(job_id="ft-202403261451-d26b"):
    print(event.output)
```

ジョブが完了するまでブロックして待機します（30 秒ごとにポーリング）——README のクイックスタートで使用されているものと同じヘルパーです：

```python
from dashscope import FineTunes

result = FineTunes.wait(job_id="ft-202403261451-d26b")
print(result.output.status)
```

## ジョブのキャンセルと削除

```python
from dashscope import FineTunes

FineTunes.cancel(job_id="ft-202403261451-d26b")
FineTunes.delete(job_id="ft-202403261451-d26b")
```

## ファインチューニング済みモデルのデプロイ

完了したジョブが生成したモデルをデプロイします（上記の `wait()` 呼び出しの結果に含まれる `result.output.finetuned_output` が学習済みモデルの ID です）：

```python
from dashscope import Deployments

deployment = Deployments.call(model=result.output.finetuned_output, capacity=1)
deployed_model = deployment.output.deployed_model
print(deployed_model, deployment.output.status)
```

デプロイのステータス確認、一覧表示、容量のスケーリング、削除は以下の通りです：

```python
from dashscope import Deployments

status = Deployments.get(deployed_model)
print(status.output.status)  # 例：PENDING、RUNNING

deployments = Deployments.list(page_no=1, page_size=10)
for d in deployments.output.deployments:
    print(d.deployed_model, d.status)

Deployments.scale(deployed_model, capacity=2)

Deployments.delete(deployed_model)
```

デプロイのステータスが `RUNNING` になったら、通常のモデルと同じように呼び出せます：

```python
from dashscope import Generation

response = Generation.call(model=deployed_model, messages=[{"role": "user", "content": "Hi"}])
print(response.output.choices[0].message.content)
```

## Agentic RL ファインチューニング

カスタムの rollout/reward 関数を使用する Agentic RL ファインチューニング（YAML 駆動のトレーニングジョブ、トレーシング/可観測性）については、専用ガイドの [`dashscope/finetune/reinforcement/examples/workspace/README.md`](../../dashscope/finetune/reinforcement/examples/workspace/README.md)（クイックスタート）と [`UserGuide.md`](../../dashscope/finetune/reinforcement/examples/workspace/UserGuide.md)（完全なリファレンス）を参照してください。
