"""
会话管理模块
参考 OpenClaw 的会话管理：JSONL 存储、会话重置、会话隔离
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import uuid
import threading


@dataclass
class SessionMessage:
    """会话消息"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    role: str = "user"  # user, assistant, system, error
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    tokens_used: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "content": self.content,
            "role": self.role,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "tokens_used": self.tokens_used
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionMessage':
        """从字典创建"""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            content=data.get("content", ""),
            role=data.get("role", "user"),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.now(),
            metadata=data.get("metadata", {}),
            tokens_used=data.get("tokens_used", 0)
        )


@dataclass
class Session:
    """会话"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str = ""
    channel: str = "default"
    peer: str = ""
    scope: str = "per-peer"  # main, per-peer, per-channel-peer
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)
    messages: List[SessionMessage] = field(default_factory=list)
    reset_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "channel": self.channel,
            "peer": self.peer,
            "scope": self.scope,
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat(),
            "messages": [msg.to_dict() for msg in self.messages],
            "reset_count": self.reset_count,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Session':
        """从字典创建"""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            agent_id=data.get("agent_id", ""),
            channel=data.get("channel", "default"),
            peer=data.get("peer", ""),
            scope=data.get("scope", "per-peer"),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            last_active=datetime.fromisoformat(data["last_active"]) if "last_active" in data else datetime.now(),
            messages=[SessionMessage.from_dict(msg) for msg in data.get("messages", [])],
            reset_count=data.get("reset_count", 0),
            metadata=data.get("metadata", {})
        )


class SessionManager:
    """
    会话管理器
    参考 OpenClaw 的会话管理：
    - JSONL 文件存储
    - 会话隔离（per-peer, per-channel-peer）
    - 自动重置（daily, idle）
    - 会话元数据跟踪
    """
    
    def __init__(self, sessions_dir: str):
        self.sessions_dir = Path(sessions_dir)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        
        # 内存缓存
        self.sessions: Dict[str, Session] = {}
        self.sessions_meta: Dict[str, Dict[str, Any]] = {}
        
        # 锁
        self._lock = threading.Lock()
        
        # 加载现有会话
        self._load_all_sessions()
    
    def _get_session_file(self, session_id: str) -> Path:
        """获取会话文件路径"""
        return self.sessions_dir / f"{session_id}.jsonl"
    
    def _get_meta_file(self) -> Path:
        """获取元数据文件路径"""
        return self.sessions_dir / "sessions.json"
    
    def _load_all_sessions(self):
        """加载所有会话"""
        meta_file = self._get_meta_file()
        
        if meta_file.exists():
            with open(meta_file, 'r', encoding='utf-8') as f:
                self.sessions_meta = json.load(f)
            
            # 加载每个会话
            for session_id, meta in self.sessions_meta.items():
                session_file = self._get_session_file(session_id)
                if session_file.exists():
                    messages = self._load_session_messages(session_file)
                    session = Session(
                        id=session_id,
                        agent_id=meta.get("agent_id", ""),
                        channel=meta.get("channel", "default"),
                        peer=meta.get("peer", ""),
                        scope=meta.get("scope", "per-peer"),
                        created_at=datetime.fromisoformat(meta["created_at"]) if "created_at" in meta else datetime.now(),
                        last_active=datetime.fromisoformat(meta["last_active"]) if "last_active" in meta else datetime.now(),
                        messages=messages,
                        reset_count=meta.get("reset_count", 0),
                        metadata=meta.get("metadata", {})
                    )
                    self.sessions[session_id] = session
    
    def _load_session_messages(self, file_path: Path) -> List[SessionMessage]:
        """从 JSONL 文件加载会话消息"""
        messages = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    messages.append(SessionMessage.from_dict(data))
        return messages
    
    def _save_session_messages(self, session: Session):
        """保存会话消息到 JSONL 文件"""
        file_path = self._get_session_file(session.id)
        with open(file_path, 'w', encoding='utf-8') as f:
            for message in session.messages:
                f.write(json.dumps(message.to_dict(), ensure_ascii=False) + '\n')
    
    def _save_meta(self):
        """保存会话元数据"""
        meta_file = self._get_meta_file()
        meta_data = {
            session_id: {
                "agent_id": session.agent_id,
                "channel": session.channel,
                "peer": session.peer,
                "scope": session.scope,
                "created_at": session.created_at.isoformat(),
                "last_active": session.last_active.isoformat(),
                "reset_count": session.reset_count,
                "metadata": session.metadata
            }
            for session_id, session in self.sessions.items()
        }
        with open(meta_file, 'w', encoding='utf-8') as f:
            json.dump(meta_data, f, indent=2, ensure_ascii=False)
    
    def get_or_create_session(
        self,
        agent_id: str,
        channel: str = "default",
        peer: str = "",
        scope: str = "per-peer"
    ) -> Session:
        """获取或创建会话"""
        with self._lock:
            # 根据 scope 生成会话键
            if scope == "main":
                session_key = f"main:{agent_id}"
            elif scope == "per-peer":
                session_key = f"peer:{agent_id}:{peer}"
            elif scope == "per-channel-peer":
                session_key = f"channel:{agent_id}:{channel}:{peer}"
            else:
                session_key = f"unknown:{agent_id}"
            
            # 查找现有会话
            for session in self.sessions.values():
                if scope == "main" and session.agent_id == agent_id:
                    return session
                elif scope == "per-peer" and session.agent_id == agent_id and session.peer == peer:
                    return session
                elif scope == "per-channel-peer" and session.agent_id == agent_id and session.channel == channel and session.peer == peer:
                    return session
            
            # 创建新会话
            session = Session(
                agent_id=agent_id,
                channel=channel,
                peer=peer,
                scope=scope
            )
            self.sessions[session.id] = session
            self._save_meta()
            
            return session
    
    def add_message(self, session_id: str, message: SessionMessage):
        """添加消息到会话"""
        with self._lock:
            if session_id not in self.sessions:
                raise ValueError(f"Session {session_id} not found")
            
            session = self.sessions[session_id]
            session.messages.append(message)
            session.last_active = datetime.now()
            
            # 保存到 JSONL 文件
            self._save_session_messages(session)
            self._save_meta()
    
    def get_messages(self, session_id: str, limit: int = 50) -> List[SessionMessage]:
        """获取会话消息"""
        with self._lock:
            if session_id not in self.sessions:
                return []
            
            session = self.sessions[session_id]
            return session.messages[-limit:]
    
    def reset_session(self, session_id: str, keep_messages: bool = False) -> Session:
        """重置会话"""
        with self._lock:
            if session_id not in self.sessions:
                raise ValueError(f"Session {session_id} not found")
            
            session = self.sessions[session_id]
            session.reset_count += 1
            session.last_active = datetime.now()
            
            if not keep_messages:
                session.messages = []
                # 清空 JSONL 文件
                file_path = self._get_session_file(session_id)
                with open(file_path, 'w', encoding='utf-8') as f:
                    pass
            
            self._save_meta()
            return session
    
    def delete_session(self, session_id: str):
        """删除会话"""
        with self._lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
            
            # 删除文件
            file_path = self._get_session_file(session_id)
            if file_path.exists():
                file_path.unlink()
            
            self._save_meta()
    
    def list_sessions(self, agent_id: Optional[str] = None) -> List[str]:
        """列出会话"""
        with self._lock:
            if agent_id:
                return [
                    session_id for session_id, session in self.sessions.items()
                    if session.agent_id == agent_id
                ]
            return list(self.sessions.keys())
    
    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """获取会话统计"""
        with self._lock:
            if session_id not in self.sessions:
                return {}
            
            session = self.sessions[session_id]
            total_tokens = sum(msg.tokens_used for msg in session.messages)
            
            return {
                "id": session.id,
                "agent_id": session.agent_id,
                "channel": session.channel,
                "peer": session.peer,
                "message_count": len(session.messages),
                "total_tokens": total_tokens,
                "created_at": session.created_at.isoformat(),
                "last_active": session.last_active.isoformat(),
                "reset_count": session.reset_count
            }
    
    def cleanup_old_sessions(self, max_age_days: int = 30):
        """清理旧会话"""
        with self._lock:
            cutoff = datetime.now() - timedelta(days=max_age_days)
            to_delete = []
            
            for session_id, session in self.sessions.items():
                if session.last_active < cutoff:
                    to_delete.append(session_id)
            
            for session_id in to_delete:
                self.delete_session(session_id)
            
            return len(to_delete)
    
    def compact_session(self, session_id: str, instructions: str = "") -> Dict[str, Any]:
        """压缩会话（保留重要消息）"""
        with self._lock:
            if session_id not in self.sessions:
                return {"error": "Session not found"}
            
            session = self.sessions[session_id]
            
            # 简单实现：保留系统消息和最近的消息
            compacted = []
            for msg in session.messages:
                if msg.role == "system" or msg.tokens_used > 100:
                    compacted.append(msg)
            
            # 保留最近 20 条消息
            recent = session.messages[-20:]
            compacted.extend(recent)
            
            # 去重
            seen_ids = set()
            unique_compacted = []
            for msg in compacted:
                if msg.id not in seen_ids:
                    unique_compacted.append(msg)
                    seen_ids.add(msg.id)
            
            session.messages = unique_compacted
            self._save_session_messages(session)
            
            return {
                "original_count": len(session.messages),
                "compacted_count": len(unique_compacted),
                "remaining_context": len(unique_compacted)
            }


class SessionRouter:
    """会话路由器"""
    
    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager
    
    def resolve_session(
        self,
        agent_id: str,
        channel: str,
        peer: str,
        scope: str = "per-peer"
    ) -> Session:
        """解析会话"""
        return self.session_manager.get_or_create_session(
            agent_id=agent_id,
            channel=channel,
            peer=peer,
            scope=scope
        )
    
    def should_reset_session(self, session: Session, triggers: List[str]) -> bool:
        """检查是否应该重置会话"""
        # 检查最后一条消息是否包含重置触发词
        if session.messages:
            last_message = session.messages[-1]
            for trigger in triggers:
                if trigger in last_message.content:
                    return True
        return False
    
    def route_message(
        self,
        agent_id: str,
        channel: str,
        peer: str,
        message: str,
        scope: str = "per-peer",
        reset_triggers: Optional[List[str]] = None
    ) -> Session:
        """路由消息到会话"""
        session = self.resolve_session(agent_id, channel, peer, scope)
        
        # 检查是否需要重置
        if reset_triggers and self.should_reset_session(session, reset_triggers):
            self.session_manager.reset_session(session.id, keep_messages=False)
            # 创建新会话
            session = self.resolve_session(agent_id, channel, peer, scope)
        
        return session
