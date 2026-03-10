# 工具系统（Tool System）使用指南

## 概述

工具系统是 MAgentClaw v1.3.0 的核心功能之一，提供了安全、可扩展的工具执行框架。支持工具注册、权限控制、沙箱隔离等特性。

## 核心特性

- ✅ **模块化设计** - 基于 BaseTool 抽象基类
- ✅ **权限控制** - 细粒度的权限管理
- ✅ **沙箱隔离** - 安全的工具执行环境
- ✅ **速率限制** - 防止滥用
- ✅ **分类管理** - 按类别组织工具
- ✅ **执行历史** - 完整的审计日志
- ✅ **并发控制** - 限制同时执行数

## 快速开始

### 1. 使用内置工具

```python
from pathlib import Path
from maagentclaw.managers.tool_manager import ToolManager

# 创建工具管理器
workspace_path = Path("./workspaces/my-agent")
manager = ToolManager(workspace_path)

# 执行工具
result = await manager.execute_tool(
    "json-processor",
    {"operation": "format", "json_string": '{"name":"Alice"}'}
)
print(result.data["formatted"])
```

### 2. 创建自定义工具

```python
from maagentclaw.managers.tool_manager import (
    BaseTool, ToolMetadata, ToolConfig, ToolResult, ToolPermission
)

class MyCustomTool(BaseTool):
    metadata = ToolMetadata(
        name="my-custom-tool",
        version="1.0.0",
        description="我的自定义工具",
        author="Your Name",
        category="custom",
        tags=["custom", "example"],
        permissions=[ToolPermission.READ],
        timeout=30
    )
    
    config = ToolConfig(
        enabled=True,
        sandbox_enabled=True
    )
    
    async def execute(self, **kwargs) -> ToolResult:
        # 实现工具逻辑
        return ToolResult(
            success=True,
            data={"result": "Success"}
        )

# 保存为 tools/my_custom_tool.py
```

## 内置工具

### 1. Web Search (`web-search`)

网络搜索工具（模拟）。

**权限**: NETWORK, READ

**参数**:
- `query` (str): 搜索关键词
- `num_results` (int): 结果数量，默认 5

**示例**:
```python
result = await manager.execute_tool(
    "web-search",
    {"query": "python tutorial", "num_results": 3}
)
# {"query": "python tutorial", "results": [...], "total": 3}
```

### 2. URL Fetcher (`url-fetcher`)

获取网页内容。

**权限**: NETWORK, READ

**参数**:
- `url` (str): 要抓取的 URL
- `timeout` (int, optional): 超时时间（秒）

**示例**:
```python
result = await manager.execute_tool(
    "url-fetcher",
    {"url": "https://example.com", "timeout": 30}
)
# {"url": "...", "status": 200, "content": "...", "content_type": "text/html"}
```

### 3. JSON Processor (`json-processor`)

JSON 格式化和验证。

**权限**: READ

**参数**:
- `operation` (str): 操作类型 (format, validate, parse, stringify)
- `json_string` (str): JSON 字符串（用于 format/validate/parse）
- `data` (dict): 数据（用于 stringify）

**示例**:
```python
# 格式化 JSON
result = await manager.execute_tool(
    "json-processor",
    {"operation": "format", "json_string": '{"name":"Alice","age":30}'}
)

# 验证 JSON
result = await manager.execute_tool(
    "json-processor",
    {"operation": "validate", "json_string": '{"invalid":}'}
)
```

### 4. Text Processor (`text-processor`)

文本转换和分析。

**权限**: READ

**参数**:
- `operation` (str): 操作类型
- `text` (str): 要处理的文本

**支持的操作**:
- `uppercase`: 转大写
- `lowercase`: 转小写
- `reverse`: 反转
- `word_count`: 统计词数
- `extract_emails`: 提取邮箱
- `extract_urls`: 提取 URL
- `replace`: 替换文本

**示例**:
```python
# 统计词数
result = await manager.execute_tool(
    "text-processor",
    {"operation": "word_count", "text": "Hello World"}
)

# 提取邮箱
result = await manager.execute_tool(
    "text-processor",
    {
        "operation": "extract_emails",
        "text": "Contact: test@example.com"
    }
)
```

### 5. Code Executor (`code-executor`)

安全执行 Python 代码。

**权限**: EXECUTE, ADMIN

**参数**:
- `code` (str): Python 代码
- `timeout` (int, optional): 超时时间

