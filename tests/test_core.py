"""
MAgentClaw Test Suite - 核心模块测试

使用 pytest 框架的正式测试
"""

import pytest
import asyncio
import tempfile
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestHeartbeatManager:
    """心跳管理器测试"""

    @pytest.mark.asyncio
    async def test_heartbeat_config_creation(self):
        """测试心跳配置创建"""
        from maagentclaw.managers.heartbeat_manager import HeartbeatConfig

        config = HeartbeatConfig(
            enabled=True,
            interval=30,
            max_retries=3,
            timeout=60
        )

        assert config.enabled is True
        assert config.interval == 30
        assert config.max_retries == 3
        assert config.timeout == 60
        assert config.suppress_duplicates is True

    @pytest.mark.asyncio
    async def test_heartbeat_task_creation(self):
        """测试心跳任务创建"""
        from maagentclaw.managers.heartbeat_manager import HeartbeatTask, TaskStatus

        task = HeartbeatTask(
            name="test-task",
            interval=60,
            command="test-command",
            enabled=True
        )

        assert task.name == "test-task"
        assert task.interval == 60
        assert task.command == "test-command"
        assert task.enabled is True
        assert task.status == TaskStatus.PENDING
        assert task.execution_count == 0

    @pytest.mark.asyncio
    async def test_heartbeat_task_to_dict(self):
        """测试心跳任务序列化"""
        from maagentclaw.managers.heartbeat_manager import HeartbeatTask

        task = HeartbeatTask(
            name="test-task",
            interval=60,
            command="test-command"
        )

        task_dict = task.to_dict()

        assert task_dict["name"] == "test-task"
        assert task_dict["interval"] == 60
        assert task_dict["command"] == "test-command"
        assert task_dict["enabled"] is True

    @pytest.mark.asyncio
    async def test_heartbeat_manager_init(self):
        """测试心跳管理器初始化"""
        from maagentclaw.managers.heartbeat_manager import HeartbeatManager, HeartbeatConfig

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            config = HeartbeatConfig()

            manager = HeartbeatManager(workspace, config)

            assert manager.workspace_path == workspace
            assert manager.config == config
            assert isinstance(manager.tasks, dict)
            assert manager.running is False


class TestSkillManager:
    """技能管理器测试"""

    @pytest.mark.asyncio
    async def test_skill_metadata_creation(self):
        """测试技能元数据创建"""
        from maagentclaw.managers.skill_manager import SkillMetadata

        metadata = SkillMetadata(
            name="test-skill",
            version="1.0.0",
            description="Test skill",
            author="Test Author",
            email="test@example.com",
            tags=["test", "example"]
        )

        assert metadata.name == "test-skill"
        assert metadata.version == "1.0.0"
        assert metadata.description == "Test skill"
        assert metadata.tags == ["test", "example"]

    @pytest.mark.asyncio
    async def test_skill_config_creation(self):
        """测试技能配置创建"""
        from maagentclaw.managers.skill_manager import SkillConfig

        config = SkillConfig(
            enabled=True,
            timeout=60,
            max_retries=3,
            rate_limit=10
        )

        assert config.enabled is True
        assert config.timeout == 60
        assert config.max_retries == 3
        assert config.rate_limit == 10

    @pytest.mark.asyncio
    async def test_skill_result_creation(self):
        """测试技能结果创建"""
        from maagentclaw.managers.skill_manager import SkillResult

        result = SkillResult(
            success=True,
            data={"message": "Hello"},
            duration=0.5
        )

        assert result.success is True
        assert result.data == {"message": "Hello"}
        assert result.duration == 0.5

    @pytest.mark.asyncio
    async def test_skill_result_error(self):
        """测试技能错误结果"""
        from maagentclaw.managers.skill_manager import SkillResult

        result = SkillResult(
            success=False,
            error="Test error",
            duration=0.1
        )

        assert result.success is False
        assert result.error == "Test error"


