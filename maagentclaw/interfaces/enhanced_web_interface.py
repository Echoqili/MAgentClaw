"""
增强的 Web 界面
添加配置管理、会话查看、工作空间编辑等功能
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import json
from pathlib import Path
from typing import Any, Dict, Optional
import asyncio
from datetime import datetime
import os


class EnhancedWebInterface:
    """增强的 Web 管理界面"""
    
    def __init__(self, agent_manager: Any, config_manager: Any,
                 workspace_manager: Optional[Any] = None,
                 session_manager: Optional[Any] = None,
                 channel_manager: Optional[Any] = None,
                 model_manager: Optional[Any] = None):
        self.agent_manager = agent_manager
        self.config_manager = config_manager
        self.workspace_manager = workspace_manager
        self.session_manager = session_manager
        self.channel_manager = channel_manager
        self.model_manager = model_manager
        
        self.app = Flask(__name__,
                        template_folder='templates',
                        static_folder='static')
        CORS(self.app)
        
        self.setup_routes()
    
    def setup_routes(self):
        """设置路由"""
        
        # ===== 主页 =====
        @self.app.route('/')
        def index():
            """主页"""
            return render_template('enhanced_index.html')
        
        # ===== Agent 管理 =====
        @self.app.route('/api/agents', methods=['GET'])
        def get_agents():
            """获取所有 Agent"""
            agents = self.agent_manager.list_agents()
            states = self.agent_manager.get_all_states()
            return jsonify({
                "agents": agents,
                "states": {name: {
                    "id": state.id,
                    "name": state.name,
                    "status": state.status,
                    "current_task": state.current_task,
                    "last_active": state.last_active.isoformat()
                } for name, state in states.items()}
            })
        
        @self.app.route('/api/agents/<name>/start', methods=['POST'])
        def start_agent(name: str):
            """启动 Agent"""
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(self.agent_manager.start_agent(name))
                loop.close()
                return jsonify({"success": result})
            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 500
        
        @self.app.route('/api/agents/<name>/stop', methods=['POST'])
        def stop_agent(name: str):
            """停止 Agent"""
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(self.agent_manager.stop_agent(name))
                loop.close()
                return jsonify({"success": result})
            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 500
        
        # ===== 配置管理 =====
        @self.app.route('/api/config/agents', methods=['GET'])
        def get_config_agents():
            """获取 Agent 配置"""
            agents = self.config_manager.agents
            return jsonify({
                "agents": {name: {
                    "name": config.name,
                    "role": config.role,
                    "description": config.description,
                    "model": config.model,
                    "workspace": config.workspace
                } for name, config in agents.items()}
            })
        
        @self.app.route('/api/config/agents', methods=['POST'])
        def create_agent_config():
            """创建 Agent 配置"""
            try:
                data = request.json
                from maagentclaw.config.enhanced_config import AgentConfigData
                config = AgentConfigData(**data)
                self.config_manager.add_agent(config)
                return jsonify({"success": True, "config": data})
            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 500
        
        @self.app.route('/api/config/agents/<name>', methods=['PUT'])
        def update_agent_config(name: str):
            """更新 Agent 配置"""
            try:
                data = request.json
                self.config_manager.update_agent(name, data)
                return jsonify({"success": True})
            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 500
        
        @self.app.route('/api/config/agents/<name>', methods=['DELETE'])
        def delete_agent_config(name: str):
            """删除 Agent 配置"""
            try:
                self.config_manager.remove_agent(name)
                return jsonify({"success": True})
            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 500
        
        @self.app.route('/api/config/models', methods=['GET'])
        def get_config_models():
            """获取模型配置"""
            models = self.config_manager.models
            return jsonify({
                "models": {name: {
                    "name": config.name,
                    "provider": config.provider,
                    "model_name": config.model_name,
                    "context_window": config.context_window
                } for name, config in models.items()}
            })
        
        @self.app.route('/api/config/system', methods=['GET'])
        def get_config_system():
            """获取系统配置"""
            system = self.config_manager.system
            return jsonify({
                "system": {
                    "workspace_base": system.workspace_base,
                    "log_level": system.log_level,
                    "web_port": system.web_port,
                    "enable_web_interface": system.enable_web_interface
                }
            })
        
        # ===== 会话管理 =====
        @self.app.route('/api/sessions', methods=['GET'])
        def get_sessions():
            """获取会话列表"""
            if not self.session_manager:
                return jsonify({"sessions": []})
            
            sessions = self.session_manager.list_sessions()
            return jsonify({"sessions": sessions})
        
        @self.app.route('/api/sessions/<session_id>', methods=['GET'])
        def get_session(session_id: str):
            """获取会话详情"""
            if not self.session_manager:
                return jsonify({"error": "Session manager not available"}), 500
            
            messages = self.session_manager.get_messages(session_id, limit=50)
            stats = self.session_manager.get_session_stats(session_id)
            
            return jsonify({
                "session": stats,
                "messages": [msg.to_dict() for msg in messages]
            })
        
        @self.app.route('/api/sessions/<session_id>', methods=['DELETE'])
        def delete_session(session_id: str):
            """删除会话"""
            if not self.session_manager:
                return jsonify({"error": "Session manager not available"}), 500
            
            try:
                self.session_manager.delete_session(session_id)
                return jsonify({"success": True})
            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 500
        
        @self.app.route('/api/sessions/<session_id>/reset', methods=['POST'])
        def reset_session(session_id: str):
            """重置会话"""
            if not self.session_manager:
                return jsonify({"error": "Session manager not available"}), 500
            
            try:
                self.session_manager.reset_session(session_id)
                return jsonify({"success": True})
            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 500
        
        # ===== 工作空间管理 =====
        @self.app.route('/api/workspaces', methods=['GET'])
        def get_workspaces():
            """获取工作空间列表"""
            if not self.workspace_manager:
                return jsonify({"workspaces": []})
            
            workspaces = self.workspace_manager.list_workspaces()
            return jsonify({"workspaces": workspaces})
        
        @self.app.route('/api/workspaces/<agent_id>', methods=['GET'])
        def get_workspace(agent_id: str):
            """获取工作空间详情"""
            if not self.workspace_manager:
                return jsonify({"error": "Workspace manager not available"}), 500
            
            try:
                workspace = self.workspace_manager.get_workspace(agent_id)
                files = {}
                
                # 读取核心文件
                for filename in workspace.CORE_FILES.keys():
                    content = workspace.read_file(filename)
                    if content:
                        files[filename] = content
                
                return jsonify({
                    "workspace": {
                        "agent_id": agent_id,
                        "path": str(workspace.agent_dir)
                    },
                    "files": files
                })
            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 500
        
        @self.app.route('/api/workspaces/<agent_id>/<filename>', methods=['PUT'])
        def update_workspace_file(agent_id: str, filename: str):
            """更新工作空间文件"""
            if not self.workspace_manager:
                return jsonify({"error": "Workspace manager not available"}), 500
            
            try:
                data = request.json
                content = data.get('content', '')
                
                workspace = self.workspace_manager.get_workspace(agent_id)
                workspace.write_file(filename, content)
                
                return jsonify({"success": True})
            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 500
        
        # ===== 渠道管理 =====
        @self.app.route('/api/channels', methods=['GET'])
        def get_channels():
            """获取渠道列表"""
            if not self.channel_manager:
                return jsonify({"channels": []})
            
            channels = self.channel_manager.list_channels()
            stats = self.channel_manager.get_stats()
            
            return jsonify({
                "channels": channels,
                "stats": stats
            })
        
        # ===== 模型管理 =====
        @self.app.route('/api/models', methods=['GET'])
        def get_models():
            """获取模型列表"""
            if not self.model_manager:
                return jsonify({"models": []})
            
            models = self.model_manager.list_models()
            stats = self.model_manager.get_stats()
            
            return jsonify({
                "models": models,
                "stats": stats
            })
        
        # ===== 系统统计 =====
        @self.app.route('/api/stats', methods=['GET'])
        def get_stats():
            """获取系统统计"""
            stats = {
                "agents": len(self.agent_manager.list_agents()) if self.agent_manager else 0,
                "configs": len(self.config_manager.agents) if self.config_manager else 0,
                "sessions": len(self.session_manager.list_sessions()) if self.session_manager else 0,
                "workspaces": len(self.workspace_manager.list_workspaces()) if self.workspace_manager else 0,
                "timestamp": datetime.now().isoformat()
            }
            return jsonify(stats)
        
        # ===== 健康检查 =====
        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            """健康检查"""
            return jsonify({
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "version": "1.2.0"
            })
    
    def run(self, host: str = "0.0.0.0", port: int = 8000, debug: bool = False):
        """运行 Web 服务器"""
        self.app.run(host=host, port=port, debug=debug, threaded=True)
