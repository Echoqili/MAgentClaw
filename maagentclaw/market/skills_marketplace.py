"""
Skills Marketplace - Skills 市场对接模块

对接 ClawHub 等 Skills 市场
"""

import asyncio
import json
import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


class SkillCategory(Enum):
    """技能分类"""
    PRODUCTIVITY = "productivity"
    DEVELOPMENT = "development"
    DESIGN = "design"
    MARKETING = "marketing"
    DATA = "data"
    COMMUNICATION = "communication"
    UTILITY = "utility"
    OTHER = "other"


class SkillRating(Enum):
    """技能评级"""
    ONE_STAR = 1
    TWO_STARS = 2
    THREE_STARS = 3
    FOUR_STARS = 4
    FIVE_STARS = 5


@dataclass
class MarketplaceSkill:
    """市场技能"""
    id: str
    name: str
    description: str
    author: str
    version: str
    category: SkillCategory
    tags: List[str] = field(default_factory=list)
    downloads: int = 0
    rating: float = 0.0
    price: float = 0.0  # 0 = free
    thumbnail: Optional[str] = None
    readme: str = ""
    dependencies: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "author": self.author,
            "version": self.version,
            "category": self.category.value,
            "tags": self.tags,
            "downloads": self.downloads,
            "rating": self.rating,
            "price": self.price,
            "thumbnail": self.thumbnail,
            "dependencies": self.dependencies,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


@dataclass
class InstallResult:
    """安装结果"""
    success: bool
    skill_id: str
    path: Optional[str] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "skill_id": self.skill_id,
            "path": self.path,
            "error": self.error
        }


