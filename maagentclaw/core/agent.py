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
    """Agent 配置类 - 增强版角色定义"""
    name: str
    role: str
    description: str = ""
    
    # 模型配置
    model: str = "default"
    workspace: str = "default"
    max_iterations: int = 10
    temperature: float = 0.7
    
    # 工具配置
    tools: List[str] = field(default_factory=list)
    available_tools: List[str] = field(default_factory=list)  # 可用工具列表
    
    # 记忆配置
    memory_enabled: bool = True
    max_memory_size: int = 100  # 最大记忆数量
    
    # 日志配置
    verbose: bool = False
    
    # ======= 新增：增强角色定义 (CrewAI 风格) =======
    goal: str = ""  # 目标 - Agent 要达成什么
    backstory: str = ""  # 背景故事 - Agent 的身份设定
    responsibilities: List[str] = field(default_factory=list)  # 职责列表
    skills: List[str] = field(default_factory=list)  # 技能列表
    allow_delegation: bool = False  # 是否允许委托任务给其他 Agent
    max_delegation_depth: int = 2  # 最大委托深度
    
    # 约束配置
    constraints: List[str] = field(default_factory=list)  # 约束条件
    output_format: Optional[str] = None  # 输出格式要求
    
    # 性能配置
    timeout: int = 300  # 超时时间（秒）
    retry_count: int = 3  # 重试次数
    cache_enabled: bool = True  # 是否启用缓存


