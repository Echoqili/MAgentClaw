import secrets
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
import json


class Permission(Enum):
    """权限类型"""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    ADMIN = "admin"


@dataclass
class APIKey:
    """API 密钥"""
    key_id: str
    key_hash: str
    name: str
    permissions: List[Permission]
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key_id": self.key_id,
            "name": self.name,
            "permissions": [p.value for p in self.permissions],
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "is_active": self.is_active,
            "metadata": self.metadata
        }

    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.expires_at:
            return datetime.now() > self.expires_at
        return False


class AuthManager:
    """认证管理器"""

    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path
        self._keys: Dict[str, APIKey] = {}

        if storage_path and storage_path.exists():
            self._load()

    def _hash_key(self, key: str) -> str:
        """哈希密钥"""
        return hashlib.sha256(key.encode()).hexdigest()

    def create_key(
        self,
        name: str,
        permissions: List[Permission],
        expires_days: Optional[int] = None
    ) -> tuple[str, APIKey]:
        """创建 API 密钥"""
        key = f"mac_{secrets.token_urlsafe(32)}"
        key_hash = self._hash_key(key)

        expires_at = None
        if expires_days:
            expires_at = datetime.now() + timedelta(days=expires_days)

        api_key = APIKey(
            key_id=secrets.token_hex(8),
            key_hash=key_hash,
            name=name,
            permissions=permissions,
            created_at=datetime.now(),
            expires_at=expires_at
        )

        self._keys[key_hash] = api_key
        self._save()

        return key, api_key

    def verify_key(self, key: str) -> Optional[APIKey]:
        """验证密钥"""
        key_hash = self._hash_key(key)
        api_key = self._keys.get(key_hash)

        if not api_key:
            return None

        if not api_key.is_active:
            return None

        if api_key.is_expired():
            return None

        api_key.last_used = datetime.now()
        self._save()

        return api_key

    def revoke_key(self, key_id: str) -> bool:
        """撤销密钥"""
        for key_hash, api_key in self._keys.items():
            if api_key.key_id == key_id:
                api_key.is_active = False
                self._save()
                return True
        return False

    def list_keys(self) -> List[Dict[str, Any]]:
        """列出所有密钥"""
        return [key.to_dict() for key in self._keys.values()]

    def get_key(self, key_id: str) -> Optional[APIKey]:
        """获取密钥信息"""
        for key in self._keys.values():
            if key.key_id == key_id:
                return key
        return None

    def has_permission(
        self,
        key: str,
        required_permission: Permission
    ) -> bool:
        """检查权限"""
        api_key = self.verify_key(key)
        if not api_key:
            return False

        for perm in api_key.permissions:
            if perm == Permission.ADMIN:
                return True
            if perm == required_permission:
                return True

        return False

    def _save(self) -> None:
        """保存到磁盘"""
        if not self.storage_path:
            return

        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            key_hash: key.to_dict()
            for key_hash, key in self._keys.items()
        }

        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _load(self) -> None:
        """从磁盘加载"""
        if not self.storage_path or not self.storage_path.exists():
            return

        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            for key_hash, key_data in data.items():
                key_data["created_at"] = datetime.fromisoformat(key_data["created_at"])
                if key_data.get("expires_at"):
                    key_data["expires_at"] = datetime.fromisoformat(key_data["expires_at"])
                if key_data.get("last_used"):
                    key_data["last_used"] = datetime.fromisoformat(key_data["last_used"])
                key_data["permissions"] = [Permission(p) for p in key_data["permissions"]]

                api_key = APIKey(**key_data)
                self._keys[key_hash] = api_key

        except Exception as e:
            print(f"Error loading API keys: {e}")
