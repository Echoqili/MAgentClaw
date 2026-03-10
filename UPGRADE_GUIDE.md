# MAgentClaw 升级指南

## 从 v1.2.0 升级到 v1.3.0

### 新增功能

v1.3.0 引入了三个核心功能：

1. **心跳机制** - 周期性任务调度
2. **技能系统** - 可扩展的技能框架
3. **工具系统** - 安全的工具执行

### 升级步骤

#### 1. 备份现有配置

```bash
# 备份工作空间
cp -r workspaces/ workspaces.backup/

# 备份配置文件
cp config/*.json config.backup/
```

#### 2. 更新代码

```bash
# 如果使用 Git
git pull origin main

# 或者重新克隆
git clone https://github.com/your-org/MAgentClaw.git
cd MAgentClaw
```

#### 3. 更新依赖

```bash
# 更新 pip 包
pip install --upgrade -r requirements.txt

# 或者从 PyPI 安装
pip install --upgrade maagentclaw
```

#### 4. 验证安装

```bash
# 运行测试
python test_heartbeat.py
python test_skills.py
python test_tools.py

# 检查版本
python -c "import maagentclaw; print(maagentclaw.__version__)"
```

### 配置变更

#### 1. 工作空间结构

v1.3.0 新增了以下目录：

```
workspaces/
  your-agent/
    HEARTBEAT.md      # 新增：心跳任务配置
    skills/           # 新增：自定义技能
    tools/            # 新增：自定义工具
    AGENTS.md
    SOUL.md
    TOOLS.md
```

#### 2. 配置文件

无需修改现有配置文件，v1.3.0 完全向后兼容。

### 使用新功能

#### 1. 心跳机制

创建工作空间中的 `HEARTBEAT.md`：

```markdown
# Heartbeat Tasks

## Task: health-check
- Interval: 60
- Command: check-health
- Enabled: true

## Task: data-sync
- Interval: 300
- Command: sync-data
- Enabled: true
```

#### 2. 技能系统

创建自定义技能 `skills/my_skill.py`：

```python
from maagentclaw.managers.skill_manager import (
    BaseSkill, SkillMetadata, SkillConfig, SkillResult
)

class MySkill(BaseSkill):
    metadata = SkillMetadata(
        name="my-skill",
        version="1.0.0",
        description="My custom skill",
        author="Your Name",
        category="custom"
    )
    
    async def execute(self, **kwargs) -> SkillResult:
        return SkillResult(success=True, data={"result": "Success"})
```

#### 3. 工具系统

创建自定义工具 `tools/my_tool.py`：

```python
from maagentclaw.managers.tool_manager import (
    BaseTool, ToolMetadata, ToolConfig, ToolResult, ToolPermission
)

class MyTool(BaseTool):
    metadata = ToolMetadata(
        name="my-tool",
        version="1.0.0",
        description="My custom tool",
        author="Your Name",
        category="custom",
        permissions=[ToolPermission.READ]
    )
    
    async def execute(self, **kwargs) -> ToolResult:
        return ToolResult(success=True, data={"result": "Success"})
```

### API 变更

#### 新增管理器

```python
from maagentclaw.managers import (
    HeartbeatManager,
    SkillManager,
    ToolManager
)

# 心跳管理器
heartbeat = HeartbeatManager(workspace_path)

# 技能管理器
skills = SkillManager(workspace_path)

# 工具管理器
tools = ToolManager(workspace_path)
```

#### 增强的 Web 界面

v1.3.0 的 Web 界面新增了以下端点：

```python
# 心跳管理
GET  /api/heartbeat/tasks
POST /api/heartbeat/tasks
DELETE /api/heartbeat/tasks/{name}

# 技能管理
GET  /api/skills
POST /api/skills/{name}/execute

# 工具管理
GET  /api/tools
POST /api/tools/{name}/execute
```

### 迁移示例

#### 旧代码（v1.2.0）

```python
from maagentclaw.main_enhanced import EnhancedAgent

agent = EnhancedAgent()
agent.start()
```

#### 新代码（v1.3.0）

```python
from maagentclaw.main_enhanced import EnhancedAgent
from maagentclaw.managers import SkillManager, ToolManager, HeartbeatManager

# 创建 Agent
agent = EnhancedAgent()

# 获取管理器
skill_mgr = SkillManager(agent.workspace_path)
tool_mgr = ToolManager(agent.workspace_path)
heartbeat_mgr = HeartbeatManager(agent.workspace_path)

# 启动心跳
await heartbeat_mgr.start()

# 使用技能
result = skill_mgr.execute_skill("hello-world", name="Alice")

# 使用工具
result = await tool_mgr.execute_tool(
    "json-processor",
    {"operation": "format", "json_string": '{}'}
)

agent.start()
```

### 性能影响

v1.3.0 的新功能对性能的影响：

- **心跳机制**: 轻微（后台异步任务）
- **技能系统**: 轻微（按需加载）
- **工具系统**: 中等（沙箱隔离）

### 已知问题

#### 1. 工具沙箱在某些系统上可能不工作

**解决方案**: 禁用沙箱

```python
config = ToolConfig(sandbox_enabled=False)
```

#### 2. 技能加载顺序不确定

**解决方案**: 使用明确的技能名称

```python
# 不要依赖加载顺序
skill = skill_mgr.get_skill("my-skill")  # ✓ 正确
```

### 常见问题

#### Q: 升级后现有功能还能用吗？

A: 是的，v1.3.0 完全向后兼容 v1.2.0。

#### Q: 需要修改现有代码吗？

A: 不需要，新功能都是可选的。

#### Q: 如何禁用新功能？

A: 在配置中设置：

```python
config = {
    "heartbeat_enabled": False,
    "skills_enabled": False,
    "tools_enabled": False
}
```

#### Q: 数据会丢失吗？

A: 不会，所有现有数据都保持不变。

### 回滚

如果需要回滚到 v1.2.0：

```bash
# 使用 Git
git checkout v1.2.0

# 或者重新安装旧版本
pip install maagentclaw==1.2.0
```

### 获取帮助

- **文档**: https://maagentclaw.readthedocs.io
- **Issues**: https://github.com/your-org/MAgentClaw/issues
- **讨论**: https://github.com/your-org/MAgentClaw/discussions

---

**最后更新**: 2026 年 3 月 8 日  
**维护者**: MAgentClaw Team