**示例**:
```python
code = """
x = 10
y = 20
print(f"Sum: {x + y}")
result = x * y
"""

result = await manager.execute_tool(
    "code-executor",
    {"code": code}
)
# {"stdout": "Sum: 30\n", "variables": {"x": "10", "y": "20", "result": "200"}}
```

## API 参考

### ToolMetadata

工具元数据类：

```python
@dataclass
class ToolMetadata:
    name: str                      # 工具名称
    version: str                   # 版本号
    description: str               # 描述
    author: str                    # 作者
    category: str                  # 分类
    tags: List[str]                # 标签
    permissions: List[ToolPermission]  # 权限
    timeout: int = 30              # 超时（秒）
```

### ToolPermission

工具权限枚举：

```python
class ToolPermission(Enum):
    READ = "read"              # 只读权限
    WRITE = "write"            # 写入权限
    EXECUTE = "execute"        # 执行权限
    NETWORK = "network"        # 网络访问
    FILESYSTEM = "filesystem"  # 文件系统
    ADMIN = "admin"            # 管理员
```

### ToolConfig

工具配置类：

```python
@dataclass
class ToolConfig:
    enabled: bool = True           # 是否启用
    max_concurrent: int = 10       # 最大并发数
    rate_limit: Optional[int] = None  # 速率限制
    sandbox_enabled: bool = True   # 启用沙箱
    parameters: Dict[str, Any]     # 自定义参数
```

### ToolResult

工具执行结果类：

```python
@dataclass
class ToolResult:
    success: bool                  # 是否成功
    data: Any                      # 返回数据
    error: Optional[str]           # 错误信息
    duration: Optional[float]      # 执行时长
    metadata: Dict[str, Any]       # 元数据
```

### BaseTool

工具基类（抽象类）：

```python
class BaseTool(ABC):
    metadata: ToolMetadata
    config: ToolConfig
    
    async def execute(self, **kwargs) -> ToolResult:
        """执行工具（必须实现）"""
        pass
    
    def validate_permissions(self, permissions: List[ToolPermission]) -> bool:
        """验证权限"""
        pass
```

### ToolManager

工具管理器：

```python
manager = ToolManager(workspace_path)

# 执行工具
result = await manager.execute_tool(
    "tool-name",
    {"param1": "value1"},
    user_id="user123"
)

# 设置用户权限
manager.set_user_permissions(
    "user123",
    [ToolPermission.READ, ToolPermission.NETWORK]
)

# 列出工具
tools = manager.list_tools()
categories = manager.list_categories()

# 统计信息
stats = manager.get_statistics()
```

## 权限系统

### 权限类型

| 权限 | 说明 | 需要的工具 |
|------|------|-----------|
| READ | 只读操作 | json-processor, text-processor |
| WRITE | 写入操作 | file-writer |
| EXECUTE | 执行操作 | code-executor |
| NETWORK | 网络访问 | web-search, url-fetcher |
| FILESYSTEM | 文件系统 | file-reader, file-writer |
| ADMIN | 管理员权限 | code-executor |

### 设置用户权限

```python
# 普通用户（只读）
manager.set_user_permissions(
    "user1",
    [ToolPermission.READ]
)

# 高级用户（读写 + 网络）
manager.set_user_permissions(
    "user2",
    [ToolPermission.READ, ToolPermission.WRITE, ToolPermission.NETWORK]
)

# 管理员
manager.set_user_permissions(
    "admin",
    list(ToolPermission)  # 所有权限
)
```

### 权限检查

```python
# 检查用户权限
user_perms = manager.get_user_permissions("user1")

# 工具会自动检查权限
result = await manager.execute_tool(
    "web-search",  # 需要 NETWORK 权限
    {"query": "test"},
    user_id="user1"  # 如果 user1 没有 NETWORK 权限，会失败
)
```

## 沙箱机制

### 沙箱限制

```python
class ToolSandbox:
    def __init__(self):
        self.restrictions = {
            "max_memory_mb": 256,           # 最大内存
            "max_cpu_percent": 50,          # 最大 CPU
            "max_execution_time": 30,       # 最大执行时间
            "allowed_paths": [],            # 允许的路径
            "blocked_operations": []        # 禁止的操作
        }
```

### 禁用沙箱

某些可信工具可以禁用沙箱：

```python
config = ToolConfig(
    sandbox_enabled=False  # 禁用沙箱
)
```

## 工具开发指南

### 1. 基本结构

