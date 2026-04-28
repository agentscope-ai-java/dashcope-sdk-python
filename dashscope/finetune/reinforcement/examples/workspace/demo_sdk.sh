#!/usr/bin/env bash
#****************************************************************#
# ScriptName: run_fc.sh
# Author: @alibaba-inc.com
# Create Date: 2026-03-04 17:22
# Modify Author: @alibaba-inc.com
# Modify Date: 2026-03-25 14:27
# Function:
#***************************************************************#
export DASHSCOPE_API_KEY='sk-ttt'
export DASHSCOPE_HTTP_BASE_URL='https://poc-dashscope.aliyuncs.com/api/v1'
export DEBUG_AGENTIC_RL=True
export LOG_LEVEL="info"


python3 demo_sdk_agentic_rl_functions.py
python3 demo_sdk_agentic_rl_tuning.py
python3 demo_sdk_agentic_rl_workflows.py
python3 demo_sdk_agentic_rl_workflows_yaml.py
