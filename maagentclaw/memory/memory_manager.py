from pathlib import Path
from typing import Any, Dict, List, Optional
from .base_memory import MemoryItem, MemoryType
from .short_term import ShortTermMemory
from .long_term import LongTermMemory
from .vector_store import VectorStore, InMemoryVectorStore


class MemoryManager:
    """记忆管理器 - 统一管理短期和长期记忆"""

    def __init__(
        self,
        workspace_path: Path,
        short_term_max: int = 50,
        long_term_max: int = 1000
    ):
        self.workspace_path = Path(workspace_path)

        self.short_term = ShortTermMemory(max_items=short_term_max)
        self.long_term = LongTermMemory(
            max_items=long_term_max,
            storage_path=self.workspace_path / "memory" / "long_term.json"
        )

    async def add(
        self,
        content: str,
        memory_type: str = "auto",
        metadata: Optional[Dict[str, Any]] = None,
        importance: float = 0.5
    ) -> MemoryItem:
        """添加记忆 - 自动选择类型"""
        if memory_type == "auto":
            memory_type = self._select_memory_type(content, importance)

        if memory_type == "short_term":
            return await self.short_term.add(content, metadata, importance)
        elif memory_type == "long_term":
            return await self.long_term.add(content, metadata, importance)
        else:
            return await self.short_term.add(content, metadata, importance)

    async def get(self, memory_id: str, memory_type: Optional[str] = None) -> Optional[MemoryItem]:
        """获取记忆"""
        if memory_type:
            return await self._get_by_type(memory_id, memory_type)

        item = await self.short_term.get(memory_id)
        if item:
            return item

        return await self.long_term.get(memory_id)

    async def search(
        self,
        query: str,
        memory_type: Optional[str] = None,
        limit: int = 5
    ) -> List[MemoryItem]:
        """搜索记忆"""
        if memory_type and memory_type != "all":
            if memory_type == "short_term":
                return await self.short_term.search(query, limit)
            elif memory_type == "long_term":
                return await self.long_term.search(query, limit)
            return []

        short_results = await self.short_term.search(query, limit)
        long_results = await self.long_term.search(query, limit)

        combined = short_results + long_results
        combined.sort(key=lambda x: x.created_at, reverse=True)

        return combined[:limit]

    async def delete(
        self,
        memory_id: str,
        memory_type: Optional[str] = None
    ) -> bool:
        """删除记忆"""
        if memory_type:
            return await self._delete_by_type(memory_id, memory_type)

        if await self.short_term.delete(memory_id):
            return True
        return await self.long_term.delete(memory_id)

    async def clear(self, memory_type: Optional[str] = None) -> None:
        """清空记忆"""
        if memory_type == "short_term" or memory_type is None:
            await self.short_term.clear()
        if memory_type == "long_term" or memory_type is None:
            await self.long_term.clear()

    async def get_recent(self, memory_type: Optional[str] = None, limit: int = 10) -> List[MemoryItem]:
        """获取最近的记忆"""
        if memory_type == "short_term":
            return self.short_term.get_recent(limit)
        elif memory_type == "long_term":
            items = self.long_term.get_all()
            return items[:limit]
        else:
            short_items = self.short_term.get_recent(limit)
            long_items = self.long_term.get_all()[:limit]

            combined = short_items + long_items
            combined.sort(key=lambda x: x.created_at, reverse=True)
            return combined[:limit]

    async def get_context(self, query: str, max_chars: int = 1000) -> str:
        """获取上下文记忆"""
        short_summary = await self.short_term.summarize(max_chars // 2)

        search_results = await self.long_term.search(query, 3)
        long_context = " | ".join(r.content for r in search_results)

        context_parts = []
        if short_summary:
            context_parts.append(f"[近期对话] {short_summary}")
        if long_context:
            context_parts.append(f"[相关记忆] {long_context}")

        return "\n\n".join(context_parts[:2])

    async def consolidate(self) -> int:
        """将重要短期记忆转入长期记忆"""
        recent = self.short_term.get_recent(10)

        consolidated = 0
        for item in recent:
            if item.importance >= 0.7:
                await self.long_term.add(
                    content=item.content,
                    metadata={**item.metadata, "consolidated_from": item.id},
                    importance=item.importance
                )
                consolidated += 1

        return consolidated

    async def get_stats(self) -> Dict[str, Any]:
        """获取记忆统计"""
        long_term_stats = await self.long_term.get_stats()

        return {
            "short_term": {
                "count": self.short_term.count(),
                "max_items": self.short_term.max_items
            },
            "long_term": long_term_stats,
            "total": self.short_term.count() + self.long_term.count()
        }

    async def _get_by_type(self, memory_id: str, memory_type: str) -> Optional[MemoryItem]:
        """按类型获取"""
        if memory_type == "short_term":
            return await self.short_term.get(memory_id)
        elif memory_type == "long_term":
            return await self.long_term.get(memory_id)
        return None

    async def _delete_by_type(self, memory_id: str, memory_type: str) -> bool:
        """按类型删除"""
        if memory_type == "short_term":
            return await self.short_term.delete(memory_id)
        elif memory_type == "long_term":
            return await self.long_term.delete(memory_id)
        return False

    def _select_memory_type(self, content: str, importance: float) -> str:
        """自动选择记忆类型"""
        if importance >= 0.7:
            return "long_term"

        content_length = len(content)
        if content_length > 500:
            return "long_term"

        return "short_term"
