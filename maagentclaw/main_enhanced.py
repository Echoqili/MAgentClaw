"""
MAgentClaw 主程序入口（增强版）
集成 OpenClaw 学习成果：
- 工作空间管理
- 增强配置管理
- 会话管理
- 上下文注入
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from maagentclaw.core.agent import AgentConfig, AgentMessage
from maagentclaw.managers.agent_manager import AgentManager
from maagentclaw.managers.collaboration import CollaborationManager, CollaborationMode
from maagentclaw.managers.workspace import WorkspaceManager, AgentWorkspace
from maagentclaw.managers.session_manager import SessionManager, SessionRouter
from maagentclaw.config.enhanced_config import EnhancedConfigManager, AgentConfigData
from maagentclaw.agents.examples import SimpleAgent, TaskAgent, CoordinatorAgent
from maagentclaw.interfaces.web_interface import WebInterface
from maagentclaw.utils.helpers import setup_logger


class EnhancedAgent(SimpleAgent):
    """增强 Agent - 集成工作空间和会话管理"""
    
    def __init__(self, config: AgentConfig, workspace: AgentWorkspace, session_manager: SessionManager):
        super().__init__(config)
        self.workspace = workspace
        self.session_manager = session_manager
        self.context_injected = False
    
    async def initialize(self) -> bool:
        """初始化 Agent（注入上下文）"""
        print(f"Initializing EnhancedAgent: {self.config.name}")
        
        # 注入工作空间上下文
        if not self.context_injected:
            context = self.workspace.get_context_for_agent()
            if context:
                # 将上下文作为系统消息
                system_message = AgentMessage(
                    content=context,
                    role="system"
                )
                self.add_to_memory(system_message)
                self.context_injected = True
                print(f"[{self.config.name}] 上下文注入完成")
        
        return True
    
    async def process(self, message: AgentMessage) -> AgentMessage:
        """处理消息（带会话管理）"""
        # 获取或创建会话
        session = self.session_manager.get_or_create_session(
            agent_id=self.id,
            channel="default",
            peer="user",
            scope="per-peer"
        )
        
        # 添加用户消息到会话
        self.session_manager.add_message(session.id, message)
        
        # 处理消息
        response = await super().process(message)
        
        # 添加助手响应到会话
        self.session_manager.add_message(session.id, response)
        
        return response


async def main():
    """主函数"""
    # 设置日志
    logger = setup_logger("maagentclaw")
    logger.info("启动 MAgentClaw 系统（增强版）...")
    
    # 初始化增强配置管理器
    logger.info("初始化配置管理器...")
    config_manager = EnhancedConfigManager()
    config_manager.create_default_configs()
    
    # 验证配置
    errors = config_manager.validate_all_configs()
    if errors:
        logger.warning("配置验证警告:")
        for error in errors:
            logger.warning(f"  - {error}")
    
    # 启动配置热重载
    config_manager.start_config_watcher(interval=5.0)
    logger.info("配置热重载已启动")
    
    # 初始化工作空间管理器
    logger.info("初始化工作空间管理器...")
    workspace_manager = WorkspaceManager()
    
    # 初始化会话管理器
    logger.info("初始化会话管理器...")
    session_manager = SessionManager("~/.maagentclaw/sessions")
    session_router = SessionRouter(session_manager)
    
    # 初始化 Agent 管理器
    agent_manager = AgentManager()
    
    # 创建增强 Agent
    agents_config = [
        AgentConfig(
            name="assistant",
            role="assistant",
            description="通用助手 Agent",
            model="default",
            workspace="assistant"
        ),
        AgentConfig(
            name="task_executor",
            role="executor",
            description="任务执行 Agent",
            model="default",
            workspace="executor"
        ),
        AgentConfig(
            name="coordinator",
            role="coordinator",
            description="协调器 Agent",
            model="default",
            workspace="coordinator"
        )
    ]
    
    # 注册 Agent
    for config in agents_config:
        # 获取或创建工作空间
        workspace = workspace_manager.get_workspace(config.workspace)
        
        # 创建增强 Agent
        if config.role == "assistant":
            agent = EnhancedAgent(config, workspace, session_manager)
        elif config.role == "executor":
            agent = EnhancedAgent(config, workspace, session_manager)
        elif config.role == "coordinator":
            agent = EnhancedAgent(config, workspace, session_manager)
        else:
            agent = EnhancedAgent(config, workspace, session_manager)
        
        agent_manager.register_agent(agent, config)
        logger.info(f"注册 Agent: {config.name} ({config.role}) - 工作空间：{config.workspace}")
    
    # 初始化协作管理器
    collaboration_manager = CollaborationManager(agent_manager)
    
    # 创建协作会话示例
    session = collaboration_manager.create_session(
        mode=CollaborationMode.COLLABORATIVE,
        participants=["assistant", "task_executor"]
    )
    logger.info(f"创建协作会话：{session.id}")
    
    # 初始化 Web 界面（使用增强配置管理器）
    web_interface = WebInterface(
        agent_manager=agent_manager,
        config_manager=config_manager,
        collaboration_manager=collaboration_manager
    )
    
    # 显示系统信息
    logger.info("=" * 60)
    logger.info("MAgentClaw 系统初始化完成")
    logger.info(f"工作空间目录：{workspace_manager.base_dir}")
    logger.info(f"会话目录：{session_manager.sessions_dir}")
    logger.info(f"配置目录：{config_manager.config_dir}")
    logger.info(f"Web 界面地址：http://localhost:8000")
    logger.info("按 Ctrl+C 退出")
    logger.info("=" * 60)
    
    # 显示 Agent 信息
    logger.info("已注册 Agent:")
    for agent_name in agent_manager.list_agents():
        agent = agent_manager.get_agent(agent_name)
        if agent:
            workspace = workspace_manager.get_workspace(agent.config.workspace)
            logger.info(f"  - {agent_name}: {agent.config.role} (工作空间：{agent.config.workspace})")
    
    # 显示配置信息
    logger.info("配置信息:")
    logger.info(f"  - Agent 数量：{len(config_manager.agents)}")
    logger.info(f"  - 模型数量：{len(config_manager.models)}")
    logger.info(f"  - 系统配置：{config_manager.system.log_level} 日志级别")
    
    # 运行 Web 服务器
    try:
        web_interface.run(host="0.0.0.0", port=8000, debug=False)
    except KeyboardInterrupt:
        logger.info("正在关闭系统...")
        
        # 停止配置监视器
        config_manager.stop_config_watcher()
        
        # 停止所有 Agent
        for agent_name in agent_manager.list_agents():
            await agent_manager.stop_agent(agent_name)
        
        logger.info("系统已关闭")


if __name__ == "__main__":
    asyncio.run(main())
