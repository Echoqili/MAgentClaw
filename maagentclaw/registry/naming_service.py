"""
Nacos 风格的命名服务

提供服务命名、域名管理、服务路由功能
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass
class NamingInfo:
    """命名信息"""
    name: str = ""
    name_type: str = "domain"  # domain, alias, pattern
    target: str = ""  # 目标服务名
    
    # 路由规则
    routing_rules: Dict[str, Any] = field(default_factory=dict)
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 状态
    enabled: bool = True
    
    # 时间
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class RouteRule:
    """路由规则"""
    rule_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    condition: str = ""  # 条件表达式
    action: str = ""  # 动作: forward, redirect, reject
    target: str = ""  # 目标
    priority: int = 0  # 优先级
    enabled: bool = True


class NamingService:
    """命名服务
    
    参考 Nacos 的命名服务机制
    提供服务命名、域名管理、服务路由功能
    """
    
    def __init__(self):
        # 命名信息: name -> NamingInfo
        self.namings: Dict[str, NamingInfo] = {}
        
        # 服务别名: alias -> target_name
        self.aliases: Dict[str, str] = {}
        
        # 路由规则: name -> [RouteRule]
        self.route_rules: Dict[str, List[RouteRule]] = {}
        
        # 锁
        import asyncio
        self._lock = asyncio.Lock()
    
    async def register_name(
        self,
        name: str,
        name_type: str = "domain",
        target: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """注册命名"""
        async with self._lock:
            naming = NamingInfo(
                name=name,
                name_type=name_type,
                target=target or name,
                metadata=metadata or {}
            )
            
            self.namings[name] = naming
            
            # 如果是别名，建立映射
            if name_type == "alias" and target:
                self.aliases[name] = target
            
            return name
    
    async def deregister_name(self, name: str) -> bool:
        """注销命名"""
        async with self._lock:
            if name in self.namings:
                del self.namings[name]
                
                if name in self.aliases:
                    del self.aliases[name]
                
                if name in self.route_rules:
                    del self.route_rules[name]
                
                return True
            return False
    
    async def resolve_name(self, name: str) -> Optional[str]:
        """解析命名（支持别名）"""
        # 检查是否是别名
        if name in self.aliases:
            return self.aliases[name]
        
        # 检查是否存在
        if name in self.namings:
            return name
        
        return None
    
    async def add_route_rule(
        self,
        name: str,
        condition: str,
        action: str,
        target: str,
        priority: int = 0
    ) -> str:
        """添加路由规则"""
        async with self._lock:
            rule = RouteRule(
                condition=condition,
                action=action,
                target=target,
                priority=priority
            )
            
            if name not in self.route_rules:
                self.route_rules[name] = []
            
            self.route_rules[name].append(rule)
            
            # 按优先级排序
            self.route_rules[name].sort(key=lambda r: r.priority, reverse=True)
            
            return rule.rule_id
    
    async def remove_route_rule(self, name: str, rule_id: str) -> bool:
        """移除路由规则"""
        async with self._lock:
            if name in self.route_rules:
                rules = self.route_rules[name]
                self.route_rules[name] = [r for r in rules if r.rule_id != rule_id]
                return True
            return False
    
    async def route(self, name: str, context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """路由"""
        context = context or {}
        
        # 解析名称
        resolved = await self.resolve_name(name)
        if not resolved:
            return None
        
        # 检查是否有路由规则
        if name in self.route_rules:
            rules = self.route_rules[name]
            
            for rule in rules:
                if not rule.enabled:
                    continue
                
                # 简单条件匹配
                if self._match_condition(rule.condition, context):
                    if rule.action == "forward":
                        return rule.target
                    elif rule.action == "redirect":
                        return rule.target
                    elif rule.action == "reject":
                        return None
        
        return resolved
    
    def _match_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """匹配条件"""
        if not condition:
            return True
        
        # 简单条件解析
        # 例如: "version >= 2.0" 或 "region == cn-shanghai"
        try:
            parts = condition.split()
            if len(parts) >= 3:
                key = parts[0]
                op = parts[1]
                value = parts[2]
                
                ctx_value = context.get(key)
                
                if op == "==":
                    return str(ctx_value) == value
                elif op == "!=":
                    return str(ctx_value) != value
                elif op == ">":
                    return float(ctx_value) > float(value)
                elif op == "<":
                    return float(ctx_value) < float(value)
                elif op == ">=":
                    return float(ctx_value) >= float(value)
                elif op == "<=":
                    return float(ctx_value) <= float(value)
        except:
            pass
        
        return True
    
    def get_naming(self, name: str) -> Optional[NamingInfo]:
        """获取命名信息"""
        return self.namings.get(name)
    
    def get_all_namings(self, name_type: Optional[str] = None) -> List[NamingInfo]:
        """获取所有命名"""
        if name_type:
            return [n for n in self.namings.values() if n.name_type == name_type]
        return list(self.namings.values())
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计"""
        return {
            "total_namings": len(self.namings),
            "domain_count": len([n for n in self.namings.values() if n.name_type == "domain"]),
            "alias_count": len([n for n in self.namings.values() if n.name_type == "alias"]),
            "pattern_count": len([n for n in self.namings.values() if n.name_type == "pattern"]),
            "total_route_rules": sum(len(rules) for rules in self.route_rules.values())
        }
