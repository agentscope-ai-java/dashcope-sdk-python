#!/usr/bin/env bash
#****************************************************************#
# ScriptName: run_fc.sh
# Author: @alibaba-inc.com
# Create Date: 2026-03-04 17:22
# Modify Author: @alibaba-inc.com
# Modify Date: 2026-03-25 14:27
# Function:
#***************************************************************#
# Upload dataset
# output:
#{
#  "uploaded_training_ids": [
#    "531ab326-07d1-4cef-bc7f-afd34b941208"
#  ],
#  "uploaded_validation_ids": []
#}
dashscope rl upload_data --training-files "./data/training.jsonl" -o json
TRAIN_ID="13822545-4da6-4e62-809a-1e7b26d1b491"

# Submit job
# output:
#┏━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━┓
#┃ Key     ┃ Value                    ┃
#┡━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━┩
#│ job_id  │ ft-202604061134-eb72-poc │
#│ status  │ PENDING                  │
#│ message │                          │
#└─────────┴──────────────────────────┘
ROLLOUT_ENTITY_ID="ro-23891b34-8eba-4f03-aaff-3107c60a075a"
REWARD_ENTITY_ID="rw-21859d66-fab8-46d1-92ec-f878056707b0"
REWARD_ENTITY_ID2="rw-71bd64cb-3231-41a4-a33a-193b85e263c6"
GROUP_REWARD_ENTITY_ID="grw-40f632b5-feda-4905-b9b2-559539811255"
dashscope rl submit \
  --model "qwen3-32b" \
  --rollout-id "$ROLLOUT_ENTITY_ID" \
  --rollout-name "rollout-1" \
  --reward-ids "$REWARD_ENTITY_ID" \
  --reward-ids "$REWARD_ENTITY_ID2" \
  --reward-names "reward-1" \
  --reward-names "reward-2" \
  --training-file-ids "$TRAIN_ID" \
  --reward-metric-weights '{}' \
  --reward-metric-weights '{"toxicity": 0.7, "refusal": 0.3}' \
  --hyper-parameters '{"batch_size": "256"}'

# output:
#┏━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━┓
#┃ Key     ┃ Value                    ┃
#┡━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━┩
#│ job_id  │ ft-202604061134-175c-poc │
#│ status  │ PENDING                  │
#│ message │                          │
#└─────────┴──────────────────────────┘
dashscope rl submit \
  --model "qwen3-32b" \
  --rollout-id "$ROLLOUT_ENTITY_ID" \
  --rollout-name "rollout-1" \
  --group-reward-ids "$GROUP_REWARD_ENTITY_ID" \
  --rollout-runtime '{"layer_code": "layer_ce4a35f318ae44559b944e8491ddc074", "cpu": 2, "memory_size": 4096, "disk_size": 10240, "concurrency": 10, "env": {}, "capacity": 8}' \
  --group-reward-runtimes '[{"cpu": 2, "memory_size": 4096, "disk_size": 10240, "concurrency": 10}]' \
  --group-reward-names "group-reward-1" \
  --training-file-ids "$TRAIN_ID" \
  --hyper-parameters '{"batch_size": "256"}'

JOB_ID="ft-202604231812-4749-poc"

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

# Result
#┏━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
#┃ Key       ┃ Value                                                                      ┃
#┡━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
#│ jobs      │ [                                                                          │
#│           │   {                                                                        │
#│           │     "job_id": "ft-202604221545-f777-poc",                                  │
#│           │     "job_name": "agentic-rl-1b9b480c",                                     │
#│           │     "status": "RUNNING",                                                   │
#│           │     "finetuned_output": "qwen3-4b-instruct-2507-ft-202604221545-f777-poc", │
#│           │     "model": "qwen3-4b-instruct-2507",                                     │
#│           │     "base_model": "qwen3-4b-instruct-2507",                                │
#│           │     "training_file_ids": [                                                 │
#│           │       "77eb325b-fc38-42d5-a0f9-65b72f3fad13"                               │
#│           │     ],                                                                     │
#│           │     "validation_file_ids": [                                               │
#│           │       "4963037d-9c18-4b1d-ac12-5afc7d0586f2"                               │
#│           │     ],                                                                     │
#│           │     "training_datasets": [],                                               │
#│           │     "validation_datasets": [],                                             │
#│           │     "hyper_parameters": {                                                  │
#│           │       "n_epochs": 5,                                                       │
#│           │       "learning_rate": 1e-06,                                              │
#│           │       "max_prompt_length": 1024,                                           │
#│           │       "batch_size": 128                                                    │
#│           │     },                                                                     │
#│           │     "training_type": "reinforcement",                                      │
#│           │     "create_time": "2026-04-22 15:45:46",                                  │
#│           │     "workspace_id": "llm-5rwyknsoxp4y7h5u",                                │
#│           │     "user_identity": "1654290265984853",                                   │
#│           │     "modifier": "1654290265984853",                                        │
#│           │     "creator": "1654290265984853",                                         │
#│           │     "group": "llm",                                                        │
#│           │     "model_name": "agentic-rl-1b9b480c",                                   │
#│           │     "max_output_cnt": 2                                                    │
#│           │   }                                                                        │
#│           │ ]                                                                          │
#│ page_no   │ 1                                                                          │
#│ page_size │ 10                                                                         │
#│ total     │ 5165                                                                       │
#└───────────┴────────────────────────────────────────────────────────────────────────────┘
dashscope rl list --page 1 --size 10
