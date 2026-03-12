"""
MAgentClaw Test Suite - 心跳模块测试
"""

import pytest
import asyncio
import tempfile
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestHeartbeatTask:
    """心跳任务测试"""

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


class TestHeartbeatConfig:
    """心跳配置测试"""

    @pytest.mark.asyncio
    async def test_heartbeat_config_defaults(self):
        """测试心跳配置默认值"""
        from maagentclaw.managers.heartbeat_manager import HeartbeatConfig

        config = HeartbeatConfig()

        assert config.enabled is True
        assert config.interval == 60
        assert config.max_retries == 3
        assert config.timeout == 300

    @pytest.mark.asyncio
    async def test_heartbeat_config_custom(self):
        """测试自定义心跳配置"""
        from maagentclaw.managers.heartbeat_manager import HeartbeatConfig

        config = HeartbeatConfig(
            enabled=False,
            interval=30,
            max_retries=5,
            timeout=600
        )

        assert config.enabled is False
        assert config.interval == 30
        assert config.max_retries == 5
        assert config.timeout == 600


class TestHeartbeatParser:
    """心跳解析器测试"""

    @pytest.mark.asyncio
    async def test_heartbeat_parser_empty(self):
        """测试解析空文件"""
        from maagentclaw.managers.heartbeat_manager import HeartbeatParser

        with tempfile.TemporaryDirectory() as tmpdir:
            empty_file = Path(tmpdir) / "empty.md"
            empty_file.write_text("")

            tasks = HeartbeatParser.parse(empty_file)

            assert tasks == []


class TestHeartbeatManager:
    """心跳管理器测试"""

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

    @pytest.mark.asyncio
    async def test_heartbeat_add_task(self):
        """测试添加心跳任务"""
        from maagentclaw.managers.heartbeat_manager import HeartbeatManager, HeartbeatTask, HeartbeatConfig

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            config = HeartbeatConfig()
            manager = HeartbeatManager(workspace, config)

            task = HeartbeatTask(
                name="add-test-task",
                interval=60,
                command="test-command"
            )

            manager.add_task(task)

            assert "add-test-task" in manager.tasks

    @pytest.mark.asyncio
    async def test_heartbeat_enable_task(self):
        """测试启用心跳任务"""
        from maagentclaw.managers.heartbeat_manager import HeartbeatManager, HeartbeatTask, HeartbeatConfig

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            config = HeartbeatConfig()
            manager = HeartbeatManager(workspace, config)

            task = HeartbeatTask(
                name="enable-test-task",
                interval=60,
                command="test-command",
                enabled=False
            )

            manager.add_task(task)
            manager.enable_task("enable-test-task")

            assert manager.tasks["enable-test-task"].enabled is True

    @pytest.mark.asyncio
    async def test_heartbeat_disable_task(self):
        """测试禁用心跳任务"""
        from maagentclaw.managers.heartbeat_manager import HeartbeatManager, HeartbeatTask, HeartbeatConfig

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            config = HeartbeatConfig()
            manager = HeartbeatManager(workspace, config)

            task = HeartbeatTask(
                name="disable-test-task",
                interval=60,
                command="test-command",
                enabled=True
            )

            manager.add_task(task)
            manager.disable_task("disable-test-task")

            assert manager.tasks["disable-test-task"].enabled is False

    @pytest.mark.asyncio
    async def test_heartbeat_get_task_status(self):
        """测试获取任务状态"""
        from maagentclaw.managers.heartbeat_manager import HeartbeatManager, HeartbeatTask, HeartbeatConfig

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            config = HeartbeatConfig()
            manager = HeartbeatManager(workspace, config)

            task = HeartbeatTask(
                name="status-test-task",
                interval=60,
                command="test-command"
            )

            manager.add_task(task)
            status = manager.get_task_status("status-test-task")

            assert status is not None
            assert status["name"] == "status-test-task"

    @pytest.mark.asyncio
    async def test_heartbeat_statistics(self):
        """测试心跳统计"""
        from maagentclaw.managers.heartbeat_manager import HeartbeatManager, HeartbeatTask, HeartbeatConfig

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            config = HeartbeatConfig()
            manager = HeartbeatManager(workspace, config)

            task = HeartbeatTask(
                name="stats-task",
                interval=60,
                command="test-command"
            )

            manager.add_task(task)
            stats = manager.get_statistics()

            assert "total_tasks" in stats
            assert stats["total_tasks"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
