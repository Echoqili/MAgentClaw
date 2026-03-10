# 心跳机制（Heartbeat）开发总结

## 概述

已完成 MAgentClaw v1.3.0 的心跳机制开发，实现了完整的周期性任务调度和状态监控功能。

## 开发内容

### 1. 核心文件

#### `maagentclaw/managers/heartbeat_manager.py` (442 行)

**核心类：**

1. **TaskStatus** (枚举)
   - PENDING, RUNNING, COMPLETED, FAILED, SKIPPED
   - 任务状态管理

2. **HeartbeatTask** (数据类)
   - 任务定义和状态跟踪
   - 支持序列化和反序列化
   - 执行历史记录

3. **HeartbeatConfig** (数据类)
   - 心跳配置管理
   - 支持重试、超时、抑制等配置

4. **HeartbeatParser** (解析器)
   - HEARTBEAT.md 文件解析
   - 正则表达式匹配任务块
   - 属性自动类型转换

5. **HeartbeatManager** (管理器)
   - 任务生命周期管理
   - 心跳循环调度
   - 执行抑制逻辑
   - 错误处理和重试
   - 统计和历史记录

### 2. 测试文件

#### `test_heartbeat.py` (270 行)

**测试套件：**

1. **test_basic_functionality()**
   - 基本功能测试
   - HEARTBEAT.md 解析
   - 任务加载和查询

2. **test_task_management()**
   - 添加/移除任务
   - 启用/禁用任务

3. **test_heartbeat_loop()**
   - 心跳循环测试
   - 实际执行验证
   - 统计信息检查

4. **test_suppression_logic()**
   - 抑制逻辑验证
   - 防止重复执行

5. **test_error_handling()**
   - 错误处理测试
   - 自动重试机制

### 3. 文档

#### `HEARTBEAT_GUIDE.md` (完整使用指南)

**内容：**
- 概述和特性
- 快速开始指南
- HEARTBEAT.md 文件格式
- API 完整参考
- 心跳抑制逻辑详解
- 错误处理和重试策略
- 执行回调示例
- 监控和告警
- 最佳实践
- 故障排查

## 核心功能

### 1. 周期性任务调度

```python
# 定义任务
task = HeartbeatTask(
    name="health-check",
    interval=60,        # 60 秒执行一次
    command="check-health",
    enabled=True
)

# 自动调度
manager.add_task(task)
await manager.start()  # 自动按间隔执行
```

### 2. HEARTBEAT.md 文件格式

```markdown
# Heartbeat Tasks

## Task: health-check
- Interval: 60
- Command: check-health --service=all
- Enabled: true

## Task: data-sync
- Interval: 300
- Command: sync-data --source=db --target=cache
- Enabled: true
```

### 3. 心跳抑制逻辑

防止任务重复执行的机制：

```python
def _should_suppress(self, task: HeartbeatTask) -> bool:
    # 1. 运行中抑制
    if task.status == TaskStatus.RUNNING:
        return True
    
    # 2. 时间间隔抑制
    if task.name in self._last_execution:
        elapsed = (datetime.now() - self._last_execution[task.name]).total_seconds()
        if elapsed < task.interval * 0.5:  # 至少间隔 50%
            return True
    
    return False
```

### 4. 错误处理和重试

```python
try:
    # 执行任务
    result = await self.execution_callback(command, metadata)
    task.status = TaskStatus.COMPLETED
    task.execution_count += 1
except Exception as e:
    task.status = TaskStatus.FAILED
    task.failure_count += 1
    
    # 重试逻辑
    if task.failure_count < self.config.max_retries:
        task.next_run = datetime.now() + timedelta(seconds=self.config.retry_delay)
    else:
        task.next_run = datetime.now() + timedelta(seconds=task.interval)
```

### 5. 状态监控

```python
# 获取任务状态
status = manager.get_task_status("health-check")

# 获取统计信息
stats = manager.get_statistics()
# {
#     "total_tasks": 5,
#     "enabled_tasks": 4,
#     "running_tasks": 1,
#     "failed_tasks": 0,
#     "total_executions": 120,
#     "total_failures": 2,
#     "success_rate": 98.33
# }

# 获取执行历史
history = manager.get_execution_history(limit=100)
```

## 技术亮点

### 1. 异步编程

完全基于 asyncio 实现：

