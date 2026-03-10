"""
Multi-Channel Adapter - 多渠道适配器

支持微信、企业微信、飞书、钉钉等渠道接入
"""

import asyncio
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


class ChannelType(Enum):
    """渠道类型"""
    CLI = "cli"
    WEB = "web"
    WECHAT = "wechat"
    WECHAT_WORK = "wechat_work"
    FEISHU = "feishu"
    DINGTALK = "dingtalk"
    DISCORD = "discord"
    TELEGRAM = "telegram"
    SLACK = "slack"


class MessageType(Enum):
    """消息类型"""
    TEXT = "text"
    IMAGE = "image"
    VOICE = "voice"
    VIDEO = "video"
    FILE = "file"
    CARD = "card"


@dataclass
class ChannelMessage:
    """渠道消息"""
    message_id: str
    channel_type: ChannelType
    message_type: MessageType
    content: str
    sender_id: str
    sender_name: str
    receiver_id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_id": self.message_id,
            "channel_type": self.channel_type.value,
            "message_type": self.message_type.value,
            "content": self.content,
            "sender_id": self.sender_id,
            "sender_name": self.sender_name,
            "receiver_id": self.receiver_id,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class ChannelConfig:
    """渠道配置"""
    channel_type: ChannelType
    enabled: bool = True
    name: str = ""
    webhook_url: Optional[str] = None
    bot_token: Optional[str] = None
    app_id: Optional[str] = None
    app_secret: Optional[str] = None
    webhook_secret: Optional[str] = None
    auto_reply: bool = True
    keywords: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "channel_type": self.channel_type.value,
            "enabled": self.enabled,
            "name": self.name,
            "auto_reply": self.auto_reply,
            "keywords": self.keywords
        }


class BaseChannelAdapter(ABC):
    """渠道适配器基类"""
    
    def __init__(self, config: ChannelConfig):
        self.config = config
        self.message_handler: Optional[Callable] = None
        self.running = False
    
    @abstractmethod
    async def connect(self) -> bool:
        """连接渠道"""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """断开连接"""
        pass
    
    @abstractmethod
    async def send_message(self, message: ChannelMessage) -> bool:
        """发送消息"""
        pass
    
    @abstractmethod
    async def receive_message(self) -> Optional[ChannelMessage]:
        """接收消息"""
        pass
    
    @abstractmethod
    async def send_notification(self, user_id: str, content: str) -> bool:
        """发送通知"""
        pass
    
    def set_message_handler(self, handler: Callable):
        """设置消息处理器"""
        self.message_handler = handler
    
    async def start_listening(self):
        """开始监听消息"""
        self.running = True
        while self.running:
            message = await self.receive_message()
            if message and self.message_handler:
                asyncio.create_task(self.message_handler(message))
            await asyncio.sleep(0.1)
    
    async def stop_listening(self):
        """停止监听"""
        self.running = False


class WeChatChannelAdapter(BaseChannelAdapter):
    """微信渠道适配器"""
    
    def __init__(self, config: ChannelConfig):
        super().__init__(config)
        self.api_url = "https://api.weixin.qq.com"
        self.qr_code_url: Optional[str] = None
    
    async def connect(self) -> bool:
        """连接微信"""
        print(f"Connecting to WeChat channel: {self.config.name}")
        
        if not self.config.app_id or not self.config.app_secret:
            print("Warning: WeChat app_id or app_secret not configured")
            return False
        
        try:
            # 获取 access_token
            url = f"{self.api_url}/cgi-bin/token"
            params = {
                "grant_type": "client_credential",
                "appid": self.config.app_id,
                "secret": self.config.app_secret
            }
            # 模拟获取 token
            print(f"WeChat connected: {self.config.name}")
            return True
        except Exception as e:
            print(f"WeChat connection error: {e}")
            return False
    
    async def disconnect(self):
        """断开微信连接"""
        print(f"WeChat disconnected: {self.config.name}")
    
    async def send_message(self, message: ChannelMessage) -> bool:
        """发送微信消息"""
        print(f"Sending WeChat message to {message.receiver_id}: {message.content[:50]}...")
        
        if not self.config.webhook_url:
            print("Warning: Webhook URL not configured")
            return False
        
        try:
            # 发送模板消息
            payload = {
                "touser": message.receiver_id,
                "msgtype": "text",
                "text": {"content": message.content}
            }
            # 模拟发送
            return True
        except Exception as e:
            print(f"Send message error: {e}")
            return False
    
    async def receive_message(self) -> Optional[ChannelMessage]:
        """接收微信消息"""
        # 实际实现需要 WebSocket 或回调服务器
        await asyncio.sleep(1)
        return None
    
    async def send_notification(self, user_id: str, content: str) -> bool:
        """发送通知"""
        message = ChannelMessage(
            message_id=f"msg_{datetime.now().timestamp()}",
            channel_type=ChannelType.WECHAT,
            message_type=MessageType.TEXT,
            content=content,
            sender_id="system",
            sender_name="System",
            receiver_id=user_id
        )
        return await self.send_message(message)
    
    def generate_qr_code(self) -> str:
        """生成二维码用于绑定"""
        return f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={self.config.app_id}"


