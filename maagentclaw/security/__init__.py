"""
安全模块 - 参考OpenClaw安全设计

四层安全防护体系：
1. 输入过滤 - 防止Prompt注入
2. 权限沙箱 - 限制操作范围
3. 行为监控 - 检测异常行为
4. API限流 - 控制资源使用
"""

from .input_filter import InputFilter, FilterResult, FilterLevel
from .permission_sandbox import PermissionSandbox, Permission, PermissionScope
from .behavior_monitor import BehaviorMonitor, BehaviorType, AlertLevel, BehaviorEvent
from .api_rate_limiter import APIRateLimiter, RateLimitConfig

__all__ = [
    "InputFilter",
    "FilterResult",
    "FilterLevel",
    "PermissionSandbox",
    "Permission",
    "PermissionScope",
    "BehaviorMonitor",
    "BehaviorType",
    "AlertLevel",
    "BehaviorEvent",
    "APIRateLimiter",
    "RateLimitConfig",
]
