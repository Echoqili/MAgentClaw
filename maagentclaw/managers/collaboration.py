"""
多 Agent 协作框架模块
实现 Agent 之间的通信、任务分配和协作机制
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
from enum import Enum
import uuid

from ..core.agent import BaseAgent, AgentConfig, AgentMessage, AgentState


class CollaborationMode(Enum):
    """协作模式枚举"""
    SEQUENTIAL = "sequential"  # 顺序执行
    PARALLEL = "parallel"  # 并行执行
    HIERARCHICAL = "hierarchical"  # 层级模式
    COLLABORATIVE = "collaborative"  # 协作模式


@dataclass
class Task:
    """任务类 - 增强版"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    status: str = "pending"  # pending, running, completed, failed, paused
    priority: int = 0  # 优先级，数字越大优先级越高
    assigned_to: Optional[str] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # ======= 新增字段 =======
    retry_count: int = 0  # 重试次数
    max_retries: int = 3  # 最大重试次数
    execution_time: float = 0.0  # 执行时间（秒）
    subtasks: List[str] = field(default_factory=list)  # 子任务列表
    output_var: Optional[str] = None  # 输出变量名（用于工作流）


@dataclass
class CollaborationSession:
    """协作会话类 - 增强版（支持断点续传）"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""  # 会话名称
    mode: CollaborationMode = CollaborationMode.COLLABORATIVE
    participants: List[str] = field(default_factory=list)
    tasks: List[Task] = field(default_factory=list)
    messages: List[AgentMessage] = field(default_factory=list)
    status: str = "active"  # active, paused, completed, cancelled
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)
    
    # ======= 新增字段：断点续传支持 =======
    checkpoint_enabled: bool = True  # 是否启用检查点
    checkpoint_path: Optional[str] = None  # 检查点文件路径
    checkpoint_interval: int = 60  # 检查点保存间隔（秒）
    last_checkpoint: Optional[datetime] = None  # 上次检查点时间
    
    # 状态管理
    state: Dict[str, Any] = field(default_factory=dict)  # 会话状态
    variables: Dict[str, Any] = field(default_factory=dict)  # 工作流变量
    
    # 执行控制
    max_execution_time: int = 3600  # 最大执行时间（秒）
    error_strategy: str = "stop"  # 错误策略：stop, retry, skip
    
    def save_checkpoint(self) -> Dict[str, Any]:
        """保存检查点数据"""
        checkpoint_data = {
            "id": self.id,
            "name": self.name,
            "mode": self.mode.value,
            "participants": self.participants,
            "status": self.status,
            "context": self.context,
            "state": self.state,
            "variables": self.variables,
            "tasks": [
                {
                    "id": t.id,
                    "description": t.description,
                    "status": t.status,
                    "priority": t.priority,
                    "assigned_to": t.assigned_to,
                    "result": str(t.result) if t.result else None,
                    "error": t.error,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                    "started_at": t.started_at.isoformat() if t.started_at else None,
                    "completed_at": t.completed_at.isoformat() if t.completed_at else None,
                    "dependencies": t.dependencies,
                    "retry_count": t.retry_count,
                    "execution_time": t.execution_time
                }
                for t in self.tasks
            ],
            "messages": [
                {
                    "id": m.id,
                    "content": m.content,
                    "role": m.role,
                    "timestamp": m.timestamp.isoformat()
                }
                for m in self.messages[-50:]  # 只保留最近50条消息
            ],
            "updated_at": datetime.now().isoformat()
        }
        
        self.last_checkpoint = datetime.now()
        return checkpoint_data
    
    def load_checkpoint(self, checkpoint_data: Dict[str, Any]):
        """加载检查点数据"""
        self.name = checkpoint_data.get("name", "")
        self.mode = CollaborationMode(checkpoint_data.get("mode", "collaborative"))
        self.participants = checkpoint_data.get("participants", [])
        self.status = checkpoint_data.get("status", "paused")
        self.context = checkpoint_data.get("context", {})
        self.state = checkpoint_data.get("state", {})
        self.variables = checkpoint_data.get("variables", {})
        
        # 恢复任务
        tasks_data = checkpoint_data.get("tasks", [])
        self.tasks = []
        for t_data in tasks_data:
            task = Task(
                id=t_data.get("id", str(uuid.uuid4())),
                description=t_data.get("description", ""),
                status=t_data.get("status", "pending"),
                priority=t_data.get("priority", 0),
                assigned_to=t_data.get("assigned_to"),
                result=t_data.get("result"),
                error=t_data.get("error"),
                created_at=datetime.fromisoformat(t_data["created_at"]) if t_data.get("created_at") else datetime.now(),
                started_at=datetime.fromisoformat(t_data["started_at"]) if t_data.get("started_at") else None,
                completed_at=datetime.fromisoformat(t_data["completed_at"]) if t_data.get("completed_at") else None,
                dependencies=t_data.get("dependencies", []),
                retry_count=t_data.get("retry_count", 0),
                execution_time=t_data.get("execution_time", 0.0)
            )
            self.tasks.append(task)
        
        # 恢复消息
        messages_data = checkpoint_data.get("messages", [])
        self.messages = []
        for m_data in messages_data:
            message = AgentMessage(
                id=m_data.get("id", str(uuid.uuid4())),
                content=m_data.get("content", ""),
                role=m_data.get("role", "user"),
                timestamp=datetime.fromisoformat(m_data["timestamp"]) if m_data.get("timestamp") else datetime.now()
            )
            self.messages.append(message)
    
    def should_save_checkpoint(self) -> bool:
        """检查是否应该保存检查点"""
        if not self.checkpoint_enabled:
            return False
        if self.last_checkpoint is None:
            return True
        elapsed = (datetime.now() - self.last_checkpoint).total_seconds()
        return elapsed >= self.checkpoint_interval


class TaskCoordinator:
    """任务协调器 - 增强版（支持断点续传）"""
    
    def __init__(self, checkpoint_dir: str = "checkpoints"):
        self.tasks: Dict[str, Task] = {}
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self._lock = asyncio.Lock()
        self.checkpoint_dir = checkpoint_dir
    
    def create_task(self, description: str, assigned_to: Optional[str] = None, 
                   dependencies: Optional[List[str]] = None, priority: int = 0,
                   max_retries: int = 3) -> Task:
        """创建任务"""
        task = Task(
            description=description,
            assigned_to=assigned_to,
            dependencies=dependencies or [],
            priority=priority,
            max_retries=max_retries
        )
        self.tasks[task.id] = task
        return task
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务"""
        return self.tasks.get(task_id)
    
    def update_task_status(self, task_id: str, status: str, result: Any = None, error: str = None):
        """更新任务状态"""
        task = self.get_task(task_id)
        if task:
            task.status = status
            task.result = result
            task.error = error
            if status == "running" and task.started_at is None:
                task.started_at = datetime.now()
            elif status in ["completed", "failed"]:
                task.completed_at = datetime.now()
                if task.started_at:
                    task.execution_time = (datetime.now() - task.started_at).total_seconds()
    
    async def get_next_task(self, agent_name: str) -> Optional[Task]:
        """获取下一个可执行任务（考虑优先级）"""
        async with self._lock:
            # 按优先级和创建时间排序
            pending_tasks = [
                t for t in self.tasks.values()
                if t.status == "pending" and t.assigned_to in [None, agent_name]
            ]
            
            # 检查依赖并排序
            executable_tasks = []
            for task in pending_tasks:
                dependencies_met = all(
                    self.tasks.get(dep_id, Task()).status == "completed"
                    for dep_id in task.dependencies
                )
                if dependencies_met:
                    executable_tasks.append(task)
            
            # 按优先级排序（高优先级在前）
            executable_tasks.sort(key=lambda t: (-t.priority, t.created_at))
            
            if executable_tasks:
                next_task = executable_tasks[0]
                next_task.status = "running"
                next_task.started_at = datetime.now()
                return next_task
        
        return None
    
    def get_pending_tasks(self) -> List[Task]:
        """获取所有待执行任务"""
        return [t for t in self.tasks.values() if t.status == "pending"]
    
    def get_completed_tasks(self) -> List[Task]:
        """获取所有已完成任务"""
        return [t for t in self.tasks.values() if t.status == "completed"]
    
    def get_failed_tasks(self) -> List[Task]:
        """获取所有失败任务"""
        return [t for t in self.tasks.values() if t.status == "failed"]
    
    def retry_task(self, task_id: str) -> bool:
        """重试失败任务"""
        task = self.get_task(task_id)
        if task and task.status == "failed":
            if task.retry_count < task.max_retries:
                task.status = "pending"
                task.retry_count += 1
                task.error = None
                return True
        return False
    
    def save_checkpoint(self, session_id: str) -> str:
        """保存检查点到文件"""
        import json
        from pathlib import Path
        
        checkpoint_path = Path(self.checkpoint_dir)
        checkpoint_path.mkdir(parents=True, exist_ok=True)
        
        checkpoint_file = checkpoint_path / f"{session_id}_tasks.json"
        
        checkpoint_data = {
            "session_id": session_id,
            "tasks": [
                {
                    "id": t.id,
                    "description": t.description,
                    "status": t.status,
                    "priority": t.priority,
                    "assigned_to": t.assigned_to,
                    "result": str(t.result) if t.result else None,
                    "error": t.error,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                    "started_at": t.started_at.isoformat() if t.started_at else None,
                    "completed_at": t.completed_at.isoformat() if t.completed_at else None,
                    "dependencies": t.dependencies,
                    "retry_count": t.retry_count,
                    "max_retries": t.max_retries,
                    "execution_time": t.execution_time
                }
                for t in self.tasks.values()
            ],
            "timestamp": datetime.now().isoformat()
        }
        
        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint_data, f, ensure_ascii=False, indent=2)
        
        return str(checkpoint_file)
    
    def load_checkpoint(self, checkpoint_file: str) -> bool:
        """从文件加载检查点"""
        import json
        
        try:
            with open(checkpoint_file, 'r', encoding='utf-8') as f:
                checkpoint_data = json.load(f)
            
            tasks_data = checkpoint_data.get("tasks", [])
            for t_data in tasks_data:
                task = Task(
                    id=t_data.get("id", str(uuid.uuid4())),
                    description=t_data.get("description", ""),
                    status=t_data.get("status", "pending"),
                    priority=t_data.get("priority", 0),
                    assigned_to=t_data.get("assigned_to"),
                    result=t_data.get("result"),
                    error=t_data.get("error"),
                    created_at=datetime.fromisoformat(t_data["created_at"]) if t_data.get("created_at") else datetime.now(),
                    started_at=datetime.fromisoformat(t_data["started_at"]) if t_data.get("started_at") else None,
                    completed_at=datetime.fromisoformat(t_data["completed_at"]) if t_data.get("completed_at") else None,
                    dependencies=t_data.get("dependencies", []),
                    retry_count=t_data.get("retry_count", 0),
                    max_retries=t_data.get("max_retries", 3),
                    execution_time=t_data.get("execution_time", 0.0)
                )
                self.tasks[task.id] = task
            
            return True
        except Exception as e:
            print(f"Failed to load checkpoint: {e}")
            return False


