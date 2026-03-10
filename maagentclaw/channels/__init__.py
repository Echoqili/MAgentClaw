"""
渠道管理模块
支持多种消息渠道：WebSocket、REST API、CLI 等
"""

from .base_channel import BaseChannel, ChannelConfig, ChannelMessage, ChannelType
from .channel_manager import ChannelManager
from .channel_router import ChannelRouter

__all__ = [
    "BaseChannel",
    "ChannelConfig",
    "ChannelMessage",
    "ChannelType",
    "ChannelManager",
    "ChannelRouter"
]
