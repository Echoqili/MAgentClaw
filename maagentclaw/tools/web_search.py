"""
内置工具 - 网络搜索

模拟网络搜索功能
"""

from ..managers.tool_manager import BaseTool, ToolMetadata, ToolConfig, ToolResult, ToolPermission


class WebSearchTool(BaseTool):
    """网络搜索工具"""
    
    metadata = ToolMetadata(
        name="web-search",
        version="1.0.0",
        description="执行网络搜索",
        author="MAgentClaw Team",
        category="search",
        tags=["search", "web", "internet"],
        permissions=[ToolPermission.NETWORK, ToolPermission.READ],
        timeout=30
    )
    
    config = ToolConfig(
        enabled=True,
        rate_limit=5,  # 每秒最多 5 次
        sandbox_enabled=True
    )
    
    # 模拟搜索结果
    MOCK_RESULTS = {
        "python": [
            {"title": "Python Official Website", "url": "https://python.org", "snippet": "The official Python programming language website"},
            {"title": "Python Tutorial", "url": "https://w3schools.com/python", "snippet": "Learn Python programming with examples"},
            {"title": "Python Documentation", "url": "https://docs.python.org", "snippet": "Complete Python documentation"}
        ],
        "ai": [
            {"title": "What is AI?", "url": "https://wikipedia.org/wiki/AI", "snippet": "Artificial Intelligence explained"},
            {"title": "AI Tutorial", "url": "https://tutorialspoint.com/ai", "snippet": "Learn AI concepts"}
        ]
    }
    
    async def execute(self, query: str, num_results: int = 5) -> ToolResult:
        """执行搜索"""
        try:
            # 模拟搜索延迟
            await asyncio.sleep(0.5)
            
            # 查找模拟结果
            query_lower = query.lower()
            results = []
            
            for keyword, mock_results in self.MOCK_RESULTS.items():
                if keyword in query_lower:
                    results.extend(mock_results[:num_results])
            
            # 如果没有匹配，返回通用结果
            if not results:
                results = [
                    {
                        "title": f"Result for: {query}",
                        "url": f"https://example.com/search?q={query}",
                        "snippet": f"Search results for '{query}'"
                    }
                ]
            
            return ToolResult(
                success=True,
                data={
                    "query": query,
                    "results": results[:num_results],
                    "total": len(results)
                },
                metadata={
                    "search_type": "mock",
                    "num_results": num_results
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Search error: {str(e)}"
            )


# 自动注册
tool = WebSearchTool()
