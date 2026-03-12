"""
工作流编排模块

提供高级工作流编排能力
"""

from typing import Dict, List, Optional, Any, Callable, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
import asyncio
import json


class WorkflowStatus(Enum):
    """工作流状态"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(Enum):
    """步骤状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    WAITING = "waiting"


class ConditionType(Enum):
    """条件类型"""
    ALWAYS = "always"           # 总是执行
    EQUALS = "equals"          # 等于
    NOT_EQUALS = "not_equals"  # 不等于
    CONTAINS = "contains"       # 包含
    GREATER_THAN = "gt"         # 大于
    LESS_THAN = "lt"           # 小于
    REGEX = "regex"            # 正则匹配
    CUSTOM = "custom"          # 自定义条件


@dataclass
class WorkflowStep:
    """工作流步骤"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    agent: Optional[str] = None  # 执行的 Agent
    task: str = ""               # 任务描述
    tools: List[str] = field(default_factory=list)  # 使用的工具
    
    # 流程控制
    condition: Optional[str] = None  # 执行条件
    condition_type: ConditionType = ConditionType.ALWAYS
    depends_on: List[str] = field(default_factory=list)  # 依赖步骤
    retry_count: int = 0            # 已重试次数
    max_retries: int = 3            # 最大重试次数
    
    # 输入输出
    input_mapping: Dict[str, str] = field(default_factory=dict)  # 输入映射
    output_var: Optional[str] = None  # 输出变量名
    
    # 状态
    status: StepStatus = StepStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_time: float = 0.0
    
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Workflow:
    """工作流"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    steps: List[WorkflowStep] = field(default_factory=list)
    
    # 状态
    status: WorkflowStatus = WorkflowStatus.PENDING
    current_step: Optional[str] = None  # 当前步骤 ID
    
    # 变量
    variables: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    
    # 元数据
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_by: Optional[str] = None
    
    def add_step(self, step: WorkflowStep):
        """添加步骤"""
        self.steps.append(step)
    
    def get_step(self, step_id: str) -> Optional[WorkflowStep]:
        """获取步骤"""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None
    
    def get_step_by_name(self, name: str) -> Optional[WorkflowStep]:
        """通过名称获取步骤"""
        for step in self.steps:
            if step.name == name:
                return step
        return None
    
    def get_ready_steps(self) -> List[WorkflowStep]:
        """获取就绪的步骤（所有依赖都已完成）"""
        ready = []
        for step in self.steps:
            if step.status != StepStatus.PENDING:
                continue
            
            # 检查依赖是否都完成
            deps_completed = True
            for dep_id in step.depends_on:
                dep_step = self.get_step(dep_id)
                if dep_step is None or dep_step.status != StepStatus.COMPLETED:
                    deps_completed = False
                    break
            
            if deps_completed:
                ready.append(step)
        
        return ready


