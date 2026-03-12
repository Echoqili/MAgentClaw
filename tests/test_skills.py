"""
MAgentClaw Test Suite - 技能和其他功能测试
"""

import pytest
import asyncio
import tempfile
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestWebScrapeSkill:
    """网页抓取技能测试"""

    @pytest.mark.asyncio
    async def test_web_scrape_init(self):
        """测试网页抓取初始化"""
        from maagentclaw.skills.web_scrape import WebScrapeSkill

        skill = WebScrapeSkill()

        assert skill is not None


class TestTextExtractSkill:
    """文本提取技能测试"""

    @pytest.mark.asyncio
    async def test_text_extract_init(self):
        """测试文本提取初始化"""
        from maagentclaw.skills.text_extract import TextExtractSkill

        skill = TextExtractSkill()

        assert skill is not None


class TestImageAnalysisSkill:
    """图像分析技能测试"""

    @pytest.mark.asyncio
    async def test_image_analysis_init(self):
        """测试图像分析初始化"""
        from maagentclaw.skills.image_analysis import ImageAnalysisSkill

        skill = ImageAnalysisSkill()

        assert skill is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
