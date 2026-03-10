"""
内置技能 - 日期时间处理

日期时间解析和转换
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from ..managers.skill_manager import BaseSkill, SkillMetadata, SkillConfig, SkillResult


class DateTimeSkill(BaseSkill):
    """日期时间处理技能"""

    metadata = SkillMetadata(
        name="datetime",
        version="1.0.0",
        description="日期时间解析、格式化和计算",
        author="MAgentClaw Team",
        email="team@maagentclaw.com",
        tags=["datetime", "time", "date", "utility"],
        category="utility"
    )

    config = SkillConfig(
        enabled=True,
        timeout=10
    )

    async def execute(
        self,
        operation: str,
        value: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> SkillResult:
        """执行日期时间操作"""
        params = params or {}

        try:
            if operation == "parse":
                return await self._parse_datetime(value, params)
            elif operation == "format":
                return await self._format_datetime(value, params)
            elif operation == "diff":
                return await self._datetime_diff(value, params)
            elif operation == "add":
                return await self._datetime_add(value, params)
            elif operation == "now":
                return await self._get_now(params)
            elif operation == "range":
                return await self._datetime_range(value, params)
            else:
                return SkillResult(
                    success=False,
                    error=f"Unknown operation: {operation}"
                )

        except Exception as e:
            return SkillResult(
                success=False,
                error=str(e)
            )

    async def _parse_datetime(
        self,
        value: str,
        params: Dict[str, Any]
    ) -> SkillResult:
        """解析日期时间"""
        formats = params.get("formats", [
            "%Y-%m-%d",
            "%Y-%m-%d %H:%M:%S",
            "%Y/%m/%d",
            "%d/%m/%Y",
            "%m/%d/%Y",
            "%Y年%m月%d日"
        ])

        dt = None
        used_format = None

        for fmt in formats:
            try:
                dt = datetime.strptime(value, fmt)
                used_format = fmt
                break
            except ValueError:
                continue

        if dt is None:
            return SkillResult(
                success=False,
                error=f"Unable to parse date: {value}"
            )

        return SkillResult(
            success=True,
            data={
                "datetime": dt.isoformat(),
                "date": dt.date().isoformat(),
                "time": dt.time().isoformat(),
                "timestamp": dt.timestamp(),
                "format": used_format,
                "weekday": dt.strftime("%A"),
                "year": dt.year,
                "month": dt.month,
                "day": dt.day,
                "hour": dt.hour,
                "minute": dt.minute,
                "second": dt.second
            }
        )

    async def _format_datetime(
        self,
        value: str,
        params: Dict[str, Any]
    ) -> SkillResult:
        """格式化日期时间"""
        fmt = params.get("format", "%Y-%m-%d %H:%M:%S")

        if value == "now":
            dt = datetime.now()
        else:
            dt = datetime.fromisoformat(value)

        formatted = dt.strftime(fmt)

        return SkillResult(
            success=True,
            data={
                "formatted": formatted,
                "original": value,
                "format": fmt
            }
        )

    async def _datetime_diff(
        self,
        value: str,
        params: Dict[str, Any]
    ) -> SkillResult:
        """计算日期时间差"""
        start = params.get("start")
        end = params.get("end")

        if not start or not end:
            return SkillResult(
                success=False,
                error="start and end are required"
            )

        dt_start = datetime.fromisoformat(start)
        dt_end = datetime.fromisoformat(end)

        diff = dt_end - dt_start

        return SkillResult(
            success=True,
            data={
                "seconds": diff.total_seconds(),
                "minutes": diff.total_seconds() / 60,
                "hours": diff.total_seconds() / 3600,
                "days": diff.days,
                "start": start,
                "end": end
            }
        )

    async def _datetime_add(
        self,
        value: str,
        params: Dict[str, Any]
    ) -> SkillResult:
        """日期时间加减"""
        days = params.get("days", 0)
        hours = params.get("hours", 0)
        minutes = params.get("minutes", 0)
        seconds = params.get("seconds", 0)

        if value == "now":
            dt = datetime.now()
        else:
            dt = datetime.fromisoformat(value)

        delta = timedelta(
            days=days,
            hours=hours,
            minutes=minutes,
            seconds=seconds
        )

        result = dt + delta

        return SkillResult(
            success=True,
            data={
                "result": result.isoformat(),
                "original": value,
                "added": {
                    "days": days,
                    "hours": hours,
                    "minutes": minutes,
                    "seconds": seconds
                }
            }
        )

    async def _get_now(self, params: Dict[str, Any]) -> SkillResult:
        """获取当前时间"""
        tz = params.get("timezone", "local")

        dt = datetime.now()

        return SkillResult(
            success=True,
            data={
                "datetime": dt.isoformat(),
                "date": dt.date().isoformat(),
                "time": dt.time().isoformat(),
                "timestamp": dt.timestamp(),
                "timezone": tz
            }
        )

    async def _datetime_range(
        self,
        value: str,
        params: Dict[str, Any]
    ) -> SkillResult:
        """生成日期范围"""
        start = params.get("start")
        end = params.get("end")
        freq = params.get("frequency", "days")

        if not start or not end:
            return SkillResult(
                success=False,
                error="start and end are required"
            )

        dt_start = datetime.fromisoformat(start)
        dt_end = datetime.fromisoformat(end)

        dates = []
        current = dt_start

        if freq == "days":
            step = timedelta(days=1)
        elif freq == "hours":
            step = timedelta(hours=1)
        elif freq == "minutes":
            step = timedelta(minutes=1)
        else:
            step = timedelta(days=1)

        while current <= dt_end:
            dates.append(current.isoformat())
            current += step

        return SkillResult(
            success=True,
            data={
                "dates": dates,
                "count": len(dates),
                "start": start,
                "end": end,
                "frequency": freq
            }
        )


skill = DateTimeSkill()
