# MAgentClaw - 多 Agent 管理与协作系统

基于 OpenClaw 和 CoClaw 架构设计的多 Agent 管理系统，提供完整的 Agent 管理、任务协作和 Web 管理界面功能。

## 特性

- 🤖 **多 Agent 管理** - 支持创建、管理和监控多个 AI Agent
- 🔄 **协作框架** - 提供顺序、并行、层级等多种协作模式
- 🎯 **任务调度** - 智能任务分配和依赖管理
- 🌐 **Web 界面** - 美观的管理界面，实时监控 Agent 状态
- ⚙️ **配置管理** - 灵活的配置文件系统
- 🔧 **可扩展** - 易于添加新的 Agent 和工具

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行系统

```bash
python maagentclaw/main.py
```

访问 http://localhost:8000 查看 Web 管理界面

## 项目结构

```
MAgentClaw/
├── maagentclaw/
│   ├── __init__.py              # 包初始化
│   ├── main.py                  # 主程序入口
│   ├── core/
│   │   └── agent.py             # Agent 基类
│   ├── managers/
│   │   ├── agent_manager.py     # Agent 管理器
│   │   └── collaboration.py     # 协作管理器
│   ├── config/
│   │   └── config_manager.py    # 配置管理器
│   ├── agents/
│   │   └── examples.py          # 示例 Agent
│   ├── interfaces/
│   │   └── web_interface.py     # Web 界面
│   ├── utils/
│   │   └── helpers.py           # 工具函数
│   ├── web/
│   │   ├── templates/           # HTML 模板
│   │   └── static/              # 静态资源
│   ├── workspaces/              # 工作空间
│   └── logs/                    # 日志目录
├── requirements.txt             # 依赖列表
└── README.md                    # 本文档
```

## 使用示例

### 创建自定义 Agent

```python
from maagentclaw.core.agent import BaseAgent, AgentConfig, AgentMessage

class MyAgent(BaseAgent):
    async def initialize(self) -> bool:
        # 初始化逻辑
        return True
    
    async def process(self, message: AgentMessage) -> AgentMessage:
        # 处理消息逻辑
        response = AgentMessage(content="响应内容", role="assistant")
        return response
    
    async def execute_task(self, task: str, context=None):
        # 执行任务逻辑
        return {"result": "任务完成"}

# 使用 Agent
config = AgentConfig(name="my_agent", role="custom")
agent = MyAgent(config)
await agent.initialize()
```

### 管理 Agent

```python
from maagentclaw.managers.agent_manager import AgentManager

manager = AgentManager()

# 注册 Agent
manager.register_agent(agent)

# 启动 Agent
await manager.start_agent("my_agent")

# 发送消息
from maagentclaw.core.agent import AgentMessage
message = AgentMessage(content="你好", role="user")
response = await agent.process(message)
```

### 协作任务

```python
from maagentclaw.managers.collaboration import CollaborationManager, CollaborationMode

collab_manager = CollaborationManager(agent_manager)

# 创建协作会话
session = collab_manager.create_session(
    mode=CollaborationMode.PARALLEL,
    participants=["agent1", "agent2"]
)

# 并行执行任务
results = await collab_manager.execute_parallel(
    session.id,
    ["任务 1", "任务 2", "任务 3"]
)
```

## API 接口

### Agent 管理

- `GET /api/agents` - 获取所有 Agent
- `GET /api/agents/<name>` - 获取指定 Agent
- `POST /api/agents/<name>/start` - 启动 Agent
- `POST /api/agents/<name>/stop` - 停止 Agent
- `POST /api/agents/<name>/message` - 发送消息

### 配置管理

- `GET /api/config/agents` - 获取 Agent 配置
- `POST /api/config/agents` - 创建 Agent 配置
- `GET /api/config/models` - 获取模型配置

### 任务管理

- `POST /api/tasks` - 创建任务
- `POST /api/sessions` - 创建协作会话

## 配置说明

### Agent 配置 (config/agents.json)

```json
{
  "assistant": {
    "name": "assistant",
    "role": "assistant",
    "description": "通用助手",
    "model": "default",
    "workspace": "default",
    "tools": []
  }
}
```

### 模型配置 (config/models.json)

```json
{
  "default": {
    "name": "default",
    "provider": "openai",
    "api_key": "your-api-key",
    "model_name": "gpt-3.5-turbo"
  }
}
```

## 开发计划

- [ ] 集成更多 AI 模型提供商
- [ ] 添加 Agent 技能市场
- [ ] 实现 Agent 间通信协议
- [ ] 添加任务可视化编排界面
- [ ] 支持分布式部署
- [ ] 添加监控和告警功能

## 技术栈

- **Python 3.8+** - 主要编程语言
- **Flask** - Web 框架
- **Asyncio** - 异步编程
- **Dataclasses** - 数据结构

## 参考项目

- [OpenClaw](https://github.com/OpenClaw) - AI 助手框架
- [CoClaw](https://github.com/CoClaw) - 协作 Agent 系统

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
