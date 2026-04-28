#!/usr/bin/env bash
#****************************************************************#
# ScriptName: run_fc.sh
# Author: @alibaba-inc.com
# Create Date: 2026-03-04 17:22
# Modify Author: @alibaba-inc.com
# Modify Date: 2026-03-25 14:27
# Function:
#***************************************************************#
# run workflow
# output:                                                                           Result
#┏━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
#┃ Key         ┃ Value                                                                                                                                                          ┃
#┡━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
#│ output      │ {'job_id': 'ft-202604061043-b5cd-poc', 'job_name': 'agentic-rl-job-e251feaf', 'status': 'PENDING', 'finetuned_output': 'qwen3-32b-ft-202604061043-b5cd-poc',   │
#│             │ 'model': 'qwen3-32b', 'base_model': 'qwen3-32b', 'training_file_ids': ['d90e7f73-9bb9-47cf-b50d-c6db310cd005'], 'validation_file_ids':                         │
#│             │ ['04e08c6a-656e-45c2-97c6-6f52f1112c49'], 'hyper_parameters': {'batch_size': '128', 'learning_rate': '1e-4', 'n_epochs': 10}, 'training_type':                 │
#│             │ 'reinforcement', 'create_time': '2026-04-06 10:43:05', 'workspace_id': 'llm-5rwyknsoxp4y7h5u', 'user_identity': '1654290265984853', 'modifier':                │
#│             │ '1654290265984853', 'creator': '1654290265984853', 'group': 'llm', 'model_name': 'rl-job-e251feaf', 'max_output_cnt': 2, 'dynamic_metric': True,       │
#│             │ 'end_time': None, 'usage': None}                                                                                                                               │
#│ status_code │ 200                                                                                                                                                            │
#│ request_id  │ dc7eb83d-1354-9a37-a80d-89ec77c60111                                                                                                                           │
#│ code        │ None                                                                                                                                                           │
#│ message     │                                                                                                                                                                │
#│ usage       │ None                                                                                                                                                           │
#└─────────────┴────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
dashscope rl run \
  --job-name "test-0428-4" \
  --model "qwen3-4b-instruct-2507" \
  --rollout-classpath "functions.rollout.demo_rollout.CalcXRolloutProcessor" \
  --reward-classpaths "functions.reward.demo_reward.DemoRewardProcessor" \
  --rollout-name "rollout-1" \
  --rollout-runtime '{"cpu": 2, "memory_size": 4096, "disk_size": 512, "concurrency": 30,
                           "env": {}, "capacity": 30, "min_capacity": 30, "max_capacity": 60,
                           "memory_scale_threshold": 0.6,"concurrency_scale_threshold": 0.6}' \
  --reward-names "rewards-1" \
  --reward-runtimes '{"cpu": 2, "memory_size": 4096, "disk_size": 512, "concurrency": 30,
                           "env": {}, "capacity": 30, "min_capacity": 30, "max_capacity": 60,
                           "memory_scale_threshold": 0.6,"concurrency_scale_threshold": 0.6}' \
  --training-files "./data/calc_train.jsonl" \
  --validation-files "./data/calc_validation.jsonl" \
  --hyper-parameters '{"n_epochs": 1, "learning_rate": 1e-6, "max_prompt_length": 2048, "batch_size": 128}' \
  --verbose

# Submit and wait in non-interactive mode
# output:
#{
#  "job_id": "ft-202604061138-b031-poc",
#  "status": "PENDING",
#  "message": ""
#}
dashscope rl run -c config.yaml -o json

JOB_ID="ft-202604281405-6827-poc"

# Check status
# output:
#{
#  "job_id": "ft-202604061134-175c-poc",
#  "status": "RUNNING",
#  "created_at": "N/A"
#}
dashscope rl get "$JOB_ID" -o json

#✅ Job ft-202604081026-c188-poc canceled successfully
#dashscope rl cancel "$JOB_ID"

# Fetch paginated logs
# output:
#┏━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━┓
#┃ Key    ┃ Value                    ┃
#┡━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━┩
#│ job_id │ ft-202604061011-5a61-poc │
#│ logs   │                          │
#└────────┴──────────────────────────┘
dashscope rl logs "$JOB_ID" --offset 1 --lines 50
