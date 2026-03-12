"""
仲裁员 (Arbitrator Agent)

负责解决Agent之间的冲突和争议，如同古代的"三公"之一
当Agent之间出现分歧时，由仲裁员做出公正裁决
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid


class DisputeType(Enum):
    """争议类型"""
    RESOURCE_CONFLICT = "resource_conflict"     # 资源争夺
    TASK_ASSIGNMENT = "task_assignment"       # 任务分配
    OUTPUT_CONFLICT = "output_conflict"       # 输出冲突
    AUTHORITY_DISPUTE = "authority_dispute"   # 权限争议
    PRIORITY_CONFLICT = "priority_conflict"   # 优先级冲突
    COMMUNICATION_BREAKDOWN = "communication_breakdown"  # 通信故障


class ResolutionStrategy(Enum):
    """解决策略"""
    PRIORITY_BASED = "priority_based"         # 基于优先级
    ROUND_ROBIN = "round_robin"              # 轮询
    ARBITRATION = "arbitration"              # 仲裁
    ESCALATION = "escalation"               # 升级
    MERGE = "merge"                        # 合并


@dataclass
class Dispute:
    """争议"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    dispute_type: DisputeType = DisputeType.RESOURCE_CONFLICT
    
    # 参与方
    parties: List[str] = field(default_factory=list)
    
    # 争议内容
    description: str = ""
    evidence: Dict[str, Any] = field(default_factory=dict)
    
    # 状态
    status: str = "open"  # open, resolving, resolved, escalated
    priority: int = 0
    
    # 时间
    created_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    
    # 解决方案
    resolution: Optional[str] = None
    resolution_strategy: Optional[ResolutionStrategy] = None


@dataclass
class ArbitrationResult:
    """仲裁结果"""
    dispute_id: str = ""
    decision: str = ""
    winners: List[str] = field(default_factory=list)
    losers: List[str] = field(default_factory=list)
    conditions: List[str] = field(default_factory=list)
    appeals: List[str] = field(default_factory=list)


@dataclass
class ArbitratorConfig:
    """仲裁员配置"""
    name: str = "arbitrator"
    role: str = "仲裁员"
    
    # 仲裁规则
    max_retries: int = 3                     # 最大重试次数
    timeout_seconds: int = 300             # 超时时间
    auto_resolve_simple: bool = True       # 自动解决简单争议
    
    # 优先级设置
    priority_weights: Dict[str, float] = field(default_factory=lambda: {
        "reviewer": 1.0,
        "presenter": 0.9,
        "researcher": 0.8,
        "writer": 0.7,
        "editor": 0.6
    })
    
    # 升级阈值
    escalation_threshold: int = 3           # 升级阈值
    
    # 角色定义
    goal: str = "公正解决Agent之间的冲突，维护系统秩序"
    backstory: str = """你是一位公正无私的仲裁者，精通各类冲突的解决之道。
    你会根据事实和规则做出公正的裁决，不会偏袒任何一方。
    你的目标是维护系统的整体利益和长期稳定。"""
    responsibilities: List[str] = field(default_factory=lambda: [
        "接收和处理争议",
        "调查事实真相",
        "制定解决方案",
        "执行仲裁裁决",
        "防止冲突升级"
    ])


