"""
Skill System - 技能系统

参考 OpenClaw 的技能设计理念，实现 Agent 的技能加载、注册、执行和管理
"""

import asyncio
import importlib
import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type


class SkillStatus(Enum):
    """技能状态"""
    LOADED = "loaded"
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"
    RUNNING = "running"


class SkillType(Enum):
    """技能类型"""
    BUILTIN = "builtin"      # 内置技能
    CUSTOM = "custom"        # 自定义技能
    MARKET = "market"        # 技能市场
    PLUGIN = "plugin"        # 插件技能


@dataclass
class SkillMetadata:
    """技能元数据"""
    name: str
    version: str
    description: str
    author: str
    email: str
    tags: List[str] = field(default_factory=list)
    category: str = "general"
    dependencies: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "email": self.email,
            "tags": self.tags,
            "category": self.category,
            "dependencies": self.dependencies,
            "permissions": self.permissions
        }


@dataclass
class SkillConfig:
    """技能配置"""
    enabled: bool = True
    timeout: int = 30  # 执行超时（秒）
    max_retries: int = 0
    retry_delay: int = 1
    rate_limit: Optional[int] = None  # 速率限制（次/秒）
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "enabled": self.enabled,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "rate_limit": self.rate_limit,
            "parameters": self.parameters
        }


