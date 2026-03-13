"""
轻量化分布式模块
"""

from typing import Any, Dict, List
from dataclasses import dataclass, field
import asyncio
import uuid


@dataclass
class NodeInfo:
    node_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    node_name: str = ""
    host: str = "localhost"
    port: int = 8000
    is_local: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


class SimpleClusterManager:
    def __init__(self, node_name: str, host: str = "localhost", port: int = 8000):
        self.node_name = node_name
        self.host = host
        self.port = port
        self._local_node = NodeInfo(node_name=node_name, host=host, port=port, is_local=True)
        self._peers: Dict[str, NodeInfo] = {}
        self._lock = asyncio.Lock()
    
    @property
    def local_node(self) -> NodeInfo:
        return self._local_node
    
    async def add_peer(self, node: NodeInfo):
        async with self._lock:
            self._peers[node.node_id] = node
    
    async def remove_peer(self, node_id: str):
        async with self._lock:
            self._peers.pop(node_id, None)
    
    async def get_all_nodes(self) -> List[NodeInfo]:
        async with self._lock:
            return [self._local_node] + list(self._peers.values())
    
    def get_statistics(self) -> Dict:
        return {
            "local_node": self.node_name,
            "peer_count": len(self._peers),
        }


class SimpleDataSync:
    def __init__(self):
        self._data: Dict[str, Any] = {}
        self._lock = asyncio.Lock()
    
    async def put(self, key: str, value: Any):
        async with self._lock:
            self._data[key] = value
    
    async def get(self, key: str, default: Any = None) -> Any:
        async with self._lock:
            return self._data.get(key, default)
    
    async def delete(self, key: str):
        async with self._lock:
            self._data.pop(key, None)
    
    async def keys(self, pattern: str = "*") -> List[str]:
        import fnmatch
        async with self._lock:
            return [k for k in self._data.keys() if fnmatch.fnmatch(k, pattern)]


__all__ = ["NodeInfo", "SimpleClusterManager", "SimpleDataSync"]
