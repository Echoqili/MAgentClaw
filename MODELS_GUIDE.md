# AI 模型使用指南

## 📋 概述

MAgentClaw v1.2.0 开始支持多种 AI 模型，包括：

- **OpenAI GPT 系列** (GPT-3.5, GPT-4, GPT-4o 等)
- **阿里云通义千问** (Qwen-turbo, Qwen-plus, Qwen-max 等)
- **可扩展支持其他模型**

## 🚀 快速开始

### 1. 安装依赖

```bash
# OpenAI 模型
pip install openai

# 阿里云 Qwen 模型
pip install dashscope

# Token 计数（OpenAI）
pip install tiktoken
```

### 2. 配置 API Key

```bash
# 设置环境变量（推荐）
$env:OPENAI_API_KEY="your-openai-api-key"
$env:DASHSCOPE_API_KEY="your-dashscope-api-key"

# 或在代码中直接配置
```

### 3. 基本使用

```python
import asyncio
from maagentclaw.models.openai_model import create_openai_model
from maagentclaw.models.base_model import Message

async def main():
    # 创建模型
    model = create_openai_model(
        model_name="gpt-3.5-turbo",
        api_key="your-api-key"
    )
    
    # 初始化
    await model.initialize()
    
    # 对话
    messages = [Message(role="user", content="你好")]
    response = await model.chat(messages)
    
    print(f"AI: {response.content}")

asyncio.run(main())
```

## 📖 详细使用

### OpenAI GPT 模型

#### 创建模型

```python
from maagentclaw.models.openai_model import create_openai_model, OpenAIModel

# 方式 1: 使用便捷函数
model = create_openai_model(
    model_name="gpt-4o",
    api_key="sk-...",  # 可选，如果设置了环境变量
    temperature=0.7,
    max_tokens=2000
)

# 方式 2: 使用 ModelConfig
from maagentclaw.models.base_model import ModelConfig

config = ModelConfig(
    name="my-gpt4",
    provider="openai",
    model_name="gpt-4",
    api_key="sk-...",
    temperature=0.7,
    max_tokens=4000
)

model = OpenAIModel(config)
```

#### 支持的模型

```python
# 预定义模型配置
OPENAI_MODELS = {
    "gpt-3.5-turbo": {4096, 4096},
    "gpt-4": {8192, 8192},
    "gpt-4-turbo": {128000, 4096},
    "gpt-4o": {128000, 4096},
    "gpt-4o-mini": {128000, 16384}
}
```

#### 对话示例

```python
# 简单对话
messages = [Message(role="user", content="你好")]
response = await model.chat(messages)
print(response.content)

# 多轮对话
messages = [
    Message(role="system", content="你是一个有帮助的助手"),
    Message(role="user", content="你好"),
    Message(role="assistant", content="你好！有什么可以帮助你的？"),
    Message(role="user", content="今天天气如何？")
]
response = await model.chat(messages)

# 带历史的对话
history = []
while True:
    user_input = input("You: ")
    if user_input == "quit":
        break
    
    messages = [Message(role="user", content=user_input)]
    response = await model.chat(messages)
    
    # 添加到历史
    history.append(Message(role="user", content=user_input))
    history.append(response)
    
    print(f"AI: {response.content}")
```

#### 流式对话

```python
# 流式输出
messages = [Message(role="user", content="请写一篇关于 AI 的短文")]

async for chunk in model.chat_stream(messages):
    print(chunk, end="", flush=True)
```

#### Token 计数

```python
messages = [
    Message(role="user", content="你好"),
    Message(role="assistant", content="你好！有什么可以帮助你的？")
]

token_count = await model.count_tokens(messages)
print(f"Token 数：{token_count}")
```

---

### 阿里云 Qwen 模型

#### 创建模型

```python
from maagentclaw.models.qwen_model import create_qwen_model, QwenModel

# 方式 1: 使用便捷函数
model = create_qwen_model(
    model_name="qwen-plus",
    api_key="sk-...",  # 阿里云 DashScope API Key
    temperature=0.7
)

# 方式 2: 使用 ModelConfig
config = ModelConfig(
    name="my-qwen",
    provider="qwen",
    model_name="qwen-max",
    api_key="sk-...",
    temperature=0.7
)

model = QwenModel(config)
```

#### 支持的模型

```python
QWEN_MODELS = {
    "qwen-turbo": {8000, 2000},
    "qwen-plus": {32000, 2000},
    "qwen-max": {32000, 2000},
    "qwen-max-longcontext": {28000, 2000}
}
```

#### 对话示例

```python
# 简单对话
messages = [Message(role="user", content="你好")]
response = await model.chat(messages)
print(response.content)

# 流式对话
messages = [Message(role="user", content="请介绍杭州")]

async for chunk in model.chat_stream(messages):
    print(chunk, end="", flush=True)
```

---

### 模型管理器

模型管理器提供多模型管理和自动回退功能。

#### 基本使用

```python
from maagentclaw.models.model_manager import ModelManager
from maagentclaw.models.openai_model import create_openai_model
from maagentclaw.models.qwen_model import create_qwen_model

# 创建管理器
manager = ModelManager()

# 注册模型
openai_model = create_openai_model("gpt-3.5-turbo")
qwen_model = create_qwen_model("qwen-turbo")

manager.register_model(openai_model, set_default=True)
manager.register_model(qwen_model)

# 查看模型列表
models = manager.list_models()
for model in models:
    print(f"{model['name']} (默认：{model['is_default']})")

# 使用默认模型对话
messages = [Message(role="user", content="你好")]
response = await manager.chat(messages)

# 使用指定模型
response = await manager.chat(messages, model_name="qwen/qwen-turbo")
```

