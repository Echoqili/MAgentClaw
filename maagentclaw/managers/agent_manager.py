"""
Agent 管理器模块
负责管理多个 Agent 的生命周期和协作
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
from pathlib import Path
import json

from ..core.agent import BaseAgent, AgentConfig, AgentState, AgentMessage


class AgentManager:
    """Agent 管理器"""
    
    def __init__(self, workspace_dir: str = "workspaces"):
        self.workspace_dir = Path(workspace_dir)
        self.agents: Dict[str, BaseAgent] = {}
        self.agent_configs: Dict[str, AgentConfig] = {}
        self._lock = asyncio.Lock()
    
    def register_agent(self, agent: BaseAgent, config: Optional[AgentConfig] = None):
        """注册 Agent"""
        if config is None:
            config = agent.config
        
        self.agents[config.name] = agent
        self.agent_configs[config.name] = config
        
        if config.workspace != "default":
            workspace_path = self.workspace_dir / config.workspace
            workspace_path.mkdir(parents=True, exist_ok=True)
    
    def unregister_agent(self, name: str):
        """注销 Agent"""
        if name in self.agents:
            del self.agents[name]
        if name in self.agent_configs:
            del self.agent_configs[name]
    
    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """获取 Agent"""
        return self.agents.get(name)
    
    def list_agents(self) -> List[str]:
        """列出所有 Agent 名称"""
        return list(self.agents.keys())
    
    def get_all_states(self) -> Dict[str, AgentState]:
        """获取所有 Agent 状态"""
        return {name: agent.get_state() for name, agent in self.agents.items()}
    
    async def start_agent(self, name: str) -> bool:
        """启动指定 Agent"""
        agent = self.get_agent(name)
        if agent:
            await agent.start()
            return True
        return False
    
    async def stop_agent(self, name: str) -> bool:
        """停止指定 Agent"""
        agent = self.get_agent(name)
        if agent:
            await agent.stop()
            return True
        return False
    
    async def broadcast_message(self, message: AgentMessage, exclude: Optional[List[str]] = None) -> Dict[str, AgentMessage]:
        """广播消息给所有 Agent"""
        if exclude is None:
            exclude = []
        
        results = {}
        for name, agent in self.agents.items():
            if name not in exclude:
                try:
                    response = await agent.process(message)
                    results[name] = response
                except Exception as e:
                    results[name] = AgentMessage(
                        content=f"Error: {str(e)}",
                        role="error"
                    )
        
        return results
    
    async def route_task(self, task: str, target_agents: Optional[List[str]] = None) -> Dict[str, Any]:
        """路由任务到指定 Agent 或所有 Agent"""
        if target_agents is None:
            target_agents = list(self.agents.keys())
        
        results = {}
        for name in target_agents:
            agent = self.get_agent(name)
            if agent:
                try:
                    result = await agent.execute_task(task)
                    results[name] = {
                        "success": True,
                        "result": result
                    }
                except Exception as e:
                    results[name] = {
                        "success": False,
                        "error": str(e)
                    }
        
        return results
    
    def save_configs(self, filepath: str):
        """保存所有 Agent 配置到文件"""
        configs_data = {
            name: {
                "name": config.name,
                "role": config.role,
                "description": config.description,
                "model": config.model,
                "workspace": config.workspace,
                "tools": config.tools
            }
            for name, config in self.agent_configs.items()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(configs_data, f, ensure_ascii=False, indent=2)
    
    def load_configs(self, filepath: str) -> Dict[str, AgentConfig]:
        """从文件加载 Agent 配置"""
        with open(filepath, 'r', encoding='utf-8') as f:
            configs_data = json.load(f)
        
        configs = {}
        for name, data in configs_data.items():
            config = AgentConfig(**data)
            configs[name] = config
        
        return configs
