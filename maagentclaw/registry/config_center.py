"""
Nacos 风格的配置中心

支持配置的动态发布、版本管理、配置监听、灰度发布
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import hashlib
import uuid


class ConfigType(Enum):
    """配置类型"""
    PROPERTIES = "properties"
    JSON = "json"
    YAML = "yaml"
    XML = "xml"
    TEXT = "text"


class ConfigStatus(Enum):
    """配置状态"""
    ACTIVE = "active"
    ROLLBACK = "rollback"
    DELETED = "deleted"


class PublishType(Enum):
    """发布类型"""
    NORMAL = "normal"         # 正常发布
    GRAY = "gray"           # 灰度发布
    ROLLBACK = "rollback"   # 回滚


@dataclass
class ConfigVersion:
    """配置版本"""
    version: int = 0
    content: str = ""
    md5: str = ""
    publish_type: PublishType = PublishType.NORMAL
    gray_instances: List[str] = field(default_factory=list)  # 灰度实例
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    comment: str = ""


@dataclass
class ConfigInfo:
    """配置信息"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    namespace: str = "public"    # 命名空间
    group: str = "DEFAULT_GROUP"  # 分组
    data_id: str = ""            # 配置ID
    content: str = ""             # 配置内容
    config_type: ConfigType = ConfigType.JSON
    
    # 版本管理
    versions: List[ConfigVersion] = field(default_factory=list)
    current_version: int = 1
    
    # 状态
    status: ConfigStatus = ConfigStatus.ACTIVE
    
    # 元数据
    app_name: str = ""
    description: str = ""
    tags: Dict[str, str] = field(default_factory=dict)
    
    # 监听者
    listeners: List[str] = field(default_factory=list)  # 监听实例ID
    
    # 时间
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def get_md5(self) -> str:
        """计算MD5"""
        return hashlib.md5(self.content.encode()).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "namespace": self.namespace,
            "group": self.group,
            "data_id": self.data_id,
            "content": self.content,
            "config_type": self.config_type.value,
            "current_version": self.current_version,
            "status": self.status.value,
            "app_name": self.app_name,
            "description": self.description,
            "tags": self.tags,
            "md5": self.get_md5(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class ConfigListener:
    """配置监听器"""
    
    def __init__(self, instance_id: str, callback: Callable):
        self.instance_id = instance_id
        self.callback = callback
        self.last_md5: Optional[str] = None


class ConfigurationCenter:
    """配置中心
    
    参考 Nacos 的配置管理机制
    支持配置的动态发布、版本管理、配置监听、灰度发布
    """
    
    def __init__(self):
        # 配置存储: (namespace, group, data_id) -> ConfigInfo
        self.configs: Dict[tuple, ConfigInfo] = {}
        
        # 索引: namespace -> [data_ids]
        self.namespace_index: Dict[str, List[str]] = {}
        
        # 监听器: (namespace, group, data_id) -> [listeners]
        self.listeners: Dict[tuple, List[ConfigListener]] = {}
        
        # 锁
        import asyncio
        self._lock = asyncio.Lock()
    
    def _make_key(self, namespace: str, group: str, data_id: str) -> tuple:
        """创建键"""
        return (namespace, group, data_id)
    
    async def publish_config(
        self,
        namespace: str,
        group: str,
        data_id: str,
        content: str,
        config_type: ConfigType = ConfigType.JSON,
        app_name: str = "",
        description: str = "",
        tags: Optional[Dict[str, str]] = None,
        publish_type: PublishType = PublishType.NORMAL,
        gray_instances: Optional[List[str]] = None,
        comment: str = ""
    ) -> str:
        """发布配置"""
        async with self._lock:
            key = self._make_key(namespace, group, data_id)
            
            # 检查配置是否存在
            if key in self.configs:
                config = self.configs[key]
                config.content = content
                config.status = ConfigStatus.ACTIVE
                config.current_version += 1
                config.updated_at = datetime.now()
            else:
                config = ConfigInfo(
                    namespace=namespace,
                    group=group,
                    data_id=data_id,
                    content=content,
                    config_type=config_type,
                    app_name=app_name,
                    description=description,
                    tags=tags or {}
                )
                self.configs[key] = config
            
            # 创建新版本
            version = ConfigVersion(
                version=config.current_version,
                content=content,
                md5=config.get_md5(),
                publish_type=publish_type,
                gray_instances=gray_instances or [],
                comment=comment
            )
            config.versions.append(version)
            
            # 更新索引
            if namespace not in self.namespace_index:
                self.namespace_index[namespace] = []
            if data_id not in self.namespace_index[namespace]:
                self.namespace_index[namespace].append(data_id)
            
            # 通知监听器
            await self._notify_listeners(namespace, group, data_id, config)
            
            return config.id
    
    async def get_config(
        self,
        namespace: str,
        group: str,
        data_id: str
    ) -> Optional[ConfigInfo]:
        """获取配置"""
        key = self._make_key(namespace, group, data_id)
        config = self.configs.get(key)
        
        if config and config.status == ConfigStatus.ACTIVE:
            return config
        
        return None
    
    async def get_config_by_id(self, config_id: str) -> Optional[ConfigInfo]:
        """通过ID获取配置"""
        for config in self.configs.values():
            if config.id == config_id:
                return config
        return None
    
    async def delete_config(
        self,
        namespace: str,
        group: str,
        data_id: str
    ) -> bool:
        """删除配置"""
        async with self._lock:
            key = self._make_key(namespace, group, data_id)
            
            if key in self.configs:
                config = self.configs[key]
                config.status = ConfigStatus.DELETED
                
                # 通知监听器
                await self._notify_listeners(namespace, group, data_id, None)
                
                return True
        
        return False
    
    async def rollback(
        self,
        namespace: str,
        group: str,
        data_id: str,
        target_version: Optional[int] = None
    ) -> bool:
        """回滚配置"""
        async with self._lock:
            key = self._make_key(namespace, group, data_id)
            config = self.configs.get(key)
            
            if not config or not config.versions:
                return False
            
            # 默认回滚到上一个版本
            if target_version is None:
                if len(config.versions) >= 2:
                    target_version = config.versions[-2].version
                else:
                    return False
            
            # 查找目标版本
            target = None
            for v in config.versions:
                if v.version == target_version:
                    target = v
                    break
            
            if not target:
                return False
            
            # 回滚
            config.content = target.content
            config.current_version = target.version
            config.status = ConfigStatus.ROLLBACK
            config.updated_at = datetime.now()
            
            # 通知监听器
            await self._notify_listeners(namespace, group, data_id, config)
            
            return True
    
    async def listen_config(
        self,
        namespace: str,
        group: str,
        data_id: str,
        instance_id: str,
        callback: Callable
    ):
        """监听配置变化"""
        key = self._make_key(namespace, group, data_id)
        
        if key not in self.listeners:
            self.listeners[key] = []
        
        listener = ConfigListener(instance_id, callback)
        self.listeners[key].append(listener)
        
        # 返回当前MD5
        config = self.configs.get(key)
        if config:
            listener.last_md5 = config.get_md5()
    
    async def unlisten_config(
        self,
        namespace: str,
        group: str,
        data_id: str,
        instance_id: str
    ):
        """取消监听"""
        key = self._make_key(namespace, group, data_id)
        
        if key in self.listeners:
            self.listeners[key] = [
                l for l in self.listeners[key]
                if l.instance_id != instance_id
            ]
    
    async def _notify_listeners(
        self,
        namespace: str,
        group: str,
        data_id: str,
        config: Optional[ConfigInfo]
    ):
        """通知监听器"""
        key = self._make_key(namespace, group, data_id)
        
        if key not in self.listeners:
            return
        
        new_md5 = config.get_md5() if config else None
        
        for listener in self.listeners[key]:
            # 检查是否变化
            if listener.last_md5 != new_md5:
                try:
                    if asyncio.iscoroutinefunction(listener.callback):
                        await listener.callback(config)
                    else:
                        listener.callback(config)
                except Exception as e:
                    print(f"Listener callback error: {e}")
                
                listener.last_md5 = new_md5
    
    def search_configs(
        self,
        namespace: Optional[str] = None,
        group: Optional[str] = None,
        data_id_pattern: Optional[str] = None
    ) -> List[ConfigInfo]:
        """搜索配置"""
        results = []
        
        for config in self.configs.values():
            if config.status != ConfigStatus.ACTIVE:
                continue
            
            # 命名空间过滤
            if namespace and config.namespace != namespace:
                continue
            
            # 分组过滤
            if group and config.group != group:
                continue
            
            # data_id 模糊匹配
            if data_id_pattern:
                import re
                if not re.match(data_id_pattern, config.data_id):
                    continue
            
            results.append(config)
        
        return results
    
    def get_namespaces(self) -> List[str]:
        """获取命名空间列表"""
        return list(self.namespace_index.keys())
    
    def get_groups(self, namespace: str = "public") -> List[str]:
        """获取分组列表"""
        groups = set()
        for key, config in self.configs.items():
            if config.namespace == namespace:
                groups.add(config.group)
        return list(groups)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计"""
        active_count = sum(
            1 for c in self.configs.values()
            if c.status == ConfigStatus.ACTIVE
        )
        
        return {
            "total_configs": len(self.configs),
            "active_configs": active_count,
            "namespaces": len(self.namespace_index),
            "total_listeners": sum(
                len(listeners) for listeners in self.listeners.values()
            )
        }


import asyncio
