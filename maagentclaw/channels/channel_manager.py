"""
渠道管理器
管理多个渠道的生命周期
"""

from typing import Dict, List, Optional, Any
from .base_channel import BaseChannel, ChannelConfig, ChannelMessage, ChannelType


class ChannelManager:
    """
    渠道管理器
    管理多个渠道的生命周期和消息路由
    """
    
    def __init__(self):
        self.channels: Dict[str, BaseChannel] = {}
        self.default_channel: Optional[str] = None
    
    def register_channel(self, channel: BaseChannel, set_default: bool = False):
        """
        注册渠道
        参数:
            channel: 渠道实例
            set_default: 是否设为默认渠道
        """
        self.channels[channel.name] = channel
        
        if set_default or not self.default_channel:
            self.default_channel = channel.name
        
        print(f"[ChannelManager] 注册渠道：{channel.name} ({channel.channel_type.value})")
    
    def unregister_channel(self, channel_name: str):
        """注销渠道"""
        if channel_name in self.channels:
            del self.channels[channel_name]
            
            if self.default_channel == channel_name:
                self.default_channel = list(self.channels.keys())[0] if self.channels else None
            
            print(f"[ChannelManager] 注销渠道：{channel_name}")
    
    def get_channel(self, channel_name: Optional[str] = None) -> Optional[BaseChannel]:
        """
        获取渠道
        参数:
            channel_name: 渠道名称，None 则返回默认渠道
        """
        name = channel_name or self.default_channel
        
        if not name:
            print("[ChannelManager] 没有可用的渠道")
            return None
        
        if name not in self.channels:
            print(f"[ChannelManager] 渠道不存在：{name}")
            return None
        
        return self.channels[name]
    
    def set_default_channel(self, channel_name: str):
        """设置默认渠道"""
        if channel_name in self.channels:
            self.default_channel = channel_name
            print(f"[ChannelManager] 设置默认渠道：{channel_name}")
        else:
            print(f"[ChannelManager] 渠道不存在，无法设置默认：{channel_name}")
    
    async def initialize_all(self) -> bool:
        """初始化所有渠道"""
        success_count = 0
        
        for channel in self.channels.values():
            try:
                if await channel.initialize():
                    success_count += 1
            except Exception as e:
                print(f"[ChannelManager] 初始化渠道 {channel.name} 失败：{e}")
        
        print(f"[ChannelManager] 初始化完成：{success_count}/{len(self.channels)}")
        return success_count == len(self.channels)
    
    async def shutdown_all(self):
        """关闭所有渠道"""
        for channel in self.channels.values():
            try:
                await channel.shutdown()
            except Exception as e:
                print(f"[ChannelManager] 关闭渠道 {channel.name} 失败：{e}")
        
        print("[ChannelManager] 所有渠道已关闭")
    
    async def send_message(
        self,
        message: ChannelMessage,
        channel_name: Optional[str] = None
    ) -> bool:
        """
        发送消息
        参数:
            message: 消息
            channel_name: 渠道名称，None 则使用默认渠道
        """
        channel = self.get_channel(channel_name)
        
        if not channel:
            return False
        
        return await channel.send_message(message)
    
    async def broadcast(
        self,
        content: str,
        channel_names: Optional[List[str]] = None
    ) -> int:
        """
        广播消息
        参数:
            content: 消息内容
            channel_names: 渠道列表，None 表示所有渠道
        返回:
            int: 成功发送的总数
        """
        total_sent = 0
        
        channels = channel_names or list(self.channels.keys())
        
        for channel_name in channels:
            channel = self.get_channel(channel_name)
            
            if channel:
                sent = await channel.broadcast(content)
                total_sent += sent
        
        return total_sent
    
    def list_channels(self) -> List[Dict[str, Any]]:
        """列出所有渠道"""
        return [
            {
                "name": channel.name,
                "type": channel.channel_type.value,
                "enabled": channel.enabled,
                "initialized": channel._initialized,
                "is_default": channel.name == self.default_channel
            }
            for channel in self.channels.values()
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_channels": len(self.channels),
            "default_channel": self.default_channel,
            "channels": self.list_channels()
        }


# 便捷的渠道创建函数
def create_channel_from_config(config: ChannelConfig) -> Optional[BaseChannel]:
    """
    从配置创建渠道
    参数:
        config: 渠道配置
    返回:
        BaseChannel: 渠道实例
    """
    if config.channel_type == ChannelType.WEBSOCKET:
        from .websocket_channel import WebSocketChannel
        return WebSocketChannel(config)
    
    elif config.channel_type == ChannelType.REST_API:
        from .rest_api_channel import RESTAPIChannel
        return RESTAPIChannel(config)
    
    elif config.channel_type == ChannelType.CLI:
        from .cli_channel import CLIChannel
        return CLIChannel(config)
    
    else:
        print(f"[ChannelManager] 不支持的渠道类型：{config.channel_type}")
        return None