@dataclass
class AgentMessage:
    """Agent 消息类 - 增强版"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    role: str = "user"  # user, assistant, system, tool, human
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # ======= 新增消息字段 =======
    sender: Optional[str] = None  # 发送者名称
    recipient: Optional[str] = None  # 接收者名称
    message_type: str = "text"  # text, tool_call, tool_result, system, human_feedback
    tool_name: Optional[str] = None  # 如果是工具调用，工具名称
    tool_args: Optional[Dict[str, Any]] = None  # 工具参数
    tool_result: Optional[str] = None  # 工具执行结果
    reply_to: Optional[str] = None  # 回复的消息ID
    delegation_level: int = 0  # 委托级别
    tokens_used: int = 0  # 使用的 token 数量


@dataclass
class AgentState:
    """Agent 状态类 - 增强版"""
    id: str
    name: str
    status: str = "idle"  # idle, running, paused, stopped, error
    current_task: Optional[str] = None
    last_active: datetime = field(default_factory=datetime.now)
    created_at: datetime = field(default_factory=datetime.now)
    error_message: Optional[str] = None
    
    # ======= 新增状态字段 =======
    task_history: List[Dict[str, Any]] = field(default_factory=list)  # 任务历史
    delegation_depth: int = 0  # 当前委托深度
    tool_calls: int = 0  # 工具调用次数
    messages_processed: int = 0  # 已处理消息数
    total_execution_time: float = 0.0  # 总执行时间
    
    # 指标
    metrics: Dict[str, Any] = field(default_factory=dict)
    
    # 断点续传支持
    checkpoint_data: Optional[Dict[str, Any]] = None  # 检查点数据
    last_checkpoint: Optional[datetime] = None  # 上次检查点时间


class BaseAgent(ABC):
    """Agent 基类 - 增强版"""
    
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
    
    # ======= 新增方法 =======
    
    def generate_system_prompt(self) -> str:
        """生成系统提示（基于增强的角色定义）"""
        prompt_parts = []
        
        # 角色定义
        prompt_parts.append(f"# 角色：{self.config.role}")
        
        # 描述
        if self.config.description:
            prompt_parts.append(f"## 描述\n{self.config.description}")
        
        # 目标
        if self.config.goal:
            prompt_parts.append(f"## 目标\n{self.config.goal}")
        
        # 背景故事
        if self.config.backstory:
            prompt_parts.append(f"## 背景故事\n{self.config.backstory}")
        
        # 职责
        if self.config.responsibilities:
            prompt_parts.append("## 职责")
            for resp in self.config.responsibilities:
                prompt_parts.append(f"- {resp}")
        
        # 技能
        if self.config.skills:
            prompt_parts.append("## 技能")
            for skill in self.config.skills:
                prompt_parts.append(f"- {skill}")
        
        # 可用工具
        if self.config.available_tools:
            prompt_parts.append("## 可用工具")
            for tool in self.config.available_tools:
                prompt_parts.append(f"- {tool}")
        
        # 约束
        if self.config.constraints:
            prompt_parts.append("## 约束")
            for constraint in self.config.constraints:
                prompt_parts.append(f"- {constraint}")
        
        # 输出格式
        if self.config.output_format:
            prompt_parts.append(f"## 输出格式\n{self.config.output_format}")
        
        return "\n\n".join(prompt_parts)
    
    def get_checkpoint_data(self) -> Dict[str, Any]:
        """获取检查点数据"""
        return {
            "agent_id": self.id,
            "name": self.config.name,
            "role": self.config.role,
            "state": {
                "status": self.state.status,
                "current_task": self.state.current_task,
                "task_history": self.state.task_history,
                "tool_calls": self.state.tool_calls,
                "messages_processed": self.state.messages_processed,
                "total_execution_time": self.state.total_execution_time
            },
            "memory": [
                {
                    "id": m.id,
                    "content": m.content,
                    "role": m.role,
                    "timestamp": m.timestamp.isoformat()
                }
                for m in self.memory
            ],
            "timestamp": datetime.now().isoformat()
        }
    
    def load_checkpoint_data(self, data: Dict[str, Any]):
        """加载检查点数据"""
        if "state" in data:
            state_data = data["state"]
            self.state.status = state_data.get("status", "idle")
            self.state.current_task = state_data.get("current_task")
            self.state.task_history = state_data.get("task_history", [])
            self.state.tool_calls = state_data.get("tool_calls", 0)
            self.state.messages_processed = state_data.get("messages_processed", 0)
            self.state.total_execution_time = state_data.get("total_execution_time", 0.0)
        
        if "memory" in data:
            self.memory = [
                AgentMessage(
                    id=m["id"],
                    content=m["content"],
                    role=m["role"],
                    timestamp=datetime.fromisoformat(m["timestamp"])
                )
                for m in data["memory"]
            ]
    
    def add_task_to_history(self, task: str, result: Dict[str, Any]):
        """添加任务到历史记录"""
        self.state.task_history.append({
            "task": task,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
        # 保持历史记录在合理范围内
        if len(self.state.task_history) > 100:
            self.state.task_history = self.state.task_history[-50:]
    
    def can_delegate(self) -> bool:
        """检查是否允许委托"""
        if not self.config.allow_delegation:
            return False
        return self.state.delegation_depth < self.config.max_delegation_depth
    
    def increment_delegation(self):
        """增加委托深度"""
        self.state.delegation_depth += 1
    
    def decrement_delegation(self):
        """减少委托深度"""
        self.state.delegation_depth = max(0, self.state.delegation_depth - 1)
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        return {
            "total_tasks": len(self.state.task_history),
            "total_tool_calls": self.state.tool_calls,
            "total_messages": self.state.messages_processed,
            "total_execution_time": self.state.total_execution_time,
            "avg_task_time": (
                self.state.total_execution_time / len(self.state.task_history)
                if self.state.task_history else 0
            ),
            "memory_size": len(self.memory)
        }
    
    # ======= 原有方法 =======
    
    def add_to_memory(self, message: AgentMessage):
        """添加消息到记忆（带大小限制）"""
        if self.config.memory_enabled:
            self.memory.append(message)
            # 保持记忆在合理范围内
            if len(self.memory) > self.config.max_memory_size:
                self.memory = self.memory[-self.config.max_memory_size:]
    
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
