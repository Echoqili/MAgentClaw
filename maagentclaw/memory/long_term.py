from datetime import datetime
from typing import Any, Dict, List, Optional
import json
from pathlib import Path
from .base_memory import BaseMemory, MemoryItem, MemoryType
from .vector_store import VectorStore, InMemoryVectorStore


class LongTermMemory(BaseMemory):
    """长期记忆 - 持久化存储，支持向量检索"""

    def __init__(
        self,
        max_items: int = 1000,
        storage_path: Optional[Path] = None,
        vector_store: Optional[VectorStore] = None
    ):
        super().__init__(max_items)
        self.storage_path = storage_path
        self.vector_store = vector_store or InMemoryVectorStore()

        if storage_path and storage_path.exists():
            self._load_from_disk()

    async def add(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        importance: float = 0.7
    ) -> MemoryItem:
        """添加长期记忆"""
        item = MemoryItem(
            content=content,
            metadata=metadata or {},
            memory_type=MemoryType.LONG_TERM,
            importance=importance
        )

        self._items[item.id] = item
        await self.vector_store.add(item)

        if len(self._items) > self.max_items:
            await self._evict_least_important()

        if self.storage_path:
            self._save_to_disk()

        return item

    async def get(self, memory_id: str) -> Optional[MemoryItem]:
        """获取记忆"""
        item = self._items.get(memory_id)
        if item:
            item.access_count += 1
            item.last_accessed = datetime.now()
        return item

    async def search(self, query: str, limit: int = 5) -> List[MemoryItem]:
        """向量搜索记忆"""
        results = await self.vector_store.search(query, limit)
        return results

    async def delete(self, memory_id: str) -> bool:
        """删除记忆"""
        if memory_id in self._items:
            del self._items[memory_id]
            await self.vector_store.delete(memory_id)

            if self.storage_path:
                self._save_to_disk()
            return True
        return False

    async def clear(self) -> None:
        """清空长期记忆"""
        self._items.clear()
        self.vector_store.clear()

        if self.storage_path and self.storage_path.exists():
            self.storage_path.unlink()

    async def _evict_least_important(self) -> None:
        """驱逐最不重要的记忆"""
        if not self._items:
            return

        sorted_items = sorted(
            self._items.values(),
            key=lambda x: (x.importance, x.access_count)
        )

        to_remove = sorted_items[:max(1, len(sorted_items) // 10)]
        for item in to_remove:
            await self.delete(item.id)

    def _save_to_disk(self) -> None:
        """保存到磁盘"""
        if not self.storage_path:
            return

        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            item_id: item.to_dict()
            for item_id, item in self._items.items()
        }

        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _load_from_disk(self) -> None:
        """从磁盘加载"""
        if not self.storage_path or not self.storage_path.exists():
            return

        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            for item_id, item_data in data.items():
                item = MemoryItem(
                    id=item_data["id"],
                    content=item_data["content"],
                    metadata=item_data.get("metadata", {}),
                    memory_type=MemoryType(item_data.get("memory_type", "long_term")),
                    created_at=datetime.fromisoformat(item_data["created_at"]),
                    importance=item_data.get("importance", 0.5),
                    access_count=item_data.get("access_count", 0),
                    last_accessed=datetime.fromisoformat(item_data["last_accessed"])
                    if item_data.get("last_accessed") else None
                )
                self._items[item_id] = item

        except Exception as e:
            print(f"Error loading long-term memory: {e}")

    async def get_by_tag(self, tag: str) -> List[MemoryItem]:
        """按标签获取记忆"""
        results = []
        for item in self._items.values():
            if item.metadata.get("tags") and tag in item.metadata["tags"]:
                results.append(item)
        return sorted(results, key=lambda x: x.created_at, reverse=True)

    async def get_stats(self) -> Dict[str, Any]:
        """获取记忆统计"""
        return {
            "total_items": self.count(),
            "max_items": self.max_items,
            "storage_path": str(self.storage_path) if self.storage_path else None,
            "avg_importance": sum(i.importance for i in self._items.values()) / max(1, len(self._items)),
            "total_accesses": sum(i.access_count for i in self._items.values())
        }
