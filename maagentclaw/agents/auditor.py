"""
审计员 (Auditor Agent)

负责审计和监控Agent的异常行为，如同古代的"郡监"
负责监察地方官员的行为，防止腐败和渎职
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import time


class AuditLevel(Enum):
    """审计级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AnomalyType(Enum):
    """异常类型"""
    HIGH_TOKEN_USAGE = "high_token_usage"      # 高Token消耗
    HIGH_LATENCY = "high_latency"              # 高延迟
    REPEATED_ERRORS = "repeated_errors"         # 重复错误
    SUSPICIOUS_PATTERN = "suspicious_pattern"   # 可疑模式
    RESOURCE_LEAK = "resource_leak"            # 资源泄漏
    DEADLOCK = "deadlock"                       # 死锁
    INFINITE_LOOP = "infinite_loop"             # 无限循环


@dataclass
class AuditRecord:
    """审计记录"""
    id: str = field(default_factory=lambda: str(time.time()))
    agent_name: str = ""
    action: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    level: AuditLevel = AuditLevel.INFO
    
    # 详细信息
    details: Dict[str, Any] = field(default_factory=dict)
    resource_usage: Dict[str, float] = field(default_factory=dict)
    duration: float = 0.0
    
    # 上下文
    session_id: Optional[str] = None
    task_id: Optional[str] = None


@dataclass
class AnomalyReport:
    """异常报告"""
    anomaly_type: AnomalyType
    severity: AuditLevel
    agent_name: str
    description: str
    evidence: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class AuditConfig:
    """审计配置"""
    name: str = "auditor"
    role: str = "审计员"
    
    # Token 异常阈值
    token_usage_threshold: int = 50000        # 单小时Token使用阈值
    token_per_message_threshold: int = 10000  # 单消息Token阈值
    
    # 延迟异常阈值
    latency_threshold_ms: int = 30000          # 30秒延迟阈值
    
    # 错误率阈值
    error_rate_threshold: float = 0.3         # 30%错误率阈值
    
    # 模式识别
    detect_repetition: bool = True             # 检测重复
    detect_circular: bool = True              # 检测循环
    
    # 审计级别
    log_all_actions: bool = True              # 记录所有操作
    log_resource_usage: bool = True          # 记录资源使用
    
    # 角色定义
    goal: str = "确保系统行为合规，及时发现和处理异常"
    backstory: str = """你是一位严谨的审计人员，熟悉各类异常模式，
    能够通过日志和行为分析发现潜在问题。你铁面无私，
    不会放过任何可疑的迹象。"""
    responsibilities: List[str] = field(default_factory=lambda: [
        "监控Agent行为",
        "分析异常模式",
        "审计资源使用",
        "生成审计报告",
        "提出改进建议"
    ])


