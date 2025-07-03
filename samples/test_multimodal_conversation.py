import os
import dashscope
messages = [
{
    "role": "system",
    "content": [
    {"text": "You are a helpful assistant."}]
},
{
    "role": "user",
    "content": [
    {"image": "https://help-static-aliyun-doc.aliyuncs.com/file-manage-files/zh-CN/20241022/emyrja/dog_and_girl.jpeg"},
    {"text": "图中描绘的是什么景象?"}]
}]
response = dashscope.MultiModalConversation.call(
    api_key = os.getenv('DASHSCOPE_API_KEY'),
    model = 'qwen-vl-max-latest',
    messages = messages,
    enable_encryption = True,
)

print(response.output.choices[0].message.content[0]["text"])