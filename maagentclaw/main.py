"""
MAgentClaw 主程序入口
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from maagentclaw.core.agent import AgentConfig
from maagentclaw.managers.agent_manager import AgentManager
from maagentclaw.managers.collaboration import CollaborationManager, CollaborationMode
from maagentclaw.config.config_manager import ConfigManager
from maagentclaw.agents.examples import SimpleAgent, TaskAgent, CoordinatorAgent
from maagentclaw.interfaces.web_interface import WebInterface
from maagentclaw.utils.helpers import setup_logger


async def main():
    """主函数"""
    # 设置日志
    logger = setup_logger("maagentclaw")
    logger.info("启动 MAgentClaw 系统...")
    
    # 初始化配置管理器
    config_manager = ConfigManager()
    config_manager.create_default_configs()
    
    # 初始化 Agent 管理器
    agent_manager = AgentManager()
    
    # 创建示例 Agent
    agents_config = [
        AgentConfig(
            name="assistant",
            role="assistant",
            description="通用助手 Agent",
            model="default"
        ),
        AgentConfig(
            name="task_executor",
            role="executor",
            description="任务执行 Agent",
            model="default"
        ),
        AgentConfig(
            name="coordinator",
            role="coordinator",
            description="协调器 Agent",
            model="default"
        )
    ]
    
    # 注册 Agent
    for config in agents_config:
        if config.role == "assistant":
            agent = SimpleAgent(config)
        elif config.role == "executor":
            agent = TaskAgent(config)
        elif config.role == "coordinator":
            agent = CoordinatorAgent(config)
        else:
            agent = SimpleAgent(config)
        
        agent_manager.register_agent(agent, config)
        logger.info(f"注册 Agent: {config.name} ({config.role})")
    
    # 初始化协作管理器
    collaboration_manager = CollaborationManager(agent_manager)
    
    # 创建协作会话示例
    session = collaboration_manager.create_session(
        mode=CollaborationMode.COLLABORATIVE,
        participants=["assistant", "task_executor"]
    )
    logger.info(f"创建协作会话：{session.id}")
    
    # 初始化 Web 界面
    web_interface = WebInterface(
        agent_manager=agent_manager,
        config_manager=config_manager,
        collaboration_manager=collaboration_manager
    )
    
    logger.info("MAgentClaw 系统初始化完成")
    logger.info(f"Web 界面地址：http://localhost:8000")
    logger.info("按 Ctrl+C 退出")
    
    # 运行 Web 服务器
    try:
        web_interface.run(host="0.0.0.0", port=8000, debug=False)
    except KeyboardInterrupt:
        logger.info("正在关闭系统...")
        # 停止所有 Agent
        for agent_name in agent_manager.list_agents():
            await agent_manager.stop_agent(agent_name)
        logger.info("系统已关闭")


if __name__ == "__main__":
    asyncio.run(main())
