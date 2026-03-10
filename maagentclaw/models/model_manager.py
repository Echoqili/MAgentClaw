"""
模型管理器
管理多个 AI 模型，提供路由和回退机制
"""

from typing import Dict, List, Optional, Any
from .base_model import BaseModel, ModelConfig, ModelResponse, Message


class ModelManager:
    """
    AI 模型管理器
    支持多模型注册、路由和自动回退
    """
    
    def __init__(self):
        self.models: Dict[str, BaseModel] = {}
        self.default_model: Optional[str] = None
        self.model_order: List[str] = []  # 模型优先级列表
    
    def register_model(self, model: BaseModel, set_default: bool = False):
        """
        注册模型
        参数:
            model: 模型实例
            set_default: 是否设为默认模型
        """
        self.models[model.name] = model
        self.model_order.append(model.name)
        
        if set_default or not self.default_model:
            self.default_model = model.name
        
        print(f"[ModelManager] 注册模型：{model.name}")
    
    def unregister_model(self, model_name: str):
        """注销模型"""
        if model_name in self.models:
            del self.models[model_name]
            if model_name in self.model_order:
                self.model_order.remove(model_name)
            
            if self.default_model == model_name:
                self.default_model = self.model_order[0] if self.model_order else None
            
            print(f"[ModelManager] 注销模型：{model_name}")
    
    def get_model(self, model_name: Optional[str] = None) -> Optional[BaseModel]:
        """
        获取模型
        参数:
            model_name: 模型名称，None 则返回默认模型
        """
        name = model_name or self.default_model
        
        if not name:
            print("[ModelManager] 没有可用的模型")
            return None
        
        if name not in self.models:
            print(f"[ModelManager] 模型不存在：{name}")
            return None
        
        return self.models[name]
    
    def set_default_model(self, model_name: str):
        """设置默认模型"""
        if model_name in self.models:
            self.default_model = model_name
            print(f"[ModelManager] 设置默认模型：{model_name}")
        else:
            print(f"[ModelManager] 模型不存在，无法设置默认：{model_name}")
    
    def set_model_priority(self, model_names: List[str]):
        """
        设置模型优先级
        参数:
            model_names: 模型名称列表（按优先级排序）
        """
        # 验证所有模型都存在
        for name in model_names:
            if name not in self.models:
                print(f"[ModelManager] 模型不存在，跳过：{name}")
                return
        
        self.model_order = model_names
        print(f"[ModelManager] 设置模型优先级：{model_names}")
    
    async def chat(
        self,
        messages: List[Message],
        model_name: Optional[str] = None,
        use_fallback: bool = True
    ) -> ModelResponse:
        """
        聊天接口（支持自动回退）
        参数:
            messages: 消息列表
            model_name: 模型名称，None 则使用默认模型
            use_fallback: 是否启用回退机制
        返回:
            ModelResponse: 模型响应
        """
        # 获取模型
        model = self.get_model(model_name)
        
        if not model:
            return ModelResponse(
                content="",
                error="No available model"
            )
        
        # 尝试使用主模型
        response = await model.chat(messages)
        
        # 如果成功，直接返回
        if not response.is_error:
            return response
        
        # 如果不启用回退，返回错误
        if not use_fallback:
            return response
        
        # 尝试回退到其他模型
        print(f"[ModelManager] 模型 {model.name} 失败，尝试回退...")
        
        for fallback_name in self.model_order:
            if fallback_name == model.name:
                continue
            
            fallback_model = self.models[fallback_name]
            print(f"[ModelManager] 尝试回退到：{fallback_name}")
            
            response = await fallback_model.chat(messages)
            
            if not response.is_error:
                print(f"[ModelManager] 回退到 {fallback_name} 成功")
                return response
        
        # 所有模型都失败
        print("[ModelManager] 所有模型都失败")
        return response
    
    async def chat_stream(
        self,
        messages: List[Message],
        model_name: Optional[str] = None
    ):
        """
        流式聊天接口
        参数:
            messages: 消息列表
            model_name: 模型名称
        """
        model = self.get_model(model_name)
        
        if not model:
            yield "Error: No available model"
            return
        
        async for chunk in model.chat_stream(messages):
            yield chunk
    
    def list_models(self) -> List[Dict[str, Any]]:
        """列出所有已注册的模型"""
        return [
            {
                "name": model.name,
                "provider": model.provider,
                "model_name": model.model_name,
                "initialized": model._initialized,
                "is_default": model.name == self.default_model
            }
            for model in self.models.values()
        ]
    
    def get_model_info(self, model_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """获取模型信息"""
        model = self.get_model(model_name)
        
        if not model:
            return None
        
        return model.get_info()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取管理器统计信息"""
        return {
            "total_models": len(self.models),
            "default_model": self.default_model,
            "model_order": self.model_order,
            "models": self.list_models()
        }


# 便捷的模型创建函数
def create_model_from_config(config: ModelConfig) -> Optional[BaseModel]:
    """
    从配置创建模型
    参数:
        config: 模型配置
    返回:
        BaseModel: 模型实例
    """
    if config.provider.lower() == "openai":
        from .openai_model import OpenAIModel
        return OpenAIModel(config)
    
    elif config.provider.lower() == "qwen":
        from .qwen_model import QwenModel
        return QwenModel(config)
    
    # 可以添加更多 provider...
    
    else:
        print(f"[ModelManager] 不支持的 provider: {config.provider}")
        return None
