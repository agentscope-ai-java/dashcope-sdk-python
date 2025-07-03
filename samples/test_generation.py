import os
from dashscope import Generation

messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "你是谁？"},
]
response = Generation.call(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    model="qwen-plus",
    messages=messages,
    result_format="message",
    enable_encryption=True,
    stream=True,
)

for chunk in response:
    print(chunk.output.choices[0].message.content)

# if response.status_code == 200:
#     print(response.output.choices[0].message.content)
# else:
#     print(f"HTTP返回码：{response.status_code}")
#     print(f"错误码：{response.code}")
#     print(f"错误信息：{response.message}")
#     print("请参考文档：https://help.aliyun.com/zh/model-studio/developer-reference/error-code")