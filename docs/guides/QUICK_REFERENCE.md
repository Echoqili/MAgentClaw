# MAgentClaw 快速参考指南

## 🚀 快速启动

### 基础版
```bash
python maagentclaw/main.py
```

### 增强版（推荐）
```bash
python maagentclaw/main_enhanced.py
```

访问：http://localhost:8000

## 📁 目录结构

```
~/.maagentclaw/
├── config/           # 配置文件
│   ├── agents.json   # Agent 配置
│   ├── models.json   # 模型配置
│   ├── system.json   # 系统配置
│   └── channels.json # 渠道配置
├── workspaces/       # 工作空间
│   └── <agent-id>/
│       ├── AGENTS.md
│       ├── SOUL.md
│       ├── TOOLS.md
│       └── ...
└── sessions/         # 会话存储
    └── <session-id>.jsonl
```

## 🔧 核心 API

### 1. 配置管理

```python
from maagentclaw.config.enhanced_config import EnhancedConfigManager

config = EnhancedConfigManager()

# 创建默认配置
config.create_default_configs()

# 验证配置
errors = config.validate_all_configs()

# 添加 Agent
from maagentclaw.config.enhanced_config import AgentConfigData
agent = AgentConfigData(name="bot", role="assistant")
config.add_agent(agent)

# 启动热重载
config.start_config_watcher(interval=5.0)
```

### 2. 工作空间

```python
from maagentclaw.managers.workspace import WorkspaceManager

workspace_mgr = WorkspaceManager()

# 获取工作空间
workspace = workspace_mgr.get_workspace("assistant")

# 读取文件
content = workspace.read_file("AGENTS.md")

# 写入文件
workspace.write_file("MY_FILE.md", "# Content")

# 获取上下文
context = workspace.get_context_for_agent()
```

### 3. 会话管理

```python
from maagentclaw.managers.session_manager import SessionManager

session_mgr = SessionManager("~/.maagentclaw/sessions")

# 获取或创建会话
session = session_mgr.get_or_create_session(
    agent_id="assistant",
    channel="default",
    peer="user123",
    scope="per-peer"
)

# 添加消息
from maagentclaw.managers.session_manager import SessionMessage
msg = SessionMessage(content="你好", role="user")
session_mgr.add_message(session.id, msg)

# 获取消息
messages = session_mgr.get_messages(session.id, limit=10)

# 重置会话
session_mgr.reset_session(session.id)

# 删除会话
session_mgr.delete_session(session.id)
```

### 4. Agent 管理

```python
from maagentclaw.managers.agent_manager import AgentManager
from maagentclaw.core.agent import AgentConfig

manager = AgentManager()

# 创建 Agent
config = AgentConfig(name="bot", role="assistant")
agent = SimpleAgent(config)

# 注册 Agent
manager.register_agent(agent, config)

# 启动 Agent
await manager.start_agent("bot")

# 发送消息
from maagentclaw.core.agent import AgentMessage
msg = AgentMessage(content="你好", role="user")
response = await agent.process(msg)

# 停止 Agent
await manager.stop_agent("bot")
```

### 5. 协作管理

```python
from maagentclaw.managers.collaboration import (
    CollaborationManager,
    CollaborationMode
)

collab = CollaborationManager(agent_manager)

# 创建会话
session = collab.create_session(
    mode=CollaborationMode.PARALLEL,
    participants=["agent1", "agent2"]
)

# 顺序执行
results = await collab.execute_sequential(
    session.id,
    ["task1", "task2"]
)

# 并行执行
results = await collab.execute_parallel(
    session.id,
    ["task1", "task2"]
)
```

## 📝 配置文件示例

### Agent 配置 (agents.json)
```json
{
  "assistant": {
    "name": "assistant",
    "role": "assistant",
    "description": "通用助手",
    "model": "default",
    "workspace": "assistant",
    "heartbeat": {
      "every": "30m"
    }
  }
}
```

### 模型配置 (models.json)
```json
{
  "default": {
    "name": "default",
    "provider": "openai",
    "model_name": "gpt-3.5-turbo",
    "context_window": 4096
  }
}
```

