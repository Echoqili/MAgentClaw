"""
示例 Agent 实现
演示如何创建具体的 Agent
"""

import asyncio
from typing import Any, Dict, Optional

from ..core.agent import BaseAgent, AgentConfig, AgentMessage


class SimpleAgent(BaseAgent):
    """简单示例 Agent"""
    
    async def initialize(self) -> bool:
        """初始化 Agent"""
        print(f"Initializing SimpleAgent: {self.config.name}")
        # 在这里初始化模型、工具等
        return True
    
    async def process(self, message: AgentMessage) -> AgentMessage:
        """处理消息"""
        self.add_to_memory(message)
        
        # 简单的响应逻辑
        response_text = f"[{self.config.name}] 收到消息：{message.content}"
        
        if "你好" in message.content or "hello" in message.content.lower():
            response_text = f"你好！我是 {self.config.name}，{self.config.role}。有什么可以帮助你的吗？"
        elif "任务" in message.content or "task" in message.content.lower():
            response_text = f"我当前的任务是：{self.state.current_task or '暂无任务'}"
        elif "状态" in message.content or "status" in message.content.lower():
            response_text = f"我的状态：{self.state.status}"
        
        response = AgentMessage(
            content=response_text,
            role="assistant"
        )
        
        self.add_to_memory(response)
        return response
    
    async def execute_task(self, task: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """执行任务"""
        self.state.current_task = task
        
        # 模拟任务执行
        await asyncio.sleep(1)
        
        result = {
            "task": task,
            "status": "completed",
            "agent": self.config.name,
            "context": context
        }
        
        self.state.current_task = None
        return result


class TaskAgent(BaseAgent):
    """任务执行 Agent"""
    
    async def initialize(self) -> bool:
        """初始化 Agent"""
        print(f"Initializing TaskAgent: {self.config.name}")
        return True
    
    async def process(self, message: AgentMessage) -> AgentMessage:
        """处理消息"""
        self.add_to_memory(message)
        
        # 分析消息并决定行动
        content = message.content.lower()
        
        if "创建" in content or "create" in content:
            response_text = f"正在创建任务：{message.content}"
        elif "执行" in content or "execute" in content:
            response_text = f"正在执行任务：{message.content}"
        elif "完成" in content or "complete" in content:
            response_text = f"任务已完成：{message.content}"
        else:
            response_text = f"收到指令：{message.content}，正在处理..."
        
        response = AgentMessage(
            content=response_text,
            role="assistant"
        )
        
        self.add_to_memory(response)
        return response
    
    async def execute_task(self, task: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """执行任务"""
        self.state.current_task = task
        
        try:
            # 模拟任务执行步骤
            steps = [
                "分析任务需求",
                "制定执行计划",
                "执行任务",
                "验证结果"
            ]
            
            for step in steps:
                print(f"[{self.config.name}] {step}")
                await asyncio.sleep(0.5)
            
            result = {
                "task": task,
                "status": "completed",
                "agent": self.config.name,
                "steps_completed": steps,
                "context": context
            }
            
        except Exception as e:
            result = {
                "task": task,
                "status": "failed",
                "agent": self.config.name,
                "error": str(e)
            }
        
        finally:
            self.state.current_task = None
        
        return result


class CoordinatorAgent(BaseAgent):
    """协调器 Agent - 负责协调多个 Agent"""
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.worker_agents = []
    
    def register_worker(self, agent_name: str):
        """注册工作 Agent"""
        self.worker_agents.append(agent_name)
    
    async def initialize(self) -> bool:
        """初始化 Agent"""
        print(f"Initializing CoordinatorAgent: {self.config.name}")
        return True
    
    async def process(self, message: AgentMessage) -> AgentMessage:
        """处理消息"""
        self.add_to_memory(message)
        
        # 协调器逻辑
        if "分配" in message.content or "assign" in message.content.lower():
            response_text = f"正在分配任务给工作 Agent：{self.worker_agents}"
        elif "状态" in message.content or "status" in message.content.lower():
            response_text = f"协调器状态：{self.state.status}，工作 Agent 数量：{len(self.worker_agents)}"
        else:
            response_text = f"协调器收到：{message.content}"
        
        response = AgentMessage(
            content=response_text,
            role="assistant"
        )
        
        self.add_to_memory(response)
        return response
    
    async def execute_task(self, task: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """执行协调任务"""
        self.state.current_task = task
        
        result = {
            "task": task,
            "status": "coordinating",
            "agent": self.config.name,
            "workers": self.worker_agents,
            "context": context
        }
        
        self.state.current_task = None
        return result
