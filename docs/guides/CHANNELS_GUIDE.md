# 渠道管理使用指南

## 📋 概述

MAgentClaw v1.2.0 支持多种消息渠道，包括：

- **WebSocket**: 实时双向通信
- **REST API**: HTTP RESTful 接口
- **CLI**: 命令行交互
- **可扩展**: 自定义渠道

## 🚀 快速开始

### 1. 安装依赖

```bash
# WebSocket 支持
pip install websockets

# REST API 支持（已包含）
pip install aiohttp
```

### 2. 基本使用

```python
import asyncio
from maagentclaw.channels.cli_channel import create_cli_channel
from maagentclaw.channels.base_channel import ChannelMessage, ChannelType

async def main():
    # 创建 CLI 渠道
    channel = create_cli_channel()
    
    # 初始化
    await channel.initialize()
    
    # 注册消息处理器
    @channel.on_message
    async def handle_message(msg):
        print(f"收到：{msg.content}")
        
        # 回复
        reply = ChannelMessage(
            content=f"回复：{msg.content}",
            sender_id="system",
            receiver_id=msg.sender_id,
            channel_type=ChannelType.CLI
        )
        await channel.send_message(reply)
    
    # 保持运行
    await asyncio.sleep(60)
    
    # 关闭
    await channel.shutdown()

asyncio.run(main())
```

## 📖 详细使用

### WebSocket 渠道

#### 创建渠道

```python
from maagentclaw.channels.websocket_channel import create_websocket_channel

# 创建 WebSocket 渠道
channel = create_websocket_channel(
    name="websocket",
    host="0.0.0.0",
    port=8765
)
```

#### 消息处理

```python
@channel.on_message
async def handle_message(msg):
    print(f"收到消息：{msg.content}")
    
    # 回复
    reply = ChannelMessage(
        content="收到你的消息",
        sender_id="system",
        receiver_id=msg.sender_id
    )
    await channel.send_message(reply)

# 错误处理
@channel.on_error
async def handle_error(error, context):
    print(f"发生错误：{error}")
```

#### 广播消息

```python
# 广播给所有连接
count = await channel.broadcast("系统通知")

# 广播给指定连接
count = await channel.broadcast(
    "定向消息",
    recipients=["conn_1", "conn_2"]
)
```

#### 客户端示例

```javascript
// JavaScript 客户端
const ws = new WebSocket('ws://localhost:8765');

ws.onopen = () => {
    console.log('已连接');
    
    // 发送消息
    ws.send(JSON.stringify({
        content: '你好',
        sender_id: 'user1'
    }));
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('收到:', data);
};
```

---

### REST API 渠道

#### 创建渠道

```python
from maagentclaw.channels.rest_api_channel import create_rest_api_channel

# 创建 REST API 渠道
channel = create_rest_api_channel(
    name="rest_api",
    host="0.0.0.0",
    port=8080
)
```

#### API 端点

**发送消息**
```bash
POST http://localhost:8080/api/message
Content-Type: application/json

{
  "content": "你好",
  "sender_id": "user1",
  "metadata": {}
}
```

**健康检查**
```bash
GET http://localhost:8080/api/health
```

**统计信息**
```bash
GET http://localhost:8080/api/stats
```

#### 响应格式

```json
{
  "success": true,
  "message_id": "uuid",
  "status": "received"
}
```

---

### CLI 渠道

#### 创建渠道

```python
from maagentclaw.channels.cli_channel import create_cli_channel

# 创建 CLI 渠道
channel = create_cli_channel(
    name="cli",
    prompt="You: ",
    show_timestamp=True
)
```

#### 自定义提示符

```python
# 设置提示符
channel.set_prompt("AI Assistant: ")

# 启用/禁用时间戳
channel.enable_timestamp(True)
```

#### 消息处理

```python
@channel.on_message
async def handle_message(msg):
    content = msg.content.strip()
    
    if content.lower() == 'quit':
        return
    
    # 处理命令
    if content.startswith('/'):
        await handle_command(content)
    else:
        # 普通对话
        reply = ChannelMessage(
            content=f"收到：{content}",
            sender_id="system"
        )
        await channel.send_message(reply)
```

---

## 🔧 渠道管理器

### 基本使用

```python
from maagentclaw.channels.channel_manager import ChannelManager
from maagentclaw.channels.websocket_channel import create_websocket_channel
from maagentclaw.channels.cli_channel import create_cli_channel

# 创建管理器
manager = ChannelManager()

# 创建渠道
ws_channel = create_websocket_channel()
cli_channel = create_cli_channel()

# 注册渠道
manager.register_channel(ws_channel, set_default=True)
manager.register_channel(cli_channel)

# 初始化所有渠道
await manager.initialize_all()

# 发送消息
message = ChannelMessage(
    content="你好",
    sender_id="system"
)
await manager.send_message(message)

# 广播消息
count = await manager.broadcast("系统通知")

# 查看渠道列表
channels = manager.list_channels()
for channel in channels:
    print(f"{channel['name']} ({channel['type']})")

# 获取统计
stats = manager.get_stats()
print(f"总渠道数：{stats['total_channels']}")

# 关闭所有渠道
await manager.shutdown_all()
```

---

## 🎯 渠道路由器

### 基本使用

