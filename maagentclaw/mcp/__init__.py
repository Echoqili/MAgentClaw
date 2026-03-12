"""
MCP (Model Context Protocol) 支持模块

提供 MCP 协议的工具和资源管理能力
"""

from typing import Dict, List, Optional, Any, Callable, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
import asyncio
import json


class MCPMessageType(Enum):
    """MCP 消息类型"""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"


class MCPMethod(Enum):
    """MCP 方法"""
    # 工具相关
    TOOLS_LIST = "tools/list"
    TOOLS_CALL = "tools/call"
    
    # 资源相关
    RESOURCES_LIST = "resources/list"
    RESOURCES_READ = "resources/read"
    RESOURCES_SUBSCRIBE = "resources/subscribe"
    
    # 提示相关
    PROMPTS_LIST = "prompts/list"
    PROMPTS_GET = "prompts/get"
    
    # 采样
    SAMPLING_CREATE_MESSAGE = "sampling/createMessage"
    
    # 工具定义
    TOOLS_DEFINITION = "tools/definition"


@dataclass
class MCPTool:
    """MCP 工具"""
    name: str = ""
    description: str = ""
    input_schema: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema
        }


@dataclass
class MCPResource:
    """MCP 资源"""
    uri: str = ""
    name: str = ""
    description: str = ""
    mime_type: str = "text/plain"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "uri": self.uri,
            "name": self.name,
            "description": self.description,
            "mimeType": self.mime_type
        }


@dataclass
class MCPPrompt:
    """MCP 提示"""
    name: str = ""
    description: str = ""
    arguments: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "arguments": self.arguments
        }


@dataclass
class MCPMessage:
    """MCP 消息"""
    jsonrpc: str = "2.0"
    id: Optional[str] = None
    method: str = ""
    params: Optional[Dict[str, Any]] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = {"jsonrpc": self.jsonrpc}
        
        if self.id is not None:
            data["id"] = self.id
        
        if self.method:
            data["method"] = self.method
        
        if self.params is not None:
            data["params"] = self.params
        
        if self.result is not None:
            data["result"] = self.result
        
        if self.error is not None:
            data["error"] = self.error
        
        return data
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'MCPMessage':
        return MCPMessage(
            jsonrpc=data.get("jsonrpc", "2.0"),
            id=data.get("id"),
            method=data.get("method", ""),
            params=data.get("params"),
            result=data.get("result"),
            error=data.get("error")
        )


class MCPToolHandler:
    """MCP 工具处理器"""
    
    def __init__(self):
        self.tools: Dict[str, Callable] = {}
        self.tool_definitions: Dict[str, MCPTool] = {}
    
    def register_tool(
        self,
        name: str,
        handler: Callable,
        description: str = "",
        input_schema: Optional[Dict[str, Any]] = None
    ):
        """注册工具"""
        self.tools[name] = handler
        
        self.tool_definitions[name] = MCPTool(
            name=name,
            description=description,
            input_schema=input_schema or {
                "type": "object",
                "properties": {}
            }
        )
    
    def unregister_tool(self, name: str):
        """注销工具"""
        if name in self.tools:
            del self.tools[name]
        if name in self.tool_definitions:
            del self.tool_definitions[name]
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """调用工具"""
        if name not in self.tools:
            raise ValueError(f"Tool {name} not found")
        
        handler = self.tools[name]
        
        if asyncio.iscoroutinefunction(handler):
            return await handler(**arguments)
        else:
            return handler(**arguments)
    
    def list_tools(self) -> List[MCPTool]:
        """列出所有工具"""
        return list(self.tool_definitions.values())


class MCPResourceHandler:
    """MCP 资源处理器"""
    
    def __init__(self):
        self.resources: Dict[str, MCPResource] = {}
        self.resource_handlers: Dict[str, Callable] = {}
    
    def register_resource(
        self,
        uri: str,
        handler: Callable,
        name: str = "",
        description: str = "",
        mime_type: str = "text/plain"
    ):
        """注册资源"""
        self.resources[uri] = MCPResource(
            uri=uri,
            name=name or uri,
            description=description,
            mime_type=mime_type
        )
        self.resource_handlers[uri] = handler
    
    def unregister_resource(self, uri: str):
        """注销资源"""
        if uri in self.resources:
            del self.resources[uri]
        if uri in self.resource_handlers:
            del self.resource_handlers[uri]
    
    async def read_resource(self, uri: str) -> Optional[str]:
        """读取资源"""
        if uri not in self.resource_handlers:
            return None
        
        handler = self.resource_handlers[uri]
        
        if asyncio.iscoroutinefunction(handler):
            return await handler()
        else:
            return handler()
    
    def list_resources(self) -> List[MCPResource]:
        """列出所有资源"""
        return list(self.resources.values())


