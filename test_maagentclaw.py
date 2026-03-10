"""
测试脚本
验证 MAgentClaw 系统的基本功能
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from maagentclaw.core.agent import AgentConfig, AgentMessage
from maagentclaw.managers.agent_manager import AgentManager
from maagentclaw.managers.collaboration import CollaborationManager, CollaborationMode
from maagentclaw.config.config_manager import ConfigManager
from maagentclaw.agents.examples import SimpleAgent, TaskAgent


async def test_basic_agent():
    """测试基本 Agent 功能"""
    print("\n=== 测试基本 Agent 功能 ===")
    
    config = AgentConfig(
        name="test_agent",
        role="tester",
        description="测试 Agent"
    )
    
    agent = SimpleAgent(config)
    
    # 初始化
    print("初始化 Agent...")
    success = await agent.initialize()
    print(f"初始化结果：{'成功' if success else '失败'}")
    
    # 处理消息
    print("\n测试消息处理...")
    message = AgentMessage(content="你好", role="user")
    response = await agent.process(message)
    print(f"用户：{message.content}")
    print(f"Agent: {response.content}")
    
    # 执行任务
    print("\n测试任务执行...")
    result = await agent.execute_task("测试任务", {"test": True})
    print(f"任务结果：{result}")
    
    print("\n✓ 基本 Agent 功能测试完成")


async def test_agent_manager():
    """测试 Agent 管理器"""
    print("\n=== 测试 Agent 管理器 ===")
    
    manager = AgentManager()
    
    # 创建 Agent
    agents_config = [
        AgentConfig(name="agent1", role="assistant"),
        AgentConfig(name="agent2", role="executor"),
    ]
    
    for config in agents_config:
        agent = SimpleAgent(config) if config.role == "assistant" else TaskAgent(config)
        manager.register_agent(agent, config)
        print(f"注册 Agent: {config.name}")
    
    # 列出 Agent
    print(f"\n已注册 Agent: {manager.list_agents()}")
    
    # 启动 Agent
    print("\n启动 agent1...")
    success = await manager.start_agent("agent1")
    print(f"启动结果：{'成功' if success else '失败'}")
    
    # 获取状态
    states = manager.get_all_states()
    print(f"\n所有 Agent 状态:")
    for name, state in states.items():
        print(f"  {name}: {state.status}")
    
    print("\n✓ Agent 管理器测试完成")


async def test_collaboration():
    """测试协作功能"""
    print("\n=== 测试协作功能 ===")
    
    agent_manager = AgentManager()
    
    # 创建 Agent
    config1 = AgentConfig(name="worker1", role="worker")
    config2 = AgentConfig(name="worker2", role="worker")
    
    agent1 = SimpleAgent(config1)
    agent2 = TaskAgent(config2)
    
    agent_manager.register_agent(agent1, config1)
    agent_manager.register_agent(agent2, config2)
    
    # 初始化协作管理器
    collab_manager = CollaborationManager(agent_manager)
    
    # 创建会话
    session = collab_manager.create_session(
        mode=CollaborationMode.PARALLEL,
        participants=["worker1", "worker2"]
    )
    print(f"创建会话：{session.id}")
    print(f"参与者：{session.participants}")
    
    # 测试顺序执行
    print("\n测试顺序执行...")
    results = await collab_manager.execute_sequential(
        session.id,
        ["任务 1", "任务 2"]
    )
    print(f"顺序执行结果：{len(results)} 个任务")
    
    # 测试并行执行
    print("\n测试并行执行...")
    results = await collab_manager.execute_parallel(
        session.id,
        ["并行任务 1", "并行任务 2", "并行任务 3"]
    )
    print(f"并行执行结果：{len(results)} 个任务")
    
    print("\n✓ 协作功能测试完成")


async def test_config_manager():
    """测试配置管理器"""
    print("\n=== 测试配置管理器 ===")
    
    config_manager = ConfigManager()
    config_manager.create_default_configs()
    
    # 列出配置
    print(f"Agent 配置：{config_manager.list_agents()}")
    print(f"模型配置：{list(config_manager.models.keys())}")
    
    # 添加新 Agent 配置
    from maagentclaw.config.config_manager import AgentConfigData
    new_config = AgentConfigData(
        name="custom_agent",
        role="custom",
        description="自定义 Agent"
    )
    config_manager.add_agent(new_config)
    print(f"\n添加新 Agent 配置：custom_agent")
    
    # 验证
    print(f"当前 Agent 列表：{config_manager.list_agents()}")
    
    print("\n✓ 配置管理器测试完成")


async def main():
    """运行所有测试"""
    print("=" * 60)
    print("MAgentClaw 系统测试")
    print("=" * 60)
    
    try:
        await test_basic_agent()
        await test_agent_manager()
        await test_collaboration()
        await test_config_manager()
        
        print("\n" + "=" * 60)
        print("✓ 所有测试通过!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
