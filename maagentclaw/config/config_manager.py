"""
配置管理模块
管理 Agent 配置、模型配置和系统配置
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from datetime import datetime


@dataclass
class ModelConfig:
    """模型配置类"""
    name: str
    provider: str  # openai, azure, qwen, local 等
    api_key: str = ""
    api_base: str = ""
    model_name: str = ""
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 30
    retry_times: int = 3


@dataclass
class AgentConfigData:
    """Agent 配置数据类"""
    name: str
    role: str
    description: str = ""
    model: str = "default"
    workspace: str = "default"
    max_iterations: int = 10
    temperature: float = 0.7
    tools: List[str] = field(default_factory=list)
    memory_enabled: bool = True
    verbose: bool = False
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class SystemConfig:
    """系统配置类"""
    workspace_base: str = "workspaces"
    log_level: str = "INFO"
    log_dir: str = "logs"
    max_concurrent_agents: int = 10
    default_model: str = "default"
    enable_web_interface: bool = True
    web_host: str = "0.0.0.0"
    web_port: int = 8000
    enable_api: bool = True
    api_host: str = "0.0.0.0"
    api_port: int = 8001


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.agents_config_file = self.config_dir / "agents.json"
        self.models_config_file = self.config_dir / "models.json"
        self.system_config_file = self.config_dir / "system.json"
        
        self.agents: Dict[str, AgentConfigData] = {}
        self.models: Dict[str, ModelConfig] = {}
        self.system: SystemConfig = SystemConfig()
        
        self.load_all_configs()
    
    def load_all_configs(self):
        """加载所有配置"""
        self.load_agents_config()
        self.load_models_config()
        self.load_system_config()
    
    def load_agents_config(self) -> Dict[str, AgentConfigData]:
        """加载 Agent 配置"""
        if self.agents_config_file.exists():
            with open(self.agents_config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.agents = {
                    name: AgentConfigData(**config)
                    for name, config in data.items()
                }
        return self.agents
    
    def load_models_config(self) -> Dict[str, ModelConfig]:
        """加载模型配置"""
        if self.models_config_file.exists():
            with open(self.models_config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.models = {
                    name: ModelConfig(**config)
                    for name, config in data.items()
                }
        return self.models
    
    def load_system_config(self) -> SystemConfig:
        """加载系统配置"""
        if self.system_config_file.exists():
            with open(self.system_config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.system = SystemConfig(**data)
        return self.system
    
    def save_agents_config(self):
        """保存 Agent 配置"""
        data = {
            name: asdict(config)
            for name, config in self.agents.items()
        }
        with open(self.agents_config_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def save_models_config(self):
        """保存模型配置"""
        data = {
            name: asdict(config)
            for name, config in self.models.items()
        }
        with open(self.models_config_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def save_system_config(self):
        """保存系统配置"""
        with open(self.system_config_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(self.system), f, ensure_ascii=False, indent=2)
    
    def add_agent(self, config: AgentConfigData):
        """添加 Agent 配置"""
        self.agents[config.name] = config
        self.save_agents_config()
    
    def update_agent(self, name: str, updates: Dict[str, Any]):
        """更新 Agent 配置"""
        if name in self.agents:
            agent = self.agents[name]
            for key, value in updates.items():
                if hasattr(agent, key):
                    setattr(agent, key, value)
            agent.updated_at = datetime.now().isoformat()
            self.save_agents_config()
    
    def remove_agent(self, name: str):
        """删除 Agent 配置"""
        if name in self.agents:
            del self.agents[name]
            self.save_agents_config()
    
    def get_agent(self, name: str) -> Optional[AgentConfigData]:
        """获取 Agent 配置"""
        return self.agents.get(name)
    
    def list_agents(self) -> List[str]:
        """列出所有 Agent 名称"""
        return list(self.agents.keys())
    
    def add_model(self, config: ModelConfig):
        """添加模型配置"""
        self.models[config.name] = config
        self.save_models_config()
    
    def get_model(self, name: str) -> Optional[ModelConfig]:
        """获取模型配置"""
        return self.models.get(name)
    
    def get_system(self) -> SystemConfig:
        """获取系统配置"""
        return self.system
    
    def update_system(self, updates: Dict[str, Any]):
        """更新系统配置"""
        for key, value in updates.items():
            if hasattr(self.system, key):
                setattr(self.system, key, value)
        self.save_system_config()
    
    def create_default_configs(self):
        """创建默认配置"""
        # 默认模型配置
        if not self.models:
            default_model = ModelConfig(
                name="default",
                provider="openai",
                model_name="gpt-3.5-turbo"
            )
            self.add_model(default_model)
        
        # 默认 Agent 配置
        if not self.agents:
            default_agent = AgentConfigData(
                name="assistant",
                role="assistant",
                description="默认助手 Agent",
                model="default"
            )
            self.add_agent(default_agent)
        
        # 默认系统配置
        if not self.system_config_file.exists():
            self.save_system_config()
