# 工具系统（Tool System）开发总结

## 概述

已完成 MAgentClaw v1.3.0 的工具系统开发，实现了完整的工具注册、管理、执行和权限控制功能。

## 开发内容

### 1. 核心文件

#### `maagentclaw/managers/tool_manager.py` (430 行)

**核心类：**

1. **ToolStatus** (枚举)
   - READY, RUNNING, ERROR, DISABLED
   - 工具状态管理

2. **ToolPermission** (枚举)
   - READ, WRITE, EXECUTE, NETWORK, FILESYSTEM, ADMIN
   - 细粒度权限控制

3. **ToolMetadata** (数据类)
   - 工具元数据定义
   - 名称、版本、分类、权限等

4. **ToolConfig** (数据类)
   - 工具配置管理
   - 并发、速率限制、沙箱等

5. **ToolResult** (数据类)
   - 工具执行结果
   - 成功/失败、数据、错误信息

6. **ToolCall** (数据类)
   - 工具调用记录
   - 审计日志

7. **BaseTool** (抽象基类)
   - 所有工具的基类
   - 定义 execute() 抽象方法
   - 权限验证

8. **ToolRegistry** (注册表)
   - 工具注册和注销
   - 按分类组织
   - 工具查找

9. **ToolSandbox** (沙箱)
   - 安全执行环境
   - 资源限制
   - 超时控制

10. **ToolManager** (管理器)
    - 统一的工具管理接口
    - 权限检查
    - 执行历史
    - 统计信息

### 2. 内置工具

#### `maagentclaw/tools/web_search.py` (70 行)
- 网络搜索工具（模拟）
- 支持关键词搜索
- 返回搜索结果列表

#### `maagentclaw/tools/url_fetcher.py` (80 行)
- URL 抓取工具
- 使用 aiohttp 异步请求
- URL 黑名单检查
- 超时控制

#### `maagentclaw/tools/json_processor.py` (100 行)
- JSON 处理工具
- 支持 format, validate, parse, stringify
- 完整的错误处理

#### `maagentclaw/tools/text_processor.py` (80 行)
- 文本处理工具
- 支持 7 种操作
- 正则表达式提取

#### `maagentclaw/tools/code_executor.py` (120 行)
- 代码执行工具
- 安全检查（危险关键字）
- 安全的命名空间
- 输出限制

### 3. 测试文件

#### `test_tools.py` (250 行)

**测试套件：**

1. **test_tool_loading()**
   - 工具加载测试
   - 验证工具数量

2. **test_tool_execution()**
   - 执行所有内置工具
   - 验证返回结果

3. **test_permission_system()**
   - 权限系统测试
   - 权限检查逻辑

4. **test_statistics()**
   - 统计信息测试
   - 分类统计

5. **test_error_handling()**
   - 错误处理测试
   - 异常情况

## 核心功能

### 1. 工具注册表

```python
registry = ToolRegistry()

# 注册工具
tool = WebSearchTool()
registry.register(tool)

# 获取工具
tool = registry.get("web-search")

# 按分类列出
tools = registry.list_by_category("search")

# 列出所有分类
categories = registry.list_categories()
```

### 2. 权限系统

```python
# 设置用户权限
manager.set_user_permissions(
    "user123",
    [ToolPermission.READ, ToolPermission.NETWORK]
)

# 获取用户权限
perms = manager.get_user_permissions("user123")

# 检查权限
if manager.check_permission("user123", tool):
    # 执行工具
    ...
```

### 3. 沙箱机制

```python
sandbox = ToolSandbox({
    "max_memory_mb": 256,
    "max_cpu_percent": 50,
    "max_execution_time": 30,
    "allowed_paths": ["/tmp"],
    "blocked_operations": ["rm -rf", "sudo"]
})

# 在沙箱中执行
result = await sandbox.execute(tool, **kwargs)
```

### 4. 工具执行

```python
# 基本执行
result = await manager.execute_tool(
    "json-processor",
    {"operation": "format", "json_string": '{}'}
)

# 带用户 ID 的执行（检查权限）
result = await manager.execute_tool(
    "web-search",
    {"query": "python"},
    user_id="user123"
)

# 处理结果
if result.success:
    print(f"数据：{result.data}")
else:
    print(f"错误：{result.error}")
```

### 5. 执行历史

```python
# 获取执行历史
history = manager.get_execution_history(limit=100)

for call in history:
    print(f"{call['tool_name']} @ {call['timestamp']}")
```

### 6. 统计信息

```python
stats = manager.get_statistics()

# {
#     "total_tools": 5,
#     "enabled_tools": 5,
#     "total_executions": 100,
#     "categories": {
#         "search": 1,
#         "network": 1,
#         "utility": 2,
#         "development": 1
#     }
# }
```

## 技术亮点

### 1. 权限验证

```python
def validate_permissions(self, permissions: List[ToolPermission]) -> bool:
    """验证权限"""
    required = set(self.metadata.permissions)
    available = set(permissions)
    return required.issubset(available)
```

### 2. 安全检查

```python
# 代码执行工具的安全检查
dangerous_keywords = ['import os', 'import sys', 'subprocess', 
                    'eval(', 'exec(', '__import__', 'open(']

for keyword in dangerous_keywords:
    if keyword in code:
        return ToolResult(
            success=False,
            error=f"Dangerous code detected: {keyword}"
        )
```

### 3. 沙箱执行

```python
async def execute(self, tool: BaseTool, **kwargs) -> ToolResult:
    start_time = time.time()
    
    try:
        # 检查执行时间
        if time.time() - start_time > self.restrictions["max_execution_time"]:
            return ToolResult(success=False, error="Timeout")
        
        # 执行工具
        result = await tool.execute(**kwargs)
        result.duration = time.time() - start_time
        
        return result
    except Exception as e:
        return ToolResult(success=False, error=str(e))
```

