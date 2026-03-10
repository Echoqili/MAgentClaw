"""
阿里云通义千问（Qwen）模型实现
"""

import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
import json

from .base_model import BaseModel, ModelConfig, ModelResponse, Message


class QwenModel(BaseModel):
    """
    阿里云通义千问模型实现
    使用 DashScope API
    """
    
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.client = None
        self._api_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    
    async def initialize(self) -> bool:
        """初始化 Qwen 客户端"""
        try:
            # 动态导入 dashscope 库
            import dashscope
            
            # 配置 API key
            dashscope.api_key = self.config.api_key or ""
            
            if self.config.api_base:
                self._api_url = self.config.api_base
            
            self._initialized = True
            print(f"[Qwen] 模型 {self.model_name} 初始化成功")
            return True
            
        except ImportError:
            print("[Qwen] dashscope 库未安装，请运行：pip install dashscope")
            return False
        except Exception as e:
            print(f"[Qwen] 初始化失败：{e}")
            return False
    
    async def chat(self, messages: List[Message]) -> ModelResponse:
        """聊天接口"""
        if not self._initialized:
            return ModelResponse(
                content="",
                error="Model not initialized"
            )
        
        try:
            # 导入 dashscope
            from dashscope import Generation
            
            # 转换消息格式
            qwen_messages = self._convert_messages(messages)
            
            # 调用 API
            response = await asyncio.to_thread(
                Generation.call,
                model=self.model_name,
                messages=qwen_messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                result_format='message'
            )
            
            # 检查响应
            if response.status_code == 200:
                content = response.output.choices[0].message.content
                return ModelResponse(
                    content=content,
                    role="assistant",
                    model=self.model_name,
                    usage=response.usage if hasattr(response, 'usage') else {}
                )
            else:
                return ModelResponse(
                    content="",
                    error=f"Qwen API error: {response.code} - {response.message}"
                )
            
        except Exception as e:
            return ModelResponse(
                content="",
                error=f"Qwen API error: {str(e)}"
            )
    
    async def chat_stream(self, messages: List[Message]) -> AsyncGenerator[str, None]:
        """流式聊天接口"""
        if not self._initialized:
            yield "Error: Model not initialized"
            return
        
        try:
            # 导入 dashscope
            from dashscope import Generation
            
            # 转换消息格式
            qwen_messages = self._convert_messages(messages)
            
            # 调用流式 API
            responses = Generation.call(
                model=self.model_name,
                messages=qwen_messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                stream=True,
                result_format='message'
            )
            
            # 处理流式响应
            for response in responses:
                if response.status_code == 200:
                    content = response.output.choices[0].message.content
                    if content:
                        yield content
                else:
                    yield f"Error: {response.code} - {response.message}"
                    
        except Exception as e:
            yield f"Error: {str(e)}"
    
    async def count_tokens(self, messages: List[Message]) -> int:
        """计算 token 数量"""
        try:
            # 使用 dashscope 的 token 计数
            import dashscope
            
            # 转换消息
            qwen_messages = self._convert_messages(messages)
            
            # 调用计数 API
            response = dashscope.Tokenization.count(
                model=self.model_name,
                messages=qwen_messages
            )
            
            if response.status_code == 200:
                return response.usage.total_tokens
            else:
                # 粗略估计
                total_chars = sum(len(m.content) for m in messages)
                return int(total_chars * 1.2)
            
        except Exception as e:
            print(f"[Qwen] Token 计数失败：{e}")
            # 粗略估计：中文字符数 * 1.2
            total_chars = sum(len(m.content) for m in messages)
            return int(total_chars * 1.2)
    
    def _convert_messages(self, messages: List[Message]) -> List[Dict[str, str]]:
        """转换消息格式为 Qwen 格式"""
        qwen_messages = []
        
        for msg in messages:
            qwen_message = {
                "role": msg.role,
                "content": msg.content
            }
            qwen_messages.append(qwen_message)
        
        return qwen_messages


# 预定义的 Qwen 模型配置
QWEN_MODELS = {
    "qwen-turbo": {
        "context_window": 8000,
        "max_tokens": 2000
    },
    "qwen-plus": {
        "context_window": 32000,
        "max_tokens": 2000
    },
    "qwen-max": {
        "context_window": 32000,
        "max_tokens": 2000
    },
    "qwen-max-longcontext": {
        "context_window": 28000,
        "max_tokens": 2000
    }
}


def create_qwen_model(
    model_name: str = "qwen-turbo",
    api_key: str = "",
    temperature: float = 0.7,
    **kwargs
) -> QwenModel:
    """
    创建 Qwen 模型的便捷函数
    """
    # 获取模型配置
    model_config = QWEN_MODELS.get(model_name, {})
    
    config = ModelConfig(
        name=f"qwen/{model_name}",
        provider="qwen",
        model_name=model_name,
        api_key=api_key,
        temperature=temperature,
        context_window=model_config.get("context_window", 8000),
        max_tokens=model_config.get("max_tokens", 2000),
        extra_config=kwargs
    )
    
    return QwenModel(config)