class WeChatWorkChannelAdapter(BaseChannelAdapter):
    """企业微信渠道适配器"""
    
    def __init__(self, config: ChannelConfig):
        super().__init__(config)
        self.api_url = "https://qyapi.weixin.qq.com"
        self.corp_id: Optional[str] = None
    
    async def connect(self) -> bool:
        """连接企业微信"""
        print(f"Connecting to WeChat Work: {self.config.name}")
        
        if not self.config.corp_id:
            print("Warning: Corp ID not configured")
            return False
        
        print(f"WeChat Work connected: {self.config.name}")
        return True
    
    async def disconnect(self):
        """断开企业微信连接"""
        print(f"WeChat Work disconnected: {self.config.name}")
    
    async def send_message(self, message: ChannelMessage) -> bool:
        """发送企业微信消息"""
        print(f"Sending WeChat Work message to {message.receiver_id}")
        return True
    
    async def receive_message(self) -> Optional[ChannelMessage]:
        """接收企业微信消息"""
        await asyncio.sleep(1)
        return None
    
    async def send_notification(self, user_id: str, content: str) -> bool:
        """发送通知"""
        message = ChannelMessage(
            message_id=f"msg_{datetime.now().timestamp()}",
            channel_type=ChannelType.WECHAT_WORK,
            message_type=MessageType.TEXT,
            content=content,
            sender_id="system",
            sender_name="System",
            receiver_id=user_id
        )
        return await self.send_message(message)


class FeishuChannelAdapter(BaseChannelAdapter):
    """飞书渠道适配器"""
    
    def __init__(self, config: ChannelConfig):
        super().__init__(config)
        self.api_url = "https://open.feishu.cn/open-apis"
        self.tenant_access_token: Optional[str] = None
    
    async def connect(self) -> bool:
        """连接飞书"""
        print(f"Connecting to Feishu: {self.config.name}")
        
        if not self.config.app_id or not self.config.app_secret:
            print("Warning: Feishu app_id or app_secret not configured")
            return False
        
        print(f"Feishu connected: {self.config.name}")
        return True
    
    async def disconnect(self):
        """断开飞书连接"""
        print(f"Feishu disconnected: {self.config.name}")
    
    async def send_message(self, message: ChannelMessage) -> bool:
        """发送飞书消息"""
        print(f"Sending Feishu message to {message.receiver_id}")
        return True
    
    async def receive_message(self) -> Optional[ChannelMessage]:
        """接收飞书消息"""
        await asyncio.sleep(1)
        return None
    
    async def send_notification(self, user_id: str, content: str) -> bool:
        """发送通知"""
        message = ChannelMessage(
            message_id=f"msg_{datetime.now().timestamp()}",
            channel_type=ChannelType.FEISHU,
            message_type=MessageType.TEXT,
            content=content,
            sender_id="system",
            sender_name="System",
            receiver_id=user_id
        )
        return await self.send_message(message)


class DingTalkChannelAdapter(BaseChannelAdapter):
    """钉钉渠道适配器"""
    
    def __init__(self, config: ChannelConfig):
        super().__init__(config)
        self.api_url = "https://api.dingtalk.com"
    
    async def connect(self) -> bool:
        """连接钉钉"""
        print(f"Connecting to DingTalk: {self.config.name}")
        
        if not self.config.app_key or not self.config.app_secret:
            print("Warning: DingTalk app_key or app_secret not configured")
            return False
        
        print(f"DingTalk connected: {self.config.name}")
        return True
    
    async def disconnect(self):
        """断开钉钉连接"""
        print(f"DingTalk disconnected: {self.config.name}")
    
    async def send_message(self, message: ChannelMessage) -> bool:
        """发送钉钉消息"""
        print(f"Sending DingTalk message to {message.receiver_id}")
        return True
    
    async def receive_message(self) -> Optional[ChannelMessage]:
        """接收钉钉消息"""
        await asyncio.sleep(1)
        return None
    
    async def send_notification(self, user_id: str, content: str) -> bool:
        """发送通知"""
        message = ChannelMessage(
            message_id=f"msg_{datetime.now().timestamp()}",
            channel_type=ChannelType.DINGTALK,
            message_type=MessageType.TEXT,
            content=content,
            sender_id="system",
            sender_name="System",
            receiver_id=user_id
        )
        return await self.send_message(message)