@dataclass
class SkillResult:
    """技能执行结果"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    duration: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "duration": self.duration,
            "metadata": self.metadata
        }


class BaseSkill(ABC):
    """技能基类"""
    
    metadata: SkillMetadata
    config: SkillConfig = SkillConfig()
    
    def __init__(self):
        self.status = SkillStatus.LOADED
        self.execution_count = 0
        self.last_execution: Optional[datetime] = None
    
    @abstractmethod
    async def execute(self, **kwargs) -> SkillResult:
        """执行技能"""
        pass
    
    async def on_load(self):
        """技能加载时的回调"""
        pass
    
    async def on_unload(self):
        """技能卸载时的回调"""
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.metadata.name,
            "version": self.metadata.version,
            "description": self.metadata.description,
            "status": self.status.value,
            "type": self.__class__.__module__.split('.')[-1],
            "execution_count": self.execution_count,
            "last_execution": self.last_execution.isoformat() if self.last_execution else None,
            "config": self.config.to_dict(),
            "metadata": self.metadata.to_dict()
        }


class SkillRegistry:
    """技能注册表"""
    
    def __init__(self):
        self._skills: Dict[str, BaseSkill] = {}
        self._aliases: Dict[str, str] = {}
    
    def _run_async(self, coro):
        """安全运行异步协程"""
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(coro)
        except RuntimeError:
            try:
                asyncio.run(coro)
            except RuntimeError:
                pass
    
    def register(self, skill: BaseSkill, aliases: Optional[List[str]] = None):
        """注册技能"""
        skill_name = skill.metadata.name
        self._skills[skill_name] = skill
        
        # 注册别名
        if aliases:
            for alias in aliases:
                self._aliases[alias] = skill_name
        
        # 调用加载回调
        self._run_async(skill.on_load())
    
    def unregister(self, skill_name: str):
        """注销技能"""
        if skill_name in self._skills:
            skill = self._skills[skill_name]
            self._run_async(skill.on_unload())
            del self._skills[skill_name]
            
            # 移除别名
            aliases_to_remove = [
                alias for alias, name in self._aliases.items()
                if name == skill_name
            ]
            for alias in aliases_to_remove:
                del self._aliases[alias]
    
    def get(self, skill_name: str) -> Optional[BaseSkill]:
        """获取技能"""
        # 尝试直接查找
        if skill_name in self._skills:
            return self._skills[skill_name]
        
        # 尝试别名查找
        if skill_name in self._aliases:
            real_name = self._aliases[skill_name]
            return self._skills.get(real_name)
        
        return None
    
    def list_skills(self) -> List[str]:
        """列出所有技能"""
        return list(self._skills.keys())
    
    def list_aliases(self) -> Dict[str, str]:
        """列出所有别名"""
        return self._aliases.copy()
    
    def count(self) -> int:
        """技能数量"""
        return len(self._skills)


class SkillLoader:
    """技能加载器"""
    
    def __init__(self, registry: SkillRegistry):
        self.registry = registry
        self.skill_paths: List[Path] = []
    
    def add_skill_path(self, path: Path):
        """添加技能搜索路径"""
        if path.exists() and path.is_dir():
            self.skill_paths.append(path)
    
    def _is_builtin_skill_path(self, file_path: Path) -> bool:
        """检查是否是内置技能路径"""
        try:
            builtin_dir = Path(__file__).parent.parent / "skills"
            return file_path.parent.resolve() == builtin_dir.resolve()
        except Exception:
            return False
    
    def load_builtin_skill(self, module_name: str) -> Optional[BaseSkill]:
        """使用包导入方式加载内置技能"""
        try:
            module = importlib.import_module(f"maagentclaw.skills.{module_name}")
            
            # 查找技能实例
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, BaseSkill) and not isinstance(attr, type):
                    self.registry.register(attr)
                    return attr
            
            # 查找并实例化技能类
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    issubclass(attr, BaseSkill) and 
                    attr != BaseSkill):
                    skill = attr()
                    self.registry.register(skill)
                    return skill
            
            return None
        except Exception as e:
            print(f"Error loading builtin skill {module_name}: {e}")
            return None
    
    def load_from_file(self, file_path: Path) -> Optional[BaseSkill]:
        """从文件加载技能"""
        # 优先使用包导入加载内置技能
        if self._is_builtin_skill_path(file_path):
            module_name = file_path.stem
            return self.load_builtin_skill(module_name)
        
        # 自定义技能使用动态加载
        return self._load_skill_from_file(file_path)
    
    def _load_skill_from_file(self, file_path: Path) -> Optional[BaseSkill]:
        """从文件动态加载技能（用于自定义技能）"""
        try:
            # 动态导入模块
            spec = importlib.util.spec_from_file_location(
                "skill_module", file_path
            )
            if spec is None or spec.loader is None:
                return None
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 优先查找模块级别的技能实例（自动注册）
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, BaseSkill) and not isinstance(attr, type):
                    self.registry.register(attr)
                    return attr
            
            # 查找并实例化技能类
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    issubclass(attr, BaseSkill) and 
                    attr != BaseSkill):
                    # 实例化技能
                    skill = attr()
                    self.registry.register(skill)
                    return skill
            
            return None
            
        except Exception as e:
            print(f"Error loading skill from {file_path}: {e}")
            return None
    
    def load_from_directory(self, directory: Path) -> List[BaseSkill]:
        """从目录加载所有技能"""
        skills = []
        
        if not directory.exists():
            return skills
        
        # 查找所有 Python 文件
        for file_path in directory.glob("*.py"):
            if file_path.name.startswith("_"):
                continue
            
            skill = self.load_from_file(file_path)
            if skill:
                skills.append(skill)
        
        return skills
    
    def load_all(self) -> List[BaseSkill]:
        """从所有路径加载技能"""
        skills = []
        
        for path in self.skill_paths:
            skills.extend(self.load_from_directory(path))
        
        return skills


class SkillMarketplace:
    """技能市场"""
    
    def __init__(self):
        self.available_skills: List[Dict[str, Any]] = []
        self.installed_skills: Dict[str, str] = {}  # name -> version
    
    def list_available(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出可用技能"""
        if category:
            return [
                skill for skill in self.available_skills
                if skill.get("category") == category
            ]
        return self.available_skills
    
    def search(self, query: str) -> List[Dict[str, Any]]:
        """搜索技能"""
        query = query.lower()
        results = []
        
        for skill in self.available_skills:
            # 搜索名称、描述、标签
            if (query in skill.get("name", "").lower() or
                query in skill.get("description", "").lower() or
                any(query in tag.lower() for tag in skill.get("tags", []))):
                results.append(skill)
        
        return results
    
    def install(self, skill_name: str, version: str = "latest") -> bool:
        """安装技能"""
        # 模拟安装逻辑
        self.installed_skills[skill_name] = version
        return True
    
    def uninstall(self, skill_name: str) -> bool:
        """卸载技能"""
        if skill_name in self.installed_skills:
            del self.installed_skills[skill_name]
            return True
        return False
    
    def update(self, skill_name: str) -> bool:
        """更新技能"""
        if skill_name in self.installed_skills:
            self.installed_skills[skill_name] = "latest"
            return True
        return False


