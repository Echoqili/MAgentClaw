"""
MAgentClaw Test Suite - 模型测试
"""

import pytest
import asyncio
import tempfile
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestModelConfig:
    """模型配置测试"""

    @pytest.mark.asyncio
    async def test_model_config_creation(self):
        """测试模型配置创建"""
        from maagentclaw.models.base_model import ModelConfig

        config = ModelConfig(
            name="test-model",
            provider="openai",
            model_name="gpt-4",
            api_key="test-key"
        )

        assert config.name == "test-model"
        assert config.provider == "openai"
        assert config.model_name == "gpt-4"
        assert config.temperature == 0.7


class TestModelResponse:
    """模型响应测试"""

    @pytest.mark.asyncio
    async def test_model_response_creation(self):
        """测试模型响应创建"""
        from maagentclaw.models.base_model import ModelResponse

        response = ModelResponse(
            content="Hello",
            role="assistant"
        )

        assert response.content == "Hello"
        assert response.role == "assistant"


class TestMessage:
    """消息测试"""

    @pytest.mark.asyncio
    async def test_message_creation(self):
        """测试消息创建"""
        from maagentclaw.models.base_model import Message

        message = Message(
            role="user",
            content="Hello"
        )

        assert message.role == "user"
        assert message.content == "Hello"

    @pytest.mark.asyncio
    async def test_message_to_dict(self):
        """测试消息序列化"""
        from maagentclaw.models.base_model import Message

        message = Message(
            role="user",
            content="Hello"
        )

        msg_dict = message.to_dict()

        assert msg_dict["role"] == "user"
        assert msg_dict["content"] == "Hello"


class TestModelManager:
    """模型管理器测试"""

    @pytest.mark.asyncio
    async def test_model_manager_init(self):
        """测试模型管理器初始化"""
        from maagentclaw.models.model_manager import ModelManager

        manager = ModelManager()

        assert manager is not None
        assert isinstance(manager.models, dict)
        assert manager.default_model is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
