"""
渠道基类
定义所有渠道的统一接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable, AsyncGenerator, List
from dataclasses import dataclass, field
from datetime import datetime
import uuid
from enum import Enum


class ChannelType(str, Enum):
    """渠道类型枚举"""
    WEBSOCKET = "websocket"
    REST_API = "rest_api"
    CLI = "cli"
    CUSTOM = "custom"


class MessageStatus(str, Enum):
    """消息状态枚举"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


@dataclass
class ChannelMessage:
    """渠道消息类"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    sender_id: str = ""
    receiver_id: str = ""
    channel_type: ChannelType = ChannelType.CUSTOM
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: MessageStatus = MessageStatus.PENDING
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "content": self.content,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "channel_type": self.channel_type.value,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "status": self.status.value,
            "error": self.error
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChannelMessage':
        """从字典创建"""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            content=data.get("content", ""),
            sender_id=data.get("sender_id", ""),
            receiver_id=data.get("receiver_id", ""),
            channel_type=ChannelType(data.get("channel_type", "custom")),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.now(),
            metadata=data.get("metadata", {}),
            status=MessageStatus(data.get("status", "pending")),
            error=data.get("error")
        )


@dataclass
class ChannelConfig:
    """渠道配置类"""
    name: str
    channel_type: ChannelType
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseChannel(ABC):
    """
    渠道基类
    所有渠道实现都必须继承此类
    """
    
    def __init__(self, config: ChannelConfig):
        self.config = config
        self.name = config.name
        self.channel_type = config.channel_type
        self.enabled = config.enabled
        self._initialized = False
        self._message_handlers: List[Callable] = []
        self._error_handlers: List[Callable] = []
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        初始化渠道
        返回是否成功
        """
        pass
    
    @abstractmethod
    async def shutdown(self):
        """
        关闭渠道
        """
        pass
    
    @abstractmethod
    async def send_message(self, message: ChannelMessage) -> bool:
        """
        发送消息
        参数:
            message: 要发送的消息
        返回:
            bool: 是否成功
        """
        pass
    
    @abstractmethod
    async def broadcast(self, content: str, recipients: Optional[List[str]] = None) -> int:
        """
        广播消息
        参数:
            content: 消息内容
            recipients: 接收者列表，None 表示所有人
        返回:
            int: 成功发送的数量
        """
        pass
    
    def on_message(self, handler: Callable):
        """注册消息处理器"""
        self._message_handlers.append(handler)
    
    def on_error(self, handler: Callable):
        """注册错误处理器"""
        self._error_handlers.append(handler)
    
    async def _handle_message(self, message: ChannelMessage):
        """处理接收到的消息"""
        for handler in self._message_handlers:
            try:
                if hasattr(handler, '__await__'):
                    await handler(message)
                else:
                    handler(message)
            except Exception as e:
                await self._handle_error(e, message)
    
    async def _handle_error(self, error: Exception, context: Any = None):
        """处理错误"""
        for handler in self._error_handlers:
            try:
                if hasattr(handler, '__await__'):
                    await handler(error, context)
                else:
                    handler(error, context)
            except Exception as e:
                print(f"[Channel] 错误处理器异常：{e}")
    
    def get_info(self) -> Dict[str, Any]:
        """获取渠道信息"""
        return {
            "name": self.name,
            "type": self.channel_type.value,
            "enabled": self.enabled,
            "initialized": self._initialized,
            "message_handlers": len(self._message_handlers),
            "error_handlers": len(self._error_handlers)
        }
    
    def validate_config(self) -> List[str]:
        """验证配置"""
        errors = []
        
        if not self.config.name:
            errors.append("Channel name is required")
        
        if not self.config.channel_type:
            errors.append("Channel type is required")
        
        return errors