class WorkflowEngine:
    """工作流引擎"""
    
    def __init__(self, agent_manager: Optional[Any] = None):
        self.agent_manager = agent_manager
        self.workflows: Dict[str, Workflow] = {}
        self._lock = asyncio.Lock()
        
        # 回调函数
        self.callbacks: Dict[str, List[Callable]] = {
            "on_step_start": [],
            "on_step_complete": [],
            "on_step_error": [],
            "on_workflow_complete": [],
            "on_workflow_error": []
        }
    
    def create_workflow(
        self,
        name: str,
        description: str = "",
        created_by: Optional[str] = None
    ) -> Workflow:
        """创建工作流"""
        workflow = Workflow(
            name=name,
            description=description,
            created_by=created_by
        )
        self.workflows[workflow.id] = workflow
        return workflow
    
    def add_step(
        self,
        workflow_id: str,
        name: str,
        task: str,
        agent: Optional[str] = None,
        tools: Optional[List[str]] = None,
        depends_on: Optional[List[str]] = None,
        condition: Optional[str] = None,
        output_var: Optional[str] = None,
        max_retries: int = 3
    ) -> Optional[WorkflowStep]:
        """添加步骤到工作流"""
        workflow = self.workflows.get(workflow_id)
        if workflow is None:
            return None
        
        step = WorkflowStep(
            name=name,
            task=task,
            agent=agent,
            tools=tools or [],
            depends_on=depends_on or [],
            condition=condition,
            output_var=output_var,
            max_retries=max_retries
        )
        
        workflow.add_step(step)
        return step
    
    async def execute(
        self,
        workflow_id: str,
        initial_variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """执行工作流"""
        workflow = self.workflows.get(workflow_id)
        if workflow is None:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        # 初始化变量
        if initial_variables:
            workflow.variables.update(initial_variables)
        
        workflow.status = WorkflowStatus.RUNNING
        workflow.started_at = datetime.now()
        
        results = {
            "workflow_id": workflow.id,
            "workflow_name": workflow.name,
            "steps_completed": [],
            "steps_failed": [],
            "final_result": None
        }
        
        try:
            while True:
                ready_steps = workflow.get_ready_steps()
                
                if not ready_steps:
                    # 检查是否全部完成
                    if all(s.status in [StepStatus.COMPLETED, StepStatus.SKIPPED] for s in workflow.steps):
                        workflow.status = WorkflowStatus.COMPLETED
                        break
                    elif any(s.status == StepStatus.FAILED for s in workflow.steps):
                        workflow.status = WorkflowStatus.FAILED
                        break
                    else:
                        # 可能有步骤在等待条件
                        await asyncio.sleep(0.1)
                        continue
                
                # 执行就绪的步骤
                for step in ready_steps:
                    await self._execute_step(workflow, step, results)
                
                # 检查是否全部完成
                if all(s.status in [StepStatus.COMPLETED, StepStatus.SKIPPED] for s in workflow.steps):
                    workflow.status = WorkflowStatus.COMPLETED
                    break
                
                if any(s.status == StepStatus.FAILED and s.retry_count >= s.max_retries for s in workflow.steps):
                    workflow.status = WorkflowStatus.FAILED
                    break
        
        except Exception as e:
            workflow.status = WorkflowStatus.FAILED
            results["error"] = str(e)
            await self._trigger_callbacks("on_workflow_error", workflow, e)
        
        workflow.completed_at = datetime.now()
        results["final_result"] = workflow.variables
        
        await self._trigger_callbacks("on_workflow_complete", workflow, results)
        
        return results
    
    async def _execute_step(
        self,
        workflow: Workflow,
        step: WorkflowStep,
        results: Dict[str, Any]
    ):
        """执行单个步骤"""
        step.status = StepStatus.RUNNING
        step.started_at = datetime.now()
        workflow.current_step = step.id
        
        await self._trigger_callbacks("on_step_start", workflow, step)
        
        try:
            # 检查条件
            if not self._evaluate_condition(step, workflow.variables):
                step.status = StepStatus.SKIPPED
                step.completed_at = datetime.now()
                return
            
            # 准备输入变量
            input_data = self._prepare_step_input(step, workflow.variables)
            
            # 执行任务
            if step.agent and self.agent_manager:
                agent = self.agent_manager.get_agent(step.agent)
                if agent:
                    result = await agent.execute_task(step.task, input_data)
                else:
                    raise ValueError(f"Agent {step.agent} not found")
            else:
                # 模拟执行
                await asyncio.sleep(0.1)
                result = f"Executed: {step.task}"
            
            # 保存结果
            step.result = result
            if step.output_var:
                workflow.variables[step.output_var] = result
            
            step.status = StepStatus.COMPLETED
            results["steps_completed"].append(step.name)
            
            await self._trigger_callbacks("on_step_complete", workflow, step, result)
        
        except Exception as e:
            step.error = str(e)
            
            if step.retry_count < step.max_retries:
                step.retry_count += 1
                step.status = StepStatus.PENDING
            else:
                step.status = StepStatus.FAILED
                results["steps_failed"].append(step.name)
            
            await self._trigger_callbacks("on_step_error", workflow, step, e)
        
        finally:
            step.completed_at = datetime.now()
            if step.started_at:
                step.execution_time = (step.completed_at - step.started_at).total_seconds()
    
    def _evaluate_condition(self, step: WorkflowStep, variables: Dict[str, Any]) -> bool:
        """评估步骤执行条件"""
        if step.condition is None or step.condition_type == ConditionType.ALWAYS:
            return True
        
        try:
            condition = step.condition
            # 简单的条件评估
            if step.condition_type == ConditionType.EQUALS:
                key, value = condition.split("==")
                return str(variables.get(key.strip())) == value.strip()
            elif step.condition_type == ConditionType.NOT_EQUALS:
                key, value = condition.split("!=")
                return str(variables.get(key.strip())) != value.strip()
            elif step.condition_type == ConditionType.CONTAINS:
                key, value = condition.split(" in ")
                return value.strip() in str(variables.get(key.strip(), ""))
            elif step.condition_type == ConditionType.GREATER_THAN:
                key, value = condition.split(">")
                return float(variables.get(key.strip(), 0)) > float(value.strip())
            elif step.condition_type == ConditionType.LESS_THAN:
                key, value = condition.split("<")
                return float(variables.get(key.strip(), 0)) < float(value.strip())
            else:
                return True
        except:
            return True
    
    def _prepare_step_input(self, step: WorkflowStep, variables: Dict[str, Any]) -> Dict[str, Any]:
        """准备步骤输入"""
        input_data = {}
        
        for key, value in step.input_mapping.items():
            if value in variables:
                input_data[key] = variables[value]
        
        return input_data
    
    def register_callback(self, event: str, callback: Callable):
        """注册回调函数"""
        if event in self.callbacks:
            self.callbacks[event].append(callback)
    
    async def _trigger_callbacks(self, event: str, *args):
        """触发回调"""
        if event in self.callbacks:
            for callback in self.callbacks[event]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(*args)
                    else:
                        callback(*args)
                except Exception as e:
                    print(f"Callback error: {e}")
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """获取工作流状态"""
        workflow = self.workflows.get(workflow_id)
        if workflow is None:
            return None
        
        return {
            "id": workflow.id,
            "name": workflow.name,
            "status": workflow.status.value,
            "current_step": workflow.current_step,
            "steps": [
                {
                    "name": s.name,
                    "status": s.status.value,
                    "result": str(s.result) if s.result else None,
                    "error": s.error,
                    "execution_time": s.execution_time
                }
                for s in workflow.steps
            ],
            "variables": workflow.variables
        }
    
    def export_workflow(self, workflow_id: str) -> Optional[str]:
        """导出工作流为 JSON"""
        workflow = self.workflows.get(workflow_id)
        if workflow is None:
            return None
        
        data = {
            "id": workflow.id,
            "name": workflow.name,
            "description": workflow.description,
            "steps": [
                {
                    "name": s.name,
                    "description": s.description,
                    "agent": s.agent,
                    "task": s.task,
                    "tools": s.tools,
                    "depends_on": s.depends_on,
                    "condition": s.condition,
                    "output_var": s.output_var,
                    "max_retries": s.max_retries
                }
                for s in workflow.steps
            ]
        }
        
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    def import_workflow(self, json_str: str) -> Optional[Workflow]:
        """从 JSON 导入工作流"""
        try:
            data = json.loads(json_str)
            
            workflow = Workflow(
                name=data.get("name", ""),
                description=data.get("description", "")
            )
            
            step_id_map = {}  # 名称到ID的映射
            
            for step_data in data.get("steps", []):
                step = WorkflowStep(
                    name=step_data.get("name", ""),
                    description=step_data.get("description", ""),
                    agent=step_data.get("agent"),
                    task=step_data.get("task", ""),
                    tools=step_data.get("tools", []),
                    output_var=step_data.get("output_var"),
                    max_retries=step_data.get("max_retries", 3)
                )
                step_id_map[step.name] = step.id
                workflow.add_step(step)
            
            # 修复依赖关系
            for step in workflow.steps:
                step_data = next((s for s in data.get("steps", []) if s["name"] == step.name), {})
                depends_on_names = step_data.get("depends_on", [])
                step.depends_on = [step_id_map.get(name, name) for name in depends_on_names]
            
            self.workflows[workflow.id] = workflow
            return workflow
        
        except Exception as e:
            print(f"Import error: {e}")
            return None
