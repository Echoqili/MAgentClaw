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


async def test_enhanced_agent_config():
    """测试增强版 Agent 配置（角色定义）"""
    print("\n=== 测试增强版 Agent 配置 ===")
    
    # 创建带有增强角色的 Agent
    config = AgentConfig(
        name="researcher",
        role="高级研究员",
        description="专业的技术研究员",
        goal="深入分析技术趋势，提供专业见解",
        backstory="你是一位经验丰富的技术研究员，拥有10年行业经验，擅长发现新兴技术趋势",
        responsibilities=[
            "收集和分析最新技术信息",
            "撰写技术研究报告",
            "为团队提供技术咨询"
        ],
        skills=["信息检索", "数据分析", "报告撰写"],
        available_tools=["web_search", "pdf_reader", "code_interpreter"],
        allow_delegation=True,
        max_delegation_depth=2,
        verbose=True
    )
    
    agent = SimpleAgent(config)
    
    # 生成系统提示
    system_prompt = agent.generate_system_prompt()
    print(f"\n生成的系统提示：\n{system_prompt}")
    
    # 检查委托能力
    can_delegate = agent.can_delegate()
    print(f"\n允许委托：{can_delegate}")
    
    print("\n✓ 增强版 Agent 配置测试完成")


async def test_checkpoint():
    """测试断点续传功能"""
    print("\n=== 测试断点续传功能 ===")
    
    from maagentclaw.agents.examples import SimpleAgent
    from maagentclaw.managers.collaboration import CollaborationSession, CollaborationMode
    
    # 创建 Agent
    config = AgentConfig(name="test_agent", role="tester")
    agent = SimpleAgent(config)
    
    # 添加一些记忆
    for i in range(5):
        msg = AgentMessage(content=f"消息 {i}", role="user")
        agent.add_to_memory(msg)
    
    # 添加任务历史
    agent.add_task_to_history("任务1", {"result": "完成"})
    agent.add_task_to_history("任务2", {"result": "完成"})
    
    # 获取检查点数据
    checkpoint = agent.get_checkpoint_data()
    print(f"\n检查点数据已保存")
    print(f"记忆数量：{len(checkpoint['memory'])}")
    print(f"任务历史：{len(checkpoint['state']['task_history'])}")
    
    # 模拟加载检查点
    new_agent = SimpleAgent(AgentConfig(name="new_agent", role="tester"))
    new_agent.load_checkpoint_data(checkpoint)
    
    print(f"\n恢复后记忆数量：{len(new_agent.memory)}")
    print(f"恢复后任务历史：{len(new_agent.state.task_history)}")
    
    # 测试协作会话的检查点
    session = CollaborationSession(
        name="测试会话",
        mode=CollaborationMode.PARALLEL,
        participants=["agent1", "agent2"],
        checkpoint_enabled=True
    )
    
    checkpoint_data = session.save_checkpoint()
    print(f"\n协作会话检查点已保存")
    print(f"会话名称：{checkpoint_data['name']}")
    print(f"参与者：{checkpoint_data['participants']}")
    
    print("\n✓ 断点续传功能测试完成")


async def test_parallel_tools():
    """测试并行工具执行"""
    print("\n=== 测试并行工具执行 ===")
    
    from maagentclaw.tools import TaskExecutor, ToolRegistry
    from maagentclaw.tools.task_executor import BaseToolExecutor
    
    # 定义测试工具
    class MockTool(BaseToolExecutor):
        async def execute(self, **kwargs):
            await asyncio.sleep(0.1)  # 模拟执行时间
            return f"执行了 {self.name}"
    
    # 创建工具注册中心
    registry = ToolRegistry()
    registry.register(MockTool("tool1", "工具1"))
    registry.register(MockTool("tool2", "工具2"))
    registry.register(MockTool("tool3", "工具3"))
    
    # 创建执行器
    executor = TaskExecutor(registry)
    
    # 测试并行执行
    import time
    start = time.time()
    
    result = await executor.execute_single_task(
        task="测试任务",
        tools=["tool1", "tool2", "tool3"],
        context={}
    )
    
    elapsed = time.time() - start
    
    print(f"\n执行结果：")
    print(f"  成功：{result['success']}")
    print(f"  并行执行：{result['parallel']}")
    print(f"  执行时间：{elapsed:.2f}秒")
    print(f"  工具数量：{len(result['tool_results'])}")
    
    # 测试执行统计
    stats = executor.get_execution_stats()
    print(f"\n执行统计：{stats}")
    
    print("\n✓ 并行工具执行测试完成")


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
        await test_enhanced_agent_config()
        await test_checkpoint()
        await test_parallel_tools()
        
        print("\n" + "=" * 60)
        print("✓ 所有测试通过!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
