import os
import asyncio
import dashscope
from dashscope.aigc.multimodal_conversation import AioMultiModalConversation

async def test_aio_multimodal_conversation():
    """Test async multimodal conversation API."""
    
    messages = [
        {
            "role": "system",
            "content": [
                {"text": "You are a helpful assistant."}
            ]
        },
        {
            "role": "user",
            "content": [
                {"image": "https://help-static-aliyun-doc.aliyuncs.com/file-manage-files/zh-CN/20241022/emyrja/dog_and_girl.jpeg"},
                {"text": "图中描绘的是什么景象?"}
            ]
        }
    ]
    
    # 使用异步方式调用
    response = await AioMultiModalConversation.call(
        api_key=os.getenv('DASHSCOPE_API_KEY'),
        model='qwen-vl-max-latest',
        messages=messages,
        enable_encryption=True,
    )
    
    print("Response:", response.output.choices[0].message.content[0]["text"])

async def test_aio_multimodal_conversation_stream():
    """Test async multimodal conversation API with streaming."""
    
    messages = [
        {
            "role": "system",
            "content": [
                {"text": "You are a helpful assistant."}
            ]
        },
        {
            "role": "user",
            "content": [
                {"image": "https://help-static-aliyun-doc.aliyuncs.com/file-manage-files/zh-CN/20241022/emyrja/dog_and_girl.jpeg"},
                {"text": "请详细描述这张图片中的内容"}
            ]
        }
    ]
    
    # 使用异步流式调用
    async for chunk in await AioMultiModalConversation.call(
        api_key=os.getenv('DASHSCOPE_API_KEY'),
        model='qwen-vl-max-latest',
        messages=messages,
        stream=True,
        incremental_output=True,
        enable_encryption=True,
    ):
        if hasattr(chunk, 'output') and chunk.output and chunk.output.choices:
            content = chunk.output.choices[0].message.content
            if content and len(content) > 0 and "text" in content[0]:
                print(chunk.output.choices[0].message.content[0]["text"], end="", flush=True)
    print()  # 换行

async def test_aio_multimodal_conversation_local_image():
    """Test async multimodal conversation API with local image."""
    
    # 使用本地图片文件
    messages = [
        {
            "role": "system",
            "content": [
                {"text": "You are a helpful assistant."}
            ]
        },
        {
            "role": "user",
            "content": [
                {"image": "tests/data/bird.JPEG"},  # 使用测试数据中的图片
                {"text": "这张图片是什么?"}
            ]
        }
    ]
    
    try:
        response = await AioMultiModalConversation.call(
            api_key=os.getenv('DASHSCOPE_API_KEY'),
            model='qwen-vl-max-latest',
            messages=messages,
            enable_encryption=True,
        )
        
        print("Local image response:", response.output.choices[0].message.content[0]["text"])
    except Exception as e:
        print(f"Error with local image: {e}")

async def test_aio_multimodal_conversation_multiple_local_images():
    """Test async multimodal conversation API with multiple local images."""
    
    # 使用多个本地图片文件
    messages = [
        {
            "role": "system",
            "content": [
                {"text": "You are a helpful assistant."}
            ]
        },
        {
            "role": "user",
            "content": [
                {"image": "tests/data/bird.JPEG"},
                {"image": "tests/data/dogs.jpg"},
                {"text": "请比较这两张图片的差异"}
            ]
        }
    ]
    
    try:
        print("Starting multiple local images test...")
        response = await AioMultiModalConversation.call(
            api_key=os.getenv('DASHSCOPE_API_KEY'),
            model='qwen-vl-max-latest',
            messages=messages,
            enable_encryption=True,
        )
        
        print("Multiple local images response:", response.output.choices[0].message.content[0]["text"])
    except Exception as e:
        print(f"Error with multiple local images: {e}")

async def main():
    """Main function to run all tests."""
    print("Testing Async MultiModal Conversation API...")
    print("=" * 50)
    
    # 测试基本异步调用
    print("\n1. Testing basic async call:")
    await test_aio_multimodal_conversation()
    
    # 测试异步流式调用
    print("\n2. Testing async streaming call:")
    await test_aio_multimodal_conversation_stream()
    
    # 测试本地图片
    print("\n3. Testing with local image:")
    await test_aio_multimodal_conversation_local_image()
    
    # # 测试多个本地图片
    print("\n4. Testing with multiple local images:")
    await test_aio_multimodal_conversation_multiple_local_images()
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    # 运行异步测试
    asyncio.run(main())
