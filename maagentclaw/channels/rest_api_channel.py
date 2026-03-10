"""
REST API 渠道实现
支持 HTTP RESTful 接口
"""

import asyncio
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from aiohttp import web

from .base_channel import BaseChannel, ChannelConfig, ChannelMessage, ChannelType, MessageStatus


class RESTAPIChannel(BaseChannel):
    """
    REST API 渠道实现
    支持 HTTP RESTful 接口
    """
    
    def __init__(self, config: ChannelConfig):
        super().__init__(config)
        self.host = config.config.get("host", "0.0.0.0")
        self.port = config.config.get("port", 8080)
        self.app = web.Application()
        self.runner = None
        self._message_queue = asyncio.Queue()
        self._setup_routes()
    
    def _setup_routes(self):
        """设置路由"""
        self.app.router.add_post('/api/message', self.handle_message)
        self.app.router.add_get('/api/message/{message_id}', self.handle_get_message)
        self.app.router.add_get('/api/health', self.handle_health)
        self.app.router.add_get('/api/stats', self.handle_stats)
    
    async def initialize(self) -> bool:
        """初始化 REST API 服务器"""
        try:
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()
            
            site = web.TCPSite(self.runner, self.host, self.port)
            await site.start()
            
            self._initialized = True
            print(f"[REST API] 服务器已启动：http://{self.host}:{self.port}")
            return True
            
        except Exception as e:
            print(f"[REST API] 初始化失败：{e}")
            return False
    
    async def shutdown(self):
        """关闭 REST API 服务器"""
        if self.runner:
            await self.runner.cleanup()
        print("[REST API] 服务器已关闭")
    
    async def handle_message(self, request: web.Request) -> web.Response:
        """处理消息请求"""
        try:
            data = await request.json()
            
            # 创建消息
            message = ChannelMessage(
                content=data.get("content", ""),
                sender_id=data.get("sender_id", "anonymous"),
                receiver_id=data.get("receiver_id", ""),
                channel_type=self.channel_type,
                metadata=data.get("metadata", {})
            )
            
            # 处理消息
            asyncio.create_task(self._handle_message(message))
            
            # 返回响应
            return web.json_response({
                "success": True,
                "message_id": message.id,
                "status": "received"
            })
            
        except json.JSONDecodeError:
            return web.json_response({
                "success": False,
                "error": "Invalid JSON"
            }, status=400)
        except Exception as e:
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    async def handle_get_message(self, request: web.Request) -> web.Response:
        """获取消息状态"""
        message_id = request.match_info['message_id']
        
        # 这里可以实现消息状态查询
        return web.json_response({
            "message_id": message_id,
            "status": "not_implemented"
        })
    
    async def handle_health(self, request: web.Request) -> web.Response:
        """健康检查"""
        return web.json_response({
            "status": "healthy",
            "channel": self.name,
            "type": self.channel_type.value,
            "initialized": self._initialized
        })
    
    async def handle_stats(self, request: web.Request) -> web.Response:
        """获取统计信息"""
        return web.json_response(self.get_info())
    
    async def send_message(self, message: ChannelMessage) -> bool:
        """发送消息（对于 REST API 主要是接收）"""
        # REST API 主要是被动接收消息
        # 发送消息可以通过 WebSocket 或其他方式
        message.status = MessageStatus.SENT
        return True
    
    async def broadcast(self, content: str, recipients: Optional[List[str]] = None) -> int:
        """广播消息（不直接支持）"""
        # REST API 不直接支持广播
        # 可以通过其他方式实现
        return 0


def create_rest_api_channel(
    name: str = "rest_api",
    host: str = "0.0.0.0",
    port: int = 8080,
    **kwargs
) -> RESTAPIChannel:
    """
    创建 REST API 渠道的便捷函数
    """
    config = ChannelConfig(
        name=name,
        channel_type=ChannelType.REST_API,
        config={
            "host": host,
            "port": port,
            **kwargs
        }
    )
    
    return RESTAPIChannel(config)