class MCPPromptHandler:
    """MCP 提示处理器"""
    
    def __init__(self):
        self.prompts: Dict[str, Callable] = {}
        self.prompt_definitions: Dict[str, MCPPrompt] = {}
    
    def register_prompt(
        self,
        name: str,
        handler: Callable,
        description: str = "",
        arguments: Optional[List[Dict[str, Any]]] = None
    ):
        """注册提示"""
        self.prompts[name] = handler
        
        self.prompt_definitions[name] = MCPPrompt(
            name=name,
            description=description,
            arguments=arguments or []
        )
    
    async def get_prompt(self, name: str, arguments: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """获取提示"""
        if name not in self.prompts:
            return None
        
        handler = self.prompts[name]
        args = arguments or {}
        
        if asyncio.iscoroutinefunction(handler):
            return await handler(**args)
        else:
            return handler(**args)
    
    def list_prompts(self) -> List[MCPPrompt]:
        """列出所有提示"""
        return list(self.prompt_definitions.values())


class MCPClient:
    """MCP 客户端"""
    
    def __init__(self, server_url: str = ""):
        self.server_url = server_url
        self.session_id: Optional[str] = None
        
        self.tool_handler = MCPToolHandler()
        self.resource_handler = MCPResourceHandler()
        self.prompt_handler = MCPPromptHandler()
        
        self._connected = False
    
    async def connect(self, server_url: Optional[str] = None):
        """连接到 MCP 服务器"""
        if server_url:
            self.server_url = server_url
        
        # 实际连接逻辑需要根据服务器类型实现
        # 这里简化处理
        self._connected = True
        self.session_id = str(uuid.uuid4())
    
    async def disconnect(self):
        """断开连接"""
        self._connected = False
        self.session_id = None
    
    @property
    def is_connected(self) -> bool:
        return self._connected
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """列出工具"""
        tools = self.tool_handler.list_tools()
        return [tool.to_dict() for tool in tools]
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """调用工具"""
        return await self.tool_handler.call_tool(name, arguments)
    
    async def list_resources(self) -> List[Dict[str, Any]]:
        """列出资源"""
        resources = self.resource_handler.list_resources()
        return [resource.to_dict() for resource in resources]
    
    async def read_resource(self, uri: str) -> Optional[str]:
        """读取资源"""
        return await self.resource_handler.read_resource(uri)
    
    async def list_prompts(self) -> List[Dict[str, Any]]:
        """列出提示"""
        prompts = self.prompt_handler.list_prompts()
        return [prompt.to_dict() for prompt in prompts]
    
    async def get_prompt(self, name: str, arguments: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """获取提示"""
        return await self.prompt_handler.get_prompt(name, arguments)


class MCPServer:
    """MCP 服务器"""
    
    def __init__(self, name: str = "MAgentClaw Server"):
        self.name = name
        self.version = "1.0.0"
        
        self.tool_handler = MCPToolHandler()
        self.resource_handler = MCPResourceHandler()
        self.prompt_handler = MCPPromptHandler()
        
        self.capabilities = {
            "tools": {"listChanged": True},
            "resources": {"subscribe": True, "listChanged": True},
            "prompts": {"listChanged": True}
        }
    
    def get_server_info(self) -> Dict[str, Any]:
        """获取服务器信息"""
        return {
            "name": self.name,
            "version": self.version,
            "capabilities": self.capabilities
        }
    
    async def handle_message(self, message: MCPMessage) -> MCPMessage:
        """处理 MCP 消息"""
        try:
            method = message.method
            
            if method == MCPMethod.TOOLS_LIST.value:
                tools = self.tool_handler.list_tools()
                return MCPMessage(
                    id=message.id,
                    result={
                        "tools": [tool.to_dict() for tool in tools]
                    }
                )
            
            elif method == MCPMethod.TOOLS_CALL.value:
                params = message.params or {}
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                
                result = await self.tool_handler.call_tool(tool_name, arguments)
                
                return MCPMessage(
                    id=message.id,
                    result={"content": [{"type": "text", "text": str(result)}]}
                )
            
            elif method == MCPMethod.RESOURCES_LIST.value:
                resources = self.resource_handler.list_resources()
                return MCPMessage(
                    id=message.id,
                    result={
                        "resources": [resource.to_dict() for resource in resources]
                    }
                )
            
            elif method == MCPMethod.RESOURCES_READ.value:
                params = message.params or {}
                uri = params.get("uri")
                
                content = await self.resource_handler.read_resource(uri)
                
                return MCPMessage(
                    id=message.id,
                    result={
                        "contents": [{
                            "uri": uri,
                            "mimeType": "text/plain",
                            "text": content or ""
                        }]
                    }
                )
            
            elif method == MCPMethod.PROMPTS_LIST.value:
                prompts = self.prompt_handler.list_prompts()
                return MCPMessage(
                    id=message.id,
                    result={
                        "prompts": [prompt.to_dict() for prompt in prompts]
                    }
                )
            
            elif method == MCPMethod.PROMPTS_GET.value:
                params = message.params or {}
                name = params.get("name")
                arguments = params.get("arguments", {})
                
                content = await self.prompt_handler.get_prompt(name, arguments)
                
                return MCPMessage(
                    id=message.id,
                    result={
                        "messages": [{
                            "role": "user",
                            "content": {"type": "text", "text": content or ""}
                        }]
                    }
                )
            
            else:
                return MCPMessage(
                    id=message.id,
                    error={
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                )
        
        except Exception as e:
            return MCPMessage(
                id=message.id,
                error={
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            )
    
    async def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理请求"""
        message = MCPMessage.from_dict(request_data)
        response = await self.handle_message(message)
        return response.to_dict()


class MCPIntegration:
    """MCP 集成管理器
    
    用于集成多个 MCP 服务器和工具
    """
    
    def __init__(self):
        self.servers: Dict[str, MCPClient] = {}
        self.local_server = MCPServer()
        
        # 本地工具注册
        self.local_server.tool_handler.register_tool(
            "search_memory",
            self._search_memory,
            "搜索记忆",
            {"type": "object", "properties": {"query": {"type": "string"}}}
        )
        
        self.local_server.tool_handler.register_tool(
            "get_agent_status",
            self._get_agent_status,
            "获取 Agent 状态",
            {"type": "object", "properties": {"agent_name": {"type": "string"}}}
        )
    
    async def connect_server(self, name: str, server_url: str):
        """连接 MCP 服务器"""
        client = MCPClient(server_url)
        await client.connect()
        self.servers[name] = client
    
    async def disconnect_server(self, name: str):
        """断开 MCP 服务器"""
        if name in self.servers:
            await self.servers[name].disconnect()
            del self.servers[name]
    
    async def list_all_tools(self) -> List[Dict[str, Any]]:
        """列出所有工具"""
        tools = await self.local_server.tool_handler.list_tools()
        result = [tool.to_dict() for tool in tools]
        
        for name, server in self.servers.items():
            if server.is_connected:
                server_tools = await server.list_tools()
                for tool in server_tools:
                    tool["server"] = name
                    result.append(tool)
        
        return result
    
    async def call_tool(self, name: str, arguments: Dict[str, Any], server: Optional[str] = None) -> Any:
        """调用工具"""
        if server and server in self.servers:
            return await self.servers[server].call_tool(name, arguments)
        
        # 优先使用本地工具
        if name in self.local_server.tool_handler.tools:
            return await self.local_server.tool_handler.call_tool(name, arguments)
        
        # 尝试在远程服务器中查找
        for server_name, server in self.servers.items():
            if server.is_connected:
                try:
                    return await server.call_tool(name, arguments)
                except:
                    continue
        
        raise ValueError(f"Tool {name} not found")
    
    async def _search_memory(self, query: str) -> str:
        """搜索记忆（示例工具）"""
        return f"搜索记忆: {query}"
    
    async def _get_agent_status(self, agent_name: str) -> str:
        """获取 Agent 状态（示例工具）"""
        return f"Agent {agent_name} 状态: 运行中"
