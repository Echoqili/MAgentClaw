"""
OpenAI GPT 模型实现
"""

import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
import json

from .base_model import BaseModel, ModelConfig, ModelResponse, Message


class OpenAIModel(BaseModel):
    """
    OpenAI GPT 模型实现
    支持 GPT-3.5, GPT-4, GPT-4o 等模型
    """
    
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.client = None
        self._stream_buffer = []
    
    async def initialize(self) -> bool:
        """初始化 OpenAI 客户端"""
        try:
            # 动态导入 openai 库
            import openai
            
            # 配置客户端
            self.client = openai.AsyncOpenAI(
                api_key=self.config.api_key or "",
                base_url=self.config.api_base or None,
                timeout=self.config.timeout
            )
            
            self._initialized = True
            print(f"[OpenAI] 模型 {self.model_name} 初始化成功")
            return True
            
        except ImportError:
            print("[OpenAI] openai 库未安装，请运行：pip install openai")
            return False
        except Exception as e:
            print(f"[OpenAI] 初始化失败：{e}")
            return False
    
    async def chat(self, messages: List[Message]) -> ModelResponse:
        """聊天接口"""
        if not self._initialized:
            return ModelResponse(
                content="",
                error="Model not initialized"
            )
        
        try:
            # 转换消息格式
            openai_messages = self._convert_messages(messages)
            
            # 调用 API
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=openai_messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                timeout=self.config.timeout
            )
            
            # 解析响应
            content = response.choices[0].message.content or ""
            
            return ModelResponse(
                content=content,
                role="assistant",
                model=self.model_name,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                } if response.usage else {}
            )
            
        except Exception as e:
            return ModelResponse(
                content="",
                error=f"OpenAI API error: {str(e)}"
            )
    
    async def chat_stream(self, messages: List[Message]) -> AsyncGenerator[str, None]:
        """流式聊天接口"""
        if not self._initialized:
            yield "Error: Model not initialized"
            return
        
        try:
            # 转换消息格式
            openai_messages = self._convert_messages(messages)
            
            # 调用流式 API
            stream = await self.client.chat.completions.create(
                model=self.model_name,
                messages=openai_messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                stream=True,
                timeout=self.config.timeout
            )
            
            # 处理流式响应
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    yield content
                    
        except Exception as e:
            yield f"Error: {str(e)}"
    
    async def count_tokens(self, messages: List[Message]) -> int:
        """计算 token 数量"""
        try:
            # 使用 tiktoken 库计算
            import tiktoken
            
            encoding = tiktoken.encoding_for_model(self.model_name)
            
            num_tokens = 0
            for message in messages:
                num_tokens += 4  # message format
                for key, value in message.to_dict().items():
                    if isinstance(value, str):
                        num_tokens += len(encoding.encode(value))
            
            num_tokens += 3  # assistant reply primer
            return num_tokens
            
        except Exception as e:
            print(f"[OpenAI] Token 计数失败：{e}")
            # 粗略估计：中文字符数 * 1.5
            total_chars = sum(len(m.content) for m in messages)
            return int(total_chars * 1.5)
    
    def _convert_messages(self, messages: List[Message]) -> List[Dict[str, str]]:
        """转换消息格式为 OpenAI 格式"""
        openai_messages = []
        
        for msg in messages:
            openai_message = {
                "role": msg.role,
                "content": msg.content
            }
            
            # 添加元数据（如果有）
            if msg.metadata:
                # 某些元数据可以添加到消息中
                if "name" in msg.metadata:
                    openai_message["name"] = msg.metadata["name"]
            
            openai_messages.append(openai_message)
        
        return openai_messages


# 预定义的 OpenAI 模型配置
OPENAI_MODELS = {
    "gpt-3.5-turbo": {
        "context_window": 4096,
        "max_tokens": 4096
    },
    "gpt-4": {
        "context_window": 8192,
        "max_tokens": 8192
    },
    "gpt-4-turbo": {
        "context_window": 128000,
        "max_tokens": 4096
    },
    "gpt-4o": {
        "context_window": 128000,
        "max_tokens": 4096
    },
    "gpt-4o-mini": {
        "context_window": 128000,
        "max_tokens": 16384
    }
}


def create_openai_model(
    model_name: str = "gpt-3.5-turbo",
    api_key: str = "",
    api_base: str = "",
    temperature: float = 0.7,
    **kwargs
) -> OpenAIModel:
    """
    创建 OpenAI 模型的便捷函数
    """
    # 获取模型配置
    model_config = OPENAI_MODELS.get(model_name, {})
    
    config = ModelConfig(
        name=f"openai/{model_name}",
        provider="openai",
        model_name=model_name,
        api_key=api_key,
        api_base=api_base,
        temperature=temperature,
        context_window=model_config.get("context_window", 4096),
        max_tokens=model_config.get("max_tokens", 4096),
        extra_config=kwargs
    )
    
    return OpenAIModel(config)
