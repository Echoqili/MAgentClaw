"""
核心 Agent 基类模块
定义所有 Agent 的基础接口和抽象类
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass
class AgentConfig:
    """Agent 配置类"""
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


@dataclass
class AgentMessage:
    """Agent 消息类"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    role: str = "user"
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentState:
    """Agent 状态类"""
    id: str
    name: str
    status: str = "idle"  # idle, running, paused, stopped
    current_task: Optional[str] = None
    last_active: datetime = field(default_factory=datetime.now)
    metrics: Dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC):
    """Agent 基类"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.id = str(uuid.uuid4())
        self.state = AgentState(
            id=self.id,
            name=config.name
        )
        self.memory: List[AgentMessage] = []
        self.tools: Dict[str, Any] = {}
        self._initialized = False
    
    @abstractmethod
    async def initialize(self) -> bool:
        """初始化 Agent"""
        pass
    
    @abstractmethod
    async def process(self, message: AgentMessage) -> AgentMessage:
        """处理消息并返回响应"""
        pass
    
    @abstractmethod
    async def execute_task(self, task: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """执行任务"""
        pass
    
    def add_to_memory(self, message: AgentMessage):
        """添加消息到记忆"""
        if self.config.memory_enabled:
            self.memory.append(message)
    
    def get_memory(self, limit: int = 10) -> List[AgentMessage]:
        """获取最近的记忆"""
        return self.memory[-limit:]
    
    def clear_memory(self):
        """清空记忆"""
        self.memory.clear()
    
    def register_tool(self, name: str, tool_func: Any):
        """注册工具"""
        self.tools[name] = tool_func
    
    def get_state(self) -> AgentState:
        """获取 Agent 状态"""
        self.state.last_active = datetime.now()
        return self.state
    
    async def start(self):
        """启动 Agent"""
        self.state.status = "running"
        if not self._initialized:
            await self.initialize()
            self._initialized = True
    
    async def stop(self):
        """停止 Agent"""
        self.state.status = "stopped"
        self.state.current_task = None
    
    async def pause(self):
        """暂停 Agent"""
        self.state.status = "paused"
    
    async def resume(self):
        """恢复 Agent"""
        self.state.status = "running"
