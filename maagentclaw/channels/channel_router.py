"""
渠道路由器
根据规则将消息路由到合适的渠道
"""

from typing import Dict, List, Optional, Any, Callable
from .base_channel import BaseChannel, ChannelMessage, ChannelType
from .channel_manager import ChannelManager


class RoutingRule:
    """路由规则类"""
    
    def __init__(
        self,
        name: str,
        condition: Callable[[ChannelMessage], bool],
        target_channels: List[str],
        priority: int = 0
    ):
        self.name = name
        self.condition = condition
        self.target_channels = target_channels
        self.priority = priority
    
    def match(self, message: ChannelMessage) -> bool:
        """检查消息是否匹配规则"""
        try:
            return self.condition(message)
        except Exception as e:
            print(f"[RoutingRule] 规则匹配失败 {self.name}: {e}")
            return False


class ChannelRouter:
    """
    渠道路由器
    根据规则将消息路由到合适的渠道
    """
    
    def __init__(self, channel_manager: ChannelManager):
        self.channel_manager = channel_manager
        self.rules: List[RoutingRule] = []
        self.default_strategy = "all"  # all, first, random
    
    def add_rule(self, rule: RoutingRule):
        """添加路由规则"""
        self.rules.append(rule)
        # 按优先级排序
        self.rules.sort(key=lambda r: r.priority, reverse=True)
        print(f"[ChannelRouter] 添加路由规则：{rule.name}")
    
    def remove_rule(self, rule_name: str):
        """移除路由规则"""
        self.rules = [r for r in self.rules if r.name != rule_name]
        print(f"[ChannelRouter] 移除路由规则：{rule_name}")
    
    def route_message(self, message: ChannelMessage) -> List[str]:
        """
        路由消息到渠道
        参数:
            message: 消息
        返回:
            List[str]: 目标渠道列表
        """
        # 尝试匹配规则
        for rule in self.rules:
            if rule.match(message):
                return rule.target_channels
        
        # 没有匹配规则，使用默认策略
        return self._get_default_channels()
    
    def _get_default_channels(self) -> List[str]:
        """获取默认渠道"""
        if self.default_strategy == "all":
            return list(self.channel_manager.channels.keys())
        elif self.default_strategy == "first":
            return [self.channel_manager.default_channel] if self.channel_manager.default_channel else []
        else:
            return []
    
    async def send_message(self, message: ChannelMessage) -> Dict[str, bool]:
        """
        发送消息（自动路由）
        参数:
            message: 消息
        返回:
            Dict[str, bool]: 各渠道发送结果
        """
        # 获取目标渠道
        targets = self.route_message(message)
        
        results = {}
        
        for channel_name in targets:
            channel = self.channel_manager.get_channel(channel_name)
            
            if channel:
                success = await channel.send_message(message)
                results[channel_name] = success
            else:
                results[channel_name] = False
        
        return results
    
    # 预定义规则创建器
    
    @staticmethod
    def create_type_rule(
        message_type: str,
        target_channels: List[str],
        priority: int = 0
    ) -> RoutingRule:
        """创建消息类型规则"""
        def condition(message: ChannelMessage) -> bool:
            return message.metadata.get("type") == message_type
        
        return RoutingRule(
            name=f"type_{message_type}",
            condition=condition,
            target_channels=target_channels,
            priority=priority
        )
    
    @staticmethod
    def create_sender_rule(
        sender_pattern: str,
        target_channels: List[str],
        priority: int = 0
    ) -> RoutingRule:
        """创建发送者规则"""
        def condition(message: ChannelMessage) -> bool:
            return sender_pattern in message.sender_id
        
        return RoutingRule(
            name=f"sender_{sender_pattern}",
            condition=condition,
            target_channels=target_channels,
            priority=priority
        )
    
    @staticmethod
    def create_content_rule(
        keyword: str,
        target_channels: List[str],
        priority: int = 0
    ) -> RoutingRule:
        """创建内容关键词规则"""
        def condition(message: ChannelMessage) -> bool:
            return keyword in message.content
        
        return RoutingRule(
            name=f"keyword_{keyword}",
            condition=condition,
            target_channels=target_channels,
            priority=priority
        )
    
    @staticmethod
    def create_priority_rule(
        priority_level: str,
        target_channels: List[str],
        priority: int = 10
    ) -> RoutingRule:
        """创建优先级规则"""
        def condition(message: ChannelMessage) -> bool:
            return message.metadata.get("priority") == priority_level
        
        return RoutingRule(
            name=f"priority_{priority_level}",
            condition=condition,
            target_channels=target_channels,
            priority=priority
        )


# 便捷的路由器创建函数
def create_router(
    channel_manager: ChannelManager,
    default_strategy: str = "all",
    rules: Optional[List[RoutingRule]] = None
) -> ChannelRouter:
    """
    创建路由器
    参数:
        channel_manager: 渠道管理器
        default_strategy: 默认策略
        rules: 初始规则列表
    返回:
        ChannelRouter: 路由器实例
    """
    router = ChannelRouter(channel_manager)
    router.default_strategy = default_strategy
    
    if rules:
        for rule in rules:
            router.add_rule(rule)
    
    return router
