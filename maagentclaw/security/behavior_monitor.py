"""
行为监控器 - 检测异常行为
"""

from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import time


class BehaviorType(Enum):
    FILE_CREATE = "file_create"
    FILE_DELETE = "file_delete"
    COMMAND_EXECUTE = "command_execute"
    NETWORK_REQUEST = "network_request"


class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class BehaviorEvent:
    event_type: BehaviorType
    resource: str
    timestamp: datetime = field(default_factory=datetime.now)
    agent_name: str = ""
    details: Dict = field(default_factory=dict)


@dataclass
class Alert:
    level: AlertLevel
    message: str
    event: BehaviorEvent
    recommended_action: str = ""


class BehaviorMonitor:
    def __init__(
        self,
        max_file_operations_per_minute: int = 60,
        max_network_requests_per_minute: int = 100,
        enable_auto_block: bool = True
    ):
        self.max_file_ops = max_file_operations_per_minute
        self.max_network = max_network_requests_per_minute
        self.enable_auto_block = enable_auto_block
        self._events: List[BehaviorEvent] = []
        self._alerts: List[Alert] = []
        self._blocked_agents: Dict[str, datetime] = {}
        self._rate_limiters: Dict[str, Dict] = {}
        self._lock = asyncio.Lock()
        self._alert_handlers: List[Callable] = []
    
    async def record_event(self, event: BehaviorEvent) -> Optional[Alert]:
        async with self._lock:
            self._events.append(event)
            alert = await self._check_anomaly(event)
            if alert:
                self._alerts.append(alert)
                for handler in self._alert_handlers:
                    try:
                        if asyncio.iscoroutinefunction(handler):
                            await handler(alert)
                        else:
                            handler(alert)
                    except Exception:
                        pass
                if alert.level == AlertLevel.CRITICAL and self.enable_auto_block:
                    if event.agent_name:
                        self._blocked_agents[event.agent_name] = datetime.now()
            return alert
    
    async def _check_anomaly(self, event: BehaviorEvent) -> Optional[Alert]:
        agent = event.agent_name or "default"
        if agent in self._blocked_agents:
            block_time = self._blocked_agents[agent]
            if (datetime.now() - block_time).total_seconds() < 300:
                return Alert(level=AlertLevel.CRITICAL, message=f"Agent {agent} is blocked", event=event)
            else:
                del self._blocked_agents[agent]
        if event.event_type == BehaviorType.FILE_DELETE:
            resource = event.resource.lower()
            dangerous = ["rm -rf", "del /f", "format", ".ssh"]
            for pattern in dangerous:
                if pattern in resource:
                    return Alert(level=AlertLevel.CRITICAL, message=f"Dangerous delete: {event.resource}", event=event)
        await self._check_rate_limit(event)
        return None
    
    async def _check_rate_limit(self, event: BehaviorEvent):
        agent = event.agent_name or "default"
        if agent not in self._rate_limiters:
            self._rate_limiters[agent] = {"file_ops": [], "network": []}
        limiter = self._rate_limiters[agent]
        now = time.time()
        if event.event_type in (BehaviorType.FILE_CREATE, BehaviorType.FILE_DELETE):
            limiter["file_ops"] = [t for t in limiter["file_ops"] if now - t < 60]
            limiter["file_ops"].append(now)
            if len(limiter["file_ops"]) > self.max_file_ops:
                self._alerts.append(Alert(level=AlertLevel.WARNING, message="Rate limit exceeded", event=event))
        elif event.event_type == BehaviorType.NETWORK_REQUEST:
            limiter["network"] = [t for t in limiter["network"] if now - t < 60]
            limiter["network"].append(now)
    
    def on_alert(self, handler: Callable):
        self._alert_handlers.append(handler)
    
    async def get_events(self, limit: int = 100) -> List[BehaviorEvent]:
        return self._events[-limit:]
    
    async def get_alerts(self, limit: int = 50) -> List[Alert]:
        return self._alerts[-limit:]
    
    def is_agent_blocked(self, agent_name: str) -> bool:
        return agent_name in self._blocked_agents
    
    def get_statistics(self) -> Dict:
        return {
            "total_events": len(self._events),
            "total_alerts": len(self._alerts),
            "blocked_agents": list(self._blocked_agents.keys()),
        }
