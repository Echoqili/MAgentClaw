"""
AI 模型基类
定义所有模型的统一接口
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass
class Message:
    """消息类"""
    role: str  # system, user, assistant
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "role": self.role,
            "content": self.content,
            "metadata": self.metadata
        }


@dataclass
class ModelConfig:
    """模型配置类"""
    name: str
    provider: str
    model_name: str
    api_key: str = ""
    api_base: str = ""
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 30
    retry_times: int = 3
    context_window: int = 4096
    extra_config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelResponse:
    """模型响应类"""
    content: str
    role: str = "assistant"
    model: str = ""
    usage: Dict[str, int] = field(default_factory=lambda: {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0
    })
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def is_error(self) -> bool:
        """检查是否有错误"""
        return self.error is not None


class BaseModel(ABC):
    """
    AI 模型基类
    所有模型实现都必须继承此类
    """
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.name = config.name
        self.provider = config.provider
        self.model_name = config.model_name
        self._initialized = False
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        初始化模型
        返回是否成功
        """
        pass
    
    @abstractmethod
    async def chat(self, messages: List[Message]) -> ModelResponse:
        """
        聊天接口
        参数:
            messages: 消息列表
        返回:
            ModelResponse: 模型响应
        """
        pass
    
    @abstractmethod
    async def chat_stream(self, messages: List[Message]) -> AsyncGenerator[str, None]:
        """
        流式聊天接口
        参数:
            messages: 消息列表
        返回:
            AsyncGenerator: 响应文本流
        """
        pass
    
    @abstractmethod
    async def count_tokens(self, messages: List[Message]) -> int:
        """
        计算 token 数量
        参数:
            messages: 消息列表
        返回:
            int: token 数量
        """
        pass
    
    async def generate_response(
        self,
        system_prompt: str,
        user_message: str,
        history: Optional[List[Message]] = None
    ) -> ModelResponse:
        """
        生成响应的便捷方法
        参数:
            system_prompt: 系统提示
            user_message: 用户消息
            history: 历史消息（可选）
        返回:
            ModelResponse: 模型响应
        """
        messages = []
        
        # 添加系统消息
        if system_prompt:
            messages.append(Message(role="system", content=system_prompt))
        
        # 添加历史消息
        if history:
            messages.extend(history)
        
        # 添加用户消息
        messages.append(Message(role="user", content=user_message))
        
        # 调用聊天接口
        return await self.chat(messages)
    
    def validate_config(self) -> List[str]:
        """
        验证配置
        返回:
            List[str]: 错误列表
        """
        errors = []
        
        if not self.config.name:
            errors.append("Model name is required")
        
        if not self.config.provider:
            errors.append("Provider is required")
        
        if not self.config.model_name:
            errors.append("Model name is required")
        
        if self.config.temperature < 0 or self.config.temperature > 2:
            errors.append("Temperature must be between 0 and 2")
        
        if self.config.max_tokens <= 0:
            errors.append("Max tokens must be positive")
        
        return errors
    
    def get_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "name": self.name,
            "provider": self.provider,
            "model_name": self.model_name,
            "context_window": self.config.context_window,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "initialized": self._initialized
        }
