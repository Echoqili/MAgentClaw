from datetime import datetime
from typing import Any, Dict, List, Optional
from .base_memory import BaseMemory, MemoryItem, MemoryType


class ShortTermMemory(BaseMemory):
    """短期记忆 - 会话级上下文"""

    def __init__(self, max_items: int = 50):
        super().__init__(max_items)
        self.session_id: Optional[str] = None

    def set_session(self, session_id: str) -> None:
        """设置会话 ID"""
        self.session_id = session_id

    async def add(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        importance: float = 0.5
    ) -> MemoryItem:
        """添加短期记忆"""
        item = MemoryItem(
            content=content,
            metadata=metadata or {},
            memory_type=MemoryType.SHORT_TERM,
            importance=importance
        )

        self._items[item.id] = item

        if len(self._items) > self.max_items:
            await self._evict_oldest()

        return item

    async def get(self, memory_id: str) -> Optional[MemoryItem]:
        """获取记忆"""
        item = self._items.get(memory_id)
        if item:
            item.access_count += 1
            item.last_accessed = datetime.now()
        return item

    async def search(self, query: str, limit: int = 5) -> List[MemoryItem]:
        """搜索记忆 - 简单的关键词匹配"""
        query_lower = query.lower()
        results = []

        for item in self._items.values():
            if query_lower in item.content.lower():
                results.append(item)

        results.sort(key=lambda x: x.created_at, reverse=True)
        return results[:limit]

    async def delete(self, memory_id: str) -> bool:
        """删除记忆"""
        if memory_id in self._items:
            del self._items[memory_id]
            return True
        return False

    async def clear(self) -> None:
        """清空短期记忆"""
        self._items.clear()

    async def _evict_oldest(self) -> None:
        """驱逐最旧的记忆"""
        if not self._items:
            return

        oldest = min(
            self._items.values(),
            key=lambda x: x.created_at
        )
        del self._items[oldest.id]

    def get_recent(self, limit: int = 10) -> List[MemoryItem]:
        """获取最近的记忆"""
        all_items = self.get_all()
        return all_items[:limit]

    async def summarize(self, max_chars: int = 500) -> str:
        """生成记忆摘要"""
        recent = self.get_recent(5)
        if not recent:
            return ""

        summary_parts = []
        total_chars = 0

        for item in recent:
            if total_chars + len(item.content) > max_chars:
                remaining = max_chars - total_chars
                if remaining > 50:
                    summary_parts.append(item.content[:remaining] + "...")
                break
            summary_parts.append(item.content)
            total_chars += len(item.content)

        return " | ".join(summary_parts)
