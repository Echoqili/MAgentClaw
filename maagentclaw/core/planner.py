from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
import uuid


class PlanStatus(Enum):
    """计划状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
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


@dataclass
class PlanStep:
    """计划步骤"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    action: str = ""
    params: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    status: StepStatus = StepStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "action": self.action,
            "params": self.params,
            "dependencies": self.dependencies,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


@dataclass
class Plan:
    """执行计划"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    goal: str = ""
    description: str = ""
    steps: List[PlanStep] = field(default_factory=list)
    status: PlanStatus = PlanStatus.PENDING
    current_step: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "goal": self.goal,
            "description": self.description,
            "steps": [s.to_dict() for s in self.steps],
            "status": self.status.value,
            "current_step": self.current_step,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "context": self.context
        }

    def get_pending_steps(self) -> List[PlanStep]:
        """获取待执行的步骤"""
        return [s for s in self.steps if s.status == StepStatus.PENDING]

    def get_completed_steps(self) -> List[PlanStep]:
        """获取已完成的步骤"""
        return [s for s in self.steps if s.status == StepStatus.COMPLETED]

    def can_execute_step(self, step: PlanStep) -> bool:
        """检查步骤是否可以执行"""
        if step.status != StepStatus.PENDING:
            return False

        for dep_id in step.dependencies:
            dep_step = self._get_step_by_id(dep_id)
            if not dep_step or dep_step.status != StepStatus.COMPLETED:
                return False
        return True

    def _get_step_by_id(self, step_id: str) -> Optional[PlanStep]:
        """根据 ID 获取步骤"""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None

    def get_next_step(self) -> Optional[PlanStep]:
        """获取下一个可执行的步骤"""
        for step in self.steps:
            if self.can_execute_step(step):
                return step
        return None


@dataclass
class PlanResult:
    """计划执行结果"""
    success: bool
    plan: Plan
    final_result: Optional[Any] = None
    error: Optional[str] = None
    executed_steps: int = 0
    duration: Optional[float] = None