### 系统配置 (system.json)
```json
{
  "workspace_base": "~/.maagentclaw/workspaces",
  "log_level": "INFO",
  "web_port": 8000,
  "enable_web_interface": true
}
```

### 渠道配置 (channels.json)
```json
{
  "default": {
    "name": "default",
    "enabled": true,
    "dm_policy": "pairing",
    "allow_from": []
  }
}
```

## 🎯 常用命令

### 测试
```bash
python test_maagentclaw.py
```

### 查看日志
```bash
# Windows
Get-Content maagentclaw\logs\*.log -Tail 50

# Linux/Mac
tail -f maagentclaw/logs/*.log
```

### 清理旧会话
```python
from maagentclaw.managers.session_manager import SessionManager

session_mgr = SessionManager("~/.maagentclaw/sessions")
count = session_mgr.cleanup_old_sessions(max_age_days=30)
print(f"清理了 {count} 个旧会话")
```

## 🔍 故障排查

### 问题 1: 配置加载失败
```python
# 检查配置文件是否存在
from pathlib import Path
config_dir = Path("~/.maagentclaw/config").expanduser()
print(config_dir.exists())

# 重新创建配置
config = EnhancedConfigManager()
config.create_default_configs()
```

### 问题 2: 工作空间不存在
```python
# 检查工作空间
from maagentclaw.managers.workspace import WorkspaceManager
workspace_mgr = WorkspaceManager()
print(workspace_mgr.list_workspaces())

# 创建工作空间
workspace = workspace_mgr.get_workspace("new_agent")
```

### 问题 3: 会话丢失
```python
# 检查会话目录
from pathlib import Path
sessions_dir = Path("~/.maagentclaw/sessions").expanduser()
print(list(sessions_dir.glob("*.jsonl")))

# 重新创建会话管理器
from maagentclaw.managers.session_manager import SessionManager
session_mgr = SessionManager("~/.maagentclaw/sessions")
```

## 📊 性能优化

### 1. 会话清理
```python
# 定期清理旧会话
session_mgr.cleanup_old_sessions(max_age_days=7)
```

### 2. 配置缓存
```python
# 使用配置快照
snapshot = config.get_config_snapshot()
```

### 3. 会话压缩
```python
# 压缩大会话
result = session_mgr.compact_session(session_id)
```

## 🔐 安全建议

### 1. DM 策略
```json
{
  "channels": {
    "default": {
      "dm_policy": "pairing",  // 或 "allowlist"
      "allow_from": ["user123"]
    }
  }
}
```

### 2. 工作空间隔离
```python
# 为不同 Agent 创建独立工作空间
workspace1 = workspace_mgr.get_workspace("agent1")
workspace2 = workspace_mgr.get_workspace("agent2")
```

### 3. 配置备份
```python
import shutil
from pathlib import Path

# 备份配置
config_dir = Path("~/.maagentclaw/config").expanduser()
shutil.make_archive("config_backup", 'zip', config_dir)
```

## 📚 学习资源

### 内部文档
- [README.md](README.md) - 项目介绍
- [USAGE.md](USAGE.md) - 使用指南
- [DEVELOPMENT.md](DEVELOPMENT.md) - 开发文档
- [OPENCLAW_LEARNING.md](OPENCLAW_LEARNING.md) - OpenClaw 学习

### 外部资源
- OpenClaw 官方文档：https://docs.openclaw.ai
- OpenClaw GitHub: https://github.com/openclaw/openclaw

## 💡 提示技巧

### 1. 快速重置 Agent
```python
# 重置会话并清空消息
session_mgr.reset_session(session_id, keep_messages=False)
```

### 2. 批量操作
```python
# 批量删除会话
for session_id in session_mgr.list_sessions():
    session_mgr.delete_session(session_id)
```

### 3. 监控配置变化
```python
# 注册配置重载回调
def on_reload():
    print("配置已重载！")

config.register_reload_callback(on_reload)
```

---

**版本**: v1.1.0  
**更新日期**: 2026-03-08  
**状态**: ✅ 活跃维护中

**MAgentClaw Team** 🦞