class SkillsMarketplace:
    """Skills 市场"""
    
    def __init__(self, 
                 workspace_path: Path,
                 skill_manager=None):
        self.workspace_path = Path(workspace_path)
        self.skill_manager = skill_manager
        
        # 市场配置
        self.marketplaces = {
            "clawhub": {
                "name": "ClawHub",
                "url": "https://api.clawhub.dev",
                "enabled": True
            },
            "community": {
                "name": "Community Skills",
                "url": "https://community.claw.dev",
                "enabled": True
            }
        }
        
        # 本地缓存
        self.cache_file = self.workspace_path / ".marketplace_cache.json"
        self.cache = self._load_cache()
    
    def _load_cache(self) -> Dict[str, Any]:
        """加载缓存"""
        if self.cache_file.exists():
            try:
                return json.loads(self.cache_file.read_text(encoding='utf-8'))
            except:
                pass
        return {"skills": {}, "last_update": None}
    
    def _save_cache(self):
        """保存缓存"""
        self.cache_file.write_text(
            json.dumps(self.cache, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )
    
    async def fetch_skills(self, 
                         category: Optional[SkillCategory] = None,
                         query: Optional[str] = None,
                         sort_by: str = "downloads",
                         page: int = 1,
                         page_size: int = 20) -> List[MarketplaceSkill]:
        """从市场获取技能列表"""
        skills = []
        
        # 模拟市场数据（实际需要调用 API）
        mock_skills = [
            MarketplaceSkill(
                id="github-assistant",
                name="GitHub Assistant",
                description="帮助你管理 GitHub 仓库、PR、Issues",
                author="ClawTeam",
                version="1.2.0",
                category=SkillCategory.DEVELOPMENT,
                tags=["github", "git", "development"],
                downloads=15420,
                rating=4.8,
                price=0.0,
                dependencies=["requests"]
            ),
            MarketplaceSkill(
                id="notion-sync",
                name="Notion Sync",
                description="同步 Notion 数据库和页面",
                author="ClawTeam",
                version="1.0.0",
                category=SkillCategory.PRODUCTIVITY,
                tags=["notion", "sync", "productivity"],
                downloads=8932,
                rating=4.5,
                price=0.0,
                dependencies=["requests"]
            ),
            MarketplaceSkill(
                id="data-analyzer",
                name="Data Analyzer",
                description="数据分析技能，支持 CSV、Excel、JSON",
                author="DataPro",
                version="2.1.0",
                category=SkillCategory.DATA,
                tags=["data", "analysis", "excel", "csv"],
                downloads=12340,
                rating=4.7,
                price=9.99,
                dependencies=["pandas", "openpyxl"]
            ),
            MarketplaceSkill(
                id="seo-optimzer",
                name="SEO Optimizer",
                description="网站 SEO 优化分析工具",
                author="MarketingPro",
                version="1.5.0",
                category=SkillCategory.MARKETING,
                tags=["seo", "marketing", "web"],
                downloads=6543,
                rating=4.3,
                price=0.0,
                dependencies=["requests", "beautifulsoup4"]
            ),
            MarketplaceSkill(
                id="image-processor",
                name="Image Processor",
                description="图片处理：压缩、转换、裁剪",
                author="DesignTools",
                version="1.3.0",
                category=SkillCategory.DESIGN,
                tags=["image", "design", "photo"],
                downloads=9876,
                rating=4.6,
                price=4.99,
                dependencies=["pillow"]
            ),
            MarketplaceSkill(
                id="slack-bot",
                name="Slack Bot",
                description="Slack 消息管理和自动化",
                author="CommTools",
                version="1.1.0",
                category=SkillCategory.COMMUNICATION,
                tags=["slack", "bot", "communication"],
                downloads=7654,
                rating=4.4,
                price=0.0,
                dependencies=["slack-sdk"]
            )
        ]
        
        # 筛选
        skills = mock_skills
        
        if category:
            skills = [s for s in skills if s.category == category]
        
        if query:
            query_lower = query.lower()
            skills = [
                s for s in skills 
                if query_lower in s.name.lower() 
                or query_lower in s.description.lower()
                or any(query_lower in tag.lower() for tag in s.tags)
            ]
        
        # 排序
        if sort_by == "downloads":
            skills.sort(key=lambda s: s.downloads, reverse=True)
        elif sort_by == "rating":
            skills.sort(key=lambda s: s.rating, reverse=True)
        elif sort_by == "newest":
            skills.sort(key=lambda s: s.updated_at or datetime.min, reverse=True)
        
        # 分页
        start = (page - 1) * page_size
        end = start + page_size
        skills = skills[start:end]
        
        # 更新缓存
        for skill in skills:
            self.cache["skills"][skill.id] = skill.to_dict()
        self.cache["last_update"] = datetime.now().isoformat()
        self._save_cache()
        
        return skills
    
    async def get_skill_detail(self, skill_id: str) -> Optional[MarketplaceSkill]:
        """获取技能详情"""
        # 先从缓存获取
        if skill_id in self.cache.get("skills", {}):
            skill_data = self.cache["skills"][skill_id]
            return MarketplaceSkill(**skill_data)
        
        # 模拟获取详情
        skills = await self.fetch_skills()
        for skill in skills:
            if skill.id == skill_id:
                return skill
        
        return None
    
    async def search_skills(self, query: str) -> List[MarketplaceSkill]:
        """搜索技能"""
        return await self.fetch_skills(query=query)
    
    async def get_categories(self) -> List[Dict[str, Any]]:
        """获取分类列表"""
        categories = []
        
        for cat in SkillCategory:
            skills = await self.fetch_skills(category=cat)
            categories.append({
                "id": cat.value,
                "name": cat.value.capitalize(),
                "count": len(skills)
            })
        
        return categories
    
    async def get_featured_skills(self) -> List[MarketplaceSkill]:
        """获取精选技能"""
        skills = await self.fetch_skills()
        
        # 按下载量和评分排序
        featured = sorted(
            skills,
            key=lambda s: s.downloads * 0.7 + s.rating * 1000,
            reverse=True
        )
        
        return featured[:10]
    
    async def get_popular_skills(self, limit: int = 10) -> List[MarketplaceSkill]:
        """获取热门技能"""
        skills = await self.fetch_skills(sort_by="downloads")
        return skills[:limit]
    
    async def get_recent_skills(self, limit: int = 10) -> List[MarketplaceSkill]:
        """获取最新技能"""
        skills = await self.fetch_skills(sort_by="newest")
        return skills[:limit]
    
    async def install_skill(self, skill_id: str) -> InstallResult:
        """安装技能"""
        try:
            # 获取技能详情
            skill = await self.get_skill_detail(skill_id)
            
            if not skill:
                return InstallResult(
                    success=False,
                    skill_id=skill_id,
                    error="Skill not found"
                )
            
            # 创建安装目录
            skills_dir = self.workspace_path / "skills" / skill_id
            skills_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成技能代码
            skill_code = self._generate_skill_code(skill)
            
            # 写入文件
            skill_file = skills_dir / f"{skill_id}.py"
            skill_file.write_text(skill_code, encoding='utf-8')
            
            # 写入 README
            readme_file = skills_dir / "README.md"
            readme_file.write_text(f"# {skill.name}\n\n{skill.description}", encoding='utf-8')
            
            # 更新依赖
            if skill.dependencies:
                requirements = skills_dir / "requirements.txt"
                requirements.write_text("\n".join(skill.dependencies), encoding='utf-8')
            
            return InstallResult(
                success=True,
                skill_id=skill_id,
                path=str(skills_dir)
            )
            
        except Exception as e:
            return InstallResult(
                success=False,
                skill_id=skill_id,
                error=str(e)
            )
    
    async def uninstall_skill(self, skill_id: str) -> bool:
        """卸载技能"""
        try:
            skills_dir = self.workspace_path / "skills" / skill_id
            
            if not skills_dir.exists():
                return False
            
            # 移除目录
            import shutil
            shutil.rmtree(skills_dir)
            
            # 从 skill_manager 注销
            if self.skill_manager:
                self.skill_manager.unregister_tool(skill_id)
            
            # 从缓存移除
            if skill_id in self.cache.get("skills", {}):
                del self.cache["skills"][skill_id]
                self._save_cache()
            
            return True
            
        except Exception as e:
            print(f"Uninstall error: {e}")
            return False
    
    async def update_skill(self, skill_id: str) -> InstallResult:
        """更新技能"""
        # 先卸载
        await self.uninstall_skill(skill_id)
        
        # 再安装
        return await self.install_skill(skill_id)
    
    def _generate_skill_code(self, skill: MarketplaceSkill) -> str:
        """生成技能代码"""
        code = f'''"""
{skill.name}

{skill.description}

Author: {skill.author}
Version: {skill.version}
Category: {skill.category.value}
Tags: {", ".join(skill.tags)}
"""

from maagentclaw.managers.skill_manager import (
    BaseSkill, SkillMetadata, SkillConfig, SkillResult, ToolPermission
)


class {self._to_class_name(skill.name)}Skill(BaseSkill):
    """{skill.description}"""
    
    metadata = SkillMetadata(
        name="{skill.id}",
        version="{skill.version}",
        description="{skill.description}",
        author="{skill.author}",
        category="{skill.category.value}",
        tags={skill.tags},
        permissions=[ToolPermission.READ],
        timeout=30
    )
    
    config = SkillConfig(
        enabled=True,
        sandbox_enabled=True
    )
    
    async def execute(self, **kwargs) -> SkillResult:
        """Execute {skill.name}"""
        try:
            # 实现你的技能逻辑
            return SkillResult(
                success=True,
                data={{"message": "Skill executed successfully"}},
                metadata={{
                    "skill": "{skill.name}",
                    "version": "{skill.version}"
                }}
            )
        except Exception as e:
            return SkillResult(
                success=False,
                error=str(e)
            )


# Auto-register
skill = {self._to_class_name(skill.name)}Skill()
'''
        return code
    
    def _to_class_name(self, name: str) -> str:
        """转换为类名"""
        # 将 "GitHub Assistant" 转换为 "GitHubAssistant"
        words = name.replace("-", " ").split()
        return "".join(word.capitalize() for word in words)
    
    def get_installed_skills(self) -> List[str]:
        """获取已安装的技能"""
        skills_dir = self.workspace_path / "skills"
        
        if not skills_dir.exists():
            return []
        
        installed = []
        for item in skills_dir.iterdir():
            if item.is_dir() and (item / f"{item.name}.py").exists():
                installed.append(item.name)
        
        return installed
    
    def check_updates(self) -> Dict[str, Any]:
        """检查更新"""
        updates = {}
        installed = self.get_installed_skills()
        
        for skill_id in installed:
            if skill_id in self.cache.get("skills", {}):
                skill_data = self.cache["skills"][skill_id]
                # 这里应该与市场比较版本
                updates[skill_id] = {
                    "installed_version": "1.0.0",  # 需要从本地读取
                    "latest_version": skill_data.get("version", "unknown"),
                    "has_update": True  # 简化处理
                }
        
        return updates


# 简化导入
__all__ = [
    "SkillCategory",
    "SkillRating",
    "MarketplaceSkill",
    "InstallResult",
    "SkillsMarketplace"
]
