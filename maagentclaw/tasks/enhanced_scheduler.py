"""
Enhanced Scheduler - 增强定时任务调度器

支持 Cron 表达式、复杂调度策略
"""

import asyncio
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


class ScheduleType(Enum):
    """调度类型"""
    INTERVAL = "interval"      # 固定间隔
    CRON = "cron"             # Cron 表达式
    ONCE = "once"             # 单次执行
    DAILY = "daily"           # 每天
    WEEKLY = "weekly"          # 每周
    MONTHLY = "monthly"        # 每月


class SchedulerStatus(Enum):
    """调度器状态"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"


@dataclass
class CronExpression:
    """Cron 表达式"""
    minute: str = "*"      # 0-59
    hour: str = "*"        # 0-23
    day_of_month: str = "*"  # 1-31
    month: str = "*"      # 1-12
    day_of_week: str = "*"   # 0-6 (0 = Sunday)
    
    @classmethod
    def parse(cls, expression: str) -> "CronExpression":
        """解析 Cron 表达式"""
        parts = expression.split()
        
        if len(parts) == 5:
            return cls(
                minute=parts[0],
                hour=parts[1],
                day_of_month=parts[2],
                month=parts[3],
                day_of_week=parts[4]
            )
        elif len(parts) == 6:
            # 支持秒级
            return cls(
                minute=parts[1],
                hour=parts[2],
                day_of_month=parts[3],
                month=parts[4],
                day_of_week=parts[5]
            )
        else:
            raise ValueError(f"Invalid cron expression: {expression}")
    
    def to_string(self) -> str:
        """转换为字符串"""
        return f"{self.minute} {self.hour} {self.day_of_month} {self.month} {self.day_of_week}"
    
    def get_next_run(self, from_time: datetime = None) -> datetime:
        """计算下次执行时间"""
        from_time = from_time or datetime.now()
        
        # 简单的下次执行时间计算
        # 实际实现需要完整的 cron 解析库
        
        minute = self._parse_field(self.minute, 0, 59, from_time.minute)
        hour = self._parse_field(self.hour, 0, 23, from_time.hour)
        day = self._parse_field(self.day_of_month, 1, 31, from_time.day)
        month = self._parse_field(self.month, 1, 12, from_time.month)
        dow = self._parse_field(self.day_of_week, 0, 6, from_time.weekday())
        
        next_time = from_time.replace(
            minute=minute,
            hour=hour,
            day=day,
            month=month
        )
        
        # 如果时间已过，推到下一天
        if next_time <= from_time:
            next_time += timedelta(days=1)
        
        return next_time
    
    def _parse_field(self, field: str, min_val: int, max_val: int, current: int) -> int:
        """解析单个字段"""
        if field == "*":
            return current
        
        if "," in field:
            # 列表
            values = [int(v) for v in field.split(",")]
            for v in values:
                if v >= min_val and v <= max_val and v >= current:
                    return v
            return values[0]
        
        if "-" in field:
            # 范围
            start, end = field.split("-")
            return int(start)
        
        if "/" in field:
            # 步进
            base, step = field.split("/")
            step = int(step)
            if base == "*":
                return current + step if current + step <= max_val else min_val
            else:
                base = int(base)
                return base + (current - base) // step * step
        
        # 固定值
        return int(field)
    
    def matches(self, time: datetime) -> bool:
        """检查时间是否匹配"""
        return (
            self._match_field(self.minute, time.minute) and
            self._match_field(self.hour, time.hour) and
            self._match_field(self.day_of_month, time.day) and
            self._match_field(self.month, time.month) and
            self._match_field(self.day_of_week, time.weekday())
        )
    
    def _match_field(self, field: str, value: int) -> bool:
        """检查字段是否匹配"""
        if field == "*":
            return True
        
        # 处理列表
        if "," in field:
            values = [int(v) for v in field.split(",")]
            return value in values
        
        # 处理范围
        if "-" in field:
            start, end = field.split("-")
            return int(start) <= value <= int(end)
        
        # 处理步进
        if "/" in field:
            base, step = field.split("/")
            base = 0 if base == "*" else int(base)
            step = int(step)
            return (value - base) % step == 0
        
        # 固定值
        return int(field) == value


@dataclass
class ScheduledTask:
    """定时任务"""
    id: str
    name: str
    description: str
    schedule_type: ScheduleType
    command: str
    
    # 调度配置
    interval_seconds: Optional[int] = None
    cron_expression: Optional[str] = None
    
    # 配置
    enabled: bool = True
    max_retries: int = 3
    timeout: int = 300
    
    # 状态
    status: SchedulerStatus = SchedulerStatus.IDLE
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    last_result: Optional[Dict[str, Any]] = None
    run_count: int = 0
    failure_count: int = 0
    
    # 元数据
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 状态
    status: SchedulerStatus = SchedulerStatus.IDLE
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    last_result: Optional[Dict[str, Any]] = None
    run_count: int = 0
    failure_count: int = 0
    
    # 元数据
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "schedule_type": self.schedule_type.value,
            "interval_seconds": self.interval_seconds,
            "cron_expression": self.cron_expression,
            "command": self.command,
            "enabled": self.enabled,
            "max_retries": self.max_retries,
            "timeout": self.timeout,
            "status": self.status.value,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "run_count": self.run_count,
            "failure_count": self.failure_count,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata
        }


class EnhancedScheduler:
    """增强定时任务调度器"""
    
    def __init__(self, 
                 workspace_path: Path,
                 execute_callback: Optional[Callable] = None):
        self.workspace_path = Path(workspace_path)
        self.execute_callback = execute_callback
        
        self.tasks: Dict[str, ScheduledTask] = {}
        self.running = False
        self._task: Optional[asyncio.Task] = None
        
        # 加载配置
        self.load_tasks()
    
    def add_task(self, 
                name: str,
                command: str,
                schedule_type: ScheduleType = ScheduleType.INTERVAL,
                interval_seconds: Optional[int] = None,
                cron_expression: Optional[str] = None,
                description: str = "",
                enabled: bool = True,
                max_retries: int = 3,
                timeout: int = 300) -> str:
        """添加任务"""
        import uuid
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        
        task = ScheduledTask(
            id=task_id,
            name=name,
            description=description,
            schedule_type=schedule_type,
            interval_seconds=interval_seconds,
            cron_expression=cron_expression,
            command=command,
            enabled=enabled,
            max_retries=max_retries,
            timeout=timeout
        )
        
        # 计算下次执行时间
        task.next_run = self._calculate_next_run(task)
        
        self.tasks[task_id] = task
        self.save_tasks()
        
        return task_id
    
    def remove_task(self, task_id: str) -> bool:
        """移除任务"""
        if task_id in self.tasks:
            del self.tasks[task_id]
            self.save_tasks()
            return True
        return False
    
    def enable_task(self, task_id: str) -> bool:
        """启用任务"""
        if task_id in self.tasks:
            self.tasks[task_id].enabled = True
            self.tasks[task_id].next_run = self._calculate_next_run(self.tasks[task_id])
            self.save_tasks()
            return True
        return False
    
    def disable_task(self, task_id: str) -> bool:
        """禁用任务"""
        if task_id in self.tasks:
            self.tasks[task_id].enabled = False
            self.tasks[task_id].next_run = None
            self.save_tasks()
            return True
        return False
    
    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        """获取任务"""
        return self.tasks.get(task_id)
    
    def list_tasks(self, enabled_only: bool = False) -> List[Dict[str, Any]]:
        """列出任务"""
        tasks = self.tasks.values()
        
        if enabled_only:
            tasks = [t for t in tasks if t.enabled]
        
        return [t.to_dict() for t in tasks]
    
    def _calculate_next_run(self, task: ScheduledTask) -> Optional[datetime]:
        """计算下次执行时间"""
        now = datetime.now()
        
        if task.schedule_type == ScheduleType.INTERVAL:
            if task.interval_seconds:
                return now + timedelta(seconds=task.interval_seconds)
        
        elif task.schedule_type == ScheduleType.CRON:
            if task.cron_expression:
                try:
                    cron = CronExpression.parse(task.cron_expression)
                    return cron.get_next_run(now)
                except:
                    pass
        
        elif task.schedule_type == ScheduleType.DAILY:
            # 每天固定时间
            return now + timedelta(days=1)
        
        elif task.schedule_type == ScheduleType.WEEKLY:
            return now + timedelta(weeks=1)
        
        elif task.schedule_type == ScheduleType.MONTHLY:
            # 下个月同一天
            if now.month == 12:
                return now.replace(year=now.year+1, month=1)
            else:
                return now.replace(month=now.month+1)
        
        return None
    
    async def _run_task(self, task: ScheduledTask) -> Dict[str, Any]:
        """执行任务"""
        task.status = SchedulerStatus.RUNNING
        task.last_run = datetime.now()
        
        result = {
            "task_id": task.id,
            "task_name": task.name,
            "start_time": task.last_run.isoformat(),
            "success": False,
            "error": None,
            "duration": 0
        }
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            # 执行回调
            if self.execute_callback:
                if asyncio.iscoroutinefunction(self.execute_callback):
                    output = await asyncio.wait_for(
                        self.execute_callback(task.command, task.metadata),
                        timeout=task.timeout
                    )
                else:
                    output = self.execute_callback(task.command, task.metadata)
                
                result["output"] = output
                result["success"] = True
                task.run_count += 1
                
            else:
                # 模拟执行
                await asyncio.sleep(0.5)
                result["output"] = f"Simulated: {task.command}"
                result["success"] = True
                task.run_count += 1
            
        except asyncio.TimeoutError:
            result["error"] = f"Task timeout after {task.timeout} seconds"
            result["success"] = False
            task.failure_count += 1
            
        except Exception as e:
            result["error"] = str(e)
            result["success"] = False
            task.failure_count += 1
            
            # 重试逻辑
            if task.failure_count < task.max_retries:
                # 延迟重试
                await asyncio.sleep(2 ** task.failure_count)
        
        finally:
            end_time = asyncio.get_event_loop().time()
            result["duration"] = end_time - start_time
            task.status = SchedulerStatus.IDLE
            task.last_result = result
            
            # 计算下次执行时间
            if task.enabled:
                task.next_run = self._calculate_next_run(task)
        
        return result
    
    async def _scheduler_loop(self):
        """调度循环"""
        while self.running:
            try:
                now = datetime.now()
                
                # 检查所有任务
                for task in self.tasks.values():
                    if not task.enabled:
                        continue
                    
                    if task.next_run and task.next_run <= now:
                        # 执行任务
                        asyncio.create_task(self._run_task(task))
                
                # 等待 1 秒
                await asyncio.sleep(1)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Scheduler loop error: {e}")
                await asyncio.sleep(1)
    
    async def start(self):
        """启动调度器"""
        if self.running:
            return
        
        self.running = True
        self._task = asyncio.create_task(self._scheduler_loop())
        print(f"Scheduler started with {len(self.tasks)} tasks")
    
    async def stop(self):
        """停止调度器"""
        if not self.running:
            return
        
        self.running = False
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        # 保存任务状态
        self.save_tasks()
        print("Scheduler stopped")
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total = len(self.tasks)
        enabled = sum(1 for t in self.tasks.values() if t.enabled)
        total_runs = sum(t.run_count for t in self.tasks.values())
        total_failures = sum(t.failure_count for t in self.tasks.values())
        
        # 即将执行的任务
        now = datetime.now()
        upcoming = [
            t.to_dict() for t in self.tasks.values()
            if t.enabled and t.next_run and t.next_run > now
        ]
        upcoming.sort(key=lambda x: x["next_run"])
        
        return {
            "total_tasks": total,
            "enabled_tasks": enabled,
            "total_runs": total_runs,
            "total_failures": total_failures,
            "success_rate": (total_runs - total_failures) / total_runs * 100 if total_runs > 0 else 0,
            "upcoming_tasks": upcoming[:5]
        }
    
    def save_tasks(self):
        """保存任务配置"""
        config_file = self.workspace_path / "scheduler_tasks.json"
        
        tasks_data = [
            {
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "schedule_type": t.schedule_type.value,
                "interval_seconds": t.interval_seconds,
                "cron_expression": t.cron_expression,
                "command": t.command,
                "enabled": t.enabled,
                "max_retries": t.max_retries,
                "timeout": t.timeout,
                "metadata": t.metadata
            }
            for t in self.tasks.values()
        ]
        
        config_file.write_text(
            json.dumps(tasks_data, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )
    
    def load_tasks(self):
        """加载任务配置"""
        config_file = self.workspace_path / "scheduler_tasks.json"
        
        if not config_file.exists():
            return
        
        try:
            tasks_data = json.loads(config_file.read_text(encoding='utf-8'))
            
            for td in tasks_data:
                task = ScheduledTask(
                    id=td["id"],
                    name=td["name"],
                    description=td.get("description", ""),
                    schedule_type=ScheduleType(td["schedule_type"]),
                    interval_seconds=td.get("interval_seconds"),
                    cron_expression=td.get("cron_expression"),
                    command=td["command"],
                    enabled=td.get("enabled", True),
                    max_retries=td.get("max_retries", 3),
                    timeout=td.get("timeout", 300),
                    metadata=td.get("metadata", {})
                )
                
                # 计算下次执行时间
                if task.enabled:
                    task.next_run = self._calculate_next_run(task)
                
                self.tasks[task.id] = task
                
        except Exception as e:
            print(f"Load tasks error: {e}")


# 预设调度模板
class ScheduleTemplates:
    """调度模板"""
    
    @staticmethod
    def every_minute() -> Dict[str, Any]:
        return {
            "type": ScheduleType.INTERVAL,
            "interval_seconds": 60
        }
    
    @staticmethod
    def every_hour() -> Dict[str, Any]:
        return {
            "type": ScheduleType.INTERVAL,
            "interval_seconds": 3600
        }
    
    @staticmethod
    def every_day() -> Dict[str, Any]:
        return {
            "type": ScheduleType.CRON,
            "cron_expression": "0 0 * * *"  # 每天午夜
        }
    
    @staticmethod
    def every_week() -> Dict[str, Any]:
        return {
            "type": ScheduleType.CRON,
            "cron_expression": "0 0 * * 0"  # 每周日午夜
        }
    
    @staticmethod
    def workdays_9am() -> Dict[str, Any]:
        return {
            "type": ScheduleType.CRON,
            "cron_expression": "0 9 * * 1-5"  # 工作日早上9点
        }
    
    @staticmethod
    def monthly() -> Dict[str, Any]:
        return {
            "type": ScheduleType.CRON,
            "cron_expression": "0 0 1 * *"  # 每月1日午夜
        }


# 简化导入
__all__ = [
    "ScheduleType",
    "SchedulerStatus",
    "CronExpression",
    "ScheduledTask",
    "EnhancedScheduler",
    "ScheduleTemplates"
]
