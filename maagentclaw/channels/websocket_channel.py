"""
WebSocket 渠道实现
支持实时双向通信
"""

import asyncio
import json
from typing import Dict, Any, Optional, List, Set
from datetime import datetime

from .base_channel import BaseChannel, ChannelConfig, ChannelMessage, ChannelType, MessageStatus


class WebSocketConnection:
    """WebSocket 连接管理类"""
    
    def __init__(self, websocket, connection_id: str):
        self.websocket = websocket
        self.connection_id = connection_id
        self.created_at = datetime.now()
        self.last_active = datetime.now()
        self.metadata: Dict[str, Any] = {}
        self.is_closed = False
    
    async def send(self, data: Dict[str, Any]) -> bool:
        """发送数据"""
        try:
            await self.websocket.send(json.dumps(data))
            self.last_active = datetime.now()
            return True
        except Exception as e:
            print(f"[WebSocket] 发送失败：{e}")
            return False
    
    async def close(self):
        """关闭连接"""
        try:
            await self.websocket.close()
            self.is_closed = True
        except Exception as e:
            print(f"[WebSocket] 关闭失败：{e}")


class WebSocketChannel(BaseChannel):
    """
    WebSocket 渠道实现
    支持实时双向通信
    """
    
    def __init__(self, config: ChannelConfig):
        super().__init__(config)
        self.host = config.config.get("host", "0.0.0.0")
        self.port = config.config.get("port", 8765)
        self.connections: Dict[str, WebSocketConnection] = {}
        self.server = None
        self._running = False
    
    async def initialize(self) -> bool:
        """初始化 WebSocket 服务器"""
        try:
            # 动态导入 websockets 库
            import websockets
            
            async def handler(websocket, path):
                await self._handle_connection(websocket, path)
            
            self.server = await websockets.serve(
                handler,
                self.host,
                self.port,
                ping_interval=30,
                ping_timeout=10
            )
            
            self._running = True
            self._initialized = True
            
            print(f"[WebSocket] 服务器已启动：ws://{self.host}:{self.port}")
            return True
            
        except ImportError:
            print("[WebSocket] websockets 库未安装，请运行：pip install websockets")
            return False
        except Exception as e:
            print(f"[WebSocket] 初始化失败：{e}")
            return False
    
    async def shutdown(self):
        """关闭 WebSocket 服务器"""
        self._running = False
        
        # 关闭所有连接
        for conn in list(self.connections.values()):
            await conn.close()
        
        self.connections.clear()
        
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        
        print("[WebSocket] 服务器已关闭")
    
    async def _handle_connection(self, websocket, path):
        """处理 WebSocket 连接"""
        # 创建连接
        conn_id = f"conn_{len(self.connections) + 1}"
        connection = WebSocketConnection(websocket, conn_id)
        self.connections[conn_id] = connection
        
        print(f"[WebSocket] 新连接：{conn_id}")
        
        try:
            async for message in websocket:
                connection.last_active = datetime.now()
                
                # 解析消息
                try:
                    data = json.loads(message)
                    channel_message = ChannelMessage(
                        content=data.get("content", ""),
                        sender_id=data.get("sender_id", conn_id),
                        receiver_id=data.get("receiver_id", ""),
                        channel_type=self.channel_type,
                        metadata=data.get("metadata", {})
                    )
                    
                    # 处理消息
                    await self._handle_message(channel_message)
                    
                    # 发送确认
                    await connection.send({
                        "type": "ack",
                        "message_id": channel_message.id,
                        "status": "received"
                    })
                    
                except json.JSONDecodeError:
                    # 处理纯文本消息
                    channel_message = ChannelMessage(
                        content=message,
                        sender_id=conn_id,
                        channel_type=self.channel_type
                    )
                    await self._handle_message(channel_message)
                    
        except websockets.exceptions.ConnectionClosed:
            print(f"[WebSocket] 连接关闭：{conn_id}")
        except Exception as e:
            print(f"[WebSocket] 处理消息失败：{e}")
            await self._handle_error(e)
        finally:
            # 移除连接
            if conn_id in self.connections:
                del self.connections[conn_id]
            print(f"[WebSocket] 连接移除：{conn_id}")
    
    async def send_message(self, message: ChannelMessage) -> bool:
        """发送消息到指定连接"""
        target_id = message.receiver_id
        
        if not target_id or target_id not in self.connections:
            message.status = MessageStatus.FAILED
            message.error = "Connection not found"
            return False
        
        connection = self.connections[target_id]
        
        if connection.is_closed:
            message.status = MessageStatus.FAILED
            message.error = "Connection closed"
            return False
        
        # 发送消息
        success = await connection.send({
            "type": "message",
            "content": message.content,
            "sender_id": message.sender_id,
            "timestamp": message.timestamp.isoformat(),
            "metadata": message.metadata
        })
        
        message.status = MessageStatus.SENT if success else MessageStatus.FAILED
        return success
    
    async def broadcast(self, content: str, recipients: Optional[List[str]] = None) -> int:
        """广播消息"""
        sent_count = 0
        
        # 确定接收者
        if recipients:
            targets = [cid for cid in recipients if cid in self.connections]
        else:
            targets = list(self.connections.keys())
        
        # 发送给所有目标
        for target_id in targets:
            connection = self.connections[target_id]
            
            if connection.is_closed:
                continue
            
            message = ChannelMessage(
                content=content,
                sender_id="system",
                receiver_id=target_id,
                channel_type=self.channel_type
            )
            
            if await self.send_message(message):
                sent_count += 1
        
        return sent_count
    
    async def send_to_all(self, content: str) -> int:
        """发送给所有连接"""
        return await self.broadcast(content, None)
    
    def get_connection_count(self) -> int:
        """获取连接数"""
        return len(self.connections)
    
    def get_connection_info(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """获取连接信息"""
        if connection_id in self.connections:
            conn = self.connections[connection_id]
            return {
                "id": conn.connection_id,
                "created_at": conn.created_at.isoformat(),
                "last_active": conn.last_active.isoformat(),
                "is_closed": conn.is_closed,
                "metadata": conn.metadata
            }
        return None
    
    def list_connections(self) -> List[Dict[str, Any]]:
        """列出所有连接"""
        return [
            {
                "id": conn.connection_id,
                "created_at": conn.created_at.isoformat(),
                "last_active": conn.last_active.isoformat()
            }
            for conn in self.connections.values()
        ]


def create_websocket_channel(
    name: str = "websocket",
    host: str = "0.0.0.0",
    port: int = 8765,
    **kwargs
) -> WebSocketChannel:
    """
    创建 WebSocket 渠道的便捷函数
    """
    config = ChannelConfig(
        name=name,
        channel_type=ChannelType.WEBSOCKET,
        config={
            "host": host,
            "port": port,
            **kwargs
        }
    )
    
    return WebSocketChannel(config)
