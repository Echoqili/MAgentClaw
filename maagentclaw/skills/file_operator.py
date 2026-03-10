"""
内置技能 - 文件操作

文件读写和管理
"""

from pathlib import Path
from ..managers.skill_manager import BaseSkill, SkillMetadata, SkillConfig, SkillResult


class FileOperatorSkill(BaseSkill):
    """文件操作技能"""
    
    metadata = SkillMetadata(
        name="file-operator",
        version="1.0.0",
        description="文件读写和管理操作",
        author="MAgentClaw Team",
        email="team@maagentclaw.com",
        tags=["file", "io", "utility"],
        category="utility"
    )
    
    config = SkillConfig(
        enabled=True,
        timeout=30
    )
    
    async def execute(self, operation: str, path: str, **kwargs) -> SkillResult:
        """执行文件操作"""
        try:
            file_path = Path(path)
            
            if operation == "read":
                return await self._read_file(file_path)
            elif operation == "write":
                content = kwargs.get("content", "")
                return await self._write_file(file_path, content)
            elif operation == "append":
                content = kwargs.get("content", "")
                return await self._append_file(file_path, content)
            elif operation == "delete":
                return await self._delete_file(file_path)
            elif operation == "exists":
                return await self._check_exists(file_path)
            else:
                return SkillResult(
                    success=False,
                    error=f"Unknown operation: {operation}"
                )
                
        except Exception as e:
            return SkillResult(
                success=False,
                error=f"File operation error: {str(e)}"
            )
    
    async def _read_file(self, file_path: Path) -> SkillResult:
        """读取文件"""
        if not file_path.exists():
            return SkillResult(
                success=False,
                error=f"File not found: {file_path}"
            )
        
        content = file_path.read_text(encoding='utf-8')
        
        return SkillResult(
            success=True,
            data={
                "path": str(file_path),
                "content": content,
                "size": len(content)
            }
        )
    
    async def _write_file(self, file_path: Path, content: str) -> SkillResult:
        """写入文件"""
        # 创建父目录
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 写入内容
        file_path.write_text(content, encoding='utf-8')
        
        return SkillResult(
            success=True,
            data={
                "path": str(file_path),
                "bytes_written": len(content)
            }
        )
    
    async def _append_file(self, file_path: Path, content: str) -> SkillResult:
        """追加内容"""
        if not file_path.exists():
            return await self._write_file(file_path, content)
        
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(content)
        
        return SkillResult(
            success=True,
            data={
                "path": str(file_path),
                "bytes_appended": len(content)
            }
        )
    
    async def _delete_file(self, file_path: Path) -> SkillResult:
        """删除文件"""
        if not file_path.exists():
            return SkillResult(
                success=False,
                error=f"File not found: {file_path}"
            )
        
        file_path.unlink()
        
        return SkillResult(
            success=True,
            data={"path": str(file_path)}
        )
    
    async def _check_exists(self, file_path: Path) -> SkillResult:
        """检查文件是否存在"""
        exists = file_path.exists()
        
        return SkillResult(
            success=True,
            data={
                "path": str(file_path),
                "exists": exists
            }
        )


# 自动注册
skill = FileOperatorSkill()