```python
async def _heartbeat_loop(self):
    """心跳循环"""
    while self.running:
        # 检查并执行到期的任务
        for task in self.tasks.values():
            if task.enabled and task.next_run <= datetime.now():
                await self._execute_task(task)
        
        # 等待下一次心跳
        await asyncio.sleep(self.config.interval)
```

### 2. 回调机制

灵活的任务执行回调：

```python
async def execute_task(command, metadata):
    # 可以是：
    # - 技能调用
    # - HTTP 请求
    # - 数据库操作
    # - 文件处理
    pass

manager = HeartbeatManager(
    workspace_path,
    config,
    execution_callback=execute_task
)
```

### 3. 状态持久化

自动保存任务状态到 HEARTBEAT.md：

```python
def save_tasks(self):
    content = "# Heartbeat Tasks\n\n"
    content += f"**Last Updated**: {datetime.now().isoformat()}\n\n"
    
    for task in self.tasks.values():
        content += f"## Task: {task.name}\n\n"
        content += f"- **Status**: {task.status.value}\n"
        content += f"- **Last Run**: {task.last_run.isoformat()}\n"
        # ... 更多属性
    
    self.heartbeat_file.write_text(content)
```

## 代码统计

| 文件 | 行数 | 功能 |
|------|------|------|
| heartbeat_manager.py | 442 | 核心管理器 |
| test_heartbeat.py | 270 | 测试套件 |
| HEARTBEAT_GUIDE.md | ~400 | 使用指南 |
| **总计** | **~1112** | **完整实现** |

## 使用示例

### 基础使用

```python
from pathlib import Path
from maagentclaw.managers.heartbeat_manager import (
    HeartbeatManager,
    HeartbeatConfig
)

# 配置
config = HeartbeatConfig(
    interval=60,
    max_retries=3,
    suppress_duplicates=True
)

# 管理器
manager = HeartbeatManager(
    workspace_path=Path("./workspace"),
    config=config,
    execution_callback=my_executor
)

# 启动
await manager.start()
```

### 与 Agent 集成

```python
class EnhancedAgent:
    def __init__(self):
        self.heartbeat_manager = HeartbeatManager(
            self.workspace_path,
            self.config,
            execution_callback=self.execute_skill
        )
    
    async def start(self):
        await self.heartbeat_manager.start()
    
    async def stop(self):
        await self.heartbeat_manager.stop()
```

### REST API 集成

```python
@app.route('/api/heartbeat/tasks', methods=['GET'])
def get_heartbeat_tasks():
    """获取所有心跳任务"""
    tasks = heartbeat_manager.get_all_tasks()
    return jsonify(tasks)

@app.route('/api/heartbeat/stats', methods=['GET'])
def get_heartbeat_stats():
    """获取心跳统计"""
    stats = heartbeat_manager.get_statistics()
    return jsonify(stats)

@app.route('/api/heartbeat/tasks/<name>/enable', methods=['POST'])
def enable_task(name):
    """启用任务"""
    heartbeat_manager.enable_task(name)
    return jsonify({"status": "success"})
```

## 与 OpenClaw 对比

| 特性 | OpenClaw | MAgentClaw | 改进 |
|------|----------|------------|------|
| 文件格式 | HEARTBEAT.md | HEARTBEAT.md | ✅ 保持一致 |
| 任务调度 | 基础 | 增强 | ✅ 支持重试 |
| 抑制逻辑 | 无 | 完整 | ✅ 新增 |
| 错误处理 | 简单 | 完善 | ✅ 自动重试 |
| 状态监控 | 有限 | 完整 | ✅ 历史记录 |
| API | 无 | RESTful | ✅ 新增 |

## 测试覆盖

运行测试：

```bash
$env:PYTHONPATH="D:\pyworkplace\MAgentClaw"
python test_heartbeat.py
```

测试覆盖：
- ✅ 基本功能
- ✅ 任务管理
- ✅ 心跳循环
- ✅ 抑制逻辑
- ✅ 错误处理

## 下一步

根据 DEVELOPMENT_PLAN.md，心跳机制已完成，下一步是：

1. ✅ **心跳机制** - 已完成
2. ⏳ **技能系统** - 下一步
3. ⏳ **工具系统** - 待完成
4. ⏳ **安全增强** - 待完成

## 参考资料

- [OpenClaw 项目](https://gitee.com/openclaw/openclaw)
- [MAgentClaw 开发计划](DEVELOPMENT_PLAN.md)
- [心跳使用指南](HEARTBEAT_GUIDE.md)
- [心跳管理器源码](maagentclaw/managers/heartbeat_manager.py)
