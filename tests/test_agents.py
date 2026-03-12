"""
MAgentClaw Test Suite - Agent 模块测试
"""

import pytest
import asyncio
import tempfile
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestMultiAgentOrchestrator:
    """多智能体编排器测试"""

    @pytest.mark.asyncio
    async def test_orchestrator_init(self):
        """测试编排器初始化"""
        from maagentclaw.agents.multi_agent_orchestrator import MultiAgentOrchestrator

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            orchestrator = MultiAgentOrchestrator(workspace)

            assert orchestrator is not None
            assert orchestrator.workspace_path == workspace

    @pytest.mark.asyncio
    async def test_list_agents(self):
        """测试列出智能体"""
        from maagentclaw.agents.multi_agent_orchestrator import MultiAgentOrchestrator

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            orchestrator = MultiAgentOrchestrator(workspace)

            agents = orchestrator.list_agents()
            assert isinstance(agents, list)

    @pytest.mark.asyncio
    async def test_register_agent(self):
        """测试注册自定义智能体"""
        from maagentclaw.agents.multi_agent_orchestrator import (
            MultiAgentOrchestrator, AgentRole, SubAgent
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            orchestrator = MultiAgentOrchestrator(workspace)

            custom_agent = SubAgent(
                id="test-agent",
                name="Test Agent",
                role=AgentRole.SPECIALIST,
                description="Test agent",
                instructions="You are a test agent."
            )

            orchestrator.register_agent(custom_agent)

            agents = orchestrator.list_agents()
            agent_ids = [a["id"] for a in agents]
            assert "test-agent" in agent_ids

    @pytest.mark.asyncio
    async def test_unregister_agent(self):
        """测试注销智能体"""
        from maagentclaw.agents.multi_agent_orchestrator import (
            MultiAgentOrchestrator, AgentRole, SubAgent
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            orchestrator = MultiAgentOrchestrator(workspace)

            custom_agent = SubAgent(
                id="temp-agent",
                name="Temp Agent",
                role=AgentRole.SPECIALIST,
                description="Temp agent",
                instructions="You are a temp agent."
            )

            orchestrator.register_agent(custom_agent)
            orchestrator.unregister_agent("temp-agent")

            agents = orchestrator.list_agents()
            agent_ids = [a["id"] for a in agents]
            assert "temp-agent" not in agent_ids


class TestAgents:
    """Agent 测试"""

    @pytest.mark.asyncio
    async def test_coordinator_agent(self):
        """测试协调者 Agent"""
        from maagentclaw.agents.multi_agent_orchestrator import (
            MultiAgentOrchestrator, AgentRole, SubAgent
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            orchestrator = MultiAgentOrchestrator(workspace)

            agents = orchestrator.list_agents()
            agent_ids = [a["id"] for a in agents]

            assert "coordinator" in agent_ids

    @pytest.mark.asyncio
    async def test_planner_agent(self):
        """测试规划者 Agent"""
        from maagentclaw.agents.multi_agent_orchestrator import MultiAgentOrchestrator

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            orchestrator = MultiAgentOrchestrator(workspace)

            agents = orchestrator.list_agents()
            agent_ids = [a["id"] for a in agents]

            assert "planner" in agent_ids


class TestAgentRoles:
    """Agent 角色测试"""

    @pytest.mark.asyncio
    async def test_agent_role_enum(self):
        """测试 Agent 角色枚举"""
        from maagentclaw.agents.multi_agent_orchestrator import AgentRole

        assert AgentRole.COORDINATOR.value == "coordinator"
        assert AgentRole.PLANNER.value == "planner"
        assert AgentRole.EXECUTOR.value == "executor"
        assert AgentRole.SPECIALIST.value == "specialist"


class TestAgentModes:
    """Agent 模式测试"""

    @pytest.mark.asyncio
    async def test_agent_mode_enum(self):
        """测试 Agent 模式枚举"""
        from maagentclaw.agents.multi_agent_orchestrator import AgentMode

        assert AgentMode.AUTO.value == "auto"
        assert AgentMode.RUN.value == "run"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