```python
from maagentclaw.channels.channel_router import ChannelRouter, RoutingRule

# 创建路由器
router = ChannelRouter(manager)

# 添加规则
router.add_rule(RoutingRule(
    name="urgent",
    condition=lambda msg: msg.metadata.get("priority") == "high",
    target_channels=["websocket", "cli"],
    priority=10
))

router.add_rule(RoutingRule(
    name="help",
    condition=lambda msg: "help" in msg.content.lower(),
    target_channels=["cli"],
    priority=5
))

# 路由消息
message = ChannelMessage(
    content="我需要帮助",
    sender_id="user1",
    metadata={"priority": "normal"}
)

targets = router.route_message(message)
print(f"目标渠道：{targets}")

# 发送消息（自动路由）
results = await router.send_message(message)
print(f"发送结果：{results}")
```

### 预定义规则

```python
# 消息类型规则
type_rule = ChannelRouter.create_type_rule(
    message_type="notification",
    target_channels=["websocket"],
    priority=5
)

# 发送者规则
sender_rule = ChannelRouter.create_sender_rule(
    sender_pattern="admin",
    target_channels=["websocket", "cli"],
    priority=10
)

# 内容关键词规则
keyword_rule = ChannelRouter.create_content_rule(
    keyword="紧急",
    target_channels=["cli"],
    priority=8
)

# 优先级规则
priority_rule = ChannelRouter.create_priority_rule(
    priority_level="high",
    target_channels=["websocket", "cli"],
    priority=10
)
```

---

## 💡 高级用法

### 1. 自定义渠道

```python
from maagentclaw.channels.base_channel import BaseChannel, ChannelConfig, ChannelType

class CustomChannel(BaseChannel):
    async def initialize(self) -> bool:
        # 初始化逻辑
        self._initialized = True
        return True
    
    async def shutdown(self):
        # 关闭逻辑
        pass
    
    async def send_message(self, message: ChannelMessage) -> bool:
        # 发送消息逻辑
        return True
    
    async def broadcast(self, content: str, recipients=None) -> int:
        # 广播逻辑
        return 0

# 使用自定义渠道
config = ChannelConfig(
    name="custom",
    channel_type=ChannelType.CUSTOM
)

channel = CustomChannel(config)
```

### 2. 消息队列集成

```python
import asyncio

class QueueChannel(BaseChannel):
    def __init__(self, config):
        super().__init__(config)
        self.message_queue = asyncio.Queue()
    
    async def send_message(self, message: ChannelMessage) -> bool:
        await self.message_queue.put(message)
        return True
    
    async def process_queue(self):
        while True:
            message = await self.message_queue.get()
            # 处理消息
            await self.handle_message(message)
            self.message_queue.task_done()
```

### 3. 渠道中间件

```python
class ChannelMiddleware:
    def __init__(self, channel):
        self.channel = channel
    
    async def send_message(self, message: ChannelMessage) -> bool:
        # 前置处理
        message = await self.before_send(message)
        
        # 发送
        success = await self.channel.send_message(message)
        
        # 后置处理
        await self.after_send(message, success)
        
        return success
    
    async def before_send(self, message: ChannelMessage) -> ChannelMessage:
        # 消息过滤、转换等
        message.content = message.content.strip()
        return message
    
    async def after_send(self, message: ChannelMessage, success: bool):
        # 日志、统计等
        if success:
            print(f"消息已发送：{message.id}")
```

---

## 📊 最佳实践

### 1. 错误处理

```python
@channel.on_error
async def handle_error(error, context):
    logger.error(f"渠道错误：{error}")
    
    # 重试逻辑
    if isinstance(context, ChannelMessage):
        await retry_send(context)
```

### 2. 连接管理

```python
# WebSocket 连接监控
async def monitor_connections():
    while True:
        await asyncio.sleep(60)
        
        count = channel.get_connection_count()
        print(f"当前连接数：{count}")
        
        # 清理不活跃连接
        for conn_info in channel.list_connections():
            last_active = datetime.fromisoformat(conn_info['last_active'])
            if (datetime.now() - last_active).total_seconds() > 300:
                # 关闭不活跃连接
                conn = channel.connections[conn_info['id']]
                await conn.close()
```

### 3. 性能优化

```python
# 批量发送
async def batch_send(messages: List[ChannelMessage]):
    tasks = [channel.send_message(msg) for msg in messages]
    results = await asyncio.gather(*tasks)
    return sum(results)

# 限流
from asyncio import Semaphore

semaphore = Semaphore(10)  # 最多 10 个并发

async def limited_send(message: ChannelMessage):
    async with semaphore:
        return await channel.send_message(message)
```

---

## 🧪 测试

### 运行测试脚本

```bash
python test_channels.py
```

### 单元测试

```python
import unittest
from maagentclaw.channels.cli_channel import create_cli_channel

class TestChannel(unittest.TestCase):
    async def test_send_message(self):
        channel = create_cli_channel()
        await channel.initialize()
        
        message = ChannelMessage(content="test")
        success = await channel.send_message(message)
        
        self.assertTrue(success)
        
        await channel.shutdown()

if __name__ == '__main__':
    unittest.main()
```

---

## ❓ 常见问题

### Q1: 如何选择渠道？
- **实时通信**: WebSocket
- **HTTP 集成**: REST API
- **本地调试**: CLI

### Q2: 如何添加新渠道？
继承 `BaseChannel` 并实现抽象方法。

### Q3: 如何保证消息可靠性？
实现消息确认和重试机制。

### Q4: 如何处理大量并发？
使用连接池和限流机制。

---

## 📚 参考资源

- [WebSocket RFC](https://tools.ietf.org/html/rfc6455)
- [REST API 设计](https://restfulapi.net/)
- [MAgentClaw 开发文档](DEVELOPMENT.md)

---

**更新日期**: 2026-03-08  
**版本**: v1.2.0  
**状态**: ✅ 活跃维护

**MAgentClaw Team** 🦞
