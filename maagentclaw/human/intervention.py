"""
Human-in-the-loop 支持模块

支持人工介入、审批和反馈机制
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
import asyncio


class ApprovalStatus(Enum):
    """审批状态"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class InterventionType(Enum):
    """介入类型"""
    APPROVAL = "approval"       # 审批请求
    FEEDBACK = "feedback"       # 反馈请求
    SELECTION = "selection"     # 选择请求
    CONFIRMATION = "confirmation"  # 确认请求
    ESCALATION = "escalation"   # 升级请求


@dataclass
class ApprovalRequest:
    """审批请求"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str = ""
    task_description: str = ""
    requester: str = ""          # 请求者
    approver: str = ""           # 审批人
    priority: int = 0           # 优先级
    status: ApprovalStatus = ApprovalStatus.PENDING
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    deadline: Optional[datetime] = None  # 截止时间
    timeout_seconds: int = 3600  # 默认超时时间（1小时）
    
    def approve(self, approver: str, comment: str = ""):
        """批准"""
        self.status = ApprovalStatus.APPROVED
        self.approver = approver
        self.context["comment"] = comment
        self.updated_at = datetime.now()
    
    def reject(self, approver: str, reason: str = ""):
        """拒绝"""
        self.status = ApprovalStatus.REJECTED
        self.approver = approver
        self.context["reason"] = reason
        self.updated_at = datetime.now()
    
    def cancel(self):
        """取消"""
        self.status = ApprovalStatus.CANCELLED
        self.updated_at = datetime.now()
    
    def is_timeout(self) -> bool:
        """检查是否超时"""
        if self.status != ApprovalStatus.PENDING:
            return False
        if self.deadline is None:
            deadline = datetime.fromtimestamp(
                self.created_at.timestamp() + self.timeout_seconds
            )
            return datetime.now() > deadline
        return datetime.now() > self.deadline


@dataclass
class HumanFeedback:
    """人工反馈"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    agent_name: str = ""
    content: str = ""
    feedback_type: str = "general"  # general, correction, suggestion, question
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class HumanIntervention:
    """人工介入管理器"""
    
    def __init__(self):
        self.pending_approvals: Dict[str, ApprovalRequest] = {}
        self.feedback_history: List[HumanFeedback] = []
        self.callbacks: Dict[str, List[Callable]] = {
            "on_approval": [],
            "on_rejection": [],
            "on_feedback": [],
            "on_timeout": []
        }
        self._lock = asyncio.Lock()
    
    async def request_approval(
        self,
        task_id: str,
        task_description: str,
        requester: str,
        approver: str,
        priority: int = 0,
        context: Optional[Dict[str, Any]] = None,
        timeout_seconds: int = 3600
    ) -> ApprovalRequest:
        """请求人工审批"""
        async with self._lock:
            approval = ApprovalRequest(
                task_id=task_id,
                task_description=task_description,
                requester=requester,
                approver=approver,
                priority=priority,
                context=context or {},
                timeout_seconds=timeout_seconds
            )
            
            self.pending_approvals[approval.id] = approval
            return approval
    
    async def wait_for_approval(
        self,
        approval_id: str,
        check_interval: float = 1.0
    ) -> ApprovalRequest:
        """等待审批结果"""
        start_time = datetime.now()
        
        while True:
            approval = self.pending_approvals.get(approval_id)
            if approval is None:
                raise ValueError(f"Approval {approval_id} not found")
            
            # 检查是否超时
            if approval.is_timeout():
                approval.status = ApprovalStatus.TIMEOUT
                await self._trigger_callbacks("on_timeout", approval)
                return approval
            
            # 检查审批状态
            if approval.status != ApprovalStatus.PENDING:
                if approval.status == ApprovalStatus.APPROVED:
                    await self._trigger_callbacks("on_approval", approval)
                elif approval.status == ApprovalStatus.REJECTED:
                    await self._trigger_callbacks("on_rejection", approval)
                return approval
            
            # 等待一段时间后再次检查
            await asyncio.sleep(check_interval)
    
    async def approve(
        self,
        approval_id: str,
        approver: str,
        comment: str = ""
    ) -> bool:
        """批准请求"""
        async with self._lock:
            approval = self.pending_approvals.get(approval_id)
            if approval is None:
                return False
            
            approval.approve(approver, comment)
            return True
    
    async def reject(
        self,
        approval_id: str,
        approver: str,
        reason: str = ""
    ) -> bool:
        """拒绝请求"""
        async with self._lock:
            approval = self.pending_approvals.get(approval_id)
            if approval is None:
                return False
            
            approval.reject(approver, reason)
            return True
    
    async def add_feedback(
        self,
        session_id: str,
        agent_name: str,
        content: str,
        feedback_type: str = "general",
        metadata: Optional[Dict[str, Any]] = None
    ) -> HumanFeedback:
        """添加人工反馈"""
        feedback = HumanFeedback(
            session_id=session_id,
            agent_name=agent_name,
            content=content,
            feedback_type=feedback_type,
            metadata=metadata or {}
        )
        
        self.feedback_history.append(feedback)
        await self._trigger_callbacks("on_feedback", feedback)
        
        return feedback
    
    def get_pending_approvals(self, approver: Optional[str] = None) -> List[ApprovalRequest]:
        """获取待审批列表"""
        approvals = [
            a for a in self.pending_approvals.values()
            if a.status == ApprovalStatus.PENDING
        ]
        
        if approver:
            approvals = [a for a in approvals if a.approver == approver]
        
        # 按优先级和创建时间排序
        approvals.sort(key=lambda a: (-a.priority, a.created_at))
        return approvals
    
    def get_feedback_history(
        self,
        session_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        limit: int = 100
    ) -> List[HumanFeedback]:
        """获取反馈历史"""
        feedbacks = self.feedback_history
        
        if session_id:
            feedbacks = [f for f in feedbacks if f.session_id == session_id]
        
        if agent_name:
            feedbacks = [f for f in feedbacks if f.agent_name == agent_name]
        
        return feedbacks[-limit:]
    
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


