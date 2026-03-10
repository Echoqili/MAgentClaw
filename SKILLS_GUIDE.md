# 技能系统（Skill System）使用指南

## 概述

技能系统是 MAgentClaw v1.3.0 的核心功能之一，提供了灵活、可扩展的技能框架。参考了 OpenClaw 项目的设计理念，支持内置技能、自定义技能、技能市场等多种技能来源。

## 核心特性

- ✅ **模块化设计** - 基于 BaseSkill 抽象基类
- ✅ **动态加载** - 自动从目录加载技能
- ✅ **技能注册表** - 统一的技能管理
- ✅ **技能市场** - 支持在线技能安装
- ✅ **类型安全** - 完整的类型注解
- ✅ **异步执行** - 基于 asyncio 的高性能执行
- ✅ **错误处理** - 完善的异常处理机制
- ✅ **元数据支持** - 丰富的技能信息

## 快速开始

### 1. 使用内置技能

```python
from pathlib import Path
from maagentclaw.managers.skill_manager import SkillManager

# 创建技能管理器
workspace_path = Path("./workspaces/my-agent")
manager = SkillManager(workspace_path)

# 执行技能
result = manager.execute_skill("hello-world", name="Alice")
print(result.data["message"])  # Hello, Alice!
```

### 2. 创建自定义技能

```python
from maagentclaw.managers.skill_manager import (
    BaseSkill, SkillMetadata, SkillConfig, SkillResult
)

class MyCustomSkill(BaseSkill):
    metadata = SkillMetadata(
        name="my-custom-skill",
        version="1.0.0",
        description="我的自定义技能",
        author="Your Name",
        email="your@email.com",
        tags=["custom", "example"],
        category="custom"
    )
    
    config = SkillConfig(
        enabled=True,
        timeout=30
    )
    
    async def execute(self, **kwargs) -> SkillResult:
        # 实现技能逻辑
        return SkillResult(
            success=True,
            data={"result": "Success"}
        )

# 保存为 skills/my_custom.py
```

### 3. 加载自定义技能

将技能文件放在工作空间的 `skills/` 目录下：

```
workspaces/
  my-agent/
    skills/
      my_custom.py
      another_skill.py
```

技能管理器会自动加载这些技能。

## 内置技能

### 1. Hello World (`hello-world`)

最简单的问候技能。

**参数：**
- `name` (str): 要问候的名字，默认 "World"
- `greeting` (str): 问候语，默认 "Hello"

**示例：**
```python
result = manager.execute_skill("hello-world", name="Bob", greeting="Hi")
# {"message": "Hi, Bob!"}
```

### 2. Calculator (`calculator`)

数学计算技能。

**参数：**
- `expression` (str): 数学表达式

**示例：**
```python
result = manager.execute_skill("calculator", expression="2 + 3 * 4")
# {"expression": "2 + 3 * 4", "result": 14}
```

### 3. Weather (`weather`)

天气查询技能（模拟数据）。

**参数：**
- `city` (str): 城市名称

**示例：**
```python
result = manager.execute_skill("weather", city="Beijing")
# {
#   "city": "Beijing",
#   "temperature": 25,
#   "condition": "Sunny",
#   "humidity": 45
# }
```

### 4. File Operator (`file-operator`)

文件操作技能。

**参数：**
- `operation` (str): 操作类型 (read, write, append, delete, exists)
- `path` (str): 文件路径
- `content` (str, optional): 文件内容（用于 write/append）

**示例：**
```python
# 写入文件
result = manager.execute_skill(
    "file-operator",
    operation="write",
    path="./test.txt",
    content="Hello"
)

# 读取文件
result = manager.execute_skill(
    "file-operator",
    operation="read",
    path="./test.txt"
)
```

## API 参考

### SkillMetadata

技能元数据类：

```python
@dataclass
class SkillMetadata:
    name: str                      # 技能名称
    version: str                   # 版本号
    description: str               # 描述
    author: str                    # 作者
    email: str                     # 邮箱
    tags: List[str]                # 标签
    category: str                  # 分类
    dependencies: List[str]        # 依赖
    permissions: List[str]         # 权限
```

### SkillConfig

技能配置类：

```python
@dataclass
class SkillConfig:
    enabled: bool = True           # 是否启用
    timeout: int = 30              # 执行超时（秒）
    max_retries: int = 0           # 最大重试次数
    retry_delay: int = 1           # 重试延迟（秒）
    rate_limit: Optional[int] = None  # 速率限制
    parameters: Dict[str, Any]     # 自定义参数
```

