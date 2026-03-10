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
    """任务类"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    status: str = "pending"  # pending, running, completed, failed
    assigned_to: Optional[str] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CollaborationSession:
    """协作会话类"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    mode: CollaborationMode = CollaborationMode.COLLABORATIVE
    participants: List[str] = field(default_factory=list)
    tasks: List[Task] = field(default_factory=list)
    messages: List[AgentMessage] = field(default_factory=list)
    status: str = "active"  # active, paused, completed, cancelled
    created_at: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)


class TaskCoordinator:
    """任务协调器"""
    
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self._lock = asyncio.Lock()
    
    def create_task(self, description: str, assigned_to: Optional[str] = None, 
                   dependencies: Optional[List[str]] = None) -> Task:
        """创建任务"""
        task = Task(
            description=description,
            assigned_to=assigned_to,
            dependencies=dependencies or []
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
            if status in ["completed", "failed"]:
                task.completed_at = datetime.now()
    
    async def get_next_task(self, agent_name: str) -> Optional[Task]:
        """获取下一个可执行任务"""
        async with self._lock:
            for task in self.tasks.values():
                if (task.status == "pending" and 
                    task.assigned_to in [None, agent_name]):
                    # 检查依赖
                    dependencies_met = all(
                        self.tasks.get(dep_id, Task()).status == "completed"
                        for dep_id in task.dependencies
                    )
                    if dependencies_met:
                        task.status = "running"
                        return task
        return None


class CollaborationManager:
    """协作管理器"""
    
    def __init__(self, agent_manager: Any):
        self.agent_manager = agent_manager
        self.sessions: Dict[str, CollaborationSession] = {}
        self.task_coordinator = TaskCoordinator()
        self.callbacks: Dict[str, List[Callable]] = {}
    
    def create_session(self, mode: CollaborationMode = CollaborationMode.COLLABORATIVE,
                      participants: Optional[List[str]] = None) -> CollaborationSession:
        """创建协作会话"""
        session = CollaborationSession(mode=mode, participants=participants or [])
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
