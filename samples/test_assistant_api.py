# Copyright (c) Alibaba, Inc. and its affiliates.

from dashscope import Assistants
import os


assistant = Assistants.create(
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        # 此处以qwen-max为例，可按需更换模型名称。模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
        model='qwen-max',
        name='smart helper',
        description='A tool helper.',
        instructions='You are a helpful assistant. When asked a question, use tools wherever possible.',
        tools=[{
            'type': 'search'
        }, {
            'type': 'function',
            'function': {
                'name': 'big_add',
                'description': 'Add to number',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'left': {
                            'type': 'integer',
                            'description': 'The left operator'
                        },
                        'right': {
                            'type': 'integer',
                            'description': 'The right operator.'
                        }
                    },
                    'required': ['left', 'right']
                }
            }
        }],
)
print('\n初始Assistant')
print(assistant)

# 更新智能体：仅更新模型，Tools不变
assistant = Assistants.update(assistant.id, model='qwen-plus')
print('\n更新Model后')
print(assistant)

# 更新智能体: 清空Tools
assistant = Assistants.update(assistant.id, tools=[])
print('\n清空Tools后')
print(assistant)
