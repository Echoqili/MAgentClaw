"""
增强配置管理系统
参考 OpenClaw 的配置验证、热重载和 JSON5 支持
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from dataclasses import dataclass, field, asdict
import threading
import time


@dataclass
class ModelConfig:
    """模型配置（增强版）"""
    name: str
    provider: str
    model_name: str
    api_key: str = ""
    api_base: str = ""
    context_window: int = 4096
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 30
    retry_times: int = 3
    fallbacks: List[str] = field(default_factory=list)
    alias: Optional[str] = None


@dataclass
class AgentConfigData:
    """Agent 配置（增强版）"""
    name: str
    role: str
    description: str = ""
    model: str = "default"
    models: Dict[str, Any] = field(default_factory=dict)
    workspace: str = "default"
    max_iterations: int = 10
    temperature: float = 0.7
    tools: List[str] = field(default_factory=list)
    memory_enabled: bool = True
    verbose: bool = False
    thinking_default: str = "medium"  # low, medium, high
    timeout_seconds: int = 1800
    heartbeat: Dict[str, Any] = field(default_factory=lambda: {"every": "30m"})
    sandbox: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class SessionConfig:
    """会话配置"""
    dm_scope: str = "per-channel-peer"  # main, per-peer, per-channel-peer
    reset_triggers: List[str] = field(default_factory=lambda: ["/new", "/reset"])
    reset_mode: str = "daily"  # daily, idle, manual
    reset_at_hour: int = 4
    reset_idle_minutes: int = 120
    thread_bindings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChannelConfig:
    """渠道配置"""
    name: str
    enabled: bool = True
    dm_policy: str = "pairing"  # pairing, allowlist, open, disabled
    allow_from: List[str] = field(default_factory=list)
    group_policy: str = "mention"
    groups: Dict[str, Any] = field(default_factory=dict)
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemConfig:
    """系统配置（增强版）"""
    workspace_base: str = "~/.maagentclaw/workspaces"
    config_dir: str = "~/.maagentclaw/config"
    log_level: str = "INFO"
    log_dir: str = "~/.maagentclaw/logs"
    max_concurrent_agents: int = 10
    default_model: str = "default"
    enable_web_interface: bool = True
    web_host: str = "0.0.0.0"
    web_port: int = 8000
    enable_api: bool = True
    api_host: str = "0.0.0.0"
    api_port: int = 8001
    gateway_port: int = 18789
    enable_gateway: bool = False
    session: SessionConfig = field(default_factory=SessionConfig)
    channels: Dict[str, ChannelConfig] = field(default_factory=dict)


class ConfigValidator:
    """配置验证器（参考 OpenClaw 的严格验证）"""
    
    @staticmethod
    def validate_model_config(config: ModelConfig) -> List[str]:
        """验证模型配置"""
        errors = []
        
        if not config.name:
            errors.append("Model name is required")
        
        if not config.provider:
            errors.append("Model provider is required")
        
        if config.context_window <= 0:
            errors.append("Context window must be positive")
        
        if not 0 <= config.temperature <= 2:
            errors.append("Temperature must be between 0 and 2")
        
        if config.max_tokens <= 0:
            errors.append("Max tokens must be positive")
        
        return errors
    
    @staticmethod
    def validate_agent_config(config: AgentConfigData) -> List[str]:
        """验证 Agent 配置"""
        errors = []
        
        if not config.name:
            errors.append("Agent name is required")
        
        if not config.role:
            errors.append("Agent role is required")
        
        if config.max_iterations <= 0:
            errors.append("Max iterations must be positive")
        
        if config.timeout_seconds <= 0:
            errors.append("Timeout must be positive")
        
        # 验证心跳配置
        if "every" in config.heartbeat:
            every = config.heartbeat["every"]
            if every != "0m" and not every.endswith("m") and not every.endswith("h"):
                errors.append("Heartbeat interval must be in minutes (m) or hours (h)")
        
        return errors
    
    @staticmethod
    def validate_system_config(config: SystemConfig) -> List[str]:
        """验证系统配置"""
        errors = []
        
        if config.max_concurrent_agents <= 0:
            errors.append("Max concurrent agents must be positive")
        
        if not 0 < config.web_port < 65536:
            errors.append("Web port must be between 1 and 65535")
        
        if not 0 < config.api_port < 65536:
            errors.append("API port must be between 1 and 65535")
        
        return errors
    
    @staticmethod
    def validate_channel_config(config: ChannelConfig) -> List[str]:
        """验证渠道配置"""
        errors = []
        
        if not config.name:
            errors.append("Channel name is required")
        
        valid_dm_policies = ["pairing", "allowlist", "open", "disabled"]
        if config.dm_policy not in valid_dm_policies:
            errors.append(f"DM policy must be one of: {valid_dm_policies}")
        
        return errors


class EnhancedConfigManager:
    """
    增强配置管理器
    参考 OpenClaw 的配置管理：
    - JSON5 支持（使用 json 代替，但结构兼容）
    - 严格验证
    - 热重载支持
    - 配置快照
    """
    
    def __init__(self, config_dir: str = "~/.maagentclaw/config"):
        self.config_dir = Path(config_dir).expanduser()
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # 配置文件路径
        self.agents_config_file = self.config_dir / "agents.json"
        self.models_config_file = self.config_dir / "models.json"
        self.system_config_file = self.config_dir / "system.json"
        self.channels_config_file = self.config_dir / "channels.json"
        
        # 配置数据
        self.agents: Dict[str, AgentConfigData] = {}
        self.models: Dict[str, ModelConfig] = {}
        self.system: SystemConfig = SystemConfig()
        self.channels: Dict[str, ChannelConfig] = {}
        
        # 配置快照（用于热重载）
        self._config_snapshot: Dict[str, Any] = {}
        self._last_modified: Dict[str, float] = {}
        
        # 热重载支持
        self._watch_thread: Optional[threading.Thread] = None
        self._stop_watching = False
        self._reload_callbacks: List[Callable] = []
        
        # 验证器
        self.validator = ConfigValidator()
        
        # 加载配置
        self.load_all_configs()
    
    def load_all_configs(self):
        """加载所有配置"""
        self.load_agents_config()
        self.load_models_config()
        self.load_system_config()
        self.load_channels_config()
        
        # 创建配置快照
        self._take_snapshot()
    
    def _take_snapshot(self):
        """创建配置快照"""
        self._config_snapshot = {
            "agents": {name: asdict(config) for name, config in self.agents.items()},
            "models": {name: asdict(config) for name, config in self.models.items()},
            "system": asdict(self.system),
            "channels": {name: asdict(config) for name, config in self.channels.items()}
        }
    
    def _update_timestamp(self, config_type: str):
        """更新配置时间戳"""
        self._last_modified[config_type] = time.time()
    
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
                # 处理嵌套的 SessionConfig
                if "session" in data:
                    session_data = data.pop("session")
                    self.system = SystemConfig(**data)
                    self.system.session = SessionConfig(**session_data)
                else:
                    self.system = SystemConfig(**data)
        return self.system
    
    def load_channels_config(self) -> Dict[str, ChannelConfig]:
        """加载渠道配置"""
        if self.channels_config_file.exists():
            with open(self.channels_config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.channels = {
                    name: ChannelConfig(**config)
                    for name, config in data.items()
                }
        return self.channels
    
    def save_agents_config(self, validate: bool = True):
        """保存 Agent 配置"""
        # 验证所有配置
        if validate:
            all_errors = []
            for name, config in self.agents.items():
                errors = self.validator.validate_agent_config(config)
                if errors:
                    all_errors.extend([f"{name}: {error}" for error in errors])
            
            if all_errors:
                raise ValueError(f"Agent configuration validation failed:\n" + "\n".join(all_errors))
        
        # 保存配置
        data = {
            name: asdict(config)
            for name, config in self.agents.items()
        }
        with open(self.agents_config_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        self._update_timestamp("agents")
    
    def save_models_config(self, validate: bool = True):
        """保存模型配置"""
        if validate:
            all_errors = []
            for name, config in self.models.items():
                errors = self.validator.validate_model_config(config)
                if errors:
                    all_errors.extend([f"{name}: {error}" for error in errors])
            
            if all_errors:
                raise ValueError(f"Model configuration validation failed:\n" + "\n".join(all_errors))
        
        data = {
            name: asdict(config)
            for name, config in self.models.items()
        }
        with open(self.models_config_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        self._update_timestamp("models")
    
    def save_system_config(self, validate: bool = True):
        """保存系统配置"""
        if validate:
            errors = self.validator.validate_system_config(self.system)
            if errors:
                raise ValueError(f"System configuration validation failed:\n" + "\n".join(errors))
        
        data = asdict(self.system)
        with open(self.system_config_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        self._update_timestamp("system")
    
    def save_channels_config(self, validate: bool = True):
        """保存渠道配置"""
        if validate:
            all_errors = []
            for name, config in self.channels.items():
                errors = self.validator.validate_channel_config(config)
                if errors:
                    all_errors.extend([f"{name}: {error}" for error in errors])
            
            if all_errors:
                raise ValueError(f"Channel configuration validation failed:\n" + "\n".join(all_errors))
        
        data = {
            name: asdict(config)
            for name, config in self.channels.items()
        }
        with open(self.channels_config_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        self._update_timestamp("channels")
    
    def add_agent(self, config: AgentConfigData, validate: bool = True):
        """添加 Agent 配置"""
        self.agents[config.name] = config
        self.save_agents_config(validate)
    
    def update_agent(self, name: str, updates: Dict[str, Any], validate: bool = True):
        """更新 Agent 配置"""
        if name in self.agents:
            agent = self.agents[name]
            for key, value in updates.items():
                if hasattr(agent, key):
                    setattr(agent, key, value)
            agent.updated_at = datetime.now().isoformat()
            self.save_agents_config(validate)
    
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
    
    def add_model(self, config: ModelConfig, validate: bool = True):
        """添加模型配置"""
        self.models[config.name] = config
        self.save_models_config(validate)
    
    def get_model(self, name: str) -> Optional[ModelConfig]:
        """获取模型配置"""
        return self.models.get(name)
    
    def get_system(self) -> SystemConfig:
        """获取系统配置"""
        return self.system
    
    def update_system(self, updates: Dict[str, Any], validate: bool = True):
        """更新系统配置"""
        for key, value in updates.items():
            if hasattr(self.system, key):
                setattr(self.system, key, value)
        self.save_system_config(validate)
    
    def add_channel(self, name: str, config: ChannelConfig, validate: bool = True):
        """添加渠道配置"""
        self.channels[name] = config
        self.save_channels_config(validate)
    
    def get_channel(self, name: str) -> Optional[ChannelConfig]:
        """获取渠道配置"""
        return self.channels.get(name)
    
    def create_default_configs(self):
        """创建默认配置"""
        # 默认模型配置
        if not self.models:
            default_model = ModelConfig(
                name="default",
                provider="openai",
                model_name="gpt-3.5-turbo",
                context_window=4096
            )
            self.add_model(default_model)
        
        # 默认 Agent 配置
        if not self.agents:
            default_agent = AgentConfigData(
                name="assistant",
                role="assistant",
                description="默认助手 Agent",
                model="default",
                workspace="default"
            )
            self.add_agent(default_agent)
        
        # 默认系统配置
        if not self.system_config_file.exists():
            self.save_system_config()
        
        # 默认渠道配置
        if not self.channels:
            default_channel = ChannelConfig(
                name="default",
                enabled=True,
                dm_policy="pairing"
            )
            self.add_channel("default", default_channel)
    
    def validate_all_configs(self) -> List[str]:
        """验证所有配置"""
        all_errors = []
        
        # 验证 Agent 配置
        for name, config in self.agents.items():
            errors = self.validator.validate_agent_config(config)
            if errors:
                all_errors.extend([f"Agent '{name}': {error}" for error in errors])
        
        # 验证模型配置
        for name, config in self.models.items():
            errors = self.validator.validate_model_config(config)
            if errors:
                all_errors.extend([f"Model '{name}': {error}" for error in errors])
        
        # 验证系统配置
        errors = self.validator.validate_system_config(self.system)
        if errors:
            all_errors.extend([f"System: {error}" for error in errors])
        
        # 验证渠道配置
        for name, config in self.channels.items():
            errors = self.validator.validate_channel_config(config)
            if errors:
                all_errors.extend([f"Channel '{name}': {error}" for error in errors])
        
        return all_errors
    
    def get_config_snapshot(self) -> Dict[str, Any]:
        """获取配置快照"""
        return self._config_snapshot.copy()
    
    def has_changed(self, config_type: str) -> bool:
        """检查配置是否已更改"""
        if config_type not in self._last_modified:
            return True
        
        file_path = getattr(self, f"{config_type}_config_file")
        if file_path.exists():
            current_mtime = file_path.stat().st_mtime
            return current_mtime > self._last_modified[config_type]
        
        return False
    
    def register_reload_callback(self, callback: Callable):
        """注册配置重载回调"""
        self._reload_callbacks.append(callback)
    
    def start_config_watcher(self, interval: float = 5.0):
        """启动配置监视器（热重载）"""
        def watch_loop():
            while not self._stop_watching:
                time.sleep(interval)
                
                # 检查配置是否更改
                for config_type in ["agents", "models", "system", "channels"]:
                    if self.has_changed(config_type):
                        print(f"[Config] {config_type} configuration changed, reloading...")
                        self.load_all_configs()
                        
                        # 触发回调
                        for callback in self._reload_callbacks:
                            try:
                                callback()
                            except Exception as e:
                                print(f"[Config] Reload callback error: {e}")
        
        self._watch_thread = threading.Thread(target=watch_loop, daemon=True)
        self._watch_thread.start()
    
    def stop_config_watcher(self):
        """停止配置监视器"""
        self._stop_watching = True
        if self._watch_thread:
            self._watch_thread.join(timeout=2.0)