### SkillResult

技能执行结果类：

```python
@dataclass
class SkillResult:
    success: bool                  # 是否成功
    data: Any                      # 返回数据
    error: Optional[str]           # 错误信息
    duration: Optional[float]      # 执行时长
    metadata: Dict[str, Any]       # 元数据
```

### BaseSkill

技能基类（抽象类）：

```python
class BaseSkill(ABC):
    metadata: SkillMetadata        # 元数据
    config: SkillConfig            # 配置
    
    async def execute(self, **kwargs) -> SkillResult:
        """执行技能（必须实现）"""
        pass
    
    async def on_load(self):
        """加载时的回调"""
        pass
    
    async def on_unload(self):
        """卸载时的回调"""
        pass
```

### SkillRegistry

技能注册表：

```python
registry = SkillRegistry()

# 注册技能
registry.register(skill, aliases=["alias1", "alias2"])

# 获取技能
skill = registry.get("skill-name")

# 注销技能
registry.unregister("skill-name")

# 列出所有技能
skills = registry.list_skills()
```

### SkillLoader

技能加载器：

```python
loader = SkillLoader(registry)

# 添加搜索路径
loader.add_skill_path(Path("./skills"))

# 从文件加载
skill = loader.load_from_file(Path("./skills/myskill.py"))

# 从目录加载
skills = loader.load_from_directory(Path("./skills"))

# 加载所有路径
skills = loader.load_all()
```

### SkillManager

技能管理器（推荐使用）：

```python
manager = SkillManager(workspace_path)

# 执行技能
result = manager.execute_skill("skill-name", param1="value1")

# 获取技能
skill = manager.get_skill("skill-name")

# 列出技能
skills = manager.list_skills()

# 启用/禁用
manager.enable_skill("skill-name")
manager.disable_skill("skill-name")

# 重新加载
manager.reload_skill("skill-name")

# 统计信息
stats = manager.get_statistics()
```

## 技能开发指南

### 1. 基本技能结构

```python
from maagentclaw.managers.skill_manager import (
    BaseSkill, SkillMetadata, SkillConfig, SkillResult
)

class MySkill(BaseSkill):
    metadata = SkillMetadata(
        name="my-skill",
        version="1.0.0",
        description="My awesome skill",
        author="Your Name",
        email="your@email.com",
        tags=["tag1", "tag2"],
        category="category"
    )
    
    config = SkillConfig(
        enabled=True,
        timeout=30
    )
    
    async def execute(self, **kwargs) -> SkillResult:
        try:
            # 实现技能逻辑
            result = await self.do_something(**kwargs)
            
            return SkillResult(
                success=True,
                data={"result": result},
                metadata={"info": "additional info"}
            )
        except Exception as e:
            return SkillResult(
                success=False,
                error=str(e)
            )
```

### 2. 使用参数

```python
async def execute(self, 
                  required_param: str,
                  optional_param: int = 10,
                  **kwargs) -> SkillResult:
    # 访问参数
    value = required_param
    count = optional_param
    
    # 访问额外参数
    extra = kwargs.get("extra_param", "default")
    
    return SkillResult(success=True, data={...})
```

### 3. 生命周期回调

```python
class MySkill(BaseSkill):
    async def on_load(self):
        """技能加载时调用"""
        print(f"Loading {self.metadata.name}")
        # 初始化资源
        self.resource = await self.initialize()
    
    async def on_unload(self):
        """技能卸载时调用"""
        print(f"Unloading {self.metadata.name}")
        # 清理资源
        await self.cleanup()
```

### 4. 错误处理

```python
async def execute(self, **kwargs) -> SkillResult:
    try:
        # 参数验证
        if not self.validate_params(**kwargs):
            return SkillResult(
                success=False,
                error="Invalid parameters"
            )
        
        # 执行逻辑
        result = await self.process(**kwargs)
        
        return SkillResult(
            success=True,
            data={"result": result}
        )
        
    except ValueError as e:
        return SkillResult(
            success=False,
            error=f"Validation error: {str(e)}"
        )
    except Exception as e:
        return SkillResult(
            success=False,
            error=f"Unexpected error: {str(e)}"
        )
```

### 5. 使用配置

```python
class MySkill(BaseSkill):
    config = SkillConfig(
        timeout=60,
        max_retries=3,
        parameters={
            "api_key": "your-api-key",
            "endpoint": "https://api.example.com"
        }
    )
    
    async def execute(self, **kwargs) -> SkillResult:
        # 访问配置
        api_key = self.config.parameters["api_key"]
        timeout = self.config.timeout
        
        # 使用配置执行
        result = await self.call_api(api_key, timeout)
        
        return SkillResult(success=True, data={"result": result})
```

