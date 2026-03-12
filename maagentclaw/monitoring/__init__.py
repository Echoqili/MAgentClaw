"""
性能监控和指标模块

提供系统性能监控和指标收集能力
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import uuid
import asyncio
import psutil
import time


class MetricType(Enum):
    """指标类型"""
    COUNTER = "counter"           # 计数器
    GAUGE = "gauge"             # 仪表（当前值）
    HISTOGRAM = "histogram"      # 直方图
    TIMER = "timer"              # 计时器


@dataclass
class Metric:
    """指标"""
    name: str = ""
    metric_type: MetricType = MetricType.COUNTER
    value: float = 0.0
    unit: str = ""
    tags: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    # 直方图专用
    min_value: float = float('inf')
    max_value: float = float('-inf')
    count: int = 0
    sum_values: float = 0.0
    
    # 历史记录
    history: List[Dict[str, Any]] = field(default_factory=list)
    max_history_size: int = 1000
    
    def record(self, value: float):
        """记录值"""
        self.value = value
        self.timestamp = datetime.now()
        
        if self.metric_type in [MetricType.HISTOGRAM, MetricType.TIMER]:
            self.min_value = min(self.min_value, value)
            self.max_value = max(self.max_value, value)
            self.count += 1
            self.sum_values += value
        
        # 添加到历史
        self.history.append({
            "value": value,
            "timestamp": self.timestamp.isoformat()
        })
        
        # 保持历史大小
        if len(self.history) > self.max_history_size:
            self.history = self.history[-self.max_history_size:]
    
    def increment(self, value: float = 1.0):
        """增加计数器"""
        self.value += value
        self.timestamp = datetime.now()
        
        self.history.append({
            "value": self.value,
            "timestamp": self.timestamp.isoformat()
        })
        
        if len(self.history) > self.max_history_size:
            self.history = self.history[-self.max_history_size:]
    
    def get_percentile(self, percentile: float) -> float:
        """获取百分位数"""
        if not self.history or self.metric_type not in [MetricType.HISTOGRAM, MetricType.TIMER]:
            return self.value
        
        values = [h["value"] for h in self.history]
        values.sort()
        
        index = int(len(values) * percentile / 100)
        return values[min(index, len(values) - 1)]
    
    def get_avg(self) -> float:
        """获取平均值"""
        if not self.history or self.count == 0:
            return self.value
        return self.sum_values / self.count
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = {
            "name": self.name,
            "type": self.metric_type.value,
            "current": self.value,
            "unit": self.unit,
            "timestamp": self.timestamp.isoformat()
        }
        
        if self.metric_type in [MetricType.HISTOGRAM, MetricType.TIMER]:
            stats.update({
                "min": self.min_value if self.min_value != float('inf') else 0,
                "max": self.max_value if self.max_value != float('-inf') else 0,
                "avg": self.get_avg(),
                "count": self.count,
                "p50": self.get_percentile(50),
                "p95": self.get_percentile(95),
                "p99": self.get_percentile(99)
            })
        
        return stats


class MetricsCollector:
    """指标收集器"""
    
    def __init__(self):
        self.metrics: Dict[str, Metric] = {}
        self._lock = asyncio.Lock()
    
    def get_or_create(
        self,
        name: str,
        metric_type: MetricType = MetricType.COUNTER,
        unit: str = "",
        tags: Optional[Dict[str, str]] = None
    ) -> Metric:
        """获取或创建指标"""
        key = self._make_key(name, tags or {})
        
        if key not in self.metrics:
            self.metrics[key] = Metric(
                name=name,
                metric_type=metric_type,
                unit=unit,
                tags=tags or {}
            )
        
        return self.metrics[key]
    
    def _make_key(self, name: str, tags: Dict[str, str]) -> str:
        """生成指标键"""
        if not tags:
            return name
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}[{tag_str}]"
    
    def record(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """记录指标值"""
        metric = self.get_or_create(name, MetricType.GAUGE, tags=tags)
        metric.record(value)
    
    def increment(self, name: str, value: float = 1.0, tags: Optional[Dict[str, str]] = None):
        """增加计数器"""
        metric = self.get_or_create(name, MetricType.COUNTER, tags=tags)
        metric.increment(value)
    
    def timer(self, name: str, tags: Optional[Dict[str, str]] = None):
        """创建计时器上下文"""
        return TimerContext(self, name, tags)
    
    def get_metric(self, name: str, tags: Optional[Dict[str, str]] = None) -> Optional[Metric]:
        """获取指标"""
        key = self._make_key(name, tags or {})
        return self.metrics.get(key)
    
    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """获取所有指标"""
        return {
            name: metric.get_stats()
            for name, metric in self.metrics.items()
        }
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """获取仪表板数据"""
        return {
            "metrics": self.get_all_metrics(),
            "system": SystemMonitor.get_current_stats(),
            "timestamp": datetime.now().isoformat()
        }


class TimerContext:
    """计时器上下文"""
    
    def __init__(self, collector: MetricsCollector, name: str, tags: Optional[Dict[str, str]]):
        self.collector = collector
        self.name = name
        self.tags = tags or {}
        self.start_time: Optional[float] = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            metric = self.collector.get_or_create(
                self.name,
                MetricType.TIMER,
                "seconds",
                self.tags
            )
            metric.record(duration)


class SystemMonitor:
    """系统监控器"""
    
    @staticmethod
    def get_current_stats() -> Dict[str, Any]:
        """获取当前系统统计"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "cpu": {
                    "percent": cpu_percent,
                    "count": psutil.cpu_count()
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "used": memory.used,
                    "percent": memory.percent
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": disk.percent
                },
                "timestamp": datetime.now().isoformat()
            }
        except:
            return {"error": "Failed to get system stats"}


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.metrics = MetricsCollector()
        self.agent_metrics: Dict[str, MetricsCollector] = {}
        self._lock = asyncio.Lock()
        
        # 监控任务
        self._monitor_task: Optional[asyncio.Task] = None
        self._monitoring = False
    
    async def start_monitoring(self, interval: int = 60):
        """开始系统监控"""
        self._monitoring = True
        self._monitor_task = asyncio.create_task(self._monitor_loop(interval))
    
    async def stop_monitoring(self):
        """停止系统监控"""
        self._monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
    
    async def _monitor_loop(self, interval: int):
        """监控循环"""
        while self._monitoring:
            try:
                # 记录系统指标
                stats = SystemMonitor.get_current_stats()
                
                if "error" not in stats:
                    self.metrics.record("system.cpu_percent", stats["cpu"]["percent"])
                    self.metrics.record("system.memory_percent", stats["memory"]["percent"])
                    self.metrics.record("system.disk_percent", stats["disk"]["percent"])
                
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Monitor error: {e}")
                await asyncio.sleep(interval)
    
    def get_agent_metrics(self, agent_name: str) -> MetricsCollector:
        """获取 Agent 指标收集器"""
        if agent_name not in self.agent_metrics:
            self.agent_metrics[agent_name] = MetricsCollector()
        return self.agent_metrics[agent_name]
    
    def record_agent_task(self, agent_name: str, task_name: str, duration: float):
        """记录 Agent 任务执行时间"""
        collector = self.get_agent_metrics(agent_name)
        collector.record(f"task.{task_name}", duration)
    
    def record_agent_tool_call(self, agent_name: str, tool_name: str):
        """记录 Agent 工具调用"""
        collector = self.get_agent_metrics(agent_name)
        collector.increment(f"tool.{tool_name}")
    
    def get_agent_stats(self, agent_name: str) -> Dict[str, Any]:
        """获取 Agent 统计"""
        collector = self.agent_metrics.get(agent_name)
        if collector:
            return collector.get_all_metrics()
        return {}
    
    def get_all_stats(self) -> Dict[str, Any]:
        """获取所有统计"""
        return {
            "system": self.metrics.get_all_metrics(),
            "agents": {
                name: collector.get_all_metrics()
                for name, collector in self.agent_metrics.items()
            },
            "dashboard": self.metrics.get_dashboard_data()
        }
    
    def reset_metrics(self):
        """重置所有指标"""
        self.metrics = MetricsCollector()
        self.agent_metrics = {}