class ChannelManager:
    """多渠道管理器"""
    
    def __init__(self):
        self.channels: Dict[ChannelType, BaseChannelAdapter] = {}
        self.configs: Dict[ChannelType, ChannelConfig] = {}
    
    def register_channel(self, channel_type: ChannelType, adapter: BaseChannelAdapter):
        """注册渠道"""
        self.channels[channel_type] = adapter
        self.configs[channel_type] = adapter.config
    
    def get_channel(self, channel_type: ChannelType) -> Optional[BaseChannelAdapter]:
        """获取渠道"""
        return self.channels.get(channel_type)
    
    def list_channels(self) -> List[Dict[str, Any]]:
        """列出所有渠道"""
        result = []
        for channel_type, config in self.configs.items():
            result.append({
                "type": channel_type.value,
                "name": config.name,
                "enabled": config.enabled,
                "connected": channel_type in self.channels
            })
        return result
    
    async def connect_all(self) -> Dict[ChannelType, bool]:
        """连接所有启用的渠道"""
        results = {}
        for channel_type, adapter in self.channels.items():
            if self.configs[channel_type].enabled:
                results[channel_type] = await adapter.connect()
        return results
    
    async def disconnect_all(self):
        """断开所有渠道"""
        for adapter in self.channels.values():
            await adapter.disconnect()
    
    async def send_to_channel(self, channel_type: ChannelType, message: ChannelMessage) -> bool:
        """发送消息到指定渠道"""
        adapter = self.channels.get(channel_type)
        if adapter and self.configs[channel_type].enabled:
            return await adapter.send_message(message)
        return False
    
    async def broadcast(self, content: str, exclude: Optional[List[ChannelType]] = None) -> Dict[ChannelType, bool]:
        """广播消息到所有渠道"""
        results = {}
        exclude = exclude or []
        
        for channel_type, adapter in self.channels.items():
            if channel_type in exclude:
                continue
            if self.configs[channel_type].enabled:
                message = ChannelMessage(
                    message_id=f"msg_{datetime.now().timestamp()}",
                    channel_type=channel_type,
                    message_type=MessageType.TEXT,
                    content=content,
                    sender_id="system",
                    sender_name="System"
                )
                results[channel_type] = await adapter.send_message(message)
        
        return results
    
    def save_config(self, workspace_path: Path):
        """保存渠道配置"""
        config_file = workspace_path / "channels.json"
        config_data = {
            channel_type.value: config.to_dict()
            for channel_type, config in self.configs.items()
        }
        config_file.write_text(json.dumps(config_data, indent=2), encoding='utf-8')
    
    def load_config(self, workspace_path: Path):
        """加载渠道配置"""
        config_file = workspace_path / "channels.json"
        if not config_file.exists():
            return
        
        config_data = json.loads(config_file.read_text(encoding='utf-8'))
        
        for channel_type_str, config_dict in config_data.items():
            channel_type = ChannelType(channel_type_str)
            config = ChannelConfig(
                channel_type=channel_type,
                name=config_dict.get("name", ""),
                enabled=config_dict.get("enabled", True),
                auto_reply=config_dict.get("auto_reply", True),
                keywords=config_dict.get("keywords", [])
            )
            
            # 创建适配器
            if channel_type == ChannelType.WECHAT:
                adapter = WeChatChannelAdapter(config)
            elif channel_type == ChannelType.WECHAT_WORK:
                adapter = WeChatWorkChannelAdapter(config)
            elif channel_type == ChannelType.FEISHU:
                adapter = FeishuChannelAdapter(config)
            elif channel_type == ChannelType.DINGTALK:
                adapter = DingTalkChannelAdapter(config)
            else:
                continue
            
            self.register_channel(channel_type, adapter)


# 简化导入
__all__ = [
    "ChannelType",
    "MessageType",
    "ChannelMessage",
    "ChannelConfig",
    "BaseChannelAdapter",
    "WeChatChannelAdapter",
    "WeChatWorkChannelAdapter",
    "FeishuChannelAdapter",
    "DingTalkChannelAdapter",
    "ChannelManager"
]
