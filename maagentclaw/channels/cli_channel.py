"""
CLI 渠道实现
支持命令行交互
"""

import asyncio
import sys
from typing import Dict, Any, Optional, List
from datetime import datetime

from .base_channel import BaseChannel, ChannelConfig, ChannelMessage, ChannelType, MessageStatus


class CLIChannel(BaseChannel):
    """
    CLI 渠道实现
    支持命令行交互
    """
    
    def __init__(self, config: ChannelConfig):
        super().__init__(config)
        self.prompt = config.config.get("prompt", "You: ")
        self.show_timestamp = config.config.get("show_timestamp", True)
        self._running = False
        self._task = None
    
    async def initialize(self) -> bool:
        """初始化 CLI"""
        try:
            self._initialized = True
            self._running = True
            
            print(f"[CLI] 渠道已初始化")
            print(f"[CLI] 提示符：{self.prompt}")
            print(f"[CLI] 输入 'quit' 或 'exit' 退出")
            
            # 启动读取任务
            self._task = asyncio.create_task(self._read_input())
            
            return True
            
        except Exception as e:
            print(f"[CLI] 初始化失败：{e}")
            return False
    
    async def shutdown(self):
        """关闭 CLI"""
        self._running = False
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        print("[CLI] 渠道已关闭")
    
    async def _read_input(self):
        """读取用户输入"""
        loop = asyncio.get_event_loop()
        
        while self._running:
            try:
                # 读取输入
                user_input = await loop.run_in_executor(
                    None, input, self.prompt
                )
                
                # 检查退出命令
                if user_input.lower() in ['quit', 'exit', 'q']:
                    self._running = False
                    break
                
                # 创建消息
                message = ChannelMessage(
                    content=user_input,
                    sender_id="cli_user",
                    channel_type=self.channel_type,
                    metadata={
                        "timestamp": datetime.now().isoformat() if self.show_timestamp else None
                    }
                )
                
                # 处理消息
                await self._handle_message(message)
                
            except EOFError:
                # 处理 Ctrl+D
                self._running = False
                break
            except Exception as e:
                print(f"[CLI] 读取输入失败：{e}")
                await asyncio.sleep(1)
    
    async def send_message(self, message: ChannelMessage) -> bool:
        """发送消息到 CLI"""
        try:
            # 显示消息
            if self.show_timestamp:
                timestamp = message.timestamp.strftime("%H:%M:%S")
                print(f"[{timestamp}] {message.content}")
            else:
                print(message.content)
            
            message.status = MessageStatus.DELIVERED
            return True
            
        except Exception as e:
            print(f"[CLI] 发送消息失败：{e}")
            message.status = MessageStatus.FAILED
            return False
    
    async def broadcast(self, content: str, recipients: Optional[List[str]] = None) -> int:
        """广播消息到 CLI"""
        # CLI 只有一个用户
        message = ChannelMessage(
            content=content,
            sender_id="system",
            channel_type=self.channel_type
        )
        
        return 1 if await self.send_message(message) else 0
    
    def set_prompt(self, prompt: str):
        """设置提示符"""
        self.prompt = prompt
    
    def enable_timestamp(self, enable: bool):
        """启用/禁用时间戳"""
        self.show_timestamp = enable


def create_cli_channel(
    name: str = "cli",
    prompt: str = "You: ",
    show_timestamp: bool = True,
    **kwargs
) -> CLIChannel:
    """
    创建 CLI 渠道的便捷函数
    """
    config = ChannelConfig(
        name=name,
        channel_type=ChannelType.CLI,
        config={
            "prompt": prompt,
            "show_timestamp": show_timestamp,
            **kwargs
        }
    )
    
    return CLIChannel(config)
