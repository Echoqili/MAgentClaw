"""
MAgentClaw Test Suite - 配置和工具测试
"""

import pytest
import asyncio
import tempfile
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestConfigManager:
    """配置管理器测试"""

    @pytest.mark.asyncio
    async def test_load_agents_config(self):
        """测试加载 Agent 配置"""
        from maagentclaw.config.config_manager import ConfigManager

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            config_dir = workspace / "config"
            config_dir.mkdir()

            agents_config = {
                "test-agent": {
                    "name": "test-agent",
                    "role": "assistant"
                }
            }

            (config_dir / "agents.json").write_text(json.dumps(agents_config))

            manager = ConfigManager(workspace)
            config = manager.load_agents_config()

            assert config is not None

    @pytest.mark.asyncio
    async def test_load_system_config(self):
        """测试加载系统配置"""
        from maagentclaw.config.config_manager import ConfigManager

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            config_dir = workspace / "config"
            config_dir.mkdir()

            system_config = {
                "server": {"host": "0.0.0.0", "port": 8000}
            }

            (config_dir / "system.json").write_text(json.dumps(system_config))

            manager = ConfigManager(workspace)
            config = manager.load_system_config()

            assert config is not None


class TestHelpers:
    """工具函数测试"""

    @pytest.mark.asyncio
    async def test_generate_id(self):
        """测试 ID 生成"""
        from maagentclaw.utils.helpers import generate_id

        id1 = generate_id()
        id2 = generate_id()

        assert id1 != id2
        assert len(id1) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
