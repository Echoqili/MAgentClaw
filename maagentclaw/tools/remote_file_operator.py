"""
Remote File Operations - 远程文件操作模块

远程控制电脑文件：读取、写入、截图、应用控制
"""

import asyncio
import base64
import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


class RemoteAction(Enum):
    """远程操作类型"""
    LIST_DIR = "list_dir"
    READ_FILE = "read_file"
    WRITE_FILE = "write_file"
    DELETE_FILE = "delete_file"
    COPY_FILE = "copy_file"
    MOVE_FILE = "move_file"
    CREATE_DIR = "create_dir"
    GET_SCREENSHOT = "get_screenshot"
    RUN_COMMAND = "run_command"
    GET_PROCESSES = "get_processes"
    KILL_PROCESS = "kill_process"
    GET_CLIPBOARD = "get_clipboard"
    SET_CLIPBOARD = "set_clipboard"


@dataclass
class RemoteResult:
    """远程操作结果"""
    success: bool
    action: RemoteAction
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "action": self.action.value,
            "data": self.data,
            "error": self.error,
            "metadata": self.metadata
        }


class RemoteFileOperator:
    """远程文件操作器"""
    
    def __init__(self, workspace_path: Optional[Path] = None):
        self.workspace_path = workspace_path or Path.home()
        self.allowed_paths = [self.workspace_path]
    
    def add_allowed_path(self, path: Path):
        """添加允许访问的路径"""
        path = Path(path).resolve()
        if path.exists():
            self.allowed_paths.append(path)
    
    def _is_path_allowed(self, path: Path) -> bool:
        """检查路径是否允许访问"""
        path = Path(path).resolve()
        
        for allowed in self.allowed_paths:
            try:
                path.relative_to(allowed)
                return True
            except ValueError:
                continue
        
        return False
    
    async def list_directory(self, path: str, show_hidden: bool = False) -> RemoteResult:
        """列出目录内容"""
        try:
            target_path = Path(path).resolve()
            
            if not self._is_path_allowed(target_path):
                return RemoteResult(
                    success=False,
                    action=RemoteAction.LIST_DIR,
                    error="Path not allowed"
                )
            
            if not target_path.exists():
                return RemoteResult(
                    success=False,
                    action=RemoteAction.LIST_DIR,
                    error="Path does not exist"
                )
            
            if not target_path.is_dir():
                return RemoteResult(
                    success=False,
                    action=RemoteAction.LIST_DIR,
                    error="Path is not a directory"
                )
            
            items = []
            for item in target_path.iterdir():
                if not show_hidden and item.name.startswith('.'):
                    continue
                
                stat = item.stat()
                items.append({
                    "name": item.name,
                    "type": "dir" if item.is_dir() else "file",
                    "size": stat.st_size if item.is_file() else 0,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "path": str(item)
                })
            
            # 按类型和名称排序
            items.sort(key=lambda x: (x["type"] != "dir", x["name"].lower()))
            
            return RemoteResult(
                success=True,
                action=RemoteAction.LIST_DIR,
                data={
                    "path": str(target_path),
                    "items": items,
                    "count": len(items)
                }
            )
            
        except Exception as e:
            return RemoteResult(
                success=False,
                action=RemoteAction.LIST_DIR,
                error=str(e)
            )
    
    async def read_file(self, path: str, encoding: str = "utf-8", lines: int = None) -> RemoteResult:
        """读取文件"""
        try:
            target_path = Path(path).resolve()
            
            if not self._is_path_allowed(target_path):
                return RemoteResult(
                    success=False,
                    action=RemoteAction.READ_FILE,
                    error="Path not allowed"
                )
            
            if not target_path.exists():
                return RemoteResult(
                    success=False,
                    action=RemoteAction.READ_FILE,
                    error="File does not exist"
                )
            
            if not target_path.is_file():
                return RemoteResult(
                    success=False,
                    action=RemoteAction.READ_FILE,
                    error="Path is not a file"
                )
            
            # 限制文件大小
            if target_path.stat().st_size > 10 * 1024 * 1024:  # 10MB
                return RemoteResult(
                    success=False,
                    action=RemoteAction.READ_FILE,
                    error="File too large (>10MB)"
                )
            
            content = target_path.read_text(encoding=encoding)
            
            # 限制行数
            if lines:
                content_lines = content.split('\n')
                content = '\n'.join(content_lines[:lines])
            
            return RemoteResult(
                success=True,
                action=RemoteAction.READ_FILE,
                data={
                    "path": str(target_path),
                    "content": content,
                    "size": len(content),
                    "lines": len(content.split('\n'))
                },
                metadata={
                    "encoding": encoding
                }
            )
            
        except Exception as e:
            return RemoteResult(
                success=False,
                action=RemoteAction.READ_FILE,
                error=str(e)
            )
    
    async def write_file(self, path: str, content: str, encoding: str = "utf-8", append: bool = False) -> RemoteResult:
        """写入文件"""
        try:
            target_path = Path(path).resolve()
            
            if not self._is_path_allowed(target_path):
                return RemoteResult(
                    success=False,
                    action=RemoteAction.WRITE_FILE,
                    error="Path not allowed"
                )
            
            # 创建父目录
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 写入文件
            if append:
                mode = "a"
            else:
                mode = "w"
            
            with open(target_path, mode, encoding=encoding) as f:
                f.write(content)
            
            return RemoteResult(
                success=True,
                action=RemoteAction.WRITE_FILE,
                data={
                    "path": str(target_path),
                    "bytes_written": len(content),
                    "mode": "append" if append else "write"
                }
            )
            
        except Exception as e:
            return RemoteResult(
                success=False,
                action=RemoteAction.WRITE_FILE,
                error=str(e)
            )
    
    async def delete_file(self, path: str) -> RemoteResult:
        """删除文件"""
        try:
            target_path = Path(path).resolve()
            
            if not self._is_path_allowed(target_path):
                return RemoteResult(
                    success=False,
                    action=RemoteAction.DELETE_FILE,
                    error="Path not allowed"
                )
            
            if not target_path.exists():
                return RemoteResult(
                    success=False,
                    action=RemoteAction.DELETE_FILE,
                    error="Path does not exist"
                )
            
            if target_path.is_dir():
                shutil.rmtree(target_path)
            else:
                target_path.unlink()
            
            return RemoteResult(
                success=True,
                action=RemoteAction.DELETE_FILE,
                data={"path": str(target_path)}
            )
            
        except Exception as e:
            return RemoteResult(
                success=False,
                action=RemoteAction.DELETE_FILE,
                error=str(e)
            )
    
    async def copy_file(self, source: str, destination: str) -> RemoteResult:
        """复制文件"""
        try:
            src_path = Path(source).resolve()
            dst_path = Path(destination).resolve()
            
            if not self._is_path_allowed(src_path):
                return RemoteResult(
                    success=False,
                    action=RemoteAction.COPY_FILE,
                    error="Source path not allowed"
                )
            
            if not self._is_path_allowed(dst_path):
                return RemoteResult(
                    success=False,
                    action=RemoteAction.COPY_FILE,
                    error="Destination path not allowed"
                )
            
            # 创建目标父目录
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            
            if src_path.is_dir():
                shutil.copytree(src_path, dst_path)
            else:
                shutil.copy2(src_path, dst_path)
            
            return RemoteResult(
                success=True,
                action=RemoteAction.COPY_FILE,
                data={
                    "source": str(src_path),
                    "destination": str(dst_path)
                }
            )
            
        except Exception as e:
            return RemoteResult(
                success=False,
                action=RemoteAction.COPY_FILE,
                error=str(e)
            )
    
    async def move_file(self, source: str, destination: str) -> RemoteResult:
        """移动文件"""
        try:
            src_path = Path(source).resolve()
            dst_path = Path(destination).resolve()
            
            if not self._is_path_allowed(src_path):
                return RemoteResult(
                    success=False,
                    action=RemoteAction.MOVE_FILE,
                    error="Source path not allowed"
                )
            
            if not self._is_path_allowed(dst_path):
                return RemoteResult(
                    success=False,
                    action=RemoteAction.MOVE_FILE,
                    error="Destination path not allowed"
                )
            
            # 创建目标父目录
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.move(str(src_path), str(dst_path))
            
            return RemoteResult(
                success=True,
                action=RemoteAction.MOVE_FILE,
                data={
                    "source": str(src_path),
                    "destination": str(dst_path)
                }
            )
            
        except Exception as e:
            return RemoteResult(
                success=False,
                action=RemoteAction.MOVE_FILE,
                error=str(e)
            )
    
    async def create_directory(self, path: str) -> RemoteResult:
        """创建目录"""
        try:
            target_path = Path(path).resolve()
            
            if not self._is_path_allowed(target_path):
                return RemoteResult(
                    success=False,
                    action=RemoteAction.CREATE_DIR,
                    error="Path not allowed"
                )
            
            target_path.mkdir(parents=True, exist_ok=True)
            
            return RemoteResult(
                success=True,
                action=RemoteAction.CREATE_DIR,
                data={"path": str(target_path)}
            )
            
        except Exception as e:
            return RemoteResult(
                success=False,
                action=RemoteAction.CREATE_DIR,
                error=str(e)
            )
    
    async def get_screenshot(self) -> RemoteResult:
        """获取屏幕截图"""
        try:
            # 使用 PIL 和 mss
            try:
                import mss
                import numpy as np
                from PIL import Image
                
                with mss.mss() as sct:
                    # 获取主显示器
                    monitor = sct.monitors[0]
                    screenshot = sct.grab(monitor)
                    
                    # 转换为 PIL Image
                    img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
                    
                    # 转换为 base64
                    import io
                    buffer = io.BytesIO()
                    img.save(buffer, format="PNG")
                    screenshot_base64 = base64.b64encode(buffer.getvalue()).decode()
                
                return RemoteResult(
                    success=True,
                    action=RemoteAction.GET_SCREENSHOT,
                    data={"format": "png", "size": screenshot.size},
                    metadata={"screenshot": screenshot_base64}
                )
                
            except ImportError:
                return RemoteResult(
                    success=False,
                    action=RemoteAction.GET_SCREENSHOT,
                    error="mss library not installed"
                )
            
        except Exception as e:
            return RemoteResult(
                success=False,
                action=RemoteAction.GET_SCREENSHOT,
                error=str(e)
            )
    
    async def run_command(self, command: str, shell: bool = True, timeout: int = 30) -> RemoteResult:
        """运行命令"""
        try:
            # 安全检查
            dangerous_commands = ["rm -rf /", "del /f /s /q C:", "format", "dd if="]
            for cmd in dangerous_commands:
                if cmd in command.lower():
                    return RemoteResult(
                        success=False,
                        action=RemoteAction.RUN_COMMAND,
                        error="Command not allowed for security reasons"
                    )
            
            result = subprocess.run(
                command,
                shell=shell,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return RemoteResult(
                success=result.returncode == 0,
                action=RemoteAction.RUN_COMMAND,
                data={
                    "command": command,
                    "returncode": result.returncode,
                    "stdout": result.stdout[:10000],
                    "stderr": result.stderr[:10000]
                }
            )
            
        except subprocess.TimeoutExpired:
            return RemoteResult(
                success=False,
                action=RemoteAction.RUN_COMMAND,
                error=f"Command timeout after {timeout} seconds"
            )
        except Exception as e:
            return RemoteResult(
                success=False,
                action=RemoteAction.RUN_COMMAND,
                error=str(e)
            )
    
    async def get_processes(self) -> RemoteResult:
        """获取进程列表"""
        try:
            try:
                import psutil
                
                processes = []
                for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                    try:
                        info = proc.info
                        processes.append({
                            "pid": info['pid'],
                            "name": info['name'],
                            "cpu": info['cpu_percent'],
                            "memory": info['memory_percent']
                        })
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                
                return RemoteResult(
                    success=True,
                    action=RemoteAction.GET_PROCESSES,
                    data={
                        "processes": processes[:100],  # 限制数量
                        "count": len(processes)
                    }
                )
                
            except ImportError:
                # Windows 平台
                result = subprocess.run(
                    "tasklist /FO CSV /NH",
                    shell=True,
                    capture_output=True,
                    text=True
                )
                
                processes = []
                for line in result.stdout.strip().split('\n'):
                    if line:
                        parts = line.split('","')
                        if len(parts) >= 2:
                            processes.append({
                                "name": parts[0].strip('"'),
                                "pid": parts[1].strip('"')
                            })
                
                return RemoteResult(
                    success=True,
                    action=RemoteAction.GET_PROCESSES,
                    data={
                        "processes": processes[:100],
                        "count": len(processes)
                    }
                )
                
        except Exception as e:
            return RemoteResult(
                success=False,
                action=RemoteAction.GET_PROCESSES,
                error=str(e)
            )
    
    async def kill_process(self, pid: int) -> RemoteResult:
        """终止进程"""
        try:
            try:
                import psutil
                proc = psutil.Process(pid)
                proc.kill()
            except ImportError:
                # Windows
                subprocess.run(f"taskkill /F /PID {pid}", shell=True)
            
            return RemoteResult(
                success=True,
                action=RemoteAction.KILL_PROCESS,
                data={"pid": pid}
            )
            
        except Exception as e:
            return RemoteResult(
                success=False,
                action=RemoteAction.KILL_PROCESS,
                error=str(e)
            )
    
    async def get_clipboard(self) -> RemoteResult:
        """获取剪贴板"""
        try:
            try:
                import pyperclip
                text = pyperclip.paste()
                
                return RemoteResult(
                    success=True,
                    action=RemoteAction.GET_CLIPBOARD,
                    data={"text": text}
                )
            except ImportError:
                # Windows
                import io
                import sys
                
                # 使用 PowerShell 获取剪贴板
                result = subprocess.run(
                    'powershell -Command "Get-Clipboard"',
                    shell=True,
                    capture_output=True,
                    text=True
                )
                
                return RemoteResult(
                    success=True,
                    action=RemoteAction.GET_CLIPBOARD,
                    data={"text": result.stdout.strip()}
                )
                
        except Exception as e:
            return RemoteResult(
                success=False,
                action=RemoteAction.GET_CLIPBOARD,
                error=str(e)
            )
    
    async def set_clipboard(self, text: str) -> RemoteResult:
        """设置剪贴板"""
        try:
            try:
                import pyperclip
                pyperclip.copy(text)
                
                return RemoteResult(
                    success=True,
                    action=RemoteAction.SET_CLIPBOARD,
                    data={"length": len(text)}
                )
            except ImportError:
                # Windows
                subprocess.run(
                    f'echo {text} | clip',
                    shell=True,
                    capture_output=True
                )
                
                return RemoteResult(
                    success=True,
                    action=RemoteAction.SET_CLIPBOARD,
                    data={"length": len(text)}
                )
                
        except Exception as e:
            return RemoteResult(
                success=False,
                action=RemoteAction.SET_CLIPBOARD,
                error=str(e)
            )


# 简化导入
__all__ = [
    "RemoteAction",
    "RemoteResult",
    "RemoteFileOperator"
]