class AlertManager:
    """告警管理器"""
    
    def __init__(self, monitor: PerformanceMonitor):
        self.monitor = monitor
        self.alerts: List[Dict[str, Any]] = []
        self.rules: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
        
        # 默认告警规则
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """设置默认告警规则"""
        self.add_rule(
            name="high_cpu",
            condition=lambda stats: stats.get("system", {}).get("cpu", {}).get("percent", 0) > 80,
            severity="warning",
            message="CPU 使用率高于 80%"
        )
        
        self.add_rule(
            name="high_memory",
            condition=lambda stats: stats.get("system", {}).get("memory", {}).get("percent", 0) > 85,
            severity="warning",
            message="内存使用率高于 85%"
        )
        
        self.add_rule(
            name="critical_memory",
            condition=lambda stats: stats.get("system", {}).get("memory", {}).get("percent", 0) > 95,
            severity="critical",
            message="内存使用率高于 95%！"
        )
    
    def add_rule(
        self,
        name: str,
        condition: Callable,
        severity: str = "info",
        message: str = ""
    ):
        """添加告警规则"""
        self.rules[name] = {
            "condition": condition,
            "severity": severity,
            "message": message,
            "enabled": True
        }
    
    def remove_rule(self, name: str):
        """移除告警规则"""
        if name in self.rules:
            del self.rules[name]
    
    async def check_alerts(self):
        """检查告警"""
        stats = self.monitor.get_all_stats()
        
        async with self._lock:
            for name, rule in self.rules.items():
                if not rule["enabled"]:
                    continue
                
                try:
                    if rule["condition"](stats):
                        alert = {
                            "id": str(uuid.uuid4()),
                            "rule": name,
                            "severity": rule["severity"],
                            "message": rule["message"],
                            "timestamp": datetime.now().isoformat(),
                            "stats": stats
                        }
                        
                        # 避免重复告警
                        if not any(a["rule"] == name and a["severity"] == rule["severity"] for a in self.alerts[-10:]):
                            self.alerts.append(alert)
                
                except Exception as e:
                    print(f"Alert check error: {e}")
    
    def get_active_alerts(self, severity: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取活跃告警"""
        alerts = self.alerts[-50:]  # 最近50条
        
        if severity:
            alerts = [a for a in alerts if a["severity"] == severity]
        
        return alerts
    
    def clear_alerts(self):
        """清除告警"""
        self.alerts.clear()
