"""
内置技能 - 数据处理

数据分析和转换
"""

import json
import csv
import io
from typing import Any, Dict, List, Optional
from ..managers.skill_manager import BaseSkill, SkillMetadata, SkillConfig, SkillResult


class DataProcessorSkill(BaseSkill):
    """数据处理技能"""

    metadata = SkillMetadata(
        name="data-processor",
        version="1.0.0",
        description="数据分析和转换，支持 JSON、CSV 格式",
        author="MAgentClaw Team",
        email="team@maagentclaw.com",
        tags=["data", "process", "convert", "utility"],
        category="utility"
    )

    config = SkillConfig(
        enabled=True,
        timeout=30
    )

    async def execute(
        self,
        operation: str,
        data: Any,
        options: Optional[Dict[str, Any]] = None
    ) -> SkillResult:
        """执行数据处理"""
        options = options or {}

        try:
            if operation == "json_to_csv":
                return await self._json_to_csv(data, options)
            elif operation == "csv_to_json":
                return await self._csv_to_json(data, options)
            elif operation == "filter":
                return await self._filter_data(data, options)
            elif operation == "aggregate":
                return await self._aggregate_data(data, options)
            elif operation == "sort":
                return await self._sort_data(data, options)
            elif operation == "transform":
                return await self._transform_data(data, options)
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

    async def _json_to_csv(
        self,
        data: Any,
        options: Dict[str, Any]
    ) -> SkillResult:
        """JSON 转 CSV"""
        if isinstance(data, str):
            data = json.loads(data)

        if not isinstance(data, list):
            data = [data]

        if not data:
            return SkillResult(success=True, data={"csv": ""})

        fieldnames = options.get("fields") or list(data[0].keys())

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for row in data:
            filtered = {k: row.get(k, "") for k in fieldnames}
            writer.writerow(filtered)

        return SkillResult(
            success=True,
            data={"csv": output.getvalue()}
        )

    async def _csv_to_json(
        self,
        data: str,
        options: Dict[str, Any]
    ) -> SkillResult:
        """CSV 转 JSON"""
        input_stream = io.StringIO(data)
        reader = csv.DictReader(input_stream)

        result = list(reader)

        return SkillResult(
            success=True,
            data={"json": result}
        )

    async def _filter_data(
        self,
        data: Any,
        options: Dict[str, Any]
    ) -> SkillResult:
        """过滤数据"""
        if isinstance(data, str):
            data = json.loads(data)

        if not isinstance(data, list):
            return SkillResult(success=False, error="Data must be an array")

        field = options.get("field")
        operator = options.get("operator", "eq")
        value = options.get("value")

        if not field:
            return SkillResult(success=False, error="Field is required")

        filtered = []

        for item in data:
            item_value = item.get(field)

            if operator == "eq" and item_value == value:
                filtered.append(item)
            elif operator == "ne" and item_value != value:
                filtered.append(item)
            elif operator == "gt" and item_value > value:
                filtered.append(item)
            elif operator == "lt" and item_value < value:
                filtered.append(item)
            elif operator == "contains" and value in str(item_value):
                filtered.append(item)

        return SkillResult(
            success=True,
            data={
                "filtered": filtered,
                "count": len(filtered),
                "original_count": len(data)
            }
        )

    async def _aggregate_data(
        self,
        data: Any,
        options: Dict[str, Any]
    ) -> SkillResult:
        """聚合数据"""
        if isinstance(data, str):
            data = json.loads(data)

        if not isinstance(data, list):
            return SkillResult(success=False, error="Data must be an array")

        field = options.get("field")
        operation = options.get("operation", "count")

        if not field:
            return SkillResult(success=False, error="Field is required")

        values = [item.get(field) for item in data if field in item]

        if operation == "count":
            result = len(values)
        elif operation == "sum":
            result = sum(float(v) for v in values if v is not None)
        elif operation == "avg":
            result = sum(float(v) for v in values if v is not None) / len(values) if values else 0
        elif operation == "min":
            result = min(values) if values else None
        elif operation == "max":
            result = max(values) if values else None

        return SkillResult(
            success=True,
            data={
                "operation": operation,
                "field": field,
                "result": result
            }
        )

    async def _sort_data(
        self,
        data: Any,
        options: Dict[str, Any]
    ) -> SkillResult:
        """排序数据"""
        if isinstance(data, str):
            data = json.loads(data)

        if not isinstance(data, list):
            return SkillResult(success=False, error="Data must be an array")

        field = options.get("field")
        reverse = options.get("reverse", False)

        if not field:
            return SkillResult(success=False, error="Field is required")

        sorted_data = sorted(
            data,
            key=lambda x: x.get(field, ""),
            reverse=reverse
        )

        return SkillResult(
            success=True,
            data={"sorted": sorted_data}
        )

    async def _transform_data(
        self,
        data: Any,
        options: Dict[str, Any]
    ) -> SkillResult:
        """转换数据"""
        if isinstance(data, str):
            data = json.loads(data)

        operations = options.get("operations", [])

        if not isinstance(data, list):
            data = [data]
            was_single = True
        else:
            was_single = False

        result = data

        for op in operations:
            op_type = op.get("type")

            if op_type == "rename":
                old_field = op.get("from")
                new_field = op.get("to")
                for item in result:
                    if old_field in item:
                        item[new_field] = item.pop(old_field)

            elif op_type == "add":
                field = op.get("field")
                value = op.get("value")
                for item in result:
                    item[field] = value

            elif op_type == "remove":
                field = op.get("field")
                for item in result:
                    item.pop(field, None)

        if was_single:
            result = result[0] if result else {}

        return SkillResult(
            success=True,
            data={"transformed": result}
        )


skill = DataProcessorSkill()