class TestToolManager:
    """工具管理器测试"""

    @pytest.mark.asyncio
    async def test_tool_metadata_creation(self):
        """测试工具元数据创建"""
        from maagentclaw.managers.tool_manager import ToolMetadata

        metadata = ToolMetadata(
            name="test-tool",
            version="1.0.0",
            description="Test tool",
            author="Test Author",
            category="utility"
        )

        assert metadata.name == "test-tool"
        assert metadata.version == "1.0.0"
        assert metadata.category == "utility"

    @pytest.mark.asyncio
    async def test_tool_config_creation(self):
        """测试工具配置创建"""
        from maagentclaw.managers.tool_manager import ToolConfig

        config = ToolConfig(
            enabled=True,
            sandbox_enabled=True,
            rate_limit=10
        )

        assert config.enabled is True
        assert config.sandbox_enabled is True

    @pytest.mark.asyncio
    async def test_tool_result_creation(self):
        """测试工具结果创建"""
        from maagentclaw.managers.tool_manager import ToolResult

        result = ToolResult(
            success=True,
            data={"result": "test"},
            duration=0.3
        )

        assert result.success is True
        assert result.data == {"result": "test"}

    @pytest.mark.asyncio
    async def test_tool_result_error(self):
        """测试工具错误结果"""
        from maagentclaw.managers.tool_manager import ToolResult

        result = ToolResult(
            success=False,
            error="Tool execution failed"
        )

        assert result.success is False
        assert result.error == "Tool execution failed"

    @pytest.mark.asyncio
    async def test_tool_manager_init(self):
        """测试工具管理器初始化"""
        from maagentclaw.managers.tool_manager import ToolManager

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            manager = ToolManager(workspace)

            assert manager.workspace_path == workspace
            assert isinstance(manager.user_permissions, dict)
            assert isinstance(manager.execution_history, list)


class TestTaskParser:
    """任务解析器测试"""

    @pytest.mark.asyncio
    async def test_task_parser_init(self):
        """测试任务解析器初始化"""
        from maagentclaw.tasks.task_parser import TaskParser

        parser = TaskParser()

        assert parser is not None

    @pytest.mark.asyncio
    async def test_parse_file_operation(self):
        """测试解析文件操作"""
        from maagentclaw.tasks.task_parser import TaskParser

        parser = TaskParser()
        result = parser.parse("打开文件 test.txt")

        assert result is not None
        assert hasattr(result, 'type')
        assert hasattr(result, 'action')
        assert hasattr(result, 'confidence')

    @pytest.mark.asyncio
    async def test_parse_general_task(self):
        """测试解析通用任务"""
        from maagentclaw.tasks.task_parser import TaskParser

        parser = TaskParser()
        result = parser.parse("帮我做这件事")

        assert result is not None
        assert result.confidence >= 0


class TestEnhancedScheduler:
    """增强调度器测试"""

    @pytest.mark.asyncio
    async def test_scheduler_init(self):
        """测试调度器初始化"""
        from maagentclaw.tasks.enhanced_scheduler import EnhancedScheduler

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            scheduler = EnhancedScheduler(workspace)

            assert scheduler is not None

    @pytest.mark.asyncio
    async def test_cron_expression_parse(self):
        """测试 Cron 表达式解析"""
        from maagentclaw.tasks.enhanced_scheduler import CronExpression

        cron = CronExpression.parse("0 0 * * *")

        assert cron.minute == "0"
        assert cron.hour == "0"
        assert cron.day_of_month == "*"
        assert cron.month == "*"
        assert cron.day_of_week == "*"


class TestMemory:
    """内存测试"""

    @pytest.mark.asyncio
    async def test_memory_manager_init(self):
        """测试内存管理器初始化"""
        from maagentclaw.memory.memory_manager import MemoryManager

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            manager = MemoryManager(workspace)

            assert manager is not None


class TestConfig:
    """配置测试"""

    @pytest.mark.asyncio
    async def test_config_manager_init(self):
        """测试配置管理器初始化"""
        from maagentclaw.config.config_manager import ConfigManager

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            manager = ConfigManager(workspace)

            assert manager is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