```python
from maagentclaw.managers.tool_manager import (
    BaseTool, ToolMetadata, ToolConfig, ToolResult, ToolPermission
)

class MyTool(BaseTool):
    metadata = ToolMetadata(
        name="my-tool",
        version="1.0.0",
        description="My awesome tool",
        author="Your Name",
        category="category",
        tags=["tag1", "tag2"],
        permissions=[ToolPermission.READ],
        timeout=30
    )
    
    config = ToolConfig(
        enabled=True,
        sandbox_enabled=True
    )
    
    async def execute(self, **kwargs) -> ToolResult:
        try:
            # 实现工具逻辑
            result = await self.process(**kwargs)
            
            return ToolResult(
                success=True,
                data={"result": result},
                metadata={"info": "additional info"}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e)
            )
```

### 2. 参数验证

```python
async def execute(self, **kwargs) -> ToolResult:
    # 验证必需参数
    if "required_param" not in kwargs:
        return ToolResult(
            success=False,
            error="Missing required parameter"
        )
    
    # 验证类型
    if not isinstance(kwargs["param"], str):
        return ToolResult(
            success=False,
            error="Parameter must be a string"
        )
    
    # 验证范围
    if kwargs.get("count", 0) > 100:
        return ToolResult(
            success=False,
            error="Count cannot exceed 100"
        )
    
    # 执行逻辑
    ...
```

### 3. 使用配置

```python
class MyTool(BaseTool):
    config = ToolConfig(
        parameters={
            "api_key": "your-api-key",
            "endpoint": "https://api.example.com"
        }
    )
    
    async def execute(self, **kwargs) -> ToolResult:
        # 访问配置
        api_key = self.config.parameters["api_key"]
        
        # 使用配置执行
        result = await self.call_api(api_key)
        
        return ToolResult(success=True, data={"result": result})
```

## 最佳实践

### 1. 工具命名

使用小写字母和连字符：

```python
✅ "web-search"
✅ "json-processor"
❌ "WebSearch"
❌ "jsonProcessor"
```

### 2. 权限最小化

只申请必需的权限：

```python
# ❌ 不好的做法
permissions=[ToolPermission.READ, ToolPermission.WRITE, ToolPermission.ADMIN]

# ✅ 好的做法
permissions=[ToolPermission.READ]  # 如果只需要读取
```

### 3. 错误处理

提供清晰的错误信息：

```python
try:
    result = await self.process()
    return ToolResult(success=True, data=result)
except ValueError as e:
    return ToolResult(success=False, error=f"Validation: {e}")
except Exception as e:
    return ToolResult(success=False, error=f"Error: {e}")
```

### 4. 超时设置

根据操作类型设置合理的超时：

```python
# 快速操作
timeout=10

# 网络请求
timeout=30

# 文件处理
timeout=60
```

## 测试

运行工具测试：

```bash
# 设置环境变量
$env:PYTHONPATH="D:\pyworkplace\MAgentClaw"

# 运行测试
python test_tools.py
```

## 故障排查

### 工具未加载

1. 检查工具文件是否在 `tools/` 目录下
2. 检查文件名是否以 `.py` 结尾
3. 检查是否继承自 `BaseTool`
4. 查看错误日志

### 权限被拒绝

1. 检查用户权限：`manager.get_user_permissions(user_id)`
2. 检查工具需要的权限：`tool.metadata.permissions`
3. 确保用户权限包含工具所需的所有权限

### 沙箱错误

1. 检查沙箱限制
2. 查看执行时间是否超时
3. 检查是否使用了禁止的操作

## 与技能系统对比

| 特性 | 技能系统 | 工具系统 |
|------|----------|----------|
| 用途 | 复杂任务 | 简单操作 |
| 执行时间 | 较长 | 较短 |
| 权限控制 | 简单 | 完善 |
| 沙箱 | 无 | 有 |
| 并发 | 低 | 高 |
| 状态 | 有状态 | 无状态 |

## 版本历史

### v1.3.0 (2026-03-08)

- ✅ 初始版本
- ✅ 工具注册表
- ✅ 权限控制系统
- ✅ 沙箱机制
- ✅ 5 个内置工具
- ✅ 完整的 API 文档

## 参考资料

- [MAgentClaw 开发计划](DEVELOPMENT_PLAN.md)
- [工具管理器源码](maagentclaw/managers/tool_manager.py)
- [内置工具目录](maagentclaw/tools/)
- [技能系统指南](SKILLS_GUIDE.md)
