# 파인튜닝 및 배포 라이프사이클

> [English](fine-tuning.md) | [中文](fine-tuning_zh.md) | [日本語](fine-tuning_ja.md) | [Español](fine-tuning_es.md) | **한국어**

이 가이드는 `FineTunes`로 모델을 파인튜닝하고 `Deployments`로 서비스하는 전체
라이프사이클을 다룹니다. 빠른 시작 버전(업로드 → 생성 → 대기)은 [메인 README의
"파인튜닝" 섹션](../../README_ko.md#파인튜닝fine-tuning)을 참고하세요.

## 학습 파일 형식

학습 파일은 JSONL — 한 줄에 하나의 JSON 객체입니다. 각 줄은 `Human:`/`Assistant:`
턴 마커가 포함된 전체 대화를 담은 `text` 필드를 사용합니다:

```jsonl
{"text": "\n\nHuman: I need a picture of someone crying.\n\nAssistant: I'm sorry, but as an AI language model, I do not have the ability to display images."}
```

`Files.upload`로 업로드합니다(`purpose="fine_tune"`이 기본값입니다):

```python
from dashscope import Files

file_response = Files.upload(file_path="train.jsonl", purpose="fine_tune")
file_id = file_response.output["uploaded_files"][0]["file_id"]
```

## 작업 생성 및 모니터링

`FineTunes.call`은 작업을 생성합니다; `mode`는 학습 방식(`sft` 또는
`efficient_sft`)을 선택합니다:

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

`FineTunes.get`으로 단일 작업의 상태를 확인합니다:

```python
from dashscope import FineTunes

status = FineTunes.get(job_id="ft-202403261451-d26b")
print(status.output.status)  # 예: PENDING, RUNNING, SUCCEEDED, FAILED, CANCELED
```

모든 작업을 나열합니다(페이지네이션):

```python
from dashscope import FineTunes

jobs = FineTunes.list(page_no=1, page_size=10)
for job in jobs.output.jobs:
    print(job.job_id, job.status)
```

폴링 대신 실행 중인 작업의 실시간 이벤트를 스트리밍합니다:

```python
from dashscope import FineTunes

for event in FineTunes.stream_events(job_id="ft-202403261451-d26b"):
    print(event.output)
```

작업이 완료될 때까지 블로킹합니다(30초마다 폴링) — README 빠른 시작에서
사용한 것과 동일한 헬퍼입니다:

```python
from dashscope import FineTunes

result = FineTunes.wait(job_id="ft-202403261451-d26b")
print(result.output.status)
```

## 작업 취소 및 삭제

```python
from dashscope import FineTunes

FineTunes.cancel(job_id="ft-202403261451-d26b")
FineTunes.delete(job_id="ft-202403261451-d26b")
```

## 파인튜닝된 모델 배포

완료된 작업이 생성한 모델을 배포합니다(위 `wait()` 호출의
`result.output.finetuned_output`에 학습된 모델 ID가 들어 있습니다):

```python
from dashscope import Deployments

deployment = Deployments.call(model=result.output.finetuned_output, capacity=1)
deployed_model = deployment.output.deployed_model
print(deployed_model, deployment.output.status)
```

배포 상태 확인, 전체 배포 목록 조회, 용량 확장, 삭제:

```python
from dashscope import Deployments

status = Deployments.get(deployed_model)
print(status.output.status)  # 예: PENDING, RUNNING

deployments = Deployments.list(page_no=1, page_size=10)
for d in deployments.output.deployments:
    print(d.deployed_model, d.status)

Deployments.scale(deployed_model, capacity=2)

Deployments.delete(deployed_model)
```

배포 상태가 `RUNNING`이 되면 다른 모델과 동일하게 호출할 수 있습니다:

```python
from dashscope import Generation

response = Generation.call(model=deployed_model, messages=[{"role": "user", "content": "Hi"}])
print(response.output.choices[0].message.content)
```

## Agentic RL 파인튜닝

커스텀 rollout/reward 함수 기반 Agentic RL 파인튜닝(YAML 기반 학습 작업,
트레이싱/관측성)에 대해서는 [`dashscope/finetune/reinforcement/examples/workspace/README.md`](../../dashscope/finetune/reinforcement/examples/workspace/README.md)(빠른 시작)와
[`UserGuide.md`](../../dashscope/finetune/reinforcement/examples/workspace/UserGuide.md)(전체 참고 자료)에서
전용 가이드를 참고하세요.
