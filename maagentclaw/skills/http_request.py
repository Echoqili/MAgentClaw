"""
内置技能 - HTTP 请求

发送 HTTP 请求
"""

import aiohttp
from typing import Any, Dict, Optional
from ..managers.skill_manager import BaseSkill, SkillMetadata, SkillConfig, SkillResult


class HTTPSkill(BaseSkill):
    """HTTP 请求技能"""

    metadata = SkillMetadata(
        name="http-request",
        version="1.0.0",
        description="发送 HTTP 请求，支持 GET、POST、PUT、DELETE",
        author="MAgentClaw Team",
        email="team@maagentclaw.com",
        tags=["http", "request", "api", "utility"],
        category="utility"
    )

    config = SkillConfig(
        enabled=True,
        timeout=30
    )

    async def execute(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None
    ) -> SkillResult:
        """执行 HTTP 请求"""
        headers = headers or {}
        params = params or {}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=method.upper(),
                    url=url,
                    headers=headers,
                    params=params,
                    json=json_data,
                    data=data,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    content_type = response.headers.get("Content-Type", "")

                    if "application/json" in content_type:
                        result = await response.json()
                    else:
                        result = await response.text()

                    return SkillResult(
                        success=True,
                        data={
                            "status": response.status,
                            "status_text": response.reason,
                            "headers": dict(response.headers),
                            "body": result,
                            "url": str(response.url)
                        },
                        metadata={
                            "method": method.upper(),
                            "content_type": content_type
                        }
                    )

        except aiohttp.ClientError as e:
            return SkillResult(
                success=False,
                error=f"HTTP error: {str(e)}"
            )
        except Exception as e:
            return SkillResult(
                success=False,
                error=str(e)
            )


skill = HTTPSkill()
