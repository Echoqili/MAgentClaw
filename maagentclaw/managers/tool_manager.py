"""
Tool System - 工具系统

实现工具的注册、管理、执行和权限控制
"""

import asyncio
import json
import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type


class ToolStatus(Enum):
    """工具状态"""
    READY = "ready"
    RUNNING = "running"
    ERROR = "error"
    DISABLED = "disabled"


class ToolPermission(Enum):
    """工具权限"""
    READ = "read"              # 只读权限
    WRITE = "write"            # 写入权限
    EXECUTE = "execute"        # 执行权限
    NETWORK = "network"        # 网络访问权限
    FILESYSTEM = "filesystem"  # 文件系统权限
    ADMIN = "admin"            # 管理员权限


@dataclass
class ToolMetadata:
    """工具元数据"""
    name: str
    version: str
    description: str
    author: str
    category: str = "general"
    tags: List[str] = field(default_factory=list)
    permissions: List[ToolPermission] = field(default_factory=list)
    timeout: int = 30  # 默认超时（秒）
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "category": self.category,
            "tags": self.tags,
            "permissions": [p.value for p in self.permissions],
            "timeout": self.timeout
        }


@dataclass
class ToolConfig:
    """工具配置"""
    enabled: bool = True
    max_concurrent: int = 10  # 最大并发数
    rate_limit: Optional[int] = None  # 速率限制（次/秒）
    sandbox_enabled: bool = True  # 启用沙箱
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "enabled": self.enabled,
            "max_concurrent": self.max_concurrent,
            "rate_limit": self.rate_limit,
            "sandbox_enabled": self.sandbox_enabled,
            "parameters": self.parameters
        }


