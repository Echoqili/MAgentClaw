# MAgentClaw 开发文档

## 项目概述

MAgentClaw 是一个基于 OpenClaw 和 CoClaw 架构设计的多 Agent 管理与协作系统。

## 技术架构

### 核心模块

#### 1. Core (核心层)
- **agent.py**: Agent 基类和核心数据结构
  - `BaseAgent`: 所有 Agent 的抽象基类
  - `AgentConfig`: Agent 配置数据类
  - `AgentMessage`: Agent 消息数据类
  - `AgentState`: Agent 状态数据类

#### 2. Managers (管理层)
- **agent_manager.py**: Agent 生命周期管理
  - 注册/注销 Agent
  - 启动/停止 Agent
  - 消息路由
  - 状态监控

- **collaboration.py**: 多 Agent 协作
  - `TaskCoordinator`: 任务协调器
  - `CollaborationManager`: 协作会话管理
  - 支持多种协作模式（顺序、并行、层级）

#### 3. Config (配置层)
- **config_manager.py**: 配置管理
  - Agent 配置管理
  - 模型配置管理
  - 系统配置管理

#### 4. Interfaces (接口层)
- **web_interface.py**: Web 管理界面
  - RESTful API
  - Flask Web 服务器
  - 实时监控界面

#### 5. Agents (Agent 实现)
- **examples.py**: 示例 Agent
  - `SimpleAgent`: 简单对话 Agent
  - `TaskAgent`: 任务执行 Agent
  - `CoordinatorAgent`: 协调器 Agent

#### 6. Utils (工具)
- **helpers.py**: 通用工具函数
  - 日志设置
  - 重试装饰器
  - 超时控制
  - 错误处理

## 数据流

### 消息处理流程

```
用户输入
  │
  ▼
Web Interface
  │
  ▼
Agent Manager (路由)
  │
  ▼
Target Agent
  │
  ├─► Memory (存储历史)
  ├─► Tools (调用工具)
  └─► Model (生成响应)
  │
  ▼
Agent Manager
  │
  ▼
Web Interface
  │
  ▼
用户接收
```

### 任务执行流程

```
任务创建
  │
  ▼
Collaboration Manager
  │
  ├─► Task Coordinator (任务分解)
  │       │
  │       ├─► 依赖检查
  │       └─► 优先级排序
  │
  ├─► Agent Selection (Agent 选择)
  │       │
  │       ├─► 能力匹配
  │       └─► 负载均衡
  │
  └─► Execution (执行)
          │
          ├─► Sequential (顺序)
          ├─► Parallel (并行)
          └─► Hierarchical (层级)
          │
          ▼
      结果聚合
```

## API 设计

### RESTful API 规范

#### Agent 管理

```
GET    /api/agents              # 获取所有 Agent
GET    /api/agents/:name        # 获取指定 Agent
POST   /api/agents/:name/start  # 启动 Agent
POST   /api/agents/:name/stop   # 停止 Agent
POST   /api/agents/:name/message # 发送消息
```

#### 配置管理

```
GET    /api/config/agents       # 获取 Agent 配置
POST   /api/config/agents       # 创建 Agent 配置
GET    /api/config/models       # 获取模型配置
POST   /api/config/models       # 创建模型配置
```

#### 任务管理

```
POST   /api/tasks               # 创建任务
GET    /api/tasks/:id           # 获取任务状态
POST   /api/sessions            # 创建协作会话
POST   /api/sessions/:id/execute # 执行会话任务
```

### 响应格式

成功响应:
```json
{
  "success": true,
  "data": {...},
  "message": "操作成功"
}
```

错误响应:
```json
{
  "success": false,
  "error": "错误信息",
  "code": "ERROR_CODE"
}
```

## 扩展开发

### 创建自定义 Agent

```python
from maagentclaw.core.agent import BaseAgent, AgentConfig, AgentMessage

class CustomAgent(BaseAgent):
    async def initialize(self) -> bool:
        # 1. 初始化模型
        # 2. 加载工具
        # 3. 设置配置
        return True
    
    async def process(self, message: AgentMessage) -> AgentMessage:
        # 1. 解析用户输入
        # 2. 查询记忆
        # 3. 调用模型
        # 4. 生成响应
        return AgentMessage(content="响应", role="assistant")
    
    async def execute_task(self, task: str, context=None):
        # 1. 分析任务
        # 2. 执行步骤
        # 3. 返回结果
        return {"result": "完成"}
```

### 添加新工具

```python
def register_tools(agent: BaseAgent):
    """注册工具到 Agent"""
    
    # 搜索工具
    async def search(query: str) -> list:
        # 实现搜索逻辑
        return results
    
    agent.register_tool("search", search)
    
    # 计算工具
    def calculate(expression: str) -> float:
        # 实现计算逻辑
        return result
    
    agent.register_tool("calculate", calculate)
```

