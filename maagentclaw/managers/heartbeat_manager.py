"""
Heartbeat Manager - 心跳机制管理

参考 OpenClaw 的心跳设计理念，实现 Agent 的周期性任务调度和状态监控
"""

import asyncio
import json
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class HeartbeatTask:
    """心跳任务"""
    name: str
    interval: int  # 执行间隔（秒）
    command: str  # 要执行的命令或技能
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    status: TaskStatus = TaskStatus.PENDING
    execution_count: int = 0
    failure_count: int = 0
    last_error: Optional[str] = None
    last_duration: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "interval": self.interval,
            "command": self.command,
            "enabled": self.enabled,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "status": self.status.value,
            "execution_count": self.execution_count,
            "failure_count": self.failure_count,
            "last_error": self.last_error,
            "last_duration": self.last_duration,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HeartbeatTask":
        """从字典创建"""
        task = cls(
            name=data["name"],
            interval=data["interval"],
            command=data["command"],
            enabled=data.get("enabled", True)
        )
        if data.get("last_run"):
            task.last_run = datetime.fromisoformat(data["last_run"])
        if data.get("next_run"):
            task.next_run = datetime.fromisoformat(data["next_run"])
        task.status = TaskStatus(data.get("status", "pending"))
        task.execution_count = data.get("execution_count", 0)
        task.failure_count = data.get("failure_count", 0)
        task.last_error = data.get("last_error")
        task.last_duration = data.get("last_duration")
        task.metadata = data.get("metadata", {})
        return task


@dataclass
class HeartbeatConfig:
    """心跳配置"""
    enabled: bool = True
    interval: int = 60  # 默认心跳间隔（秒）
    max_retries: int = 3  # 最大重试次数
    retry_delay: int = 5  # 重试延迟（秒）
    timeout: int = 300  # 任务超时（秒）
    suppress_duplicates: bool = True  # 抑制重复执行
    log_level: str = "INFO"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "enabled": self.enabled,
            "interval": self.interval,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "timeout": self.timeout,
            "suppress_duplicates": self.suppress_duplicates,
            "log_level": self.log_level
        }


class HeartbeatParser:
    """HEARTBEAT.md 文件解析器"""
    
    @staticmethod
    def parse(file_path: Path) -> List[HeartbeatTask]:
        """解析 HEARTBEAT.md 文件
        
        格式示例：
        ```markdown
        # Heartbeat Tasks
        
        ## Task: data-sync
        - Interval: 300
        - Command: sync-data --source=db --target=cache
        - Enabled: true
        
        ## Task: health-check
        - Interval: 60
        - Command: check-health --service=all
        - Enabled: true
        ```
        """
        tasks = []
        
        if not file_path.exists():
            return tasks
        
        content = file_path.read_text(encoding='utf-8')
        
        # 解析任务块
        task_pattern = r'## Task:\s*(\S+)\s*\n(.*?)(?=\n## Task:|\Z)'
        matches = re.findall(task_pattern, content, re.DOTALL)
        
        for task_name, task_content in matches:
            task_data = {"name": task_name.strip()}
            
            # 解析任务属性
            for line in task_content.strip().split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower().replace(' ', '_')
                    value = value.strip()
                    
                    # 类型转换
                    if key == 'interval':
                        task_data[key] = int(value)
                    elif key == 'enabled':
                        task_data[key] = value.lower() == 'true'
                    elif key == 'command':
                        task_data[key] = value
                    else:
                        task_data[key] = value
            
            # 创建任务
            if 'interval' in task_data and 'command' in task_data:
                task = HeartbeatTask(
                    name=task_data["name"],
                    interval=task_data.get("interval", 60),
                    command=task_data.get("command", ""),
                    enabled=task_data.get("enabled", True)
                )
                tasks.append(task)
        
        return tasks


