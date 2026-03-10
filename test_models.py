"""
AI 模型测试脚本
"""

import asyncio
import os
from maagentclaw.models.base_model import ModelConfig, Message
from maagentclaw.models.openai_model import OpenAIModel, create_openai_model
from maagentclaw.models.qwen_model import QwenModel, create_qwen_model
from maagentclaw.models.model_manager import ModelManager


async def test_openai_model():
    """测试 OpenAI 模型"""
    print("\n" + "="*60)
    print("测试 OpenAI GPT 模型")
    print("="*60)
    
    # 从环境变量获取 API key
    api_key = os.getenv("OPENAI_API_KEY", "")
    
    if not api_key:
        print("⚠️  未设置 OPENAI_API_KEY 环境变量，跳过测试")
        return
    
    # 创建模型
    model = create_openai_model(
        model_name="gpt-3.5-turbo",
        api_key=api_key,
        temperature=0.7
    )
    
    # 初始化
    print("初始化模型...")
    success = await model.initialize()
    
    if not success:
        print("❌ 初始化失败")
        return
    
    print("✓ 初始化成功")
    
    # 测试简单对话
    print("\n测试简单对话...")
    messages = [
        Message(role="user", content="你好，请介绍一下你自己")
    ]
    
    response = await model.chat(messages)
    
    if response.is_error:
        print(f"❌ 请求失败：{response.error}")
    else:
        print(f"✓ 响应成功")
        print(f"内容：{response.content[:200]}...")
        print(f"Token 使用：{response.usage}")
    
    # 测试流式对话
    print("\n测试流式对话...")
    messages = [
        Message(role="user", content="请用一句话解释什么是人工智能")
    ]
    
    print("流式响应：", end="", flush=True)
    async for chunk in model.chat_stream(messages):
        print(chunk, end="", flush=True)
    print()


async def test_qwen_model():
    """测试 Qwen 模型"""
    print("\n" + "="*60)
    print("测试阿里云 Qwen 模型")
    print("="*60)
    
    # 从环境变量获取 API key
    api_key = os.getenv("DASHSCOPE_API_KEY", "")
    
    if not api_key:
        print("⚠️  未设置 DASHSCOPE_API_KEY 环境变量，跳过测试")
        return
    
    # 创建模型
    model = create_qwen_model(
        model_name="qwen-turbo",
        api_key=api_key,
        temperature=0.7
    )
    
    # 初始化
    print("初始化模型...")
    success = await model.initialize()
    
    if not success:
        print("❌ 初始化失败")
        return
    
    print("✓ 初始化成功")
    
    # 测试简单对话
    print("\n测试简单对话...")
    messages = [
        Message(role="user", content="你好，请介绍一下你自己")
    ]
    
    response = await model.chat(messages)
    
    if response.is_error:
        print(f"❌ 请求失败：{response.error}")
    else:
        print(f"✓ 响应成功")
        print(f"内容：{response.content[:200]}...")
        print(f"Token 使用：{response.usage}")
    
    # 测试流式对话
    print("\n测试流式对话...")
    messages = [
        Message(role="user", content="请用一句话解释什么是人工智能")
    ]
    
    print("流式响应：", end="", flush=True)
    async for chunk in model.chat_stream(messages):
        print(chunk, end="", flush=True)
    print()


async def test_model_manager():
    """测试模型管理器"""
    print("\n" + "="*60)
    print("测试模型管理器")
    print("="*60)
    
    manager = ModelManager()
    
    # 创建测试模型（使用模拟配置）
    openai_key = os.getenv("OPENAI_API_KEY", "test-key")
    qwen_key = os.getenv("DASHSCOPE_API_KEY", "test-key")
    
    # 注册 OpenAI 模型
    openai_model = create_openai_model(
        model_name="gpt-3.5-turbo",
        api_key=openai_key
    )
    manager.register_model(openai_model, set_default=True)
    
    # 注册 Qwen 模型
    qwen_model = create_qwen_model(
        model_name="qwen-turbo",
        api_key=qwen_key
    )
    manager.register_model(qwen_model)
    
    # 查看模型列表
    print("\n已注册模型:")
    models = manager.list_models()
    for model in models:
        default_mark = " (默认)" if model["is_default"] else ""
        print(f"  - {model['name']}{default_mark}")
    
    # 测试模型回退
    print("\n测试模型回退...")
    messages = [
        Message(role="user", content="你好")
    ]
    
    response = await manager.chat(messages, use_fallback=True)
    print(f"响应：{response.content[:100] if response.content else response.error}")
    
    # 获取统计信息
    print("\n管理器统计:")
    stats = manager.get_stats()
    print(f"  总模型数：{stats['total_models']}")
    print(f"  默认模型：{stats['default_model']}")
    print(f"  模型顺序：{stats['model_order']}")


async def main():
    """主函数"""
    print("="*60)
    print("MAgentClaw AI 模型测试")
    print("="*60)
    
    # 测试各个模型
    await test_openai_model()
    await test_qwen_model()
    
    # 测试模型管理器
    await test_model_manager()
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
