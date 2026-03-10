"""
Agent 工作空间管理模块
参考 OpenClaw 的 workspace 设计
"""

import os
import json
from pathlib import Path
from typing import Dict, Optional, List, Any
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class WorkspaceConfig:
    """工作空间配置"""
    name: str
    path: str
    agent_id: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    files: Dict[str, str] = field(default_factory=dict)


class AgentWorkspace:
    """
    Agent 工作空间管理器
    参考 OpenClaw 的 workspace 设计，管理 Agent 的操作指令和记忆
    """
    
    # 核心文件列表
    CORE_FILES = {
        "AGENTS.md": "操作指令和记忆",
        "SOUL.md": "角色、边界和语气",
        "TOOLS.md": "工具使用说明",
        "IDENTITY.md": "Agent 名称/个性/表情",
        "USER.md": "用户档案和偏好",
        "HEARTBEAT.md": "心跳任务配置（可选）"
    }
    
    def __init__(self, workspace_dir: str, agent_id: str):
        self.workspace_dir = Path(workspace_dir)
        self.agent_id = agent_id
        self.agent_dir = self.workspace_dir / agent_id
        self.sessions_dir = self.agent_dir / "sessions"
        self.skills_dir = self.agent_dir / "skills"
        
        # 确保目录存在
        self._ensure_directories()
        
        # 初始化核心文件
        self._initialize_core_files()
        
        # 加载工作空间配置
        self.config = self._load_config()
    
    def _ensure_directories(self):
        """确保所有必要目录存在"""
        dirs = [
            self.workspace_dir,
            self.agent_dir,
            self.sessions_dir,
            self.skills_dir
        ]
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def _initialize_core_files(self):
        """初始化核心文件（如果不存在）"""
        for filename, description in self.CORE_FILES.items():
            file_path = self.agent_dir / filename
            if not file_path.exists():
                # 创建默认内容
                content = f"# {filename}\n\n"
                content += f"{description}\n\n"
                content += f"<!-- Created: {datetime.now().isoformat()} -->\n"
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
    
    def _load_config(self) -> WorkspaceConfig:
        """加载工作空间配置"""
        config_file = self.agent_dir / "workspace.json"
        
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return WorkspaceConfig(**data)
        else:
            # 创建默认配置
            config = WorkspaceConfig(
                name=f"workspace-{self.agent_id[:8]}",
                path=str(self.agent_dir),
                agent_id=self.agent_id
            )
            self._save_config(config)
            return config
    
    def _save_config(self, config: WorkspaceConfig):
        """保存工作空间配置"""
        config_file = self.agent_dir / "workspace.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump({
                "name": config.name,
                "path": config.path,
                "agent_id": config.agent_id,
                "created_at": config.created_at,
                "files": config.files
            }, f, indent=2, ensure_ascii=False)
    
    def read_file(self, filename: str) -> Optional[str]:
        """读取工作空间文件"""
        file_path = self.agent_dir / filename
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        return None
    
    def write_file(self, filename: str, content: str):
        """写入工作空间文件"""
        file_path = self.agent_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        self.config.files[filename] = datetime.now().isoformat()
        self._save_config(self.config)
    
    def get_bootstrap_files(self) -> Dict[str, str]:
        """获取启动文件内容（用于注入到 Agent 上下文）"""
        bootstrap_files = ["AGENTS.md", "SOUL.md", "TOOLS.md", "IDENTITY.md", "USER.md"]
        files_content = {}
        
        for filename in bootstrap_files:
            content = self.read_file(filename)
            if content:
                # 跳过空文件
                if content.strip():
                    files_content[filename] = content
        
        return files_content
    
    def get_heartbeat_prompt(self) -> Optional[str]:
        """获取心跳提示"""
        content = self.read_file("HEARTBEAT.md")
        if content and content.strip():
            return content
        return None
    
    def save_session(self, session_id: str, messages: List[Dict[str, Any]]):
        """保存会话到 JSONL 文件"""
        session_file = self.sessions_dir / f"{session_id}.jsonl"
        
        with open(session_file, 'a', encoding='utf-8') as f:
            for message in messages:
                f.write(json.dumps(message, ensure_ascii=False) + '\n')
    
    def load_session(self, session_id: str) -> List[Dict[str, Any]]:
        """加载会话历史"""
        session_file = self.sessions_dir / f"{session_id}.jsonl"
        messages = []
        
        if session_file.exists():
            with open(session_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        messages.append(json.loads(line))
        
        return messages
    
    def list_sessions(self) -> List[str]:
        """列出所有会话"""
        sessions = []
        for file in self.sessions_dir.glob("*.jsonl"):
            sessions.append(file.stem)
        return sessions
    
    def delete_session(self, session_id: str):
        """删除会话"""
        session_file = self.sessions_dir / f"{session_id}.jsonl"
        if session_file.exists():
            session_file.unlink()
    
    def get_skills_dir(self) -> Path:
        """获取技能目录"""
        return self.skills_dir
    
    def get_context_for_agent(self) -> str:
        """为 Agent 生成完整的上下文"""
        context_parts = []
        
        # 添加启动文件
        bootstrap = self.get_bootstrap_files()
        for filename, content in bootstrap.items():
            context_parts.append(f"## {filename}\n{content}\n")
        
        # 添加心跳提示（如果有）
        heartbeat = self.get_heartbeat_prompt()
        if heartbeat:
            context_parts.append(f"## HEARTBEAT.md\n{heartbeat}\n")
        
        return "\n\n".join(context_parts)
    
    def is_new_workspace(self) -> bool:
        """检查是否为新工作空间"""
        # 如果没有任何核心文件，则是新工作空间
        for filename in self.CORE_FILES.keys():
            if (self.agent_dir / filename).exists():
                return False
        return True


class WorkspaceManager:
    """工作空间管理器（管理多个 Agent 的工作空间）"""
    
    def __init__(self, base_dir: str = "~/.maagentclaw/workspaces"):
        self.base_dir = Path(base_dir).expanduser()
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.workspaces: Dict[str, AgentWorkspace] = {}
    
    def get_workspace(self, agent_id: str) -> AgentWorkspace:
        """获取或创建 Agent 工作空间"""
        if agent_id not in self.workspaces:
            workspace = AgentWorkspace(str(self.base_dir), agent_id)
            self.workspaces[agent_id] = workspace
        return self.workspaces[agent_id]
    
    def list_workspaces(self) -> List[str]:
        """列出所有工作空间"""
        return [d.name for d in self.base_dir.iterdir() if d.is_dir()]
    
    def delete_workspace(self, agent_id: str):
        """删除工作空间"""
        workspace_dir = self.base_dir / agent_id
        if workspace_dir.exists():
            import shutil
            shutil.rmtree(workspace_dir)
        if agent_id in self.workspaces:
            del self.workspaces[agent_id]
    
    def export_workspace(self, agent_id: str, output_path: str):
        """导出工作空间"""
        import shutil
        workspace = self.get_workspace(agent_id)
        shutil.make_archive(output_path, 'zip', workspace.agent_dir)
    
    def import_workspace(self, agent_id: str, archive_path: str):
        """导入工作空间"""
        import shutil
        workspace_dir = self.base_dir / agent_id
        shutil.unpack_archive(archive_path, workspace_dir)
        self.workspaces[agent_id] = AgentWorkspace(str(self.base_dir), agent_id)
