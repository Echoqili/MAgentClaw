"""
内置工具 - URL 抓取

获取网页内容
"""

import aiohttp
from typing import Optional
from ..managers.tool_manager import BaseTool, ToolMetadata, ToolConfig, ToolResult, ToolPermission


class URLFetcherTool(BaseTool):
    """URL 抓取工具"""
    
    metadata = ToolMetadata(
        name="url-fetcher",
        version="1.0.0",
        description="获取网页内容",
        author="MAgentClaw Team",
        category="network",
        tags=["url", "http", "fetch", "web"],
        permissions=[ToolPermission.NETWORK, ToolPermission.READ],
        timeout=30
    )
    
    config = ToolConfig(
        enabled=True,
        rate_limit=10,
        sandbox_enabled=True,
        parameters={
            "user_agent": "MAgentClaw/1.0",
            "timeout": 30
        }
    )
    
    async def execute(self, url: str, timeout: Optional[int] = None) -> ToolResult:
        """获取 URL 内容"""
        try:
            timeout_val = timeout or self.config.parameters.get("timeout", 30)
            
            # URL 验证
            if not url.startswith(('http://', 'https://')):
                return ToolResult(
                    success=False,
                    error="Invalid URL. Must start with http:// or https://"
                )
            
            # 黑名单检查
            blocked_domains = ['malicious.com', 'blocked.com']
            for domain in blocked_domains:
                if domain in url:
                    return ToolResult(
                        success=False,
                        error=f"Access to {domain} is blocked"
                    )
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers={"User-Agent": self.config.parameters["user_agent"]},
                    timeout=aiohttp.ClientTimeout(total=timeout_val)
                ) as response:
                    content = await response.text()
                    status = response.status
                    content_type = response.headers.get('Content-Type', '')
            
            return ToolResult(
                success=True,
                data={
                    "url": url,
                    "status": status,
                    "content": content[:10000],  # 限制返回长度
                    "content_type": content_type,
                    "length": len(content)
                },
                metadata={
                    "fetched_at": datetime.now().isoformat()
                }
            )
            
        except asyncio.TimeoutError:
            return ToolResult(
                success=False,
                error=f"Request timeout after {timeout_val} seconds"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Fetch error: {str(e)}"
            )


# 自动注册
tool = URLFetcherTool()