class SkillManager:
    """技能管理器"""
    
    def __init__(self, workspace_path: Path):
        self.workspace_path = Path(workspace_path)
        self.registry = SkillRegistry()
        self.loader = SkillLoader(self.registry)
        self.marketplace = SkillMarketplace()
        
        # 技能目录
        self.skills_dir = self.workspace_path / "skills"
        self.builtin_dir = Path(__file__).parent.parent / "skills"
        
        # 初始化技能路径
        self.loader.add_skill_path(self.skills_dir)
        self.loader.add_skill_path(self.builtin_dir)
        
        # 加载技能
        self.load_skills()
    
    def load_skills(self):
        """加载所有技能"""
        # 加载内置技能
        if self.builtin_dir.exists():
            self.loader.load_from_directory(self.builtin_dir)
        
        # 加载自定义技能
        if self.skills_dir.exists():
            self.loader.load_from_directory(self.skills_dir)
    
    def reload_skill(self, skill_name: str) -> bool:
        """重新加载技能"""
        skill = self.registry.get(skill_name)
        if skill:
            # 注销旧技能
            self.registry.unregister(skill_name)
            
            # 重新加载
            self.load_skills()
            return True
        
        return False
    
    def execute_skill(self, skill_name: str, **kwargs) -> SkillResult:
        """执行技能"""
        skill = self.registry.get(skill_name)
        if not skill:
            return SkillResult(
                success=False,
                error=f"Skill '{skill_name}' not found"
            )
        
        if not skill.config.enabled:
            return SkillResult(
                success=False,
                error=f"Skill '{skill_name}' is disabled"
            )
        
        # 执行技能
        try:
            result = asyncio.run(skill.execute(**kwargs))
            skill.execution_count += 1
            skill.last_execution = datetime.now()
            return result
        except Exception as e:
            return SkillResult(
                success=False,
                error=str(e)
            )
    
    def get_skill(self, skill_name: str) -> Optional[BaseSkill]:
        """获取技能"""
        return self.registry.get(skill_name)
    
    def list_skills(self) -> List[Dict[str, Any]]:
        """列出所有技能"""
        skills = []
        for skill_name in self.registry.list_skills():
            skill = self.registry.get(skill_name)
            if skill:
                skills.append(skill.to_dict())
        return skills
    
    def enable_skill(self, skill_name: str) -> bool:
        """启用技能"""
        skill = self.registry.get(skill_name)
        if skill:
            skill.config.enabled = True
            skill.status = SkillStatus.ENABLED
            return True
        return False
    
    def disable_skill(self, skill_name: str) -> bool:
        """禁用技能"""
        skill = self.registry.get(skill_name)
        if skill:
            skill.config.enabled = False
            skill.status = SkillStatus.DISABLED
            return True
        return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        skills = self.list_skills()
        
        total = len(skills)
        enabled = sum(1 for s in skills if s["config"]["enabled"])
        disabled = total - enabled
        total_executions = sum(s["execution_count"] for s in skills)
        
        return {
            "total_skills": total,
            "enabled_skills": enabled,
            "disabled_skills": disabled,
            "total_executions": total_executions
        }


# 简化导入
__all__ = [
    "SkillStatus",
    "SkillType",
    "SkillMetadata",
    "SkillConfig",
    "SkillResult",
    "BaseSkill",
    "SkillRegistry",
    "SkillLoader",
    "SkillMarketplace",
    "SkillManager"
]
