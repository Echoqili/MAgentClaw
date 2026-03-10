"""
内置技能 - 文本提取

从文本中提取结构化信息
"""

import re
from typing import Any, Dict, List, Optional
from ..managers.skill_manager import BaseSkill, SkillMetadata, SkillConfig, SkillResult


class TextExtractSkill(BaseSkill):
    """文本提取技能"""

    metadata = SkillMetadata(
        name="text-extract",
        version="1.0.0",
        description="从文本中提取邮箱、电话、URL 等信息",
        author="MAgentClaw Team",
        email="team@maagentclaw.com",
        tags=["text", "extract", "regex", "utility"],
        category="utility"
    )

    config = SkillConfig(
        enabled=True,
        timeout=10
    )

    async def execute(
        self,
        text: str,
        pattern: Optional[str] = None,
        extract_type: Optional[str] = None
    ) -> SkillResult:
        """执行文本提取"""
        try:
            if extract_type:
                return await self._extract_type(text, extract_type)
            elif pattern:
                return await self._extract_pattern(text, pattern)
            else:
                return await self._extract_all(text)

        except Exception as e:
            return SkillResult(
                success=False,
                error=str(e)
            )

    async def _extract_type(
        self,
        text: str,
        extract_type: str
    ) -> SkillResult:
        """按类型提取"""
        if extract_type == "email":
            results = self._extract_emails(text)
        elif extract_type == "phone":
            results = self._extract_phones(text)
        elif extract_type == "url":
            results = self._extract_urls(text)
        elif extract_type == "ip":
            results = self._extract_ips(text)
        elif extract_type == "date":
            results = self._extract_dates(text)
        elif extract_type == "hashtag":
            results = self._extract_hashtags(text)
        elif extract_type == "mention":
            results = self._extract_mentions(text)
        else:
            return SkillResult(
                success=False,
                error=f"Unknown extract type: {extract_type}"
            )

        return SkillResult(
            success=True,
            data={
                "type": extract_type,
                "results": results,
                "count": len(results)
            }
        )

    async def _extract_pattern(
        self,
        text: str,
        pattern: str
    ) -> SkillResult:
        """按正则表达式提取"""
        try:
            matches = re.findall(pattern, text)
            return SkillResult(
                success=True,
                data={
                    "pattern": pattern,
                    "results": matches,
                    "count": len(matches)
                }
            )
        except re.error as e:
            return SkillResult(
                success=False,
                error=f"Invalid regex: {e}"
            )

    async def _extract_all(self, text: str) -> SkillResult:
        """提取所有类型"""
        return SkillResult(
            success=True,
            data={
                "email": self._extract_emails(text),
                "phone": self._extract_phones(text),
                "url": self._extract_urls(text),
                "ip": self._extract_ips(text),
                "date": self._extract_dates(text),
                "hashtag": self._extract_hashtags(text),
                "mention": self._extract_mentions(text)
            }
        )

    def _extract_emails(self, text: str) -> List[str]:
        """提取邮箱"""
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return list(set(re.findall(pattern, text)))

    def _extract_phones(self, text: str) -> List[str]:
        """提取电话"""
        patterns = [
            r'\+?86\s?1[3-9]\d{9}',
            r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            r'\d{3,4}[-.\s]?\d{7,8}'
        ]
        results = []
        for pattern in patterns:
            results.extend(re.findall(pattern, text))
        return list(set(results))

    def _extract_urls(self, text: str) -> List[str]:
        """提取 URL"""
        pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        return list(set(re.findall(pattern, text)))

    def _extract_ips(self, text: str) -> List[str]:
        """提取 IP 地址"""
        pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        ips = re.findall(pattern, text)
        valid_ips = [ip for ip in ips if all(0 <= int(o) <= 255 for o in ip.split('.'))]
        return list(set(valid_ips))

    def _extract_dates(self, text: str) -> List[str]:
        """提取日期"""
        patterns = [
            r'\d{4}-\d{2}-\d{2}',
            r'\d{4}/\d{2}/\d{2}',
            r'\d{2}/\d{2}/\d{4}',
            r'\d{2}-\d{2}-\d{4}',
            r'\d{4}年\d{1,2}月\d{1,2}日'
        ]
        results = []
        for pattern in patterns:
            results.extend(re.findall(pattern, text))
        return list(set(results))

    def _extract_hashtags(self, text: str) -> List[str]:
        """提取标签"""
        pattern = r'#[\w\u4e00-\u9fa5]+'
        return list(set(re.findall(pattern, text)))

    def _extract_mentions(self, text: str) -> List[str]:
        """提取提及"""
        pattern = r'@[\w\u4e00-\u9fa5]+'
        return list(set(re.findall(pattern, text)))


skill = TextExtractSkill()