#### 自动回退

```python
# 启用自动回退
# 如果主模型失败，会自动尝试其他模型

messages = [Message(role="user", content="你好")]

# 默认启用回退
response = await manager.chat(messages, use_fallback=True)

if response.is_error:
    print(f"所有模型都失败：{response.error}")
else:
    print(f"响应：{response.content}")
```

#### 设置优先级

```python
# 设置模型优先级
manager.set_model_priority([
    "openai/gpt-4o",
    "openai/gpt-3.5-turbo",
    "qwen/qwen-plus"
])

# 查看统计信息
stats = manager.get_stats()
print(f"总模型数：{stats['total_models']}")
print(f"默认模型：{stats['default_model']}")
print(f"优先级顺序：{stats['model_order']}")
```

---

## 🔧 高级用法

### 自定义模型

```python
from maagentclaw.models.base_model import BaseModel, ModelConfig, ModelResponse, Message
from typing import List, AsyncGenerator

class MyCustomModel(BaseModel):
    async def initialize(self) -> bool:
        # 初始化逻辑
        self._initialized = True
        return True
    
    async def chat(self, messages: List[Message]) -> ModelResponse:
        # 实现聊天逻辑
        content = "响应内容"
        return ModelResponse(content=content)
    
    async def chat_stream(self, messages: List[Message]) -> AsyncGenerator[str, None]:
        # 实现流式逻辑
        yield "流式内容"
    
    async def count_tokens(self, messages: List[Message]) -> int:
        # 实现 token 计数
        return 100

# 使用自定义模型
config = ModelConfig(
    name="my-model",
    provider="custom",
    model_name="v1"
)

model = MyCustomModel(config)
await model.initialize()
```

### 错误处理

```python
from maagentclaw.models.base_model import ModelResponse

async def safe_chat(messages):
    response = await model.chat(messages)
    
    if response.is_error:
        print(f"错误：{response.error}")
        return None
    
    return response.content

# 重试机制
import asyncio

async def chat_with_retry(messages, max_retries=3):
    for attempt in range(max_retries):
        response = await model.chat(messages)
        
        if not response.is_error:
            return response
        
        print(f"尝试 {attempt + 1}/{max_retries} 失败")
        await asyncio.sleep(1)  # 等待 1 秒
    
    return response  # 返回最后一次错误
```

### 性能优化

```python
# 1. 使用流式响应减少等待时间
async for chunk in model.chat_stream(messages):
    process(chunk)  # 立即处理

# 2. 批量处理多个请求
import asyncio

tasks = [
    model.chat([Message(role="user", content=f"问题{i}")])
    for i in range(10)
]

responses = await asyncio.gather(*tasks)

# 3. 缓存常用响应
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_chat(prompt: str):
    return asyncio.run(model.chat([Message(role="user", content=prompt)]))
```

---

## 📊 最佳实践

### 1. API Key 管理

```python
# ✅ 推荐：使用环境变量
import os
api_key = os.getenv("OPENAI_API_KEY")

# ❌ 不推荐：硬编码
api_key = "sk-..."
```

### 2. 错误处理

```python
# ✅ 推荐：完整的错误处理
response = await model.chat(messages)
if response.is_error:
    logger.error(f"API 错误：{response.error}")
    # 实现回退逻辑
else:
    process(response.content)
```

### 3. Token 管理

```python
# ✅ 推荐：监控 token 使用
token_count = await model.count_tokens(messages)
if token_count > model.config.context_window * 0.8:
    print("警告：接近上下文限制")
    # 实现消息截断或总结
```

### 4. 并发控制

```python
# ✅ 推荐：限制并发请求
import asyncio

semaphore = asyncio.Semaphore(5)  # 最多 5 个并发

async def limited_chat(messages):
    async with semaphore:
        return await model.chat(messages)
```

---

## 🧪 测试

### 运行测试脚本

```bash
# 设置 API Key
$env:OPENAI_API_KEY="your-key"
$env:DASHSCOPE_API_KEY="your-key"

# 运行测试
python test_models.py
```

### 自定义测试

```python
import asyncio
from maagentclaw.models import create_openai_model, Message

async def test():
    model = create_openai_model("gpt-3.5-turbo")
    await model.initialize()
    
    # 测试对话
    messages = [Message(role="user", content="测试")]
    response = await model.chat(messages)
    
    assert not response.is_error
    assert len(response.content) > 0
    
    print("✓ 测试通过")

asyncio.run(test())
```

---

## ❓ 常见问题

### Q1: 如何切换模型？
```python
# 方式 1: 创建新模型
model = create_openai_model("gpt-4")

# 方式 2: 使用管理器
manager.set_default_model("openai/gpt-4")
```

### Q2: 如何处理长文本？
```python
# 分段处理
def split_text(text, max_length=2000):
    return [text[i:i+max_length] for i in range(0, len(text), max_length)]

chunks = split_text(long_text)
for chunk in chunks:
    response = await model.chat([Message(role="user", content=chunk)])
```

### Q3: 如何保存对话历史？
```python
import json

# 保存
history = [msg.to_dict() for msg in messages]
with open("history.json", "w") as f:
    json.dump(history, f)

# 加载
with open("history.json") as f:
    history = json.load(f)
    messages = [Message(**msg) for msg in history]
```

---

## 📚 参考资源

- [OpenAI API 文档](https://platform.openai.com/docs)
- [阿里云 DashScope 文档](https://help.aliyun.com/zh/dashscope/)
- [MAgentClaw 开发文档](DEVELOPMENT.md)

---

**更新日期**: 2026-03-08  
**版本**: v1.2.0  
**状态**: ✅ 活跃维护

**MAgentClaw Team** 🦞
