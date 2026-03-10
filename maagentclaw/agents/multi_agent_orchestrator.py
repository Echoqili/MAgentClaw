"""
Multi-Agent Orchestrator - 多智能体编排器

支持 Sub-Agent、任务分解、嵌套调用
"""

import asyncio
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


class AgentMode(Enum):
    """Agent 执行模式"""
    AUTO = "auto"        # 自动选择
    RUN = "run"          # 单次任务
    SESSION = "session"  # 持续对话


class AgentRole(Enum):
    """Agent 角色"""
    COORDINATOR = "coordinator"    # 协调者
    PLANNER = "planner"           # 规划者
    EXECUTOR = "executor"          # 执行者
    REVIEWER = "reviewer"          # 审核者
    SPECIALIST = "specialist"      # 专家


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class SubAgent:
    """子 Agent 定义"""
    id: str
    name: str
    role: AgentRole
    description: str
    model: str = "gpt-4"
    instructions: str = ""
    tools: List[str] = field(default_factory=list)
    max_iterations: int = 10
    timeout: int = 300
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role.value,
            "description": self.description,
            "model": self.model,
            "instructions": self.instructions,
            "tools": self.tools,
            "max_iterations": self.max_iterations,
            "timeout": self.timeout
        }


@dataclass
class Task:
    """任务定义"""
    id: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    priority: int = 0
    assigned_agent: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    result: Any = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "status": self.status.value,
            "priority": self.priority,
            "assigned_agent": self.assigned_agent,
            "dependencies": self.dependencies,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "metadata": self.metadata
        }


@dataclass
class ExecutionContext:
    """执行上下文"""
    task_id: str
    mode: AgentMode = AgentMode.AUTO
    thread_id: Optional[str] = None
    parent_agent_id: Optional[str] = None
    user_id: Optional[str] = None
    session_data: Dict[str, Any] = field(default_factory=dict)
    history: List[Dict[str, Any]] = field(default_factory=list)


