"""
预算管理员 (Budget Manager)

负责资源配额管理和Token消耗控制，防止资源"贪污"和Token爆炸
如同古代的"户部"，负责管理国家钱粮
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import time


class ResourceType(Enum):
    """资源类型"""
    TOKEN = "token"
    TIME = "time"
    MEMORY = "memory"
    API_CALL = "api_call"
    STORAGE = "storage"


class QuotaExceededAction(Enum):
    """配额超出时的动作"""
    WARN = "warn"           # 警告
    THROTTLE = "throttle"  # 限流
    BLOCK = "block"        # 阻止
    ESCALATE = "escalate"  # 升级


@dataclass
class ResourceQuota:
    """资源配额"""
    resource_type: ResourceType
    limit: float           # 限制值
    used: float = 0.0      # 已使用
    window_seconds: int = 3600  # 时间窗口（秒）
    exceeded_action: QuotaExceededAction = QuotaExceededAction.WARN
    
    def reset(self):
        """重置配额"""
        self.used = 0.0
    
    def consume(self, amount: float) -> bool:
        """消耗资源，返回是否成功"""
        if self.used + amount > self.limit:
            return False
        self.used += amount
        return True
    
    def get_remaining(self) -> float:
        """获取剩余配额"""
        return max(0, self.limit - self.used)
    
    def get_usage_percent(self) -> float:
        """获取使用百分比"""
        return (self.used / self.limit * 100) if self.limit > 0 else 0


@dataclass
class BudgetAlert:
    """预算警报"""
    agent_name: str
    resource_type: ResourceType
    usage_percent: float
    action: QuotaExceededAction
    message: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class BudgetConfig:
    """预算配置"""
    name: str = "budget_manager"
    role: str = "预算管理员"
    
    # Token 配额
    token_limit_per_hour: int = 100000      # 每小时Token上限
    token_limit_per_task: int = 10000       # 单任务Token上限
    
    # 时间配额
    time_limit_per_task: int = 300          # 单任务时间上限（秒）
    time_limit_per_session: int = 3600      # 会话时间上限
    
    # API 调用配额
    api_call_limit_per_minute: int = 60    # 每分钟API调用上限
    api_call_limit_per_hour: int = 1000    # 每小时API调用上限
    
    # 内存配额
    memory_limit_mb: int = 512               # 内存限制（MB）
    
    # 超出配额时的动作
    default_action: QuotaExceededAction = QuotaExceededAction.WARN
    
    # 预警阈值
    warning_threshold: float = 80.0          # 警告阈值（百分比）
    critical_threshold: float = 95.0         # 严重阈值（百分比）
    
    # 角色定义
    goal: str = "确保资源合理使用，防止浪费和滥用"
    backstory: str = """你是一位严格的预算管理员，精打细算，
    熟悉各类资源的价值和使用规则。你会严格控制资源消耗，
    确保每一分资源都用在刀刃上。"""
    responsibilities: List[str] = field(default_factory=lambda: [
        "监控Token消耗",
        "控制API调用频率",
        "管理时间预算",
        "预防资源浪费",
        "处理配额超限"
    ])


class BudgetManager:
    """预算管理器
    
    如同古代的"户部"，负责管理国家钱粮
    防止Agent"贪污"（过度消耗资源）导致系统崩溃
    """
    
    def __init__(self, config: Optional[BudgetConfig] = None):
        self.config = config or BudgetConfig()
        
        # 资源配额
        self.quotas: Dict[str, Dict[ResourceType, ResourceQuota]] = {}  # agent_name -> quota
        self.global_quotas: Dict[ResourceType, ResourceQuota] = {}
        
        # 初始化全局配额
        self._init_global_quotas()
        
        # 警报历史
        self.alerts: List[BudgetAlert] = []
        
        # 统计
        self.stats: Dict[str, Any] = {
            "total_consumed": {},
            "blocked_count": 0,
            "warn_count": 0
        }
    
    def _init_global_quotas(self):
        """初始化全局配额"""
        self.global_quotas[ResourceType.TOKEN] = ResourceQuota(
            resource_type=ResourceType.TOKEN,
            limit=self.config.token_limit_per_hour,
            window_seconds=3600,
            exceeded_action=self.config.default_action
        )
        
        self.global_quotas[ResourceType.TIME] = ResourceQuota(
            resource_type=ResourceType.TIME,
            limit=self.config.time_limit_per_session,
            window_seconds=3600,
            exceeded_action=QuotaExceededAction.BLOCK
        )
        
        self.global_quotas[ResourceType.API_CALL] = ResourceQuota(
            resource_type=ResourceType.API_CALL,
            limit=self.config.api_call_limit_per_hour,
            window_seconds=3600,
            exceeded_action=self.config.default_action
        )
    
    def register_agent(self, agent_name: str):
        """注册Agent，初始化其配额"""
        if agent_name not in self.quotas:
            self.quotas[agent_name] = {
                ResourceType.TOKEN: ResourceQuota(
                    resource_type=ResourceType.TOKEN,
                    limit=self.config.token_limit_per_task,
                    window_seconds=3600,
                    exceeded_action=self.config.default_action
                ),
                ResourceType.TIME: ResourceQuota(
                    resource_type=ResourceType.TIME,
                    limit=self.config.time_limit_per_task,
                    window_seconds=3600,
                    exceeded_action=QuotaExceededAction.BLOCK
                ),
                ResourceType.API_CALL: ResourceQuota(
                    resource_type=ResourceType.API_CALL,
                    limit=self.config.api_call_limit_per_minute,
                    window_seconds=60,
                    exceeded_action=self.config.default_action
                )
            }
    
    def can_consume(
        self,
        agent_name: str,
        resource_type: ResourceType,
        amount: float
    ) -> bool:
        """检查是否可以消耗资源"""
        # 检查Agent配额
        if agent_name in self.quotas:
            agent_quota = self.quotas[agent_name].get(resource_type)
            if agent_quota and not agent_quota.consume(amount):
                self._record_blocked(agent_name, resource_type)
                return False
        
        # 检查全局配额
        global_quota = self.global_quotas.get(resource_type)
        if global_quota and not global_quota.consume(amount):
            self._record_blocked(agent_name, resource_type)
            return False
        
        return True
    
    def consume(
        self,
        agent_name: str,
        resource_type: ResourceType,
        amount: float
    ) -> bool:
        """消耗资源"""
        success = self.can_consume(agent_name, resource_type, amount)
        
        if success:
            # 记录统计
            if resource_type.value not in self.stats["total_consumed"]:
                self.stats["total_consumed"][resource_type.value] = 0
            self.stats["total_consumed"][resource_type.value] += amount
            
            # 检查是否需要警告
            self._check_warnings(agent_name, resource_type)
        
        return success
    
    def _record_blocked(self, agent_name: str, resource_type: ResourceType):
        """记录被阻止的消耗"""
        self.stats["blocked_count"] += 1
        
        alert = BudgetAlert(
            agent_name=agent_name,
            resource_type=resource_type,
            usage_percent=100,
            action=QuotaExceededAction.BLOCK,
            message=f"阻止了 {agent_name} 的 {resource_type.value} 消耗请求"
        )
        self.alerts.append(alert)
    
    def _check_warnings(self, agent_name: str, resource_type: ResourceType):
        """检查是否需要警告"""
        # 检查Agent配额
        if agent_name in self.quotas:
            quota = self.quotas[agent_name].get(resource_type)
            if quota:
                usage = quota.get_usage_percent()
                
                if usage >= self.config.critical_threshold:
                    action = QuotaExceededAction.BLOCK
                elif usage >= self.config.warning_threshold:
                    action = QuotaExceededAction.WARN
                else:
                    return
                
                alert = BudgetAlert(
                    agent_name=agent_name,
                    resource_type=resource_type,
                    usage_percent=usage,
                    action=action,
                    message=f"{agent_name} 的 {resource_type.value} 使用已达 {usage:.1f}%"
                )
                self.alerts.append(alert)
                self.stats["warn_count"] += 1
    
    def get_remaining(
        self,
        agent_name: str,
        resource_type: ResourceType
    ) -> float:
        """获取剩余配额"""
        if agent_name in self.quotas:
            quota = self.quotas[agent_name].get(resource_type)
            if quota:
                return quota.get_remaining()
        
        global_quota = self.global_quotas.get(resource_type)
        if global_quota:
            return global_quota.get_remaining()
        
        return 0
    
    def get_status(self, agent_name: Optional[str] = None) -> Dict[str, Any]:
        """获取状态"""
        status = {
            "global": {},
            "agents": {}
        }
        
        # 全局配额
        for resource_type, quota in self.global_quotas.items():
            status["global"][resource_type.value] = {
                "limit": quota.limit,
                "used": quota.used,
                "remaining": quota.get_remaining(),
                "usage_percent": quota.get_usage_percent()
            }
        
        # Agent配额
        if agent_name and agent_name in self.quotas:
            for resource_type, quota in self.quotas[agent_name].items():
                status["agents"][agent_name] = {
                    resource_type.value: {
                        "limit": quota.limit,
                        "used": quota.used,
                        "remaining": quota.get_remaining(),
                        "usage_percent": quota.get_usage_percent()
                    }
                }
        elif agent_name is None:
            for name, quotas in self.quotas.items():
                status["agents"][name] = {}
                for resource_type, quota in quotas.items():
                    status["agents"][name][resource_type.value] = {
                        "limit": quota.limit,
                        "used": quota.used,
                        "remaining": quota.get_remaining(),
                        "usage_percent": quota.get_usage_percent()
                    }
        
        return status
    
    def get_alerts(self, limit: int = 50) -> List[BudgetAlert]:
        """获取最近的警报"""
        return self.alerts[-limit:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_consumed": self.stats["total_consumed"],
            "blocked_count": self.stats["blocked_count"],
            "warn_count": self.stats["warn_count"],
            "registered_agents": len(self.quotas),
            "active_alerts": len([a for a in self.alerts[-10:] if a.action != QuotaExceededAction.BLOCK])
        }
    
    def reset_agent(self, agent_name: str):
        """重置Agent配额"""
        if agent_name in self.quotas:
            for quota in self.quotas[agent_name].values():
                quota.reset()
    
    def reset_all(self):
        """重置所有配额"""
        for quotas in self.quotas.values():
            for quota in quotas.values():
                quota.reset()
        
        for quota in self.global_quotas.values():
            quota.reset()
        
        self.alerts.clear()
    
    def set_limit(
        self,
        agent_name: str,
        resource_type: ResourceType,
        limit: float
    ):
        """设置配额限制"""
        if agent_name not in self.quotas:
            self.register_agent(agent_name)
        
        if resource_type in self.quotas[agent_name]:
            self.quotas[agent_name][resource_type].limit = limit
        else:
            self.quotas[agent_name][resource_type] = ResourceQuota(
                resource_type=resource_type,
                limit=limit
            )
