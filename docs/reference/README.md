# MAgentClaw - 多 Agent 管理与协作系统

<div align="center">

基于 OpenClaw 和 CoClaw 架构设计的多 Agent 管理系统，提供完整的 Agent 管理、任务协作和 Web 管理界面功能。

[![GitHub](https://img.shields.io/github/license/Echoqili/MAgentClaw)](https://github.com/Echoqili/MAgentClaw/blob/main/LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

[特性](#特性) • [快速开始](#快速开始) • [使用示例](#使用示例) • [API 文档](#api-接口) • [开发计划](#开发计划)

</div>

---

## 📋 目录

- [特性](#特性)
- [快速开始](#快速开始)
- [项目结构](#项目结构)
- [使用示例](#使用示例)
- [API 接口](#api-接口)
- [配置说明](#配置说明)
- [开发计划](#开发计划)
- [技术栈](#技术栈)
- [参考项目](#参考项目)
- [许可证](#许可证)

---

## ✨ 特性

- 🤖 **多 Agent 管理** - 支持创建、管理和监控多个 AI Agent
- 🔄 **协作框架** - 提供顺序、并行、层级等多种协作模式
- 🎯 **任务调度** - 智能任务分配和依赖管理
- 🌐 **Web 界面** - 美观的管理界面，实时监控 Agent 状态
- ⚙️ **配置管理** - 灵活的配置文件系统
- 🔧 **可扩展** - 易于添加新的 Agent 和工具
- 📊 **心跳监控** - 实时监控 Agent 健康状态
- 🛠️ **工具集成** - 支持多种工具和能力扩展

---

## 🚀 快速开始

### 环境要求

- Python 3.8+
- pip 包管理器

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行系统

```bash
python maagentclaw/main.py
```

访问 http://localhost:8000 查看 Web 管理界面

### 使用启动脚本

```bash
# Windows PowerShell
.\start.ps1

# 或者增强版
.\start_enhanced.ps1
```

---

## 📁 项目结构

```
MAgentClaw/
├── maagentclaw/                    # 主程序包
│   ├── __init__.py                 # 包初始化
│   ├── main.py                     # 主程序入口
│   ├── core/
│   │   └── agent.py                # Agent 基类
│   ├── managers/
│   │   ├── agent_manager.py        # Agent 管理器
│   │   └── collaboration.py        # 协作管理器
│   ├── config/
│   │   └── config_manager.py       # 配置管理器
│   ├── agents/
│   │   └── examples.py             # 示例 Agent
│   ├── interfaces/
│   │   └── web_interface.py        # Web 界面
│   ├── utils/
│   │   └── helpers.py              # 工具函数
│   ├── web/
│   │   ├── templates/              # HTML 模板
│   │   └── static/                 # 静态资源
│   ├── workspaces/                 # 工作空间
│   └── logs/                       # 日志目录
├── config/                         # 配置文件目录
│   ├── agents.json                 # Agent 配置
│   ├── models.json                 # 模型配置
│   └── system.json                 # 系统配置
├── .github/workflows/              # GitHub Actions 配置
│   ├── pypi.yml                    # PyPI 发布
│   ├── release.yml                 # 版本发布
│   └── test.yml                    # 测试流程
├── tests/                          # 测试文件
│   ├── test_core.py                # 核心测试
│   ├── test_agents.py              # Agent 测试
│   └── test_tools.py               # 工具测试
├── requirements.txt                # 依赖列表
├── pyproject.toml                  # 项目配置
├── setup.py                        # 安装脚本
└── README.md                       # 本文档
```

---

## 💡 使用示例

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

### 心跳监控

```python
from maagentclaw.utils.heartbeat import HeartbeatMonitor

monitor = HeartbeatMonitor()

# 启动心跳监控
await monitor.start()

# 注册 Agent 心跳
monitor.register_agent("agent1", interval=30)

# 获取心跳状态
status = monitor.get_heartbeat_status("agent1")
```

---

## 🔌 API 接口

### Agent 管理

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/agents` | 获取所有 Agent |
| GET | `/api/agents/<name>` | 获取指定 Agent |
| POST | `/api/agents/<name>/start` | 启动 Agent |
| POST | `/api/agents/<name>/stop` | 停止 Agent |
| POST | `/api/agents/<name>/message` | 发送消息 |
| GET | `/api/agents/<name>/status` | 获取 Agent 状态 |

### 配置管理

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/config/agents` | 获取 Agent 配置 |
| POST | `/api/config/agents` | 创建 Agent 配置 |
| PUT | `/api/config/agents/<name>` | 更新 Agent 配置 |
| DELETE | `/api/config/agents/<name>` | 删除 Agent 配置 |
| GET | `/api/config/models` | 获取模型配置 |
| GET | `/api/config/system` | 获取系统配置 |

### 任务管理

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/tasks` | 创建任务 |
| GET | `/api/tasks/<id>` | 获取任务详情 |
| GET | `/api/tasks` | 获取任务列表 |
| POST | `/api/sessions` | 创建协作会话 |
| GET | `/api/sessions/<id>` | 获取会话详情 |

### 监控接口

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/health` | 系统健康检查 |
| GET | `/api/heartbeat` | 心跳状态 |
| GET | `/api/metrics` | 系统指标 |

---

## ⚙️ 配置说明

### Agent 配置 (config/agents.json)

```json
{
  "assistant": {
    "name": "assistant",
    "role": "assistant",
    "description": "通用助手",
    "model": "default",
    "workspace": "default",
    "tools": [],
    "heartbeat_interval": 30,
    "max_concurrent_tasks": 5
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
    "model_name": "gpt-3.5-turbo",
    "temperature": 0.7,
    "max_tokens": 2048
  },
  "qwen": {
    "name": "qwen",
    "provider": "dashscope",
    "api_key": "your-dashscope-key",
    "model_name": "qwen-max",
    "temperature": 0.7
  }
}
```

### 系统配置 (config/system.json)

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8000,
    "debug": false
  },
  "logging": {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  },
  "heartbeat": {
    "enabled": true,
    "interval": 30,
    "timeout": 60
  }
}
```

---

## 📅 开发计划

### v1.0 (已完成)
- [x] 核心 Agent 框架
- [x] Agent 管理器
- [x] Web 管理界面
- [x] 基础配置文件

### v1.1 (进行中)
- [ ] 集成更多 AI 模型提供商
  - [ ] Qwen (通义千问)
  - [ ] GLM (智谱 AI)
  - [ ] 本地模型 (vLLM)
- [ ] 添加 Agent 技能市场
- [ ] 实现 Agent 间通信协议

### v1.2 (计划中)
- [ ] 任务可视化编排界面
- [ ] 支持分布式部署
- [ ] 添加监控和告警功能
- [ ] 性能优化和压力测试

### 未来版本
- [ ] 支持更多通信渠道 (Slack, Discord, Line 等)
- [ ] 添加插件系统
- [ ] 实现持久化存储
- [ ] 支持容器化部署

---

## 🛠️ 技术栈

- **Python 3.8+** - 主要编程语言
- **Flask** - Web 框架
- **Asyncio** - 异步编程
- **Dataclasses** - 数据结构
- **JSON** - 配置格式
- **HTML/CSS/JS** - Web 界面

---

## 📚 参考项目

- [OpenClaw](https://github.com/OpenClaw) - AI 助手框架
- [CoClaw](https://github.com/CoClaw) - 协作 Agent 系统

---

## 📄 许可证

MIT License

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

### 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

<div align="center">

**Made with ❤️ by Echoqili**

[⬆ 返回顶部](#magentclaw---多-agent-管理与协作系统)

</div>