### 集成新模型

```python
class NewModelAgent(BaseAgent):
    async def initialize(self) -> bool:
        # 配置新模型
        self.model_client = NewModelClient(
            api_key=self.config.api_key,
            model=self.config.model_name
        )
        return True
    
    async def process(self, message: AgentMessage) -> AgentMessage:
        # 使用新模型生成响应
        response = await self.model_client.generate(
            prompt=message.content,
            temperature=self.config.temperature
        )
        return AgentMessage(content=response, role="assistant")
```

## 数据库设计

### Agent 配置表 (agents)

| 字段 | 类型 | 说明 |
|------|------|------|
| name | VARCHAR | Agent 名称 (主键) |
| role | VARCHAR | 角色 |
| description | TEXT | 描述 |
| model | VARCHAR | 使用模型 |
| workspace | VARCHAR | 工作空间 |
| config | JSON | 完整配置 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### 任务表 (tasks)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR | 任务 ID (主键) |
| description | TEXT | 任务描述 |
| status | VARCHAR | 状态 |
| assigned_to | VARCHAR | 执行 Agent |
| result | JSON | 执行结果 |
| created_at | DATETIME | 创建时间 |
| completed_at | DATETIME | 完成时间 |

### 会话表 (sessions)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR | 会话 ID (主键) |
| mode | VARCHAR | 协作模式 |
| participants | JSON | 参与者列表 |
| status | VARCHAR | 会话状态 |
| context | JSON | 上下文 |
| created_at | DATETIME | 创建时间 |

## 安全性

### API 安全

1. **认证**: 实现 API Key 认证
2. **授权**: 基于角色的访问控制
3. **限流**: 防止 API 滥用
4. **审计**: 记录所有操作日志

### 数据安全

1. **加密**: 敏感数据加密存储
2. **脱敏**: 日志中脱敏敏感信息
3. **备份**: 定期备份配置和数据

## 性能优化

### 异步处理

- 所有 IO 操作使用异步
- 使用 asyncio 管理并发
- 实现连接池

### 缓存策略

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_agent_config(name: str) -> AgentConfig:
    # 缓存 Agent 配置
    return config
```

### 负载均衡

```python
class LoadBalancer:
    def select_agent(self, agents: list) -> str:
        # 基于当前负载选择 Agent
        min_load = float('inf')
        selected = None
        
        for agent in agents:
            load = self.get_agent_load(agent)
            if load < min_load:
                min_load = load
                selected = agent
        
        return selected
```

## 测试策略

### 单元测试

```python
import unittest
import asyncio

class TestAgent(unittest.TestCase):
    async def test_message_processing(self):
        agent = SimpleAgent(config)
        await agent.initialize()
        
        message = AgentMessage(content="test")
        response = await agent.process(message)
        
        self.assertIsNotNone(response.content)
```

### 集成测试

```python
async def test_collaboration():
    manager = AgentManager()
    collab_manager = CollaborationManager(manager)
    
    # 创建多个 Agent
    # 执行协作任务
    # 验证结果
```

### 性能测试

```python
import time

async def performance_test():
    start = time.time()
    
    # 执行大量任务
    tasks = [execute_task(f"task_{i}") for i in range(100)]
    await asyncio.gather(*tasks)
    
    elapsed = time.time() - start
    print(f"执行 100 个任务耗时：{elapsed:.2f}s")
```

## 部署指南

### 本地开发

```bash
# 安装依赖
pip install -r requirements.txt

# 运行测试
python test_maagentclaw.py

# 启动服务
python maagentclaw/main.py
```

### Docker 部署

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "maagentclaw/main.py"]
```

### 生产环境

1. **配置管理**: 使用环境变量或配置文件
2. **日志管理**: 集中式日志收集
3. **监控告警**: Prometheus + Grafana
4. **负载均衡**: Nginx 反向代理

## 版本历史

### v1.0.0 (2026-03-08)
- ✅ 核心 Agent 框架
- ✅ Agent 管理器
- ✅ 协作框架
- ✅ Web 管理界面
- ✅ 配置管理
- ✅ 示例 Agent
- ✅ 测试套件

### 规划中
- [ ] 数据库持久化
- [ ] API 认证
- [ ] 更多 Agent 实现
- [ ] 技能市场
- [ ] 可视化编排
- [ ] 分布式支持

## 贡献指南

1. Fork 项目
2. 创建特性分支
3. 提交变更
4. 推送到分支
5. 创建 Pull Request

## 许可证

MIT License
