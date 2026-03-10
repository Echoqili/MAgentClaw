"""
内置工具 - 文本处理

文本转换和分析
"""

import re
from ..managers.tool_manager import BaseTool, ToolMetadata, ToolConfig, ToolResult, ToolPermission


class TextProcessorTool(BaseTool):
    """文本处理工具"""
    
    metadata = ToolMetadata(
        name="text-processor",
        version="1.0.0",
        description="文本转换和分析",
        author="MAgentClaw Team",
        category="utility",
        tags=["text", "string", "process", "analyze"],
        permissions=[ToolPermission.READ],
        timeout=10
    )
    
    config = ToolConfig(
        enabled=True,
        sandbox_enabled=False
    )
    
    async def execute(self, operation: str, text: str, **kwargs) -> ToolResult:
        """执行文本操作"""
        try:
            if operation == "uppercase":
                return ToolResult(success=True, data={"result": text.upper()})
            elif operation == "lowercase":
                return ToolResult(success=True, data={"result": text.lower()})
            elif operation == "reverse":
                return ToolResult(success=True, data={"result": text[::-1]})
            elif operation == "word_count":
                words = text.split()
                return ToolResult(
                    success=True,
                    data={
                        "word_count": len(words),
                        "char_count": len(text),
                        "line_count": len(text.splitlines())
                    }
                )
            elif operation == "extract_emails":
                emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
                return ToolResult(
                    success=True,
                    data={"emails": list(set(emails))}
                )
            elif operation == "extract_urls":
                urls = re.findall(r'https?://\S+', text)
                return ToolResult(
                    success=True,
                    data={"urls": urls}
                )
            elif operation == "replace":
                old = kwargs.get("old", "")
                new = kwargs.get("new", "")
                return ToolResult(
                    success=True,
                    data={"result": text.replace(old, new)}
                )
            else:
                return ToolResult(
                    success=False,
                    error=f"Unknown operation: {operation}"
                )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Text processing error: {str(e)}"
            )


# 自动注册
tool = TextProcessorTool()
