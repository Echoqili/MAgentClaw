"""
记忆管理模块

提供长期记忆和上下文管理能力
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
import json
from collections import deque


class MemoryType(Enum):
    """记忆类型"""
    SHORT_TERM = "short_term"     # 短期记忆
    LONG_TERM = "long_term"        # 长期记忆
    WORKING = "working"           # 工作记忆
    EPISODIC = "episodic"         # 情景记忆
    SEMANTIC = "semantic"         # 语义记忆


class MemoryImportance(Enum):
    """记忆重要性"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Memory:
    """记忆"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    memory_type: MemoryType = MemoryType.SHORT_TERM
    importance: MemoryImportance = MemoryImportance.MEDIUM
    
    # 元数据
    agent_name: Optional[str] = None
    session_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    # 时间戳
    created_at: datetime = field(default_factory=datetime.now)
    accessed_at: datetime = field(default_factory=datetime.now)
    last_modified: datetime = field(default_factory=datetime.now)
    
    # 访问统计
    access_count: int = 0
    
    # 关联
    related_memories: List[str] = field(default_factory=list)
    
    # 嵌入向量（用于相似度搜索）
    embedding: Optional[List[float]] = None
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def access(self):
        """访问记忆"""
        self.accessed_at = datetime.now()
        self.access_count += 1
    
    def update(self, content: str):
        """更新记忆内容"""
        self.content = content
        self.last_modified = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "content": self.content,
            "type": self.memory_type.value,
            "importance": self.importance.value,
            "agent_name": self.agent_name,
            "session_id": self.session_id,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "accessed_at": self.accessed_at.isoformat(),
            "access_count": self.access_count,
            "metadata": self.metadata
        }


class MemoryStore:
    """记忆存储"""
    
    def __init__(self):
        self.memories: Dict[str, Memory] = {}
        self.short_term: deque = deque(maxlen=1000)  # 短期记忆队列
        self.long_term: List[Memory] = []  # 长期记忆
        self.working: Dict[str, Any] = {}  # 工作记忆
    
    def add(self, memory: Memory):
        """添加记忆"""
        self.memories[memory.id] = memory
        
        if memory.memory_type == MemoryType.SHORT_TERM:
            self.short_term.append(memory.id)
        elif memory.memory_type == MemoryType.LONG_TERM:
            self.long_term.append(memory)
    
    def get(self, memory_id: str) -> Optional[Memory]:
        """获取记忆"""
        memory = self.memories.get(memory_id)
        if memory:
            memory.access()
        return memory
    
    def delete(self, memory_id: str) -> bool:
        """删除记忆"""
        if memory_id in self.memories:
            del self.memories[memory_id]
            if memory_id in self.short_term:
                self.short_term.remove(memory_id)
            self.long_term = [m for m in self.long_term if m.id != memory_id]
            return True
        return False
    
    def search_by_tags(self, tags: List[str]) -> List[Memory]:
        """通过标签搜索"""
        results = []
        for memory in self.memories.values():
            if any(tag in memory.tags for tag in tags):
                results.append(memory)
        return results
    
    def search_by_content(self, keyword: str) -> List[Memory]:
        """通过内容搜索"""
        results = []
        for memory in self.memories.values():
            if keyword.lower() in memory.content.lower():
                results.append(memory)
        return results
    
    def get_recent(self, limit: int = 10) -> List[Memory]:
        """获取最近的记忆"""
        all_memories = list(self.memories.values())
        all_memories.sort(key=lambda m: m.accessed_at, reverse=True)
        return all_memories[:limit]
    
    def get_by_type(self, memory_type: MemoryType) -> List[Memory]:
        """按类型获取记忆"""
        return [m for m in self.memories.values() if m.memory_type == memory_type]


class MemoryManager:
    """记忆管理器"""
    
    def __init__(self, max_short_term: int = 100, compression_threshold: int = 50):
        self.store = MemoryStore()
        self.max_short_term = max_short_term
        self.compression_threshold = compression_threshold
        
        # 回调函数
        self.callbacks: Dict[str, List[Callable]] = {
            "on_memory_added": [],
            "on_memory_accessed": [],
            "on_memory_compressed": [],
            "on_memory_forgotten": []
        }
    
    def create_memory(
        self,
        content: str,
        memory_type: MemoryType = MemoryType.SHORT_TERM,
        importance: MemoryImportance = MemoryImportance.MEDIUM,
        agent_name: Optional[str] = None,
        session_id: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Memory:
        """创建记忆"""
        memory = Memory(
            content=content,
            memory_type=memory_type,
            importance=importance,
            agent_name=agent_name,
            session_id=session_id,
            tags=tags or []
        )
        
        self.store.add(memory)
        
        # 触发回调
        for callback in self.callbacks.get("on_memory_added", []):
            callback(memory)
        
        # 检查是否需要压缩
        if len(self.store.short_term) >= self.compression_threshold:
            self._compress_short_term()
        
        return memory
    
    def add_short_term(
        self,
        content: str,
        agent_name: Optional[str] = None,
        session_id: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Memory:
        """添加短期记忆"""
        return self.create_memory(
            content=content,
            memory_type=MemoryType.SHORT_TERM,
            agent_name=agent_name,
            session_id=session_id,
            tags=tags
        )
    
    def add_long_term(
        self,
        content: str,
        importance: MemoryImportance = MemoryImportance.MEDIUM,
        agent_name: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Memory:
        """添加长期记忆"""
        return self.create_memory(
            content=content,
            memory_type=MemoryType.LONG_TERM,
            importance=importance,
            agent_name=agent_name,
            tags=tags
        )
    
    def add_working(
        self,
        key: str,
        value: Any,
        agent_name: Optional[str] = None
    ):
        """添加工作记忆"""
        self.store.working[key] = value
    
    def get_working(self, key: str) -> Optional[Any]:
        """获取工作记忆"""
        return self.store.working.get(key)
    
    def clear_working(self, key: Optional[str] = None):
        """清除工作记忆"""
        if key:
            if key in self.store.working:
                del self.store.working[key]
        else:
            self.store.working.clear()
    
    def get_context(
        self,
        agent_name: Optional[str] = None,
        session_id: Optional[str] = None,
        max_items: int = 10
    ) -> str:
        """获取上下文（用于 Agent 提示）"""
        context_parts = []
        
        # 添加长期记忆
        long_term = self.store.get_by_type(MemoryType.LONG_TERM)
        if long_term:
            context_parts.append("## 长期记忆")
            for memory in long_term[-5:]:
                context_parts.append(f"- {memory.content}")
        
        # 添加最近的短期记忆
        recent = self.store.get_recent(max_items)
        if recent:
            context_parts.append("\n## 最近交互")
            for memory in recent:
                role = memory.agent_name or "user"
                context_parts.append(f"{role}: {memory.content[:100]}...")
        
        # 添加工作记忆
        if self.store.working:
            context_parts.append("\n## 当前上下文")
            for key, value in self.store.working.items():
                context_parts.append(f"{key}: {value}")
        
        return "\n".join(context_parts)
    
    def _compress_short_term(self):
        """压缩短期记忆"""
        # 获取最近的短期记忆
        short_term_ids = list(self.store.short_term)
        recent_memories = [self.store.memories[mid] for mid in short_term_ids[-self.compression_threshold:]]
        
        # 生成摘要
        summary = self._generate_summary(recent_memories)
        
        # 创建长期记忆
        self.create_memory(
            content=summary,
            memory_type=MemoryType.LONG_TERM,
            importance=MemoryImportance.MEDIUM,
            tags=["summary", "compressed"]
        )
        
        # 触发回调
        for callback in self.callbacks.get("on_memory_compressed", []):
            callback(len(recent_memories))
    
    def _generate_summary(self, memories: List[Memory]) -> str:
        """生成记忆摘要"""
        if not memories:
            return ""
        
        summary_parts = [f"时间范围内的 {len(memories)} 条交互记忆："]
        
        for memory in memories[-10:]:  # 只取最近的10条
            role = memory.agent_name or "用户"
            content = memory.content[:50] + "..." if len(memory.content) > 50 else memory.content
            summary_parts.append(f"- {role}: {content}")
        
        return "\n".join(summary_parts)
    
    def search(self, query: str, limit: int = 10) -> List[Memory]:
        """搜索记忆"""
        results = []
        
        # 内容搜索
        results.extend(self.store.search_by_content(query))
        
        # 去重并排序
        seen = set()
        unique_results = []
        for memory in results:
            if memory.id not in seen:
                seen.add(memory.id)
                unique_results.append(memory)
        
        # 按重要性和访问时间排序
        unique_results.sort(
            key=lambda m: (m.importance.value, m.accessed_at),
            reverse=True
        )
        
        return unique_results[:limit]
    
    def register_callback(self, event: str, callback: Callable):
        """注册回调"""
        if event in self.callbacks:
            self.callbacks[event].append(callback)
    
    def export_memories(self, memory_type: Optional[MemoryType] = None) -> str:
        """导出记忆"""
        if memory_type:
            memories = self.store.get_by_type(memory_type)
        else:
            memories = list(self.store.memories.values())
        
        return json.dumps(
            [m.to_dict() for m in memories],
            ensure_ascii=False,
            indent=2
        )
    
    def import_memories(self, json_str: str) -> int:
        """导入记忆"""
        try:
            data = json.loads(json_str)
            count = 0
            
            for item in data:
                memory = Memory(
                    content=item.get("content", ""),
                    memory_type=MemoryType(item.get("type", "short_term")),
                    importance=MemoryImportance(item.get("importance", 2)),
                    agent_name=item.get("agent_name"),
                    session_id=item.get("session_id"),
                    tags=item.get("tags", [])
                )
                self.store.add(memory)
                count += 1
            
            return count
        except:
            return 0
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取记忆统计"""
        return {
            "total": len(self.store.memories),
            "short_term": len([m for m in self.store.memories.values() if m.memory_type == MemoryType.SHORT_TERM]),
            "long_term": len([m for m in self.store.memories.values() if m.memory_type == MemoryType.LONG_TERM]),
            "working": len(self.store.working),
            "avg_access_count": sum(m.access_count for m in self.store.memories.values()) / max(len(self.store.memories), 1)
        }
