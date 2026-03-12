"""
安全员 (Security Agent)

负责检测恶意行为和安全威胁，如同古代的"城门郎"或"卫尉"
负责保卫系统安全，防止内外部威胁
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import re


class ThreatLevel(Enum):
    """威胁级别"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ThreatType(Enum):
    """威胁类型"""
    INJECTION = "injection"             # 注入攻击
    OVERLOAD = "overload"             # 资源过载
    ESCALATION = "escalation"         # 权限提升
    DATA_LEAK = "data_leak"           # 数据泄露
    REPLAY = "replay"                 # 重放攻击
    MITM = "mitm"                     # 中间人攻击
    BRUTE_FORCE = "brute_force"       # 暴力破解
    SOCIAL_ENGINEERING = "social_engineering"  # 社会工程学


@dataclass
class SecurityAlert:
    """安全警报"""
    id: str = field(default_factory=lambda: str(datetime.now().timestamp()))
    threat_type: ThreatType = ThreatType.INJECTION
    threat_level: ThreatLevel = ThreatLevel.LOW
    
    # 来源
    source_agent: str = ""
    source_ip: Optional[str] = None
    
    # 详情
    description: str = ""
    evidence: Dict[str, Any] = field(default_factory=dict)
    
    # 行动
    action_taken: str = ""
    blocked: bool = False
    
    # 时间
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class SecurityPolicy:
    """安全策略"""
    name: str = ""
    enabled: bool = True
    
    # 输入验证
    block_sql_injection: bool = True
    block_xss: bool = True
    block_path_traversal: bool = True
    
    # 速率限制
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 60
    
    # 资源限制
    max_input_length: int = 100000
    max_file_size_mb: int = 10
    
    # 黑名单
    ip_blacklist: List[str] = field(default_factory=list)
    agent_blacklist: List[str] = field(default_factory=list)


@dataclass
class SecurityConfig:
    """安全配置"""
    name: str = "security"
    role: str = "安全员"
    
    # 安全策略
    policy: SecurityPolicy = field(default_factory=SecurityPolicy)
    
    # 监控设置
    monitor_input: bool = True
    monitor_output: bool = True
    monitor_resources: bool = True
    
    # 响应设置
    auto_block: bool = True
    alert_threshold: ThreatLevel = ThreatLevel.MEDIUM
    
    # 角色定义
    goal: str = "保卫系统安全，检测和阻止恶意行为"
    backstory: str = """你是一位经验丰富的安全专家，精通各类安全威胁和攻击模式。
    你时刻保持警惕，不会放过任何可疑的迹象。
    你的职责是保卫系统安全，防止内外部威胁。"""
    responsibilities: List[str] = field(default_factory=lambda: [
        "监控输入输出",
        "检测安全威胁",
        "阻止恶意行为",
        "生成安全报告",
        "更新安全策略"
    ])