class HeartbeatManager:
    """心跳管理器
    
    负责：
    1. 解析 HEARTBEAT.md 文件
    2. 调度周期性任务
    3. 监控任务执行状态
    4. 心跳抑制（避免重复执行）
    5. 任务执行历史记录
    """
    
    def __init__(self, workspace_path: Path, 
                 config: Optional[HeartbeatConfig] = None,
                 execution_callback: Optional[Callable] = None):
        self.workspace_path = Path(workspace_path)
        self.config = config or HeartbeatConfig()
        self.execution_callback = execution_callback
        
        self.tasks: Dict[str, HeartbeatTask] = {}
        self.running = False
        self._task: Optional[asyncio.Task] = None
        self._execution_history: List[Dict[str, Any]] = []
        self._last_execution: Dict[str, datetime] = {}
        
        # 加载心跳文件
        self.heartbeat_file = self.workspace_path / "HEARTBEAT.md"
        self.load_tasks()
    
    def load_tasks(self) -> List[HeartbeatTask]:
        """从 HEARTBEAT.md 加载任务"""
        parser = HeartbeatParser()
        tasks = parser.parse(self.heartbeat_file)
        
        for task in tasks:
            self.tasks[task.name] = task
            # 计算下次执行时间
            task.next_run = datetime.now()
        
        return tasks
    
    def save_tasks(self):
        """保存任务状态到文件"""
        content = "# Heartbeat Tasks\n\n"
        content += f"*Auto-generated by Heartbeat Manager*\n\n"
        content += f"**Last Updated**: {datetime.now().isoformat()}\n\n"
        content += f"**Total Tasks**: {len(self.tasks)}\n\n"
        content += "---\n\n"
        
        for task in self.tasks.values():
            content += f"## Task: {task.name}\n\n"
            content += f"- **Interval**: {task.interval} seconds\n"
            content += f"- **Command**: `{task.command}`\n"
            content += f"- **Enabled**: {task.enabled}\n"
            content += f"- **Status**: {task.status.value}\n"
            content += f"- **Last Run**: {task.last_run.isoformat() if task.last_run else 'Never'}\n"
            content += f"- **Next Run**: {task.next_run.isoformat() if task.next_run else 'Not scheduled'}\n"
            content += f"- **Execution Count**: {task.execution_count}\n"
            content += f"- **Failure Count**: {task.failure_count}\n"
            if task.last_error:
                content += f"- **Last Error**: {task.last_error}\n"
            if task.last_duration:
                content += f"- **Last Duration**: {task.last_duration:.2f}s\n"
            content += "\n---\n\n"
        
        self.heartbeat_file.write_text(content, encoding='utf-8')
    
    def add_task(self, task: HeartbeatTask):
        """添加任务"""
        self.tasks[task.name] = task
        task.next_run = datetime.now()
        self.save_tasks()
    
    def remove_task(self, task_name: str):
        """移除任务"""
        if task_name in self.tasks:
            del self.tasks[task_name]
            self.save_tasks()
    
    def enable_task(self, task_name: str):
        """启用任务"""
        if task_name in self.tasks:
            self.tasks[task_name].enabled = True
            self.tasks[task_name].next_run = datetime.now()
            self.save_tasks()
    
    def disable_task(self, task_name: str):
        """禁用任务"""
        if task_name in self.tasks:
            self.tasks[task_name].enabled = False
            self.save_tasks()
    
    def _should_suppress(self, task: HeartbeatTask) -> bool:
        """检查是否应该抑制执行（心跳抑制逻辑）"""
        if not self.config.suppress_duplicates:
            return False
        
        # 如果任务还在运行，抑制执行
        if task.status == TaskStatus.RUNNING:
            return True
        
        # 检查上次执行时间
        if task.name in self._last_execution:
            elapsed = (datetime.now() - self._last_execution[task.name]).total_seconds()
            if elapsed < task.interval * 0.5:  # 至少间隔 50% 的时间
                return True
        
        return False
    
    async def _execute_task(self, task: HeartbeatTask):
        """执行单个任务"""
        if not task.enabled:
            return
        
        # 检查是否应该抑制
        if self._should_suppress(task):
            return
        
        # 更新状态
        task.status = TaskStatus.RUNNING
        task.last_run = datetime.now()
        self._last_execution[task.name] = task.last_run
        
        start_time = time.time()
        
        try:
            # 执行回调
            if self.execution_callback:
                if asyncio.iscoroutinefunction(self.execution_callback):
                    result = await self.execution_callback(task.command, task.metadata)
                else:
                    result = self.execution_callback(task.command, task.metadata)
                
                task.status = TaskStatus.COMPLETED
                task.execution_count += 1
                
                # 记录历史
                self._execution_history.append({
                    "task": task.name,
                    "timestamp": datetime.now().isoformat(),
                    "status": "success",
                    "duration": time.time() - start_time
                })
                
            else:
                # 没有回调，模拟执行
                await asyncio.sleep(0.1)
                task.status = TaskStatus.COMPLETED
                task.execution_count += 1
                
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.last_error = str(e)
            task.failure_count += 1
            
            # 重试逻辑
            if task.failure_count < self.config.max_retries:
                task.next_run = datetime.now() + timedelta(seconds=self.config.retry_delay)
            else:
                task.next_run = datetime.now() + timedelta(seconds=task.interval)
            
            # 记录历史
            self._execution_history.append({
                "task": task.name,
                "timestamp": datetime.now().isoformat(),
                "status": "failed",
                "error": str(e),
                "duration": time.time() - start_time
            })
            
            return
        
        finally:
            task.last_duration = time.time() - start_time
        
        # 计算下次执行时间
        task.next_run = datetime.now() + timedelta(seconds=task.interval)
        
        # 重置失败计数
        if task.status == TaskStatus.COMPLETED:
            task.failure_count = 0
    
    async def _heartbeat_loop(self):
        """心跳循环"""
        while self.running:
            try:
                # 检查所有任务
                for task in self.tasks.values():
                    if task.enabled and task.next_run and task.next_run <= datetime.now():
                        await self._execute_task(task)
                
                # 等待下一次心跳
                await asyncio.sleep(self.config.interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Heartbeat loop error: {e}")
                await asyncio.sleep(self.config.interval)
    
    async def start(self):
        """启动心跳管理器"""
        if self.running:
            return
        
        self.running = True
        self._task = asyncio.create_task(self._heartbeat_loop())
        print(f"Heartbeat manager started with {len(self.tasks)} tasks")
    
    async def stop(self):
        """停止心跳管理器"""
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
        print("Heartbeat manager stopped")
    
    def get_task_status(self, task_name: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        if task_name not in self.tasks:
            return None
        
        task = self.tasks[task_name]
        return task.to_dict()
    
    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """获取所有任务"""
        return [task.to_dict() for task in self.tasks.values()]
    
    def get_execution_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取执行历史"""
        return self._execution_history[-limit:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total = len(self.tasks)
        enabled = sum(1 for t in self.tasks.values() if t.enabled)
        running = sum(1 for t in self.tasks.values() if t.status == TaskStatus.RUNNING)
        failed = sum(1 for t in self.tasks.values() if t.status == TaskStatus.FAILED)
        
        total_executions = sum(t.execution_count for t in self.tasks.values())
        total_failures = sum(t.failure_count for t in self.tasks.values())
        
        return {
            "total_tasks": total,
            "enabled_tasks": enabled,
            "running_tasks": running,
            "failed_tasks": failed,
            "total_executions": total_executions,
            "total_failures": total_failures,
            "success_rate": (total_executions - total_failures) / total_executions * 100 if total_executions > 0 else 0
        }


# 简化导入
__all__ = [
    "HeartbeatTask",
    "HeartbeatConfig",
    "HeartbeatParser",
    "HeartbeatManager",
    "TaskStatus"
]