class ArbitratorAgent:
    """仲裁员Agent
    
    如同古代的"三公"（太尉、司徒、司空）
    当Agent之间出现冲突时，由仲裁员做出公正裁决
    """
    
    def __init__(self, config: Optional[ArbitratorConfig] = None):
        self.config = config or ArbitratorConfig()
        
        # 争议记录
        self.disputes: Dict[str, Dispute] = {}
        
        # 历史仲裁
        self.arbitrations: List[ArbitrationResult] = []
        
        # 统计
        self.stats: Dict[str, Any] = {
            "total_disputes": 0,
            "resolved": 0,
            "escalated": 0,
            "by_type": {}
        }
    
    def register_dispute(
        self,
        dispute_type: DisputeType,
        parties: List[str],
        description: str,
        evidence: Optional[Dict[str, Any]] = None,
        priority: int = 0
    ) -> Dispute:
        """注册争议"""
        dispute = Dispute(
            dispute_type=dispute_type,
            parties=parties,
            description=description,
            evidence=evidence or {},
            priority=priority
        )
        
        self.disputes[dispute.id] = dispute
        self.stats["total_disputes"] += 1
        
        # 统计类型
        if dispute_type.value not in self.stats["by_type"]:
            self.stats["by_type"][dispute_type.value] = 0
        self.stats["by_type"][dispute_type.value] += 1
        
        return dispute
    
    async def resolve(self, dispute_id: str) -> ArbitrationResult:
        """解决争议"""
        dispute = self.disputes.get(dispute_id)
        if not dispute:
            raise ValueError(f"Dispute {dispute_id} not found")
        
        if dispute.status != "open":
            raise ValueError(f"Dispute {dispute_id} is not open")
        
        dispute.status = "resolving"
        
        # 根据争议类型选择解决策略
        strategy = self._select_strategy(dispute)
        
        # 执行仲裁
        result = await self._arbitrate(dispute, strategy)
        
        # 更新状态
        dispute.status = "resolved"
        dispute.resolved_at = datetime.now()
        dispute.resolution = result.decision
        dispute.resolution_strategy = strategy
        
        self.arbitrations.append(result)
        self.stats["resolved"] += 1
        
        return result
    
    def _select_strategy(self, dispute: Dispute) -> ResolutionStrategy:
        """选择解决策略"""
        # 简单的资源争夺，使用优先级
        if dispute.dispute_type == DisputeType.RESOURCE_CONFLICT:
            return ResolutionStrategy.PRIORITY_BASED
        
        # 任务分配问题，轮询
        elif dispute.dispute_type == DisputeType.TASK_ASSIGNMENT:
            return ResolutionStrategy.ROUND_ROBIN
        
        # 输出冲突，尝试合并
        elif dispute.dispute_type == DisputeType.OUTPUT_CONFLICT:
            return ResolutionStrategy.MERGE
        
        # 权限争议，仲裁
        elif dispute.dispute_type == DisputeType.AUTHORITY_DISPUTE:
            return ResolutionStrategy.ARBITRATION
        
        # 默认仲裁
        return ResolutionStrategy.ARBITRATION
    
    async def _arbitrate(
        self,
        dispute: Dispute,
        strategy: ResolutionStrategy
    ) -> ArbitrationResult:
        """执行仲裁"""
        if strategy == ResolutionStrategy.PRIORITY_BASED:
            return await self._resolve_by_priority(dispute)
        elif strategy == ResolutionStrategy.ROUND_ROBIN:
            return await self._resolve_by_round_robin(dispute)
        elif strategy == ResolutionStrategy.MERGE:
            return await self._resolve_by_merge(dispute)
        elif strategy == ResolutionStrategy.ARBITRATION:
            return await self._resolve_by_arbitration(dispute)
        else:
            return await self._resolve_by_arbitration(dispute)
    
    async def _resolve_by_priority(self, dispute: Dispute) -> ArbitrationResult:
        """基于优先级解决"""
        # 获取各方的优先级
        priorities = []
        for party in dispute.parties:
            priority = self.config.priority_weights.get(party, 0.5)
            priorities.append((party, priority))
        
        # 按优先级排序
        priorities.sort(key=lambda x: x[1], reverse=True)
        
        winner = priorities[0][0]
        losers = [p[0] for p in priorities[1:]]
        
        return ArbitrationResult(
            dispute_id=dispute.id,
            decision=f"基于优先级判定，{winner} 获得资源",
            winners=[winner],
            losers=losers,
            conditions=[f"{loser} 需等待 {winner} 完成"]
        )
    
    async def _resolve_by_round_robin(self, dispute: Dispute) -> ArbitrationResult:
        """轮询解决"""
        # 简单轮询，第一个party获胜
        winner = dispute.parties[0]
        losers = dispute.parties[1:]
        
        return ArbitrationResult(
            dispute_id=dispute.id,
            decision=f"轮询判定，{winner} 获得本次任务",
            winners=[winner],
            losers=losers,
            conditions=[f"下次任务轮换到 {losers[0]}" if losers else ""]
        )
    
    async def _resolve_by_merge(self, dispute: Dispute) -> ArbitrationResult:
        """合并解决"""
        return ArbitrationResult(
            dispute_id=dispute.id,
            decision="建议合并各方的输出",
            winners=dispute.parties,
            losers=[],
            conditions=["各方需配合整合输出"]
        )
    
    async def _resolve_by_arbitration(self, dispute: Dispute) -> ArbitrationResult:
        """仲裁解决"""
        # 收集证据
        evidence_summary = self._summarize_evidence(dispute.evidence)
        
        # 基于证据做出裁决
        # 这里使用简化的逻辑，实际可以更复杂
        decision = f"经仲裁调查，{evidence_summary}。判定如下："
        
        return ArbitrationResult(
            dispute_id=dispute.id,
            decision=decision,
            winners=dispute.parties[:1],
            losers=dispute.parties[1:],
            conditions=["各方需遵守仲裁结果"]
        )
    
    def _summarize_evidence(self, evidence: Dict[str, Any]) -> str:
        """总结证据"""
        if not evidence:
            return "证据不足"
        
        return f"根据提供的 {len(evidence)} 项证据"
    
    def escalate(self, dispute_id: str) -> bool:
        """升级争议"""
        dispute = self.disputes.get(dispute_id)
        if not dispute:
            return False
        
        dispute.status = "escalated"
        self.stats["escalated"] += 1
        
        return True
    
    def get_dispute(self, dispute_id: str) -> Optional[Dispute]:
        """获取争议"""
        return self.disputes.get(dispute_id)
    
    def get_open_disputes(self) -> List[Dispute]:
        """获取开放争议"""
        return [d for d in self.disputes.values() if d.status == "open"]
    
    def get_resolved_disputes(self) -> List[Dispute]:
        """获取已解决争议"""
        return [d for d in self.disputes.values() if d.status == "resolved"]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计"""
        return {
            "total_disputes": self.stats["total_disputes"],
            "resolved": self.stats["resolved"],
            "escalated": self.stats["escalated"],
            "open": len(self.get_open_disputes()),
            "by_type": self.stats["by_type"]
        }
    
    def prevent_conflict(
        self,
        agent1: str,
        agent2: str,
        resource_type: str
    ) -> str:
        """预防冲突"""
        # 简单的时间分割策略
        import time
        current_second = int(time.time()) % 60
        
        if current_second < 30:
            winner = agent1
            loser = agent2
        else:
            winner = agent2
            loser = agent1
        
        return f"时间分割：{winner} 在前30秒使用，{loser} 在后30秒使用"
