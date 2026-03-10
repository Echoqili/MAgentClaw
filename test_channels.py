"""
渠道管理测试脚本
"""

import asyncio
import sys
from maagentclaw.channels.websocket_channel import create_websocket_channel
from maagentclaw.channels.rest_api_channel import create_rest_api_channel
from maagentclaw.channels.cli_channel import create_cli_channel
from maagentclaw.channels.channel_manager import ChannelManager
from maagentclaw.channels.channel_router import ChannelRouter, RoutingRule
from maagentclaw.channels.base_channel import ChannelMessage, ChannelType


async def test_websocket_channel():
    """测试 WebSocket 渠道"""
    print("\n" + "="*60)
    print("测试 WebSocket 渠道")
    print("="*60)
    
    # 创建渠道
    channel = create_websocket_channel(port=8765)
    
    # 初始化
    print("初始化 WebSocket 服务器...")
    success = await channel.initialize()
    
    if not success:
        print("❌ 初始化失败")
        return False
    
    print("✓ 初始化成功")
    
    # 注册消息处理器
    @channel.on_message
    async def handle_message(msg):
        print(f"[收到消息] {msg.sender_id}: {msg.content}")
        
        # 回复
        reply = ChannelMessage(
            content=f"收到：{msg.content}",
            sender_id="system",
            receiver_id=msg.sender_id,
            channel_type=ChannelType.WEBSOCKET
        )
        await channel.send_message(reply)
    
    print("✓ 消息处理器已注册")
    print("\nWebSocket 服务器运行中... (按 Ctrl+C 停止)")
    
    try:
        # 保持运行
        await asyncio.sleep(10)
    except KeyboardInterrupt:
        pass
    finally:
        await channel.shutdown()
    
    return True


async def test_rest_api_channel():
    """测试 REST API 渠道"""
    print("\n" + "="*60)
    print("测试 REST API 渠道")
    print("="*60)
    
    # 创建渠道
    channel = create_rest_api_channel(port=8080)
    
    # 初始化
    print("初始化 REST API 服务器...")
    success = await channel.initialize()
    
    if not success:
        print("❌ 初始化失败")
        return False
    
    print("✓ 初始化成功")
    print("✓ API 端点:")
    print("  - POST /api/message")
    print("  - GET /api/message/{id}")
    print("  - GET /api/health")
    print("  - GET /api/stats")
    
    print("\nREST API 服务器运行中... (按 Ctrl+C 停止)")
    
    try:
        # 保持运行
        await asyncio.sleep(10)
    except KeyboardInterrupt:
        pass
    finally:
        await channel.shutdown()
    
    return True


async def test_cli_channel():
    """测试 CLI 渠道"""
    print("\n" + "="*60)
    print("测试 CLI 渠道")
    print("="*60)
    
    # 创建渠道
    channel = create_cli_channel(prompt="You: ")
    
    # 初始化
    print("初始化 CLI...")
    success = await channel.initialize()
    
    if not success:
        print("❌ 初始化失败")
        return False
    
    print("✓ 初始化成功")
    
    # 注册消息处理器
    @channel.on_message
    async def handle_message(msg):
        print(f"\n[收到消息] {msg.sender_id}: {msg.content}")
        
        # 回复
        reply = ChannelMessage(
            content=f"AI: 收到你的消息：{msg.content}",
            sender_id="system",
            channel_type=ChannelType.CLI
        )
        await channel.send_message(reply)
    
    print("✓ 消息处理器已注册")
    print("\nCLI 渠道运行中... (输入 'quit' 退出)")
    
    try:
        # 等待 CLI 运行
        while channel._running:
            await asyncio.sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        await channel.shutdown()
    
    return True


async def test_channel_manager():
    """测试渠道管理器"""
    print("\n" + "="*60)
    print("测试渠道管理器")
    print("="*60)
    
    # 创建管理器
    manager = ChannelManager()
    
    # 创建渠道
    cli_channel = create_cli_channel()
    rest_channel = create_rest_api_channel(port=8081)
    
    # 注册渠道
    manager.register_channel(cli_channel, set_default=True)
    manager.register_channel(rest_channel)
    
    # 查看渠道列表
    print("\n已注册渠道:")
    channels = manager.list_channels()
    for channel in channels:
        default_mark = " (默认)" if channel["is_default"] else ""
        print(f"  - {channel['name']} ({channel['type']}){default_mark}")
    
    # 获取统计
    stats = manager.get_stats()
    print(f"\n统计信息:")
    print(f"  总渠道数：{stats['total_channels']}")
    print(f"  默认渠道：{stats['default_channel']}")
    
    return True


async def test_channel_router():
    """测试渠道路由器"""
    print("\n" + "="*60)
    print("测试渠道路由器")
    print("="*60)
    
    # 创建管理器
    manager = ChannelManager()
    
    # 创建渠道
    cli_channel = create_cli_channel()
    rest_channel = create_rest_api_channel(port=8082)
    
    manager.register_channel(cli_channel, set_default=True)
    manager.register_channel(rest_channel)
    
    # 创建路由器
    router = ChannelRouter(manager)
    
    # 添加规则
    router.add_rule(RoutingRule(
        name="urgent",
        condition=lambda msg: msg.metadata.get("priority") == "high",
        target_channels=["cli", "rest_api"],
        priority=10
    ))
    
    router.add_rule(RoutingRule(
        name="normal",
        condition=lambda msg: "help" in msg.content.lower(),
        target_channels=["cli"],
        priority=5
    ))
    
    print("\n路由规则:")
    for rule in router.rules:
        print(f"  - {rule.name} (优先级：{rule.priority})")
    
    # 测试路由
    test_messages = [
        ChannelMessage(
            content="我需要帮助",
            sender_id="user1",
            metadata={"priority": "normal"}
        ),
        ChannelMessage(
            content="紧急通知！",
            sender_id="admin",
            metadata={"priority": "high"}
        )
    ]
    
    print("\n测试消息路由:")
    for msg in test_messages:
        targets = router.route_message(msg)
        print(f"  消息 '{msg.content[:20]}...' -> 渠道：{targets}")
    
    return True


async def main():
    """主函数"""
    print("="*60)
    print("MAgentClaw 渠道管理测试")
    print("="*60)
    
    # 选择测试
    print("\n选择测试:")
    print("1. WebSocket 渠道")
    print("2. REST API 渠道")
    print("3. CLI 渠道")
    print("4. 渠道管理器")
    print("5. 渠道路由器")
    print("6. 全部测试")
    
    choice = input("\n请输入选项 (1-6): ").strip()
    
    if choice == "1":
        await test_websocket_channel()
    elif choice == "2":
        await test_rest_api_channel()
    elif choice == "3":
        await test_cli_channel()
    elif choice == "4":
        await test_channel_manager()
    elif choice == "5":
        await test_channel_router()
    elif choice == "6":
        # 全部测试
        await test_channel_manager()
        await test_channel_router()
        print("\n✓ 所有测试完成")
    else:
        print("无效的选项")


if __name__ == "__main__":
    asyncio.run(main())