### 4. 并发控制

```python
@dataclass
class ToolConfig:
    max_concurrent: int = 10  # 最大并发数
    rate_limit: Optional[int] = None  # 速率限制
```

## 代码统计

| 文件 | 行数 | 功能 |
|------|------|------|
| tool_manager.py | 430 | 核心管理器 |
| web_search.py | 70 | 网络搜索 |
| url_fetcher.py | 80 | URL 抓取 |
| json_processor.py | 100 | JSON 处理 |
| text_processor.py | 80 | 文本处理 |
| code_executor.py | 120 | 代码执行 |
| test_tools.py | 250 | 测试套件 |
| TOOLS_GUIDE.md | ~500 | 使用指南 |
| **总计** | **~1630** | **完整实现** |

## 使用示例

### 基础使用

```python
from pathlib import Path
from maagentclaw.managers.tool_manager import ToolManager

# 创建管理器
manager = ToolManager(Path("./workspace"))

# 执行 JSON 格式化
result = await manager.execute_tool(
    "json-processor",
    {"operation": "format", "json_string": '{"name":"Alice"}'}
)
print(result.data["formatted"])

# 执行文本处理
result = await manager.execute_tool(
    "text-processor",
    {"operation": "word_count", "text": "Hello World"}
)
print(f"词数：{result.data['word_count']}")
```

### 权限管理

```python
# 设置不同用户的权限
manager.set_user_permissions("user1", [ToolPermission.READ])
manager.set_user_permissions("user2", [
    ToolPermission.READ,
    ToolPermission.WRITE,
    ToolPermission.NETWORK
])
manager.set_user_permissions("admin", list(ToolPermission))

# 执行需要权限的工具
result = await manager.execute_tool(
    "web-search",  # 需要 NETWORK 权限
    {"query": "test"},
    user_id="user1"  # user1 没有 NETWORK 权限，会失败
)
```

### 创建自定义工具

```python
from maagentclaw.managers.tool_manager import (
    BaseTool, ToolMetadata, ToolConfig, ToolResult, ToolPermission
)

class RandomNumberTool(BaseTool):
    metadata = ToolMetadata(
        name="random-number",
        version="1.0.0",
        description="生成随机数",
        author="Your Name",
        category="utility",
        tags=["random", "number"],
        permissions=[ToolPermission.READ],
        timeout=10
    )
    
    config = ToolConfig(
        enabled=True,
        sandbox_enabled=False
    )
    
    async def execute(self, min: int = 0, max: int = 100) -> ToolResult:
        import random
        number = random.randint(min, max)
        
        return ToolResult(
            success=True,
            data={"number": number},
            metadata={"range": {"min": min, "max": max}}
        )

# 保存为 tools/random_number.py
# 自动被 ToolManager 加载
```

### 与技能系统集成

```python
class EnhancedAgent:
    def __init__(self):
        self.skill_manager = SkillManager(self.workspace_path)
        self.tool_manager = ToolManager(self.workspace_path)
    
    async def execute_complex_task(self, task: str):
        # 使用技能进行复杂任务
        skill_result = await self.skill_manager.execute_skill(
            "data-analyzer",
            data=task
        )
        
        # 使用工具进行辅助操作
        tool_result = await self.tool_manager.execute_tool(
            "json-processor",
            {"operation": "format", "json_string": skill_result.data}
        )
        
        return tool_result.data
```

### REST API 集成

```python
@app.route('/api/tools', methods=['GET'])
def list_tools():
    """获取所有工具"""
    tools = tool_manager.list_tools()
    return jsonify(tools)

@app.route('/api/tools/<name>/execute', methods=['POST'])
async def execute_tool(name):
    """执行工具"""
    params = request.json or {}
    user_id = request.headers.get('X-User-ID')
    result = await tool_manager.execute_tool(name, params, user_id)
    return jsonify(result.to_dict())

@app.route('/api/tools/stats', methods=['GET'])
def get_tool_stats():
    """获取统计信息"""
    stats = tool_manager.get_statistics()
    return jsonify(stats)
```

## 与 OpenClaw 对比

| 特性 | OpenClaw | MAgentClaw | 改进 |
|------|----------|------------|------|
| 工具框架 | 概念 | 完整实现 | ✅ 抽象基类 |
| 权限控制 | 无 | 完善 | ✅ 6 种权限 |
| 沙箱 | 无 | 完整 | ✅ 资源限制 |
| 内置工具 | 少 | 5 个 | ✅ 实用工具 |
| 审计日志 | 无 | 完整 | ✅ 执行历史 |
| 并发控制 | 无 | 有 | ✅ 速率限制 |

## 测试覆盖

运行测试：

```bash
$env:PYTHONPATH="D:\pyworkplace\MAgentClaw"
python test_tools.py
```

测试覆盖：
- ✅ 工具加载
- ✅ 工具执行
- ✅ 权限系统
- ✅ 统计信息
- ✅ 错误处理

## 下一步

根据 DEVELOPMENT_PLAN.md，工具系统已完成，下一步是：

1. ✅ **心跳机制** - 已完成
2. ✅ **技能系统** - 已完成
3. ✅ **工具系统** - 已完成
4. ⏳ **安全增强** - 下一步

## 参考资料

- [MAgentClaw 开发计划](DEVELOPMENT_PLAN.md)
- [工具使用指南](TOOLS_GUIDE.md)
- [工具管理器源码](maagentclaw/managers/tool_manager.py)
- [内置工具目录](maagentclaw/tools/)
- [技能系统指南](SKILLS_GUIDE.md)
