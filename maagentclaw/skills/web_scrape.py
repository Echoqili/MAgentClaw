"""
内置技能 - 网页爬取

从网页提取内容
"""

import re
import asyncio
from typing import Any, Dict, List, Optional
from ..managers.skill_manager import BaseSkill, SkillMetadata, SkillConfig, SkillResult


class WebScrapeSkill(BaseSkill):
    """网页爬取技能"""

    metadata = SkillMetadata(
        name="web-scrape",
        version="1.0.0",
        description="从网页提取内容，支持文本、链接和图片",
        author="MAgentClaw Team",
        email="team@maagentclaw.com",
        tags=["web", "scrape", "extract", "utility"],
        category="utility"
    )

    config = SkillConfig(
        enabled=True,
        timeout=30
    )

    async def execute(
        self,
        url: str,
        extract: str = "text",
        selector: Optional[str] = None
    ) -> SkillResult:
        """执行网页爬取"""
        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as response:
                    if response.status != 200:
                        return SkillResult(
                            success=False,
                            error=f"HTTP {response.status}"
                        )

                    html = await response.text()

                    if extract == "text":
                        text = self._extract_text(html, selector)
                        return SkillResult(
                            success=True,
                            data={
                                "url": url,
                                "text": text,
                                "length": len(text)
                            }
                        )
                    elif extract == "links":
                        links = self._extract_links(html, url)
                        return SkillResult(
                            success=True,
                            data={
                                "url": url,
                                "links": links,
                                "count": len(links)
                            }
                        )
                    elif extract == "images":
                        images = self._extract_images(html, url)
                        return SkillResult(
                            success=True,
                            data={
                                "url": url,
                                "images": images,
                                "count": len(images)
                            }
                        )
                    else:
                        return SkillResult(
                            success=False,
                            error=f"Unknown extract type: {extract}"
                        )

        except asyncio.TimeoutError:
            return SkillResult(
                success=False,
                error="Request timeout"
            )
        except Exception as e:
            return SkillResult(
                success=False,
                error=str(e)
            )

    def _extract_text(self, html: str, selector: Optional[str] = None) -> str:
        """提取文本"""
        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _extract_links(self, html: str, base_url: str) -> List[str]:
        """提取链接"""
        pattern = r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>'
        matches = re.findall(pattern, html, re.IGNORECASE)

        links = []
        for link in matches:
            if link.startswith('http'):
                links.append(link)
            elif link.startswith('/'):
                from urllib.parse import urljoin
                links.append(urljoin(base_url, link))

        return list(set(links))

    def _extract_images(self, html: str, base_url: str) -> List[str]:
        """提取图片"""
        pattern = r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>'
        matches = re.findall(pattern, html, re.IGNORECASE)

        images = []
        for img in matches:
            if img.startswith('http'):
                images.append(img)
            elif img.startswith('/'):
                from urllib.parse import urljoin
                images.append(urljoin(base_url, img))

        return list(set(images))


skill = WebScrapeSkill()