class InteractiveAgentMixin:
    """交互式 Agent 混入类
    
    用于给 Agent 添加人机交互能力
    """
    
    def __init__(self):
        self.intervention: Optional[HumanIntervention] = None
    
    def set_intervention(self, intervention: HumanIntervention):
        """设置人工介入管理器"""
        self.intervention = intervention
    
    async def request_human_approval(
        self,
        task_description: str,
        approver: str = "human",
        timeout: int = 3600
    ) -> bool:
        """请求人工审批"""
        if self.intervention is None:
            return True  # 没有介入管理器，直接通过
        
        approval = await self.intervention.request_approval(
            task_id=self.config.name,
            task_description=task_description,
            requester=self.config.name,
            approver=approver,
            context={"agent": self.config.name}
        )
        
        result = await self.intervention.wait_for_approval(approval.id)
        return result.status == ApprovalStatus.APPROVED
    
    async def get_human_feedback(self, question: str) -> Optional[str]:
        """获取人工反馈"""
        if self.intervention is None:
            return None
        
        # 等待人工反馈（这里简化处理，实际可能需要更复杂的机制）
        await asyncio.sleep(0.1)
        
        feedbacks = self.intervention.get_feedback_history(
            agent_name=self.config.name
        )
        
        if feedbacks:
            return feedbacks[-1].content
        
        return None


class ApprovalWorkflow:
    """审批工作流"""
    
    def __init__(self, intervention: HumanIntervention):
        self.intervention = intervention
        self.workflows: Dict[str, Dict[str, Any]] = {}
    
    def define_workflow(
        self,
        name: str,
        steps: List[Dict[str, Any]]
    ):
        """定义审批工作流
        
        steps 格式:
        [
            {"name": "step1", "approver": "manager", "condition": "high_priority"},
            {"name": "step2", "approver": "director", "condition": "very_high_priority"}
        ]
        """
        self.workflows[name] = {
            "steps": steps,
            "created_at": datetime.now()
        }
    
    async def execute(
        self,
        workflow_name: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行审批工作流"""
        workflow = self.workflows.get(workflow_name)
        if workflow is None:
            raise ValueError(f"Workflow {workflow_name} not found")
        
        results = {
            "workflow": workflow_name,
            "steps_completed": [],
            "steps_rejected": [],
            "final_status": "completed"
        }
        
        for step in workflow["steps"]:
            step_name = step["name"]
            approver = step["approver"]
            condition = step.get("condition", "true")
            
            # 检查条件
            if not self._evaluate_condition(condition, context):
                continue
            
            # 请求审批
            approval = await self.intervention.request_approval(
                task_id=step_name,
                task_description=f"审批步骤: {step_name}",
                requester=context.get("requester", "system"),
                approver=approver,
                priority=context.get("priority", 0),
                context=context
            )
            
            # 等待审批
            result = await self.intervention.wait_for_approval(approval.id)
            
            if result.status == ApprovalStatus.APPROVED:
                results["steps_completed"].append(step_name)
                context[f"{step_name}_approved"] = True
            else:
                results["steps_rejected"].append(step_name)
                results["final_status"] = "rejected"
                break
        
        return results
    
    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """评估条件"""
        if condition == "true":
            return True
        
        # 简单条件评估
        try:
            return eval(condition, {"context": context})
        except:
            return False