class CollaborationManager:
    """协作管理器 - 增强版（支持并行执行优化）"""
    
    def __init__(self, agent_manager: Any):
        self.agent_manager = agent_manager
        self.sessions: Dict[str, CollaborationSession] = {}
        self.task_coordinator = TaskCoordinator()
        self.callbacks: Dict[str, List[Callable]] = {}
        
        # ======= 新增：任务执行器 =======
        self.task_executor: Optional[Any] = None  # 将在 init_task_executor 中初始化
    
    def init_task_executor(self, executor: Any = None):
        """初始化任务执行器"""
        if executor is None:
            from ..tools.task_executor import TaskExecutor
            self.task_executor = TaskExecutor()
        else:
            self.task_executor = executor
    
    def create_session(
        self, 
        mode: CollaborationMode = CollaborationMode.COLLABORATIVE,
        participants: Optional[List[str]] = None,
        name: str = "",
        checkpoint_enabled: bool = True
    ) -> CollaborationSession:
        """创建协作会话"""
        session = CollaborationSession(
            mode=mode, 
            participants=participants or [],
            name=name,
            checkpoint_enabled=checkpoint_enabled
        )
        self.sessions[session.id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[CollaborationSession]:
        """获取会话"""
        return self.sessions.get(session_id)
    
    def add_participant(self, session_id: str, agent_name: str):
        """添加参与者到会话"""
        session = self.get_session(session_id)
        if session and agent_name not in session.participants:
            session.participants.append(agent_name)
    
    def remove_participant(self, session_id: str, agent_name: str):
        """从会话移除参与者"""
        session = self.get_session(session_id)
        if session and agent_name in session.participants:
            session.participants.remove(agent_name)
    
    async def execute_sequential(self, session_id: str, tasks: List[str]) -> Dict[str, Any]:
        """顺序执行任务"""
        session = self.get_session(session_id)
        if not session:
            return {"error": "Session not found"}
        
        results = {}
        for task_desc in tasks:
            task = self.task_coordinator.create_task(task_desc)
            session.tasks.append(task)
            
            # 路由到合适的 Agent
            result = await self._execute_task(task, session)
            results[task.id] = result
            
            if result.get("success") is False:
                break
        
        return results
    
    async def execute_parallel(self, session_id: str, tasks: List[str]) -> Dict[str, Any]:
        """并行执行任务"""
        session = self.get_session(session_id)
        if not session:
            return {"error": "Session not found"}
        
        created_tasks = []
        for task_desc in tasks:
            task = self.task_coordinator.create_task(task_desc)
            session.tasks.append(task)
            created_tasks.append(task)
        
        # 并行执行所有任务
        coroutines = [self._execute_task(task, session) for task in created_tasks]
        results = await asyncio.gather(*coroutines, return_exceptions=True)
        
        return {
            task.id: result 
            for task, result in zip(created_tasks, results)
        }
    
    async def execute_hierarchical(self, session_id: str, main_task: str, 
                                   sub_tasks: List[str]) -> Dict[str, Any]:
        """层级执行任务（主任务 + 子任务）"""
        session = self.get_session(session_id)
        if not session:
            return {"error": "Session not found"}
        
        # 创建主任务
        main_task_obj = self.task_coordinator.create_task(main_task)
        session.tasks.append(main_task_obj)
        
        # 创建子任务，依赖主任务
        sub_task_objs = []
        for sub_task_desc in sub_tasks:
            sub_task = self.task_coordinator.create_task(
                sub_task_desc,
                dependencies=[main_task_obj.id]
            )
            session.tasks.append(sub_task)
            sub_task_objs.append(sub_task)
        
        # 执行主任务
        main_result = await self._execute_task(main_task_obj, session)
        
        # 并行执行子任务
        sub_results = await asyncio.gather(
            *[self._execute_task(task, session) for task in sub_task_objs],
            return_exceptions=True
        )
        
        return {
            "main": {main_task_obj.id: main_result},
            "sub": {task.id: result for task, result in zip(sub_task_objs, sub_results)}
        }
    
    async def _execute_task(self, task: Task, session: CollaborationSession) -> Dict[str, Any]:
        """执行单个任务"""
        try:
            # 根据任务描述和参与者选择合适的 Agent
            target_agent = self._select_agent(task, session)
            
            if target_agent:
                agent = self.agent_manager.get_agent(target_agent)
                if agent:
                    message = AgentMessage(content=task.description, role="user")
                    response = await agent.process(message)
                    
                    task.result = response.content
                    task.status = "completed"
                    
                    # 添加到会话消息
                    session.messages.append(message)
                    session.messages.append(response)
                    
                    return {"success": True, "result": response.content, "agent": target_agent}
            
            task.status = "failed"
            task.error = "No suitable agent found"
            return {"success": False, "error": "No suitable agent found"}
            
        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            return {"success": False, "error": str(e)}
    
    def _select_agent(self, task: Task, session: CollaborationSession) -> Optional[str]:
        """选择合适的 Agent 执行任务"""
        if not session.participants:
            return None
        
        # 简单实现：返回第一个可用的 Agent
        # 实际应用中应该基于任务类型、Agent 能力等进行智能选择
        for agent_name in session.participants:
            agent = self.agent_manager.get_agent(agent_name)
            if agent and agent.state.status == "idle":
                return agent_name
        
        return session.participants[0] if session.participants else None
    
    def register_callback(self, event: str, callback: Callable):
        """注册事件回调"""
        if event not in self.callbacks:
            self.callbacks[event] = []
        self.callbacks[event].append(callback)
    
    async def _trigger_callback(self, event: str, data: Any):
        """触发事件回调"""
        if event in self.callbacks:
            for callback in self.callbacks[event]:
                if asyncio.iscoroutinefunction(callback):
                    await callback(data)
                else:
                    callback(data)