## 技能市场

### 浏览可用技能

```python
manager = SkillManager(workspace_path)

# 列出所有可用技能
available = manager.marketplace.list_available()

# 按分类筛选
utils = manager.marketplace.list_available(category="utility")

# 搜索技能
results = manager.marketplace.search("weather")
```

### 安装技能

```python
# 安装技能
success = manager.marketplace.install("skill-name", version="1.0.0")

# 卸载技能
success = manager.marketplace.uninstall("skill-name")

# 更新技能
success = manager.marketplace.update("skill-name")
```

## 最佳实践

### 1. 技能命名

使用小写字母和连字符：

```python
✅ "hello-world"
✅ "file-operator"
✅ "weather-query"
❌ "HelloWorld"
❌ "fileOperator"
```

### 2. 元数据完整性

提供完整的元数据：

```python
metadata = SkillMetadata(
    name="my-skill",
    version="1.0.0",
    description="Clear and concise description",
    author="Your Name",
    email="your@email.com",
    tags=["tag1", "tag2"],
    category="category",
    dependencies=["dependency1"],
    permissions=["read", "write"]
)
```

### 3. 参数验证

始终验证输入参数：

```python
async def execute(self, **kwargs) -> SkillResult:
    # 验证必需参数
    if "required_param" not in kwargs:
        return SkillResult(
            success=False,
            error="Missing required parameter: required_param"
        )
    
    # 验证类型
    if not isinstance(kwargs["required_param"], str):
        return SkillResult(
            success=False,
            error="Parameter must be a string"
        )
    
    # 验证范围
    if kwargs.get("count", 0) > 100:
        return SkillResult(
            success=False,
            error="Count cannot exceed 100"
        )
    
    # 执行逻辑
    ...
```

### 4. 资源管理

使用生命周期回调管理资源：

```python
class DatabaseSkill(BaseSkill):
    def __init__(self):
        self.connection = None
    
    async def on_load(self):
        self.connection = await self.create_connection()
    
    async def on_unload(self):
        if self.connection:
            await self.connection.close()
    
    async def execute(self, **kwargs) -> SkillResult:
        if not self.connection:
            return SkillResult(
                success=False,
                error="Database not connected"
            )
        
        result = await self.query(self.connection, **kwargs)
        return SkillResult(success=True, data={"result": result})
```

### 5. 错误信息

提供清晰、有用的错误信息：

```python
# ❌ 不好的错误信息
return SkillResult(success=False, error="Failed")

# ✅ 好的错误信息
return SkillResult(
    success=False,
    error=f"Failed to connect to database: {host}:{port} - Connection timeout after {timeout}s"
)
```

## 测试

运行技能测试：

```bash
# 设置环境变量
$env:PYTHONPATH="D:\pyworkplace\MAgentClaw"

# 运行测试
python test_skills.py
```

## 故障排查

### 技能未加载

1. 检查技能文件是否在 `skills/` 目录下
2. 检查文件名是否以 `.py` 结尾
3. 检查是否继承自 `BaseSkill`
4. 查看错误日志

### 技能执行失败

1. 检查参数是否正确
2. 查看 `result.error` 获取错误信息
3. 检查技能是否启用
4. 查看超时配置

### 技能冲突

如果多个技能同名：

1. 使用唯一的技能名称
2. 使用不同的分类
3. 使用命名空间前缀

## 与 OpenClaw 对比

| 特性 | OpenClaw | MAgentClaw |
|------|----------|------------|
| 技能加载 | 基础 | 增强（自动发现） |
| 技能注册 | 简单 | 完整（支持别名） |
| 技能市场 | 概念 | 框架实现 |
| 内置技能 | 有限 | 4 个实用技能 |
| 错误处理 | 基础 | 完善 |
| 元数据 | 简单 | 完整 |

## 版本历史

### v1.3.0 (2026-03-08)

- ✅ 初始版本
- ✅ 技能注册表
- ✅ 技能加载器
- ✅ 技能市场框架
- ✅ 4 个内置技能
- ✅ 完整的 API 文档

## 参考资料

- [OpenClaw 项目](https://gitee.com/openclaw/openclaw)
- [MAgentClaw 开发计划](DEVELOPMENT_PLAN.md)
- [技能管理器源码](maagentclaw/managers/skill_manager.py)
- [内置技能目录](maagentclaw/skills/)
