from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import numpy as np
import hashlib


@dataclass
class EmbeddingResult:
    """嵌入结果"""
    id: str
    embedding: List[float]
    content: str
    metadata: Dict[str, Any]


class VectorStore(ABC):
    """向量存储抽象基类"""

    @abstractmethod
    async def add(self, item) -> None:
        """添加向量"""
        pass

    @abstractmethod
    async def search(self, query: str, limit: int = 5) -> List[Any]:
        """搜索向量"""
        pass

    @abstractmethod
    async def delete(self, item_id: str) -> bool:
        """删除向量"""
        pass

    @abstractmethod
    def clear(self) -> None:
        """清空向量存储"""
        pass


class InMemoryVectorStore(VectorStore):
    """内存向量存储 - 轻量级实现"""

    def __init__(self, embedding_dim: int = 384):
        self.embedding_dim = embedding_dim
        self._vectors: Dict[str, np.ndarray] = {}
        self._items: Dict[str, Any] = {}

    async def add(self, item) -> None:
        """添加向量"""
        item_id = item.id
        content = item.content

        embedding = self._compute_embedding(content)

        self._vectors[item_id] = embedding
        self._items[item_id] = item

    async def search(self, query: str, limit: int = 5) -> List[Any]:
        """搜索最相似的向量"""
        if not self._vectors:
            return []

        query_embedding = self._compute_embedding(query)

        similarities = []
        for item_id, vec in self._vectors.items():
            sim = self._cosine_similarity(query_embedding, vec)
            similarities.append((item_id, sim))

        similarities.sort(key=lambda x: x[1], reverse=True)

        results = []
        for item_id, _ in similarities[:limit]:
            if item_id in self._items:
                results.append(self._items[item_id])

        return results

    async def delete(self, item_id: str) -> bool:
        """删除向量"""
        if item_id in self._vectors:
            del self._vectors[item_id]
            del self._items[item_id]
            return True
        return False

    def clear(self) -> None:
        """清空向量存储"""
        self._vectors.clear()
        self._items.clear()

    def _compute_embedding(self, text: str) -> np.ndarray:
        """计算文本嵌入 - 简化实现"""
        text_hash = hashlib.md5(text.encode()).digest()

        np.random.seed(int.from_bytes(text_hash[:4], "little"))
        base = np.random.randn(self.embedding_dim)

        word_count = len(text.split())
        length_factor = min(word_count / 100.0, 2.0)

        for i, word in enumerate(set(text.split())):
            word_hash = hashlib.md5(word.encode()).digest()
            np.random.seed(int.from_bytes(word_hash[:4], "little"))
            base += np.random.randn(self.embedding_dim) * 0.1

        normalized = base / (np.linalg.norm(base) + 1e-8)
        return normalized * length_factor

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """余弦相似度"""
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return float(dot_product / (norm_a * norm_b))

    def count(self) -> int:
        """向量数量"""
        return len(self._vectors)
