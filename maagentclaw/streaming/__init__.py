"""
流式输出支持模块

提供实时流式输出能力，支持 Server-Sent Events (SSE)
"""

from typing import Dict, List, Optional, Any, AsyncGenerator, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import uuid
import asyncio


class StreamEventType(Enum):
    """流事件类型"""
    START = "start"
    MESSAGE = "message"
    CHUNK = "chunk"           # 文本块
    TOOL_CALL = "tool_call"   # 工具调用
    TOOL_RESULT = "tool_result"  # 工具结果
    THINKING = "thinking"     # 思考中
    COMPLETE = "complete"
    ERROR = "error"
    HEARTBEAT = "heartbeat"
    PROGRESS = "progress"


@dataclass
class StreamEvent:
    """流事件"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: StreamEventType = StreamEventType.MESSAGE
    content: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "type": self.type.value,
            "content": self.content,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }
    
    def to_sse(self) -> str:
        """转换为 SSE 格式"""
        return f"data: {json.dumps(self.to_dict(), ensure_ascii=False)}\n\n"
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'StreamEvent':
        """从字典创建"""
        return StreamEvent(
            id=data.get("id", str(uuid.uuid4())),
            type=StreamEventType(data.get("type", "message")),
            content=data.get("content"),
            data=data.get("data"),
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else datetime.now(),
            metadata=data.get("metadata", {})
        )


class StreamManager:
    """流管理器"""
    
    def __init__(self):
        self.active_streams: Dict[str, 'StreamSession'] = {}
        self._lock = asyncio.Lock()
    
    async def create_session(self, session_id: str) -> 'StreamSession':
        """创建流会话"""
        async with self._lock:
            session = StreamSession(session_id, self)
            self.active_streams[session_id] = session
            return session
    
    async def close_session(self, session_id: str):
        """关闭流会话"""
        async with self._lock:
            if session_id in self.active_streams:
                await self.active_streams[session_id].close()
                del self.active_streams[session_id]
    
    def get_session(self, session_id: str) -> Optional['StreamSession']:
        """获取流会话"""
        return self.active_streams.get(session_id)


class StreamSession:
    """流会话"""
    
    def __init__(self, session_id: str, manager: StreamManager):
        self.session_id = session_id
        self.manager = manager
        self.queues: Dict[str, asyncio.Queue] = {}
        self.active = True
        self.subscribers: List[Callable] = []
        self._lock = asyncio.Lock()
    
    async def subscribe(self, queue: asyncio.Queue):
        """订阅流"""
        async with self._lock:
            self.queues[str(uuid.uuid4())] = queue
    
    async def unsubscribe(self, queue_id: str):
        """取消订阅"""
        async with self._lock:
            if queue_id in self.queues:
                del self.queues[queue_id]
    
    async def emit(self, event: StreamEvent):
        """发送事件"""
        if not self.active:
            return
        
        async with self._lock:
            # 发送给所有订阅者
            for queue_id, queue in list(self.queues.items()):
                try:
                    await queue.put(event)
                except:
                    pass
            
            # 触发回调
            for callback in self.subscribers:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(event)
                    else:
                        callback(event)
                except:
                    pass
    
    async def emit_message(self, content: str, metadata: Optional[Dict] = None):
        """发送消息事件"""
        event = StreamEvent(
            type=StreamEventType.MESSAGE,
            content=content,
            metadata=metadata or {}
        )
        await self.emit(event)
    
    async def emit_chunk(self, chunk: str, chunk_index: int = 0):
        """发送文本块事件（用于流式输出）"""
        event = StreamEvent(
            type=StreamEventType.CHUNK,
            content=chunk,
            metadata={"index": chunk_index}
        )
        await self.emit(event)
    
    async def emit_start(self, task_id: str, description: str):
        """发送开始事件"""
        event = StreamEvent(
            type=StreamEventType.START,
            data={"task_id": task_id, "description": description}
        )
        await self.emit(event)
    
    async def emit_complete(self, task_id: str, result: Any):
        """发送完成事件"""
        event = StreamEvent(
            type=StreamEventType.COMPLETE,
            data={"task_id": task_id, "result": str(result) if result else None}
        )
        await self.emit(event)
    
    async def emit_error(self, error: str, task_id: Optional[str] = None):
        """发送错误事件"""
        event = StreamEvent(
            type=StreamEventType.ERROR,
            content=error,
            data={"task_id": task_id} if task_id else None
        )
        await self.emit(event)
    
    async def emit_progress(self, current: int, total: int, message: str = ""):
        """发送进度事件"""
        event = StreamEvent(
            type=StreamEventType.PROGRESS,
            data={
                "current": current,
                "total": total,
                "percentage": int(current / total * 100) if total > 0 else 0,
                "message": message
            }
        )
        await self.emit(event)
    
    async def emit_thinking(self, thinking: str):
        """发送思考中事件"""
        event = StreamEvent(
            type=StreamEventType.THINKING,
            content=thinking
        )
        await self.emit(event)
    
    async def emit_tool_call(self, tool_name: str, arguments: Dict[str, Any]):
        """发送工具调用事件"""
        event = StreamEvent(
            type=StreamEventType.TOOL_CALL,
            data={"tool_name": tool_name, "arguments": arguments}
        )
        await self.emit(event)
    
    async def emit_tool_result(self, tool_name: str, result: Any, success: bool = True):
        """发送工具结果事件"""
        event = StreamEvent(
            type=StreamEventType.TOOL_RESULT,
            data={
                "tool_name": tool_name,
                "result": str(result) if result else None,
                "success": success
            }
        )
        await self.emit(event)
    
    async def close(self):
        """关闭会话"""
        self.active = False
        async with self._lock:
            # 清空所有队列
            for queue in self.queues.values():
                await queue.put(None)  # 发送结束信号
            self.queues.clear()


class StreamingResponse:
    """流式响应生成器
    
    用于生成 SSE 格式的流式响应
    """
    
    def __init__(self, session: StreamSession):
        self.session = session
        self.queue: asyncio.Queue = asyncio.Queue()
    
    async def __aiter__(self):
        """异步迭代器"""
        await self.session.subscribe(self.queue)
        try:
            while self.session.active:
                event = await self.queue.get()
                if event is None:
                    break
                yield event.to_sse()
        finally:
            await self.session.unsubscribe(str(id(self.queue)))
    
    async def generate(self) -> AsyncGenerator[str, None]:
        """生成 SSE 流"""
        await self.session.subscribe(self.queue)
        try:
            while self.session.active:
                event = await self.queue.get()
                if event is None:
                    break
                yield event.to_sse()
        finally:
            await self.session.unsubscribe(str(id(self.queue)))


class StreamingAgentMixin:
    """流式输出 Agent 混入类
    
    用于给 Agent 添加流式输出能力
    """
    
    def __init__(self):
        self.stream_manager: Optional[StreamManager] = None
        self.current_stream: Optional[StreamSession] = None
    
    def set_stream_manager(self, manager: StreamManager):
        """设置流管理器"""
        self.stream_manager = manager
    
    async def start_stream(self, session_id: str) -> StreamSession:
        """开始流式输出"""
        if self.stream_manager is None:
            self.stream_manager = StreamManager()
        
        self.current_stream = await self.stream_manager.create_session(session_id)
        return self.current_stream
    
    async def stream_message(self, content: str):
        """流式输出消息"""
        if self.current_stream:
            await self.current_stream.emit_message(content)
    
    async def stream_chunk(self, chunk: str, index: int = 0):
        """流式输出文本块"""
        if self.current_stream:
            await self.current_stream.emit_chunk(chunk, index)
    
    async def stream_thinking(self, thinking: str):
        """流式输出思考内容"""
        if self.current_stream:
            await self.current_stream.emit_thinking(thinking)
    
    async def stream_tool_call(self, tool_name: str, arguments: Dict[str, Any]):
        """流式输出工具调用"""
        if self.current_stream:
            await self.current_stream.emit_tool_call(tool_name, arguments)
    
    async def stream_tool_result(self, tool_name: str, result: Any):
        """流式输出工具结果"""
        if self.current_stream:
            await self.current_stream.emit_tool_result(tool_name, result)
    
    async def end_stream(self):
        """结束流式输出"""
        if self.current_stream:
            await self.current_stream.close()
            self.current_stream = None


async def stream_text_generator(text: str, chunk_size: int = 10) -> AsyncGenerator[str, None]:
    """文本分块生成器
    
    将长文本分块流式输出
    """
    for i in range(0, len(text), chunk_size):
        chunk = text[i:i + chunk_size]
        event = StreamEvent(
            type=StreamEventType.CHUNK,
            content=chunk,
            metadata={"index": i // chunk_size, "total": len(text)}
        )
        yield event.to_sse()
        await asyncio.sleep(0.01)  # 小延迟，避免过快


async def stream_task_progress(
    current: int, 
    total: int, 
    callback: Optional[Callable] = None
) -> AsyncGenerator[str, None]:
    """任务进度生成器"""
    for i in range(current, total + 1):
        percentage = int(i / total * 100) if total > 0 else 0
        event = StreamEvent(
            type=StreamEventType.PROGRESS,
            data={
                "current": i,
                "total": total,
                "percentage": percentage
            }
        )
        yield event.to_sse()
        
        if callback:
            await callback(i, total)
        
        await asyncio.sleep(0.1)