@dataclass
class ToolResult:
    """工具执行结果"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    duration: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "duration": self.duration,
            "metadata": self.metadata
        }


@dataclass
class ToolCall:
    """工具调用请求"""
    tool_name: str
    arguments: Dict[str, Any]
    caller_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "tool_name": self.tool_name,
            "arguments": self.arguments,
            "caller_id": self.caller_id,
            "timestamp": self.timestamp.isoformat()
        }


class BaseTool(ABC):
    """工具基类"""
    
    metadata: ToolMetadata
    config: ToolConfig = ToolConfig()
    
    def __init__(self):
        self.status = ToolStatus.READY
        self.execution_count = 0
        self.last_execution: Optional[datetime] = None
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """执行工具"""
        pass
    
    def validate_permissions(self, permissions: List[ToolPermission]) -> bool:
        """验证权限"""
        required = set(self.metadata.permissions)
        available = set(permissions)
        return required.issubset(available)
    
    async def on_load(self):
        """加载时的回调"""
        pass
    
    async def on_unload(self):
        """卸载时的回调"""
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.metadata.name,
            "version": self.metadata.version,
            "description": self.metadata.description,
            "status": self.status.value,
            "category": self.metadata.category,
            "permissions": [p.value for p in self.metadata.permissions],
            "execution_count": self.execution_count,
            "last_execution": self.last_execution.isoformat() if self.last_execution else None,
            "config": self.config.to_dict(),
            "metadata": self.metadata.to_dict()
        }


class ToolRegistry:
    """工具注册表"""
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._categories: Dict[str, List[str]] = {}
    
    def register(self, tool: BaseTool):
        """注册工具"""
        tool_name = tool.metadata.name
        self._tools[tool_name] = tool
        
        # 按分类组织
        category = tool.metadata.category
        if category not in self._categories:
            self._categories[category] = []
        self._categories[category].append(tool_name)
        
        # 调用加载回调
        asyncio.create_task(tool.on_load())
    
    def unregister(self, tool_name: str):
        """注销工具"""
        if tool_name in self._tools:
            tool = self._tools[tool_name]
            asyncio.create_task(tool.on_unload())
            
            # 从分类中移除
            category = tool.metadata.category
            if category in self._categories:
                self._categories[category].remove(tool_name)
            
            del self._tools[tool_name]
    
    def get(self, tool_name: str) -> Optional[BaseTool]:
        """获取工具"""
        return self._tools.get(tool_name)
    
    def list_tools(self) -> List[str]:
        """列出所有工具"""
        return list(self._tools.keys())
    
    def list_by_category(self, category: str) -> List[str]:
        """按分类列出工具"""
        return self._categories.get(category, [])
    
    def list_categories(self) -> List[str]:
        """列出所有分类"""
        return list(self._categories.keys())
    
    def count(self) -> int:
        """工具数量"""
        return len(self._tools)


class ToolSandbox:
    """工具沙箱"""
    
    def __init__(self, restrictions: Optional[Dict[str, Any]] = None):
        self.restrictions = restrictions or {
            "max_memory_mb": 256,
            "max_cpu_percent": 50,
            "max_execution_time": 30,
            "allowed_paths": [],
            "blocked_operations": []
        }
    
    async def execute(self, tool: BaseTool, **kwargs) -> ToolResult:
        """在沙箱中执行工具"""
        start_time = time.time()
        
        try:
            # 检查执行时间
            if time.time() - start_time > self.restrictions["max_execution_time"]:
                return ToolResult(
                    success=False,
                    error="Execution timeout"
                )
            
            # 执行工具
            result = await tool.execute(**kwargs)
            
            # 记录执行时间
            result.duration = time.time() - start_time
            
            return result
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Sandbox error: {str(e)}"
            )


class ToolManager:
    """工具管理器"""
    
    def __init__(self, workspace_path: Path):
        self.workspace_path = Path(workspace_path)
        self.registry = ToolRegistry()
        self.sandbox = ToolSandbox()
        
        # 工具目录
        self.tools_dir = self.workspace_path / "tools"
        self.builtin_dir = Path(__file__).parent / "builtin_tools"
        
        # 权限映射
        self.user_permissions: Dict[str, List[ToolPermission]] = {}
        
        # 执行历史
        self.execution_history: List[ToolCall] = []
        
        # 加载内置工具
        self.load_builtin_tools()
    
    def load_builtin_tools(self):
        """加载内置工具"""
        if not self.builtin_dir.exists():
            return
        
        # 动态导入内置工具
        import importlib.util
        
        for file_path in self.builtin_dir.glob("*.py"):
            if file_path.name.startswith("_"):
                continue
            
            try:
                spec = importlib.util.spec_from_file_location(
                    "tool_module", file_path
                )
                if spec is None or spec.loader is None:
                    continue
                
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # 查找工具类
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and 
                        issubclass(attr, BaseTool) and 
                        attr != BaseTool):
                        tool = attr()
                        self.register_tool(tool)
                        
            except Exception as e:
                print(f"Error loading tool from {file_path}: {e}")
    
    def register_tool(self, tool: BaseTool):
        """注册工具"""
        self.registry.register(tool)
    
    def unregister_tool(self, tool_name: str):
        """注销工具"""
        self.registry.unregister(tool_name)
    
    def set_user_permissions(self, user_id: str, permissions: List[ToolPermission]):
        """设置用户权限"""
        self.user_permissions[user_id] = permissions
    
    def get_user_permissions(self, user_id: str) -> List[ToolPermission]:
        """获取用户权限"""
        return self.user_permissions.get(user_id, [])
    
    def check_permission(self, user_id: str, tool: BaseTool) -> bool:
        """检查用户是否有工具权限"""
        user_perms = self.get_user_permissions(user_id)
        
        # 如果用户没有设置权限，默认允许所有
        if not user_perms:
            return True
        
        return tool.validate_permissions(user_perms)
    
    async def execute_tool(self, tool_name: str, 
                          arguments: Dict[str, Any],
                          user_id: Optional[str] = None) -> ToolResult:
        """执行工具"""
        tool = self.registry.get(tool_name)
        if not tool:
            return ToolResult(
                success=False,
                error=f"Tool '{tool_name}' not found"
            )
        
        if not tool.config.enabled:
            return ToolResult(
                success=False,
                error=f"Tool '{tool_name}' is disabled"
            )
        
        # 检查权限
        if user_id and not self.check_permission(user_id, tool):
            return ToolResult(
                success=False,
                error=f"Permission denied for tool '{tool_name}'"
            )
        
        # 创建调用记录
        call = ToolCall(
            tool_name=tool_name,
            arguments=arguments,
            caller_id=user_id
        )
        self.execution_history.append(call)
        
        # 执行工具
        try:
            if tool.config.sandbox_enabled:
                result = await self.sandbox.execute(tool, **arguments)
            else:
                result = await tool.execute(**arguments)
            
            tool.execution_count += 1
            tool.last_execution = datetime.now()
            
            return result
            
        except Exception as e:
            tool.status = ToolStatus.ERROR
            return ToolResult(
                success=False,
                error=f"Execution error: {str(e)}"
            )
    
    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """获取工具"""
        return self.registry.get(tool_name)
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """列出所有工具"""
        tools = []
        for tool_name in self.registry.list_tools():
            tool = self.registry.get(tool_name)
            if tool:
                tools.append(tool.to_dict())
        return tools
    
    def list_categories(self) -> List[str]:
        """列出所有分类"""
        return self.registry.list_categories()
    
    def get_execution_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取执行历史"""
        return [call.to_dict() for call in self.execution_history[-limit:]]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        tools = self.list_tools()
        
        total = len(tools)
        enabled = sum(1 for t in tools if t["config"]["enabled"])
        total_executions = sum(t["execution_count"] for t in tools)
        
        # 按分类统计
        categories = {}
        for category in self.registry.list_categories():
            category_tools = self.registry.list_by_category(category)
            categories[category] = len(category_tools)
        
        return {
            "total_tools": total,
            "enabled_tools": enabled,
            "total_executions": total_executions,
            "categories": categories
        }


# 简化导入
__all__ = [
    "ToolStatus",
    "ToolPermission",
    "ToolMetadata",
    "ToolConfig",
    "ToolResult",
    "ToolCall",
    "BaseTool",
    "ToolRegistry",
    "ToolSandbox",
    "ToolManager"
]