class AuditorAgent:
    """审计员Agent
    
    如同古代的"郡监"，负责监察地方官员的行为
    监控所有Agent的行为，及时发现异常
    """
    
    def __init__(self, config: Optional[AuditConfig] = None):
        self.config = config or AuditConfig()
        
        # 审计记录
        self.records: List[AuditRecord] = []
        self.max_records = 10000
        
        # 异常检测
        self.anomalies: List[AnomalyReport] = []
        
        # 统计
        self.stats: Dict[str, Any] = {
            "total_records": 0,
            "by_level": {level.value: 0 for level in AuditLevel},
            "by_agent": {}
        }
        
        # 滑动窗口（用于计算速率）
        self.recent_tokens: Dict[str, List[float]] = {}  # agent -> [(timestamp, tokens)]
        self.recent_errors: Dict[str, List[datetime]] = {}  # agent -> [error_times]
        self.recent_latencies: Dict[str, List[float]] = {}  # agent -> [latencies]
    
    def record(
        self,
        agent_name: str,
        action: str,
        level: AuditLevel = AuditLevel.INFO,
        details: Optional[Dict[str, Any]] = None,
        resource_usage: Optional[Dict[str, float]] = None,
        duration: float = 0.0,
        session_id: Optional[str] = None,
        task_id: Optional[str] = None
    ) -> AuditRecord:
        """记录审计信息"""
        record = AuditRecord(
            agent_name=agent_name,
            action=action,
            level=level,
            details=details or {},
            resource_usage=resource_usage or {},
            duration=duration,
            session_id=session_id,
            task_id=task_id
        )
        
        # 添加到记录
        self.records.append(record)
        self.stats["total_records"] += 1
        self.stats["by_level"][level.value] += 1
        
        # 按Agent统计
        if agent_name not in self.stats["by_agent"]:
            self.stats["by_agent"][agent_name] = 0
        self.stats["by_agent"][agent_name] += 1
        
        # 维护滑动窗口
        self._update_sliding_windows(agent_name, resource_usage, duration)
        
        # 检查异常
        self._check_anomalies(agent_name)
        
        # 限制记录数量
        if len(self.records) > self.max_records:
            self.records = self.records[-self.max_records:]
        
        return record
    
    def _update_sliding_windows(
        self,
        agent_name: str,
        resource_usage: Optional[Dict[str, float]],
        duration: float
    ):
        """更新滑动窗口"""
        now = time.time()
        
        # Token 使用窗口
        if resource_usage and "tokens" in resource_usage:
            if agent_name not in self.recent_tokens:
                self.recent_tokens[agent_name] = []
            
            self.recent_tokens[agent_name].append((now, resource_usage["tokens"]))
            
            # 清理1小时前的数据
            self.recent_tokens[agent_name] = [
                (t, v) for t, v in self.recent_tokens[agent_name]
                if now - t < 3600
            ]
        
        # 延迟窗口
        if duration > 0:
            if agent_name not in self.recent_latencies:
                self.recent_latencies[agent_name] = []
            
            self.recent_latencies[agent_name].append(duration)
            
            # 保留最近100条
            self.recent_latencies[agent_name] = self.recent_latencies[agent_name][-100:]
    
    def _check_anomalies(self, agent_name: str):
        """检查异常"""
        now = time.time()
        
        # 1. 检查Token使用异常
        if agent_name in self.recent_tokens:
            tokens_last_hour = sum(
                v for t, v in self.recent_tokens[agent_name]
                if now - t < 3600
            )
            
            if tokens_last_hour > self.config.token_usage_threshold:
                self._report_anomaly(
                    agent_name=agent_name,
                    anomaly_type=AnomalyType.HIGH_TOKEN_USAGE,
                    severity=AuditLevel.WARNING,
                    description=f"Agent {agent_name} 过去1小时使用Token {tokens_last_hour}，超过阈值 {self.config.token_usage_threshold}",
                    evidence={"tokens": tokens_last_hour, "threshold": self.config.token_usage_threshold},
                    recommendations=["检查Agent是否有资源泄漏", "考虑限制Token使用", "审查任务复杂度"]
                )
        
        # 2. 检查延迟异常
        if agent_name in self.recent_latencies:
            latencies = self.recent_latencies[agent_name]
            if latencies:
                avg_latency = sum(latencies) / len(latencies)
                
                if avg_latency > self.config.latency_threshold_ms / 1000:
                    self._report_anomaly(
                        agent_name=agent_name,
                        anomaly_type=AnomalyType.HIGH_LATENCY,
                        severity=AuditLevel.WARNING,
                        description=f"Agent {agent_name} 平均延迟 {avg_latency:.2f}秒，超过阈值 {self.config.latency_threshold_ms/1000}秒",
                        evidence={"avg_latency": avg_latency, "threshold": self.config.latency_threshold_ms/1000},
                        recommendations=["检查Agent是否陷入死循环", "审查外部API调用", "检查网络延迟"]
                    )
        
        # 3. 检查错误率
        if agent_name in self.recent_errors:
            error_times = self.recent_errors[agent_name]
            recent_errors = [t for t in error_times if (now - t.timestamp()) < 3600]
            
            if len(recent_errors) > 10:
                self._report_anomaly(
                    agent_name=agent_name,
                    anomaly_type=AnomalyType.REPEATED_ERRORS,
                    severity=AuditLevel.ERROR,
                    description=f"Agent {agent_name} 过去1小时发生 {len(recent_errors)} 次错误",
                    evidence={"error_count": len(recent_errors)},
                    recommendations=["检查Agent代码是否有Bug", "审查外部依赖", "添加错误处理"]
                )
    
    def _report_anomaly(
        self,
        agent_name: str,
        anomaly_type: AnomalyType,
        severity: AuditLevel,
        description: str,
        evidence: Dict[str, Any],
        recommendations: List[str]
    ):
        """报告异常"""
        # 检查是否已存在类似异常（避免重复报告）
        for existing in self.anomalies[-10:]:
            if (existing.agent_name == agent_name and 
                existing.anomaly_type == anomaly_type and
                (datetime.now() - existing.timestamp).seconds < 300):
                return
        
        report = AnomalyReport(
            anomaly_type=anomaly_type,
            severity=severity,
            agent_name=agent_name,
            description=description,
            evidence=evidence,
            recommendations=recommendations
        )
        
        self.anomalies.append(report)
        
        # 记录审计
        self.record(
            agent_name=agent_name,
            action=f"anomaly_detected:{anomaly_type.value}",
            level=severity,
            details={"description": description, "evidence": evidence}
        )
    
    def get_records(
        self,
        agent_name: Optional[str] = None,
        level: Optional[AuditLevel] = None,
        limit: int = 100
    ) -> List[AuditRecord]:
        """获取审计记录"""
        records = self.records
        
        if agent_name:
            records = [r for r in records if r.agent_name == agent_name]
        
        if level:
            records = [r for r in records if r.level == level]
        
        return records[-limit:]
    
    def get_anomalies(
        self,
        agent_name: Optional[str] = None,
        severity: Optional[AuditLevel] = None,
        limit: int = 50
    ) -> List[AnomalyReport]:
        """获取异常报告"""
        anomalies = self.anomalies
        
        if agent_name:
            anomalies = [a for a in anomalies if a.agent_name == agent_name]
        
        if severity:
            anomalies = [a for a in anomalies if a.severity == severity]
        
        return anomalies[-limit:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_records": self.stats["total_records"],
            "by_level": self.stats["by_level"],
            "by_agent": self.stats["by_agent"],
            "active_anomalies": len(self.anomalies),
            "recent_anomalies": len([a for a in self.anomalies if 
                (datetime.now() - a.timestamp).seconds < 3600])
        }
    
    def analyze_agent(self, agent_name: str) -> Dict[str, Any]:
        """分析特定Agent"""
        records = [r for r in self.records if r.agent_name == agent_name]
        
        if not records:
            return {"error": "No records found"}
        
        # 计算统计
        total_duration = sum(r.duration for r in records)
        avg_duration = total_duration / len(records) if records else 0
        
        level_counts = {}
        for r in records:
            level_counts[r.level.value] = level_counts.get(r.level.value, 0) + 1
        
        return {
            "agent_name": agent_name,
            "total_actions": len(records),
            "avg_duration": avg_duration,
            "level_distribution": level_counts,
            "recent_anomalies": len([a for a in self.anomalies if a.agent_name == agent_name])
        }
    
    def clear_old_records(self, hours: int = 24):
        """清除旧记录"""
        cutoff = datetime.now() - timedelta(hours=hours)
        self.records = [r for r in self.records if r.timestamp > cutoff]
        self.anomalies = [a for a in self.anomalies if a.timestamp > cutoff]