class MultiAgentOrchestrator:
    """多智能体编排器"""
    
    def __init__(self, 
                 workspace_path: Path,
                 execute_callback: Optional[Callable] = None,
                 model_manager=None):
        self.workspace_path = Path(workspace_path)
        self.execute_callback = execute_callback
        self.model_manager = model_manager
        
        self.agents: Dict[str, SubAgent] = {}
        self.tasks: Dict[str, Task] = {}
        self.active_sessions: Dict[str, ExecutionContext] = {}
        
        # 默认 Agent 模板
        self._init_default_agents()
        
        # 加载配置
        self.load_config()
    
    def _init_default_agents(self):
        """初始化默认 Agent"""
        # 协调者
        coordinator = SubAgent(
            id="coordinator",
            name="Coordinator",
            role=AgentRole.COORDINATOR,
            description="负责协调和管理其他 Agent，分解复杂任务",
            instructions="你是一个任务协调专家，负责将复杂任务分解为子任务，并调度合适的 Agent 执行。",
            tools=["task_planner", "agent_spawner"]
        )
        
        # 规划者
        planner = SubAgent(
            id="planner",
            name="Planner",
            role=AgentRole.PLANNER,
            description="负责制定执行计划和时间表",
            instructions="你是一个规划专家，负责分析任务需求，制定详细的执行计划。",
            tools=["task_analyzer", "scheduler"]
        )
        
        # 执行者
        executor = SubAgent(
            id="executor",
            name="Executor",
            role=AgentRole.EXECUTOR,
            description="负责执行具体任务",
            instructions="你是一个执行专家，负责高效地执行分配的任务。",
            tools=["browser", "file_operator", "code_executor"]
        )
        
        # 审核者
        reviewer = SubAgent(
            id="reviewer",
            name="Reviewer",
            role=AgentRole.REVIEWER,
            description="负责审核和评估结果",
            instructions="你是一个审核专家，负责审核任务执行结果并提供反馈。",
            tools=["task_analyzer"]
        )
        
        self.agents = {
            "coordinator": coordinator,
            "planner": planner,
            "executor": executor,
            "reviewer": reviewer
        }
    
    def register_agent(self, agent: SubAgent):
        """注册 Agent"""
        self.agents[agent.id] = agent
    
    def unregister_agent(self, agent_id: str):
        """注销 Agent"""
        if agent_id in self.agents:
            del self.agents[agent_id]
    
    def get_agent(self, agent_id: str) -> Optional[SubAgent]:
        """获取 Agent"""
        return self.agents.get(agent_id)
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """列出所有 Agent"""
        return [agent.to_dict() for agent in self.agents.values()]
    
    async def create_session(self, user_id: str, mode: AgentMode = AgentMode.AUTO) -> str:
        """创建会话"""
        thread_id = f"thread_{uuid.uuid4().hex[:8]}"
        
        context = ExecutionContext(
            task_id="",
            mode=mode,
            thread_id=thread_id,
            user_id=user_id
        )
        
        self.active_sessions[thread_id] = context
        return thread_id
    
    async def close_session(self, thread_id: str):
        """关闭会话"""
        if thread_id in self.active_sessions:
            del self.active_sessions[thread_id]
    
    async def decompose_task(self, task: str) -> List[Task]:
        """分解任务"""
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        
        # 创建主任务
        main_task = Task(
            id=task_id,
            description=task,
            priority=10
        )
        
        # 使用协调者分解任务
        coordinator = self.agents.get("coordinator")
        if coordinator and self.execute_callback:
            # 调用 LLM 分解任务
            prompt = f"""分解以下任务为子任务：
{task}

请以 JSON 数组格式返回，每个子任务包含：
- id: 子任务ID
- description: 子任务描述
- priority: 优先级 (1-10)

只返回 JSON，不要其他内容。"""
            
            try:
                result = await self.execute_callback(
                    prompt,
                    {"role": "coordinator", "instructions": coordinator.instructions}
                )
                
                # 解析结果
                subtasks_data = json.loads(result)
                
                subtasks = []
                for i, st in enumerate(subtasks_data):
                    subtask = Task(
                        id=f"{task_id}_sub_{i}",
                        description=st.get("description", ""),
                        priority=st.get("priority", 5)
                    )
                    subtasks.append(subtask)
                
                self.tasks[main_task.id] = main_task
                for subtask in subtasks:
                    self.tasks[subtask.id] = subtask
                
                return [main_task] + subtasks
                
            except Exception as e:
                print(f"Task decomposition error: {e}")
        
        # 如果分解失败，返回单个任务
        self.tasks[main_task.id] = main_task
        return [main_task]
    
    async def select_agents(self, tasks: List[Task]) -> Dict[str, str]:
        """为任务选择合适的 Agent"""
        assignments = {}
        
        for task in tasks:
            # 根据任务类型选择 Agent
            if any(kw in task.description.lower() for kw in ["规划", "计划", "分析"]):
                assignments[task.id] = "planner"
            elif any(kw in task.description.lower() for kw in ["执行", "完成", "做"]):
                assignments[task.id] = "executor"
            elif any(kw in task.description.lower() for kw in ["审核", "检查", "评估"]):
                assignments[task.id] = "reviewer"
            else:
                assignments[task.id] = "coordinator"
        
        return assignments
    
    async def execute_parallel(self, 
                             tasks: List[Task], 
                             assignments: Dict[str, str],
                             thread_id: Optional[str] = None) -> List[Task]:
        """并行执行任务"""
        async def execute_single(task: Task):
            agent_id = assignments.get(task.id, "executor")
            agent = self.agents.get(agent_id)
            
            if not agent:
                task.status = TaskStatus.FAILED
                task.error = f"Agent {agent_id} not found"
                return task
            
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()
            task.assigned_agent = agent_id
            
            try:
                # 执行任务
                if self.execute_callback:
                    result = await self.execute_callback(
                        task.description,
                        {
                            "role": agent.role.value,
                            "instructions": agent.instructions,
                            "tools": agent.tools,
                            "context": thread_id
                        }
                    )
                    task.result = result
                    task.status = TaskStatus.COMPLETED
                else:
                    # 模拟执行
                    await asyncio.sleep(0.5)
                    task.result = f"Executed by {agent.name}"
                    task.status = TaskStatus.COMPLETED
                    
            except Exception as e:
                task.status = TaskStatus.FAILED
                task.error = str(e)
            
            task.completed_at = datetime.now()
            return task
        
        # 并行执行所有任务
        results = await asyncio.gather(
            *[execute_single(task) for task in tasks]
        )
        
        return results
    
    async def aggregate_results(self, tasks: List[Task]) -> Dict[str, Any]:
        """汇总结果"""
        successful = [t for t in tasks if t.status == TaskStatus.COMPLETED]
        failed = [t for t in tasks if t.status == TaskStatus.FAILED]
        
        return {
            "total": len(tasks),
            "successful": len(successful),
            "failed": len(failed),
            "results": [t.to_dict() for t in tasks],
            "summary": " / ".join([f"{t.id}: {t.status.value}" for t in tasks])
        }
    
    async def run_task(self, 
                      task: str, 
                      mode: AgentMode = AgentMode.RUN,
                      user_id: Optional[str] = None) -> Dict[str, Any]:
        """运行任务（Run 模式）"""
        # 1. 分解任务
        tasks = await self.decompose_task(task)
        
        # 2. 选择 Agent
        assignments = await self.select_agents(tasks)
        
        # 3. 执行任务
        results = await self.execute_parallel(tasks, assignments)
        
        # 4. 审核结果（可选）
        main_task = results[0]
        if len(results) > 1 and self.agents.get("reviewer"):
            reviewer = self.agents["reviewer"]
            
            # 审核结果
            review_prompt = f"""审核以下任务执行结果：

主任务: {main_task.description}
执行结果: {main_task.result}

子任务:"""
            
            for subtask in results[1:]:
                review_prompt += f"\n- {subtask.description}: {subtask.status.value}"
            
            if self.execute_callback:
                review_result = await self.execute_callback(
                    review_prompt,
                    {"role": "reviewer", "instructions": reviewer.instructions}
                )
        
        # 5. 汇总结果
        return await self.aggregate_results(results)
    
    async def session_chat(self,
                          thread_id: str,
                          message: str) -> Dict[str, Any]:
        """会话聊天（Session 模式）"""
        context = self.active_sessions.get(thread_id)
        
        if not context:
            return {"error": "Session not found"}
        
        # 添加到历史
        context.history.append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
        
        # 使用协调者处理
        coordinator = self.agents.get("coordinator")
        
        if coordinator and self.execute_callback:
            response = await self.execute_callback(
                message,
                {
                    "role": "coordinator",
                    "instructions": coordinator.instructions,
                    "history": context.history
                }
            )
        else:
            # 模拟响应
            response = f"Echo: {message}"
        
        # 添加到历史
        context.history.append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now().isoformat()
        })
        
        return {
            "response": response,
            "history": context.history
        }
    
    async def spawn_sub_agent(self, 
                             role: str, 
                             task: str,
                             parent_thread: Optional[str] = None) -> str:
        """生成子 Agent"""
        sub_agent_id = f"sub_{uuid.uuid4().hex[:8]}"
        
        # 创建子 Agent
        sub_agent = SubAgent(
            id=sub_agent_id,
            name=f"Sub-{role}",
            role=AgentRole.SPECIALIST,
            description=f"临时子 Agent，执行特定任务",
            instructions=f"你是一个{role}专家，负责执行特定任务。",
            max_iterations=5,
            timeout=120
        )
        
        self.register_agent(sub_agent)
        
        # 执行任务
        result = await self.run_task(task, AgentMode.RUN)
        
        return sub_agent_id
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        task = self.tasks.get(task_id)
        return task.to_dict() if task else None
    
    def get_session_history(self, thread_id: str) -> Optional[List[Dict[str, Any]]]:
        """获取会话历史"""
        context = self.active_sessions.get(thread_id)
        return context.history if context else None
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total = len(self.tasks)
        completed = sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in self.tasks.values() if t.status == TaskStatus.FAILED)
        
        return {
            "total_agents": len(self.agents),
            "total_tasks": total,
            "completed_tasks": completed,
            "failed_tasks": failed,
            "active_sessions": len(self.active_sessions),
            "success_rate": (completed / total * 100) if total > 0 else 0
        }
    
    def save_config(self):
        """保存配置"""
        config_file = self.workspace_path / "agents_config.json"
        
        config_data = {
            "agents": [agent.to_dict() for agent in self.agents.values()]
        }
        
        config_file.write_text(json.dumps(config_data, indent=2), encoding='utf-8')
    
    def load_config(self):
        """加载配置"""
        config_file = self.workspace_path / "agents_config.json"
        
        if not config_file.exists():
            return
        
        try:
            config_data = json.loads(config_file.read_text(encoding='utf-8'))
            
            for agent_data in config_data.get("agents", []):
                agent = SubAgent(
                    id=agent_data["id"],
                    name=agent_data["name"],
                    role=AgentRole(agent_data["role"]),
                    description=agent_data["description"],
                    model=agent_data.get("model", "gpt-4"),
                    instructions=agent_data.get("instructions", ""),
                    tools=agent_data.get("tools", []),
                    max_iterations=agent_data.get("max_iterations", 10),
                    timeout=agent_data.get("timeout", 300)
                )
                self.agents[agent.id] = agent
                
        except Exception as e:
            print(f"Load config error: {e}")


# 简化导入
__all__ = [
    "AgentMode",
    "AgentRole",
    "TaskStatus",
    "SubAgent",
    "Task",
    "ExecutionContext",
    "MultiAgentOrchestrator"
]
