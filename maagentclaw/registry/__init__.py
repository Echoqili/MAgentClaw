"""
Nacos 风格的服务注册与配置中心

将每个 Agent 作为服务进行注册和管理
支持服务发现、配置管理、命名服务等功能
"""

from .service_registry import (
    ServiceRegistry,
    ServiceDiscovery,
    ServiceInstance,
    ServiceInfo,
    ServiceStatus,
    ServiceWeightStrategy
)

from .config_center import (
    ConfigurationCenter,
    ConfigInfo,
    ConfigVersion,
    ConfigType,
    ConfigStatus,
    PublishType
)

from .naming_service import (
    NamingService,
    NamingInfo,
    RouteRule
)

__all__ = [
    # 服务注册
    "ServiceRegistry",
    "ServiceDiscovery", 
    "ServiceInstance",
    "ServiceInfo",
    "ServiceStatus",
    "ServiceWeightStrategy",
    
    # 配置中心
    "ConfigurationCenter",
    "ConfigInfo",
    "ConfigVersion",
    "ConfigType",
    "ConfigStatus",
    "PublishType",
    
    # 命名服务
    "NamingService",
    "NamingInfo",
    "RouteRule"
]
