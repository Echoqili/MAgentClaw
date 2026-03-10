"""
内置工具 - 代码执行

安全执行 Python 代码（沙箱）
"""

import sys
import io
from contextlib import redirect_stdout, redirect_stderr
from ..managers.tool_manager import BaseTool, ToolMetadata, ToolConfig, ToolResult, ToolPermission


class CodeExecutorTool(BaseTool):
    """代码执行工具"""
    
    metadata = ToolMetadata(
        name="code-executor",
        version="1.0.0",
        description="安全执行 Python 代码",
        author="MAgentClaw Team",
        category="development",
        tags=["code", "python", "execute", "eval"],
        permissions=[ToolPermission.EXECUTE, ToolPermission.ADMIN],
        timeout=10
    )
    
    config = ToolConfig(
        enabled=True,
        sandbox_enabled=True,
        max_concurrent=1,
        parameters={
            "max_output_length": 1000,
            "allowed_modules": ["math", "random", "datetime", "json", "re"]
        }
    )
    
    async def execute(self, code: str, timeout: Optional[int] = None) -> ToolResult:
        """执行 Python 代码"""
        try:
            # 安全检查
            dangerous_keywords = ['import os', 'import sys', 'subprocess', 
                                'eval(', 'exec(', '__import__', 'open(']
            
            for keyword in dangerous_keywords:
                if keyword in code:
                    return ToolResult(
                        success=False,
                        error=f"Dangerous code detected: {keyword}"
                    )
            
            # 创建输出缓冲区
            stdout_buffer = io.StringIO()
            stderr_buffer = io.StringIO()
            
            # 创建安全的命名空间
            safe_globals = {
                "__builtins__": {
                    "print": print,
                    "len": len,
                    "range": range,
                    "str": str,
                    "int": int,
                    "float": float,
                    "list": list,
                    "dict": dict,
                    "set": set,
                    "tuple": tuple,
                    "sum": sum,
                    "min": min,
                    "max": max,
                    "abs": abs,
                    "round": round,
                }
            }
            
            # 添加允许的模块
            import math
            import random
            safe_globals["math"] = math
            safe_globals["random"] = random
            
            local_vars = {}
            
            # 执行代码
            with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
                try:
                    exec(code, safe_globals, local_vars)
                except Exception as e:
                    return ToolResult(
                        success=False,
                        error=f"Execution error: {str(e)}"
                    )
            
            # 获取输出
            stdout = stdout_buffer.getvalue()[:self.config.parameters["max_output_length"]]
            stderr = stderr_buffer.getvalue()[:self.config.parameters["max_output_length"]]
            
            return ToolResult(
                success=True,
                data={
                    "stdout": stdout,
                    "stderr": stderr,
                    "variables": {k: str(v) for k, v in local_vars.items() if not k.startswith('_')}
                },
                metadata={
                    "code_length": len(code),
                    "executed": True
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Code execution error: {str(e)}"
            )


# 自动注册
tool = CodeExecutorTool()
