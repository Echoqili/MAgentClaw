# MAgentClaw 使用指南

## 目录

1. [系统架构](#系统架构)
2. [核心概念](#核心概念)
3. [快速开始](#快速开始)
4. [详细使用](#详细使用)
5. [最佳实践](#最佳实践)
6. [常见问题](#常见问题)

## 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    Web 管理界面                          │
│              (Flask + HTML/CSS/JS)                      │
└────────────────┬────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────┐
│                  API 接口层                              │
│         (RESTful API + 路由管理)                        │
└────────────────┬────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────┐
│              管理层 (Managers)                          │
│  ┌──────────────┐      ┌──────────────┐                │
│  │ AgentManager │      │Collaboration │                │
│  │   (管理)     │◄────►│ Manager      │                │
│  │              │      │   (协作)     │                │
│  └──────────────┘      └──────────────┘                │
└────────────────┬────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────┐
│              核心层 (Core)                              │
│  ┌──────────────┐      ┌──────────────┐                │
│  │  BaseAgent   │      │ AgentConfig  │                │
│  │   (基类)     │      │  (配置)      │                │
│  └──────────────┘      └──────────────┘                │
└────────────────┬────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────┐
│           具体 Agent 实现 (Examples)                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │ Simple   │  │  Task    │  │Coordinator│            │
│  │ Agent    │  │  Agent   │  │  Agent    │            │
│  └──────────┘  └──────────┘  └──────────┘             │
└─────────────────────────────────────────────────────────┘
```

## 核心概念

### Agent

Agent 是系统的基本执行单元，每个 Agent 都有：
- **角色 (Role)**: 定义 Agent 的职责
- **配置 (Config)**: 包含模型、工具等设置
- **状态 (State)**: 运行状态、当前任务等
- **记忆 (Memory)**: 历史对话记录

### 管理器 (Manager)

- **AgentManager**: 管理多个 Agent 的生命周期
- **CollaborationManager**: 管理 Agent 间的协作

### 协作模式

1. **Sequential (顺序)**: 任务按顺序依次执行
2. **Parallel (并行)**: 多个任务同时执行
3. **Hierarchical (层级)**: 主任务 + 子任务模式
4. **Collaborative (协作)**: Agent 间自由协作

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行测试

```bash
python test_maagentclaw.py
```

### 3. 启动系统

```bash
python maagentclaw/main.py
```

### 4. 访问界面

打开浏览器访问：http://localhost:8000

## 详细使用

### 创建自定义 Agent

```python
from maagentclaw.core.agent import BaseAgent, AgentConfig, AgentMessage
import asyncio

class MyCustomAgent(BaseAgent):
    """自定义 Agent"""
    
    async def initialize(self) -> bool:
        """初始化"""
        # 加载模型、工具等
        print(f"初始化 {self.config.name}")
        return True
    
    async def process(self, message: AgentMessage) -> AgentMessage:
        """处理消息"""
        # 实现消息处理逻辑
        user_input = message.content
        
        # 调用模型生成响应
        response_text = await self.generate_response(user_input)
        
        return AgentMessage(content=response_text, role="assistant")
    
    async def execute_task(self, task: str, context=None):
        """执行任务"""
        # 实现任务执行逻辑
        result = await self.perform_task(task, context)
        return result
    
    async def generate_response(self, text: str) -> str:
        """生成响应（示例方法）"""
        # 这里可以集成实际的 AI 模型
        return f"处理：{text}"

# 使用 Agent
config = AgentConfig(
    name="my_agent",
    role="assistant",
    model="gpt-3.5-turbo"
)

agent = MyCustomAgent(config)
await agent.initialize()
```

### 集成 AI 模型

```python
import openai

class LLM Agent(BaseAgent):
    """集成大语言模型的 Agent"""
    
    async def initialize(self) -> bool:
        # 配置 API
        openai.api_key = "your-api-key"
        return True
    
    async def process(self, message: AgentMessage) -> AgentMessage:
        # 构建对话历史
        messages = [
            {"role": "system", "content": f"你是{self.config.role}，{self.config.description}"}
        ]
        
        # 添加历史记忆
        for msg in self.get_memory(limit=5):
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # 添加当前消息
        messages.append({"role": "user", "content": message.content})
        
        # 调用 API
        response = openai.ChatCompletion.create(
            model=self.config.model,
            messages=messages,
            temperature=self.config.temperature
        )
        
        reply = response.choices[0].message.content
        return AgentMessage(content=reply, role="assistant")
```

### 多 Agent 协作

```python
from maagentclaw.managers.agent_manager import AgentManager
from maagentclaw.managers.collaboration import CollaborationManager, CollaborationMode

# 初始化
agent_manager = AgentManager()
collab_manager = CollaborationManager(agent_manager)

# 创建多个 Agent
for i in range(3):
    config = AgentConfig(name=f"worker_{i}", role=f"worker")
    agent = SimpleAgent(config)
    agent_manager.register_agent(agent, config)

# 创建协作会话
session = collab_manager.create_session(
    mode=CollaborationMode.PARALLEL,
    participants=["worker_0", "worker_1", "worker_2"]
)

# 执行协作任务
tasks = ["任务 A", "任务 B", "任务 C"]
results = await collab_manager.execute_parallel(session.id, tasks)

# 处理结果
for task_id, result in results.items():
    print(f"任务 {task_id}: {result}")
```

### 配置管理

```python
from maagentclaw.config.config_manager import ConfigManager, AgentConfigData

# 初始化配置管理器
config_manager = ConfigManager()

# 创建 Agent 配置
agent_config = AgentConfigData(
    name="customer_service",
    role="客服",
    description="客户服务 Agent",
    model="gpt-4",
    tools=["search", "database"]
)

# 保存配置
config_manager.add_agent(agent_config)

# 加载配置
config_manager.load_agents_config()

# 更新配置
config_manager.update_agent("customer_service", {
    "temperature": 0.8,
    "max_iterations": 15
})
```

## 最佳实践

### 1. Agent 设计原则

- **单一职责**: 每个 Agent 专注于一个特定领域
- **清晰接口**: 定义明确的输入输出接口
- **错误处理**: 完善的异常处理机制
- **日志记录**: 记录关键操作和状态变化

### 2. 任务分配策略

```python
def select_best_agent(task: str, agents: list) -> str:
    """根据任务类型选择最合适的 Agent"""
    
    task_keywords = {
        "research": ["研究", "分析", "调查"],
        "coding": ["代码", "编程", "开发"],
        "writing": ["写作", "文案", "创作"]
    }
    
    agent_roles = {
        "researcher": "research",
        "developer": "coding",
        "writer": "writing"
    }
    
    # 简单的关键词匹配
    for agent_name, role_type in agent_roles.items():
        keywords = task_keywords.get(role_type, [])
        if any(kw in task for kw in keywords):
            return agent_name
    
    # 默认返回第一个可用 Agent
    return agents[0]
```

### 3. 错误处理

```python
from maagentclaw.utils.helpers import async_retry, safe_execute

@async_retry(max_retries=3, delay=1.0)
@safe_execute(default={"error": "执行失败"})
async def robust_task_execution(task: str):
    """带重试和安全保护的执行"""
    result = await execute(task)
    return result
```

### 4. 性能优化

- 使用异步 IO 提高并发性能
- 实现 Agent 连接池
- 缓存常用响应
- 限制并发 Agent 数量

## 常见问题

### Q1: 如何集成自己的 AI 模型？

在 Agent 的 `initialize` 方法中配置模型 API，在 `process` 方法中调用模型。

### Q2: Agent 之间如何通信？

通过 CollaborationManager 创建会话，在会话中 Agent 可以互相通信。

### Q3: 如何保存 Agent 的状态？

使用 ConfigManager 保存配置，使用数据库或文件系统保存运行时状态。

### Q4: 支持哪些部署方式？

- 单机部署（默认）
- Docker 容器化部署
- 分布式部署（开发中）

### Q5: 如何监控 Agent 运行状态？

通过 Web 管理界面实时查看，或调用 `/api/agents` 接口获取状态。

## 技术支持

如有问题，请查看：
- 项目文档
- 示例代码
- 测试脚本