class SecurityAgent:
    """安全员Agent
    
    如同古代的"城门郎"或"卫尉"
    负责保卫系统安全，检测和阻止恶意行为
    """
    
    def __init__(self, config: Optional[SecurityConfig] = None):
        self.config = config or SecurityConfig()
        
        # 安全警报
        self.alerts: List[SecurityAlert] = []
        
        # 黑名单
        self.blocked_agents: set = set()
        self.blocked_ips: set = set()
        
        # 统计
        self.stats: Dict[str, Any] = {
            "total_alerts": 0,
            "blocked_count": 0,
            "by_threat_type": {},
            "by_threat_level": {}
        }
        
        # 攻击模式库
        self.attack_patterns = self._init_attack_patterns()
    
    def _init_attack_patterns(self) -> Dict[ThreatType, List[str]]:
        """初始化攻击模式"""
        return {
            ThreatType.INJECTION: [
                r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION)\b)",
                r"(--|\#|\/\*|\*\/)",
                r"(\bOR\b.*=.*\bOR\b)",
                r"('|(\\'))",
            ],
            ThreatType.OVERLOAD: [
                r"(.+){100,}",
                r"(\n){50,}",
            ],
            ThreatType.ESCALATION: [
                r"(sudo|su\s)",
                r"(chmod|chown).*777",
                r"(eval|exec|system)\s*\(",
            ],
            ThreatType.PATH_TRAVERSAL: [
                r"(\.\./|\.\.\\)",
                r"(/etc/passwd|/etc/shadow)",
                r"(c:\\\\windows)",
            ],
        }
    
    def check_input(
        self,
        content: str,
        agent_name: str,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """检查输入是否安全，返回是否允许通过"""
        # 1. 检查黑名单
        if agent_name in self.blocked_agents:
            self._create_alert(
                ThreatType.SOCIAL_ENGINEERING,
                ThreatLevel.CRITICAL,
                agent_name,
                f"Agent {agent_name} 已被加入黑名单"
            )
            return False
        
        # 2. 检查输入长度
        if len(content) > self.config.policy.max_input_length:
            self._create_alert(
                ThreatType.OVERLOAD,
                ThreatLevel.HIGH,
                agent_name,
                f"输入长度 {len(content)} 超过限制 {self.config.policy.max_input_length}"
            )
            return False
        
        # 3. 检查注入攻击
        if self.config.policy.block_sql_injection:
            for pattern in self.attack_patterns.get(ThreatType.INJECTION, []):
                if re.search(pattern, content, re.IGNORECASE):
                    self._create_alert(
                        ThreatType.INJECTION,
                        ThreatLevel.CRITICAL,
                        agent_name,
                        f"检测到SQL注入尝试",
                        {"pattern": pattern, "content": content[:100]}
                    )
                    
                    if self.config.auto_block:
                        self.blocked_agents.add(agent_name)
                    
                    return False
        
        # 4. 检查XSS攻击
        if self.config.policy.block_xss:
            xss_patterns = [
                r"<script",
                r"javascript:",
                r"on\w+\s*=",
                r"<iframe",
            ]
            for pattern in xss_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    self._create_alert(
                        ThreatType.INJECTION,
                        ThreatLevel.HIGH,
                        agent_name,
                        f"检测到XSS攻击尝试",
                        {"pattern": pattern, "content": content[:100]}
                    )
                    
                    if self.config.auto_block:
                        self.blocked_agents.add(agent_name)
                    
                    return False
        
        # 5. 检查路径遍历
        if self.config.policy.block_path_traversal:
            for pattern in self.attack_patterns.get(ThreatType.PATH_TRAVERSAL, []):
                if re.search(pattern, content, re.IGNORECASE):
                    self._create_alert(
                        ThreatType.PATH_TRAVERSAL,
                        ThreatLevel.HIGH,
                        agent_name,
                        f"检测到路径遍历尝试",
                        {"pattern": pattern}
                    )
                    return False
        
        return True
    
    def check_output(
        self,
        content: str,
        agent_name: str,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """检查输出是否包含敏感信息"""
        # 检查敏感信息泄露
        sensitive_patterns = [
            (r"(api_key|apikey|api-key)\s*[=:]\s*[\w-]{20,}", "API密钥"),
            (r"(password|passwd|pwd)\s*[=:]\s*\S+", "密码"),
            (r"(secret|token)\s*[=:]\s*[\w-]{20,}", "密钥"),
            (r"\b\d{3}-\d{2}-\d{4}\b", "SSN"),
            (r"\b\d{16}\b", "信用卡号"),
        ]
        
        for pattern, label in sensitive_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                self._create_alert(
                    ThreatType.DATA_LEAK,
                    ThreatLevel.HIGH,
                    agent_name,
                    f"检测到可能的敏感信息泄露: {label}",
                    {"type": label}
                )
        
        return True
    
    def check_resource_usage(
        self,
        agent_name: str,
        resource_type: str,
        amount: float,
        threshold: float
    ) -> bool:
        """检查资源使用是否异常"""
        if amount > threshold:
            self._create_alert(
                ThreatType.OVERLOAD,
                ThreatLevel.MEDIUM,
                agent_name,
                f"资源使用异常: {resource_type} = {amount}, 阈值 = {threshold}",
                {"resource": resource_type, "amount": amount, "threshold": threshold}
            )
            return False
        
        return True
    
    def check_rate_limit(
        self,
        agent_name: str,
        window_seconds: int = 60
    ) -> bool:
        """检查速率限制"""
        if not self.config.policy.rate_limit_enabled:
            return True
        
        # 简化实现，实际应该用滑动窗口
        import time
        key = f"{agent_name}:{int(time.time() // window_seconds)}"
        
        # 这里简化处理，实际应该有计数器
        return True
    
    def _create_alert(
        self,
        threat_type: ThreatType,
        threat_level: ThreatLevel,
        source_agent: str,
        description: str,
        evidence: Optional[Dict[str, Any]] = None
    ) -> SecurityAlert:
        """创建安全警报"""
        alert = SecurityAlert(
            threat_type=threat_type,
            threat_level=threat_level,
            source_agent=source_agent,
            description=description,
            evidence=evidence or {}
        )
        
        self.alerts.append(alert)
        self.stats["total_alerts"] += 1
        
        # 统计
        if threat_type.value not in self.stats["by_threat_type"]:
            self.stats["by_threat_type"][threat_type.value] = 0
        self.stats["by_threat_type"][threat_type.value] += 1
        
        if threat_level.value not in self.stats["by_threat_level"]:
            self.stats["by_threat_level"][threat_level.value] = 0
        self.stats["by_threat_level"][threat_level.value] += 1
        
        return alert
    
    def block_agent(self, agent_name: str, reason: str = ""):
        """阻止Agent"""
        self.blocked_agents.add(agent_name)
        
        self._create_alert(
            ThreatType.ESCALATION,
            ThreatLevel.CRITICAL,
            agent_name,
            f"Agent {agent_name} 被阻止: {reason}"
        )
        
        self.stats["blocked_count"] += 1
    
    def unblock_agent(self, agent_name: str):
        """解除阻止"""
        self.blocked_agents.discard(agent_name)
    
    def get_alerts(
        self,
        threat_level: Optional[ThreatLevel] = None,
        limit: int = 50
    ) -> List[SecurityAlert]:
        """获取安全警报"""
        alerts = self.alerts
        
        if threat_level:
            alerts = [a for a in alerts if a.threat_level == threat_level]
        
        return alerts[-limit:]
    
    def is_blocked(self, agent_name: str) -> bool:
        """检查是否被阻止"""
        return agent_name in self.blocked_agents
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_alerts": self.stats["total_alerts"],
            "blocked_count": self.stats["blocked_count"],
            "blocked_agents": list(self.blocked_agents),
            "by_threat_type": self.stats["by_threat_type"],
            "by_threat_level": self.stats["by_threat_level"],
            "recent_critical": len([
                a for a in self.alerts[-20:] 
                if a.threat_level == ThreatLevel.CRITICAL
            ])
        }
    
    def generate_report(self) -> str:
        """生成安全报告"""
        lines = ["# 安全报告", ""]
        
        lines.append(f"## 统计")
        lines.append(f"- 总警报数: {self.stats['total_alerts']}")
        lines.append(f"- 阻止次数: {self.stats['blocked_count']}")
        lines.append(f"- 被阻止Agent: {', '.join(self.blocked_agents) or '无'}")
        
        lines.append("")
        lines.append(f"## 威胁类型分布")
        for threat_type, count in self.stats["by_threat_type"].items():
            lines.append(f"- {threat_type}: {count}")
        
        lines.append("")
        lines.append(f"## 威胁级别分布")
        for level, count in self.stats["by_threat_level"].items():
            lines.append(f"- {level}: {count}")
        
        lines.append("")
        lines.append(f"## 最近严重警报")
        critical_alerts = [
            a for a in self.alerts[-10:] 
            if a.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]
        ]
        for alert in critical_alerts:
            lines.append(f"- [{alert.threat_level.value}] {alert.description}")
        
        return "\n".join(lines)
