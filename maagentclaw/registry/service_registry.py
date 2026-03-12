"""
Nacos 风格的服务注册中心

将每个 Agent 作为一个服务进行注册、发现和管理
支持服务心跳健康检查、服务分组、负载均衡
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import uuid
import asyncio


class ServiceStatus(Enum):
    """服务状态"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    STARTING = "starting"
    STOPPED = "stopped"


class ServiceWeightStrategy(Enum):
    """权重策略"""
    RANDOM = "random"
    ROUND_ROBIN = "round_robin"
    WEIGHTED = "weighted"
    LEAST_CONNECTIONS = "least_connections"


@dataclass
class ServiceInstance:
    """服务实例（对应一个 Agent）"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    service_name: str = ""
    ip: str = "localhost"
    port: int = 8000
    
    # Agent 信息
    agent_name: str = ""
    agent_type: str = ""
    role: str = ""
    
    # 状态
    status: ServiceStatus = ServiceStatus.STARTING
    weight: int = 100
    enabled: bool = True
    
    # 健康检查
    healthy: bool = True
    last_heartbeat: datetime = field(default_factory=datetime.now)
    heartbeat_interval: int = 30  # 秒
    heartbeat_timeout: int = 90   # 秒
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 统计
    request_count: int = 0
    success_count: int = 0
    fail_count: int = 0
    avg_response_time: float = 0.0
    
    # 时间
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def is_healthy(self) -> bool:
        """检查是否健康"""
        if not self.enabled or self.status == ServiceStatus.STOPPED:
            return False
        
        # 检查心跳超时
        elapsed = (datetime.now() - self.last_heartbeat).total_seconds()
        return elapsed < self.heartbeat_timeout
    
    def heartbeat(self):
        """更新心跳"""
        self.last_heartbeat = datetime.now()
        self.healthy = True
    
    def record_request(self, success: bool, response_time: float):
        """记录请求"""
        self.request_count += 1
        if success:
            self.success_count += 1
        else:
            self.fail_count += 1
        
        # 更新平均响应时间
        if self.request_count > 0:
            self.avg_response_time = (
                (self.avg_response_time * (self.request_count - 1) + response_time) 
                / self.request_count
            )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "service_name": self.service_name,
            "ip": self.ip,
            "port": self.port,
            "agent_name": self.agent_name,
            "agent_type": self.agent_type,
            "role": self.role,
            "status": self.status.value,
            "healthy": self.is_healthy(),
            "weight": self.weight,
            "enabled": self.enabled,
            "metadata": self.metadata,
            "stats": {
                "request_count": self.request_count,
                "success_count": self.success_count,
                "fail_count": self.fail_count,
                "avg_response_time": self.avg_response_time,
                "success_rate": self.success_count / max(self.request_count, 1)
            },
            "created_at": self.created_at.isoformat(),
            "last_heartbeat": self.last_heartbeat.isoformat()
        }


@dataclass
class ServiceInfo:
    """服务信息"""
    name: str = ""
    group: str = "DEFAULT_GROUP"
    description: str = ""
    instances: List[str] = field(default_factory=list)  # 实例ID列表
    
    # 保护阈值
    protect_threshold: float = 0.0  # 0.0-1.0
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 统计
    healthy_instance_count: int = 0
    instance_count: int = 0


class ServiceRegistry:
    """服务注册中心
    
    参考 Nacos 的服务注册发现机制
    每个 Agent 作为一个服务实例进行注册和管理
    """
    
    def __init__(self):
        # 服务实例: instance_id -> ServiceInstance
        self.instances: Dict[str, ServiceInstance] = {}
        
        # 服务信息: service_name -> ServiceInfo
        self.services: Dict[str, ServiceInfo] = {}
        
        # 服务分组: group -> [service_names]
        self.groups: Dict[str, List[str]] = {}
        
        # 订阅者: service_name -> [callbacks]
        self.subscribers: Dict[str, List[Callable]] = {}
        
        # 锁
        self._lock = asyncio.Lock()
        
        # 健康检查任务
        self._health_check_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def start(self):
        """启动注册中心"""
        self._running = True
        self._health_check_task = asyncio.create_task(self._health_check_loop())
    
    async def stop(self):
        """停止注册中心"""
        self._running = False
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
    
    async def register(
        self,
        service_name: str,
        agent_name: str,
        agent_type: str = "",
        role: str = "",
        group: str = "DEFAULT_GROUP",
        ip: str = "localhost",
        port: int = 8000,
        metadata: Optional[Dict[str, Any]] = None,
        weight: int = 100,
        heartbeat_interval: int = 30
    ) -> str:
        """注册服务实例（Agent）"""
        async with self._lock:
            instance = ServiceInstance(
                service_name=service_name,
                agent_name=agent_name,
                agent_type=agent_type,
                role=role,
                group_name=group if hasattr(ServiceInstance, 'group') else "DEFAULT_GROUP",
                ip=ip,
                port=port,
                weight=weight,
                heartbeat_interval=heartbeat_interval,
                metadata=metadata or {}
            )
            
            self.instances[instance.id] = instance
            
            # 更新服务信息
            if service_name not in self.services:
                self.services[service_name] = ServiceInfo(
                    name=service_name,
                    group=group
                )
            
            service = self.services[service_name]
            service.instances.append(instance.id)
            service.instance_count = len(service.instances)
            
            # 更新分组
            if group not in self.groups:
                self.groups[group] = []
            if service_name not in self.groups[group]:
                self.groups[group].append(service_name)
            
            # 通知订阅者
            await self._notify_subscribers(service_name, "register", instance)
            
            return instance.id
    
    async def deregister(self, instance_id: str) -> bool:
        """注销服务实例"""
        async with self._lock:
            instance = self.instances.get(instance_id)
            if not instance:
                return False
            
            service_name = instance.service_name
            service = self.services.get(service_name)
            
            if service and instance_id in service.instances:
                service.instances.remove(instance_id)
                service.instance_count = len(service.instances)
            
            del self.instances[instance_id]
            
            # 通知订阅者
            await self._notify_subscribers(service_name, "deregister", instance)
            
            return True
    
    async def heartbeat(self, instance_id: str) -> bool:
        """心跳"""
        async with self._lock:
            instance = self.instances.get(instance_id)
            if instance:
                instance.heartbeat()
                return True
            return False
    
    def get_instance(self, instance_id: str) -> Optional[ServiceInstance]:
        """获取实例"""
        return self.instances.get(instance_id)
    
    def get_instances(
        self,
        service_name: str,
        healthy_only: bool = True
    ) -> List[ServiceInstance]:
        """获取服务实例列表"""
        service = self.services.get(service_name)
        if not service:
            return []
        
        instances = []
        for instance_id in service.instances:
            instance = self.instances.get(instance_id)
            if instance:
                if healthy_only:
                    if instance.is_healthy():
                        instances.append(instance)
                else:
                    instances.append(instance)
        
        return instances
    
    def select_instance(
        self,
        service_name: str,
        strategy: ServiceWeightStrategy = ServiceWeightStrategy.WEIGHTED
    ) -> Optional[ServiceInstance]:
        """选择一个实例（负载均衡）"""
        instances = self.get_instances(service_name, healthy_only=True)
        
        if not instances:
            return None
        
        if strategy == ServiceWeightStrategy.RANDOM:
            import random
            return random.choice(instances)
        
        elif strategy == ServiceWeightStrategy.ROUND_ROBIN:
            # 简单轮询
            return instances[0]
        
        elif strategy == ServiceWeightStrategy.WEIGHTED:
            # 权重选择
            total_weight = sum(i.weight for i in instances)
            if total_weight == 0:
                return instances[0]
            
            import random
            r = random.randint(0, total_weight)
            for instance in instances:
                r -= instance.weight
                if r <= 0:
                    return instance
            return instances[-1]
        
        elif strategy == ServiceWeightStrategy.LEAST_CONNECTIONS:
            # 最少连接
            return min(instances, key=lambda i: i.request_count)
        
        return instances[0]
    
    def get_services(self, group: Optional[str] = None) -> List[str]:
        """获取服务列表"""
        if group:
            return self.groups.get(group, [])
        return list(self.services.keys())
    
    def get_service_info(self, service_name: str) -> Optional[ServiceInfo]:
        """获取服务信息"""
        service = self.services.get(service_name)
        if service:
            # 更新健康实例数
            healthy_count = len([
                i for i in service.instances
                if self.instances.get(i) and self.instances.get(i).is_healthy()
            ])
            service.healthy_instance_count = healthy_count
        
        return service
    
    def subscribe(self, service_name: str, callback: Callable):
        """订阅服务变化"""
        if service_name not in self.subscribers:
            self.subscribers[service_name] = []
        self.subscribers[service_name].append(callback)
    
    def unsubscribe(self, service_name: str, callback: Callable):
        """取消订阅"""
        if service_name in self.subscribers:
            if callback in self.subscribers[service_name]:
                self.subscribers[service_name].remove(callback)
    
    async def _notify_subscribers(self, service_name: str, event_type: str, instance: ServiceInstance):
        """通知订阅者"""
        if service_name in self.subscribers:
            for callback in self.subscribers[service_name]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(event_type, instance)
                    else:
                        callback(event_type, instance)
                except Exception as e:
                    print(f"Subscriber callback error: {e}")
    
    async def _health_check_loop(self):
        """健康检查循环"""
        while self._running:
            try:
                await self._check_health()
            except Exception as e:
                print(f"Health check error: {e}")
            
            await asyncio.sleep(10)  # 每10秒检查一次
    
    async def _check_health(self):
        """检查实例健康状态"""
        async with self._lock:
            now = datetime.now()
            
            for instance in self.instances.values():
                elapsed = (now - instance.last_heartbeat).total_seconds()
                
                if elapsed > instance.heartbeat_timeout:
                    # 心跳超时，标记为不健康
                    if instance.healthy:
                        instance.healthy = False
                        await self._notify_subscribers(
                            instance.service_name,
                            "unhealthy",
                            instance
                        )
                
                # 更新服务健康实例数
                service = self.services.get(instance.service_name)
                if service:
                    service.healthy_instance_count = len([
                        i for i in service.instances
                        if self.instances.get(i) and self.instances.get(i).is_healthy()
                    ])
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_instances = len(self.instances)
        healthy_instances = sum(1 for i in self.instances.values() if i.is_healthy())
        
        return {
            "total_services": len(self.services),
            "total_instances": total_instances,
            "healthy_instances": healthy_instances,
            "unhealthy_instances": total_instances - healthy_instances,
            "total_groups": len(self.groups),
            "services": {
                name: {
                    "instance_count": len(info.instances),
                    "healthy_count": info.healthy_instance_count
                }
                for name, info in self.services.items()
            }
        }


class ServiceDiscovery:
    """服务发现客户端"""
    
    def __init__(self, registry: ServiceRegistry):
        self.registry = registry
    
    async def find_service(
        self,
        service_name: str,
        healthy_only: bool = True
    ) -> List[ServiceInstance]:
        """发现服务"""
        return self.registry.get_instances(service_name, healthy_only)
    
    async def select_one(self, service_name: str) -> Optional[ServiceInstance]:
        """选择一个服务实例"""
        return self.registry.select_instance(service_name)
    
    def watch(self, service_name: str, callback: Callable):
        """监听服务变化"""
        self.registry.subscribe(service_name, callback)
    
    def unwatch(self, service_name: str, callback: Callable):
        """取消监听"""
        self.registry.unsubscribe(service_name, callback)
