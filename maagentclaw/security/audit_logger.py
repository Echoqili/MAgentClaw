from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
import json


class ActionType(Enum):
    """操作类型"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    LOGIN = "login"
    LOGOUT = "logout"
    ACCESS_DENIED = "access_denied"
    OTHER = "other"


class LogLevel(Enum):
    """日志级别"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditLog:
    """审计日志"""
    id: str
    timestamp: datetime
    action: ActionType
    user: str
    resource: str
    details: Dict[str, Any]
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    level: LogLevel = LogLevel.INFO
    success: bool = True
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "action": self.action.value,
            "user": self.user,
            "resource": self.resource,
            "details": self.details,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "level": self.level.value,
            "success": self.success,
            "error": self.error
        }


class AuditLogger:
    """审计日志记录器"""

    def __init__(
        self,
        storage_path: Optional[Path] = None,
        max_entries: int = 10000
    ):
        self.storage_path = storage_path
        self.max_entries = max_entries
        self._logs: List[AuditLog] = []

        if storage_path and storage_path.exists():
            self._load()

    async def log(
        self,
        action: ActionType,
        user: str,
        resource: str,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        level: LogLevel = LogLevel.INFO,
        success: bool = True,
        error: Optional[str] = None
    ) -> AuditLog:
        """记录日志"""
        import uuid

        log_entry = AuditLog(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            action=action,
            user=user,
            resource=resource,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
            level=level,
            success=success,
            error=error
        )

        self._logs.append(log_entry)

        if len(self._logs) > self.max_entries:
            self._logs = self._logs[-self.max_entries:]

        self._save()

        return log_entry

    async def log_access(
        self,
        user: str,
        resource: str,
        success: bool = True,
        ip_address: Optional[str] = None
    ) -> AuditLog:
        """记录访问"""
        action = ActionType.READ if success else ActionType.ACCESS_DENIED
        return await self.log(
            action=action,
            user=user,
            resource=resource,
            success=success,
            ip_address=ip_address
        )

    async def log_action(
        self,
        action: ActionType,
        user: str,
        resource: str,
        details: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """记录操作"""
        return await self.log(
            action=action,
            user=user,
            resource=resource,
            details=details
        )

    async def log_error(
        self,
        user: str,
        resource: str,
        error: str,
        details: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """记录错误"""
        return await self.log(
            action=ActionType.OTHER,
            user=user,
            resource=resource,
            details=details,
            level=LogLevel.ERROR,
            success=False,
            error=error
        )

    def query(
        self,
        user: Optional[str] = None,
        action: Optional[ActionType] = None,
        resource: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditLog]:
        """查询日志"""
        results = self._logs

        if user:
            results = [log for log in results if log.user == user]

        if action:
            results = [log for log in results if log.action == action]

        if resource:
            results = [log for log in results if resource in log.resource]

        if start_time:
            results = [log for log in results if log.timestamp >= start_time]

        if end_time:
            results = [log for log in results if log.timestamp <= end_time]

        results.sort(key=lambda x: x.timestamp, reverse=True)
        return results[:limit]

    def get_user_activity(self, user: str, limit: int = 50) -> List[AuditLog]:
        """获取用户活动"""
        return self.query(user=user, limit=limit)

    def get_failed_actions(self, limit: int = 50) -> List[AuditLog]:
        """获取失败的操作"""
        failed = [log for log in self._logs if not log.success]
        failed.sort(key=lambda x: x.timestamp, reverse=True)
        return failed[:limit]

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total = len(self._logs)
        if total == 0:
            return {"total": 0}

        action_counts: Dict[str, int] = {}
        user_counts: Dict[str, int] = {}
        failed_count = 0

        for log in self._logs:
            action_counts[log.action.value] = action_counts.get(log.action.value, 0) + 1
            user_counts[log.user] = user_counts.get(log.user, 0) + 1
            if not log.success:
                failed_count += 1

        return {
            "total": total,
            "action_counts": action_counts,
            "user_counts": user_counts,
            "failed_count": failed_count,
            "success_rate": (total - failed_count) / total if total > 0 else 0
        }

    def clear(self) -> None:
        """清空日志"""
        self._logs.clear()
        self._save()

    def _save(self) -> None:
        """保存到磁盘"""
        if not self.storage_path:
            return

        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        data = [log.to_dict() for log in self._logs]

        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _load(self) -> None:
        """从磁盘加载"""
        if not self.storage_path or not self.storage_path.exists():
            return

        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self._logs = []
            for log_data in data:
                log_data["timestamp"] = datetime.fromisoformat(log_data["timestamp"])
                log_data["action"] = ActionType(log_data["action"])
                log_data["level"] = LogLevel(log_data["level"])
                self._logs.append(AuditLog(**log_data))

        except Exception as e:
            print(f"Error loading audit logs: {e}")
