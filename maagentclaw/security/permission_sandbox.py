"""
权限沙箱 - 限制Agent操作范围
"""

from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import os


class Permission(Enum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"
    NETWORK = "network"
    FILE_SYSTEM = "file_system"


@dataclass
class PermissionScope:
    allowed_paths: List[str] = field(default_factory=list)
    denied_paths: List[str] = field(default_factory=list)
    allowed_commands: List[str] = field(default_factory=list)
    denied_commands: List[str] = field(default_factory=list)
    allowed_domains: List[str] = field(default_factory=list)


@dataclass
class PermissionResult:
    granted: bool
    permission: Permission
    reason: str = ""


class PermissionSandbox:
    DEFAULT_SCOPES = {
        "read_only": PermissionScope(
            allowed_paths=["."],
            denied_paths=["/etc", "/root"],
            allowed_commands=["ls", "cat", "head"],
        ),
        "limited": PermissionScope(
            allowed_paths=["."],
            denied_paths=["/etc", "/root"],
            allowed_commands=["ls", "cat", "head", "grep"],
        ),
        "full": PermissionScope(
            allowed_paths=["/"],
            allowed_commands=["*"],
            allowed_domains=["*"],
        ),
    }
    
    def __init__(self, scope_name: str = "limited", custom_scope: Optional[PermissionScope] = None):
        if custom_scope:
            self.scope = custom_scope
        else:
            self.scope = self.DEFAULT_SCOPES.get(scope_name, self.DEFAULT_SCOPES["limited"])
        self._audit_log: List[Dict] = []
    
    def check_permission(self, permission: Permission, resource: str = "") -> PermissionResult:
        if permission == Permission.READ:
            return self._check_read(resource)
        elif permission == Permission.WRITE:
            return self._check_write(resource)
        elif permission == Permission.DELETE:
            return self._check_delete(resource)
        elif permission == Permission.EXECUTE:
            return self._check_execute(resource)
        elif permission == Permission.NETWORK:
            return self._check_network(resource)
        return PermissionResult(granted=False, permission=permission, reason="Unknown")
    
    def _check_read(self, path: str) -> PermissionResult:
        if not path:
            return PermissionResult(granted=True, permission=Permission.READ)
        abs_path = os.path.abspath(path)
        for denied in self.scope.denied_paths:
            if self._match_path(abs_path, denied):
                return PermissionResult(granted=False, permission=Permission.READ, reason=f"Path denied")
        for allowed in self.scope.allowed_paths:
            if self._match_path(abs_path, allowed):
                return PermissionResult(granted=True, permission=Permission.READ, reason="Allowed")
        return PermissionResult(granted=False, permission=Permission.READ, reason="Not in allow list")
    
    def _check_write(self, path: str) -> PermissionResult:
        result = self._check_read(path)
        if not result.granted:
            return result
        return PermissionResult(granted=True, permission=Permission.WRITE, reason="Write allowed")
    
    def _check_delete(self, path: str) -> PermissionResult:
        result = self._check_read(path)
        if not result.granted:
            return result
        return PermissionResult(granted=True, permission=Permission.DELETE, reason="Delete allowed")
    
    def _check_execute(self, command: str) -> PermissionResult:
        if not command:
            return PermissionResult(granted=False, permission=Permission.EXECUTE)
        cmd_parts = command.split()
        if not cmd_parts:
            return PermissionResult(granted=False, permission=Permission.EXECUTE)
        cmd_name = cmd_parts[0]
        for denied in self.scope.denied_commands:
            if denied == "*" or cmd_name == denied:
                return PermissionResult(granted=False, permission=Permission.EXECUTE, reason="Command denied")
        for allowed in self.scope.allowed_commands:
            if allowed == "*" or cmd_name == allowed:
                return PermissionResult(granted=True, permission=Permission.EXECUTE, reason="Command allowed")
        return PermissionResult(granted=False, permission=Permission.EXECUTE, reason="Not allowed")
    
    def _check_network(self, domain: str) -> PermissionResult:
        if not domain:
            return PermissionResult(granted=False, permission=Permission.NETWORK, reason="No domain")
        for allowed in self.scope.allowed_domains:
            if allowed == "*" or allowed in domain:
                return PermissionResult(granted=True, permission=Permission.NETWORK, reason="Allowed")
        return PermissionResult(granted=False, permission=Permission.NETWORK, reason="Domain not allowed")
    
    def _match_path(self, path: str, pattern: str) -> bool:
        import fnmatch
        path = path.replace("\\", "/").lower()
        pattern = pattern.replace("\\", "/").lower()
        if pattern.endswith("*"):
            return path.startswith(pattern[:-1])
        return fnmatch.fnmatch(path, pattern)
    
    def get_audit_log(self) -> List[Dict]:
        return self._audit_log.copy()
    
    def get_statistics(self) -> Dict:
        return {
            "scope": "default",
            "allowed_paths": len(self.scope.allowed_paths),
            "denied_paths": len(self.scope.denied_paths),
        }
