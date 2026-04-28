#!/usr/bin/env bash
#****************************************************************#
# ScriptName: run_fc.sh
# Author: @alibaba-inc.com
# Create Date: 2026-03-04 17:22
# Modify Author: @alibaba-inc.com
# Modify Date: 2026-03-25 14:27
# Function:
#***************************************************************#
# output：✅ Template generated: my_config.yaml
# dashscope rl init -c my_config.yaml

# Register functions
# output：
#{
#  "rollout_entity_ids": [
#    "ro-750a55c1-6855-4e07-ad57-fb4caa1607bc"
#  ],
#  "reward_entity_ids": [
#    "rw-cfaf35ee-eae8-4fdf-bf39-b7638955ed07",
#    "rw-ba974a37-a5e9-4941-9aac-784da9c48ef1"
#  ],
#  "rollout_instance_ids": [
#    "ro-ins-3ca12060-384d-48a5-85a5-469580996d9e"
#  ],
#  "reward_instance_ids": [
#    "rw-ins-a5940167-1ed3-48ff-bb45-43b847c81044",
#    "rw-ins-3daeb221-365f-433e-9e62-520d28ed2990"
#  ]
#}
dashscope rl register_functions \
  --rollout-classpaths "functions.rollout.demo_rollout.DemoRolloutProcessor" \
  --reward-classpaths "functions.reward.demo_reward.DemoRewardProcessor" \
  --reward-classpaths "functions/reward/demo_reward_decorator.py:SafetyProcessor" \
  --group-reward-classpaths "functions.reward.demo_group_reward.DemoGroupRewardProcessor" \
  --no-lazy-load \
  --output-format json

# Test Rollout function
# output：
#{
#  "agent_output": {
#    "messages": [
#      {
#        "role": "user",
#        "content": "Hello, please introduce yourself"
#      }
#    ],
#    "rollout_extra": {
#      "rollout_id": "ro-ins-e8e92e94-b5c3-4546-b7b1-9832b8b948f2",
#      "training_state": {
#        "task_id": "task-001"
#      }
#    },
#    "rollout_metrics": {
#      "latency": 0.0001
#    },
#    "reward_score": null
#  },
#  "status": "success",
#  "error": null
##}
ROLLOUT_INSTANCE_ID="ro-ins-232b3421-d5cb-4717-81f6-7f65fdaf18ab"
dashscope rl test_functions "$ROLLOUT_INSTANCE_ID" \
  --type rollout \
  --input '{
  "func_type": "rollout",
  "messages": [
    {
      "role": "user",
      "content": "Hello, please introduce yourself"
    }
  ],
  "tools": null,
  "ground_truth": "",
  "rollout_extra": {
    "rollout_id": "ro-ins-e8e92e94-b5c3-4546-b7b1-9832b8b948f2",
    "training_state": {
      "task_id": "task-001"
    }
  },
  "sampling_params": {
    "temperature": 0.7,
    "max_tokens": 1024,
    "max_turns": 25,
    "timeout": 60.0
  },
  "model_resource": {
    "model_name": "qwen3.5-35b-a3b",
    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "api_key": "your-api-key-here"
  },
  "request_metadata": {
    "protocol": "openai",
    "system_prompt": "",
    "job_id": "dummy-job-id",
    "sample_id": "dummy-sample-id",
    "rollout_id": "dummy-rollout-id",
    "attempt_id": "dummy-attempt-id"
  },
  "additional_field": "any extra data you want"
}'

# Test Reward function
# output：
#{
#  "reward": {
#    "reward_score": 0.0,
#    "rollout_metrics": {
#      "accuracy": 0.95
#    }
#  },
#  "status": "success",
#  "error": null
#}
REWARD_INSTANCE_ID="rw-ins-03a1cfe5-087e-4010-a286-c91933c6bb64"
dashscope rl test_functions "$REWARD_INSTANCE_ID" \
  --type reward \
  --input resources/reward_input.json

# Test Reward function
# output：
#{
#  "reward": {
#    "reward_score": 0.85,
#    "reward_metrics": null
#  },
#  "status": "success",
#  "error": null
#}
REWARD_INSTANCE_ID="rw-ins-c85ec84e-d82a-4d26-96cc-e5e297106937"
dashscope rl test_functions "$REWARD_INSTANCE_ID" \
  --type reward \
  --input resources/reward_decorator_input.json

# Test Group Reward function
# output：
#{
#  "group_reward": {
#    "reward_score": 0.0,
#    "reward_metrics": {
#      "accuracy": 0.95
#    }
#  },
#  "status": "success",
#  "error": null
#}
GROUP_REWARD_INSTANCE_ID="grw-ins-05996ec9-6052-4d39-9c7c-ba3f5a0a77bf"
dashscope rl test_functions "$GROUP_REWARD_INSTANCE_ID" \
  --type group_reward \
  --input resources/group_reward_input.json
