from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid


class MemoryType(Enum):
    """记忆类型"""
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    WORKING = "working"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"


@dataclass
class MemoryItem:
    """记忆条目"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    memory_type: MemoryType = MemoryType.SHORT_TERM
    created_at: datetime = field(default_factory=datetime.now)
    importance: float = 0.5
    access_count: int = 0
    last_accessed: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "metadata": self.metadata,
            "memory_type": self.memory_type.value,
            "created_at": self.created_at.isoformat(),
            "importance": self.importance,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None
        }


class BaseMemory(ABC):
    """记忆基类"""

    def __init__(self, max_items: int = 100):
        self.max_items = max_items
        self._items: Dict[str, MemoryItem] = {}

    @abstractmethod
    async def add(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> MemoryItem:
        """添加记忆"""
        pass

    @abstractmethod
    async def get(self, memory_id: str) -> Optional[MemoryItem]:
        """获取记忆"""
        pass

    @abstractmethod
    async def search(self, query: str, limit: int = 5) -> List[MemoryItem]:
        """搜索记忆"""
        pass

    @abstractmethod
    async def delete(self, memory_id: str) -> bool:
        """删除记忆"""
        pass

    @abstractmethod
    async def clear(self) -> None:
        """清空记忆"""
        pass

    def count(self) -> int:
        """记忆数量"""
        return len(self._items)

    def get_all(self) -> List[MemoryItem]:
        """获取所有记忆"""
        return sorted(
            self._items.values(),
            key=lambda x: x.created_at,
            reverse=True
        )
