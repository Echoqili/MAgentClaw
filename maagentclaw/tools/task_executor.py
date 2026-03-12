"""
任务执行器模块
支持并行工具调用和任务优化执行
"""

from typing import Dict, List, Optional, Any, Callable, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import uuid
from abc import ABC, abstractmethod


@dataclass
class ToolResult:
    """工具执行结果"""
    tool_name: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


class BaseToolExecutor(ABC):
    """工具基类 - 用于任务执行器"""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
    
    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """执行工具"""
        pass
    
    def get_schema(self) -> Dict[str, Any]:
        """获取工具 schema"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {}
        }


class ToolRegistry:
    """工具注册中心 - 支持并行调用"""
    
    def __init__(self):
        self.tools: Dict[str, BaseToolExecutor] = {}
        self.tool_schemas: Dict[str, dict] = {}
    
    def register(self, tool: BaseToolExecutor):
        """注册工具"""
        self.tools[tool.name] = tool
        self.tool_schemas[tool.name] = tool.get_schema()
    
    def unregister(self, name: str):
        """注销工具"""
        if name in self.tools:
            del self.tools[name]
        if name in self.tool_schemas:
            del self.tool_schemas[name]
    
    def get_tool(self, name: str) -> Optional[BaseToolExecutor]:
        """获取工具"""
        return self.tools.get(name)
    
    def list_tools(self) -> List[dict]:
        """列出所有工具"""
        return [
            {"name": name, "schema": schema}
            for name, schema in self.tool_schemas.items()
        ]
    
    def tool_exists(self, name: str) -> bool:
        """检查工具是否存在"""
        return name in self.tools


class TaskExecutor:
    """任务执行器 - 支持并行工具调用"""
    
    def __init__(self, tool_registry: Optional[ToolRegistry] = None):
        self.tool_registry = tool_registry or ToolRegistry()
        self._execution_stats: Dict[str, int] = {}
    
    async def execute_single_task(
        self, 
        task: str, 
        tools: List[str],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """执行单个任务（支持多工具调用）"""
        start_time = datetime.now()
        context = context or {}
        
        # 如果有多个工具，尝试并行执行
        if len(tools) > 1:
            tool_results = await self.execute_parallel_tools(tools, context)
            
            # 汇总结果
            aggregated = self.aggregate_results(tool_results)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "success": all(r.success for r in tool_results),
                "task": task,
                "tool_results": [
                    {
                        "tool": r.tool_name,
                        "success": r.success,
                        "result": r.result,
                        "error": r.error,
                        "execution_time": r.execution_time
                    }
                    for r in tool_results
                ],
                "aggregated_result": aggregated,
                "execution_time": execution_time,
                "parallel": True
            }
        else:
            # 单工具顺序执行
            tool_name = tools[0] if tools else None
            tool_result = await self.execute_single_tool(tool_name, context)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "success": tool_result.success,
                "task": task,
                "tool_results": [
                    {
                        "tool": tool_result.tool_name,
                        "success": tool_result.success,
                        "result": tool_result.result,
                        "error": tool_result.error,
                        "execution_time": tool_result.execution_time
                    }
                ],
                "aggregated_result": tool_result.result,
                "execution_time": execution_time,
                "parallel": False
            }
    
    async def execute_parallel_tools(
        self,
        tool_names: List[str],
        context: Dict[str, Any]
    ) -> List[ToolResult]:
        """并行执行多个工具"""
        coroutines = []
        valid_tools = []
        
        for tool_name in tool_names:
            tool = self.tool_registry.get_tool(tool_name)
            if tool:
                coroutines.append(self._execute_tool(tool, context))
                valid_tools.append(tool_name)
            else:
                coroutines.append(
                    self._create_error_result(tool_name, f"Tool {tool_name} not found")
                )
                valid_tools.append(tool_name)
        
        # 并行执行所有工具
        results = await asyncio.gather(*coroutines, return_exceptions=True)
        
        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(
                    ToolResult(
                        tool_name=valid_tools[i] if i < len(valid_tools) else "unknown",
                        success=False,
                        error=str(result)
                    )
                )
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def execute_single_tool(
        self,
        tool_name: Optional[str],
        context: Dict[str, Any]
    ) -> ToolResult:
        """执行单个工具"""
        if not tool_name:
            return ToolResult(
                tool_name="none",
                success=False,
                error="No tool specified"
            )
        
        tool = self.tool_registry.get_tool(tool_name)
        if not tool:
            return ToolResult(
                tool_name=tool_name,
                success=False,
                error=f"Tool {tool_name} not found"
            )
        
        return await self._execute_tool(tool, context)
    
    async def _execute_tool(
        self,
        tool: BaseToolExecutor,
        context: Dict[str, Any]
    ) -> ToolResult:
        """执行工具并记录时间"""
        start_time = datetime.now()
        
        try:
            result = await tool.execute(**context)
            execution_time = (datetime.now() - start_time).total_seconds()
            
            self._execution_stats[tool.name] = self._execution_stats.get(tool.name, 0) + 1
            
            return ToolResult(
                tool_name=tool.name,
                success=True,
                result=result,
                execution_time=execution_time
            )
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return ToolResult(
                tool_name=tool.name,
                success=False,
                error=str(e),
                execution_time=execution_time
            )
    
    def _create_error_result(self, tool_name: str, error: str) -> ToolResult:
        """创建错误结果"""
        return ToolResult(
            tool_name=tool_name,
            success=False,
            error=error
        )
    
    def aggregate_results(self, results: List[ToolResult]) -> Any:
        """聚合多个工具的结果"""
        if not results:
            return None
        
        successful_results = [r.result for r in results if r.success]
        failed_results = [r.error for r in results if not r.success]
        
        return {
            "successful_results": successful_results,
            "failed_errors": failed_results,
            "total_count": len(results),
            "success_count": len(successful_results),
            "failure_count": len(failed_results)
        }
    
    def get_execution_stats(self) -> Dict[str, int]:
        """获取执行统计"""
        return self._execution_stats.copy()
    
    def reset_stats(self):
        """重置统计"""
        self._execution_stats.clear()


class StreamingTaskExecutor(TaskExecutor):
    """流式任务执行器 - 支持实时输出"""
    
    async def execute_streaming_task(
        self,
        task: str,
        tools: List[str],
        context: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """流式执行任务，实时推送进度"""
        context = context or {}
        
        yield {
            "type": "start",
            "task": task,
            "tools": tools,
            "timestamp": datetime.now().isoformat()
        }
        
        if len(tools) > 1:
            # 并行执行并实时推送结果
            for i, tool_name in enumerate(tools):
                tool = self.tool_registry.get_tool(tool_name)
                if tool:
                    yield {
                        "type": "tool_start",
                        "tool": tool_name,
                        "index": i,
                        "total": len(tools),
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    result = await self._execute_tool(tool, context)
                    
                    yield {
                        "type": "tool_complete",
                        "tool": tool_name,
                        "success": result.success,
                        "result": result.result,
                        "error": result.error,
                        "execution_time": result.execution_time,
                        "index": i,
                        "total": len(tools),
                        "timestamp": datetime.now().isoformat()
                    }
            
            # 最终汇总
            yield {
                "type": "complete",
                "task": task,
                "timestamp": datetime.now().isoformat()
            }
        else:
            # 单工具执行
            tool_name = tools[0] if tools else None
            result = await self.execute_single_tool(tool_name, context)
            
            yield {
                "type": "complete",
                "task": task,
                "success": result.success,
                "result": result.result,
                "error": result.error,
                "execution_time": result.execution_time,
                "timestamp": datetime.now().isoformat()
            }
