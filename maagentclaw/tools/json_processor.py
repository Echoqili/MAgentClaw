"""
内置工具 - JSON 处理

JSON 格式化和验证
"""

import json
from ..managers.tool_manager import BaseTool, ToolMetadata, ToolConfig, ToolResult, ToolPermission


class JSONProcessorTool(BaseTool):
    """JSON 处理工具"""
    
    metadata = ToolMetadata(
        name="json-processor",
        version="1.0.0",
        description="JSON 格式化和验证",
        author="MAgentClaw Team",
        category="utility",
        tags=["json", "format", "validate", "parse"],
        permissions=[ToolPermission.READ],
        timeout=10
    )
    
    config = ToolConfig(
        enabled=True,
        sandbox_enabled=False
    )
    
    async def execute(self, operation: str, **kwargs) -> ToolResult:
        """执行 JSON 操作"""
        try:
            if operation == "format":
                return self._format_json(kwargs.get("json_string", ""))
            elif operation == "validate":
                return self._validate_json(kwargs.get("json_string", ""))
            elif operation == "parse":
                return self._parse_json(kwargs.get("json_string", ""))
            elif operation == "stringify":
                return self._stringify_json(kwargs.get("data", {}))
            else:
                return ToolResult(
                    success=False,
                    error=f"Unknown operation: {operation}"
                )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"JSON processing error: {str(e)}"
            )
    
    def _format_json(self, json_string: str) -> ToolResult:
        """格式化 JSON"""
        try:
            data = json.loads(json_string)
            formatted = json.dumps(data, indent=2, ensure_ascii=False)
            
            return ToolResult(
                success=True,
                data={
                    "formatted": formatted,
                    "original_length": len(json_string),
                    "formatted_length": len(formatted)
                }
            )
        except json.JSONDecodeError as e:
            return ToolResult(
                success=False,
                error=f"Invalid JSON: {str(e)}"
            )
    
    def _validate_json(self, json_string: str) -> ToolResult:
        """验证 JSON"""
        try:
            json.loads(json_string)
            return ToolResult(
                success=True,
                data={"valid": True}
            )
        except json.JSONDecodeError as e:
            return ToolResult(
                success=True,
                data={
                    "valid": False,
                    "error": str(e)
                }
            )
    
    def _parse_json(self, json_string: str) -> ToolResult:
        """解析 JSON"""
        try:
            data = json.loads(json_string)
            return ToolResult(
                success=True,
                data={"parsed": data}
            )
        except json.JSONDecodeError as e:
            return ToolResult(
                success=False,
                error=f"Parse error: {str(e)}"
            )
    
    def _stringify_json(self, data: Dict[str, Any]) -> ToolResult:
        """转换为 JSON 字符串"""
        try:
            json_string = json.dumps(data, ensure_ascii=False)
            return ToolResult(
                success=True,
                data={"json_string": json_string}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Stringify error: {str(e)}"
            )


# 自动注册
tool = JSONProcessorTool()
