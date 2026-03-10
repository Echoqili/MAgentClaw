"""
Web 管理界面模块
提供基于 Flask 的 Web 管理界面
"""

from flask import Flask, render_template, request, jsonify, Response
from flask_cors import CORS
import json
from typing import Any, Dict, Optional
import asyncio
from datetime import datetime


class WebInterface:
    """Web 管理界面"""
    
    def __init__(self, agent_manager: Any, config_manager: Any, 
                 collaboration_manager: Optional[Any] = None):
        self.agent_manager = agent_manager
        self.config_manager = config_manager
        self.collaboration_manager = collaboration_manager
        
        self.app = Flask(__name__, 
                        template_folder='templates',
                        static_folder='static')
        CORS(self.app)
        
        self.setup_routes()
    
    def setup_routes(self):
        """设置路由"""
        
        @self.app.route('/')
        def index():
            """主页"""
            return render_template('index.html')
        
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
        
        @self.app.route('/api/agents/<name>', methods=['GET'])
        def get_agent(name: str):
            """获取指定 Agent"""
            agent = self.agent_manager.get_agent(name)
            if agent:
                state = agent.get_state()
                return jsonify({
                    "name": name,
                    "config": {
                        "name": agent.config.name,
                        "role": agent.config.role,
                        "description": agent.config.description,
                        "model": agent.config.model
                    },
                    "state": {
                        "id": state.id,
                        "status": state.status,
                        "current_task": state.current_task
                    }
                })
            return jsonify({"error": "Agent not found"}), 404
        
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
                return jsonify({"success": False, "error": str(e)})
        
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
                return jsonify({"success": False, "error": str(e)})
        
        @self.app.route('/api/agents/<name>/message', methods=['POST'])
        def send_message(name: str):
            """发送消息给 Agent"""
            try:
                data = request.json
                content = data.get('content', '')
                
                from ..core.agent import AgentMessage
                message = AgentMessage(content=content, role="user")
                
                agent = self.agent_manager.get_agent(name)
                if not agent:
                    return jsonify({"error": "Agent not found"}), 404
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                response = loop.run_until_complete(agent.process(message))
                loop.close()
                
                return jsonify({
                    "success": True,
                    "response": {
                        "content": response.content,
                        "role": response.role,
                        "timestamp": response.timestamp.isoformat()
                    }
                })
            except Exception as e:
                return jsonify({"success": False, "error": str(e)})
        
        @self.app.route('/api/config/agents', methods=['GET'])
        def get_config_agents():
            """获取配置的 Agent 列表"""
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
                from ..config.config_manager import AgentConfigData
                config = AgentConfigData(**data)
                self.config_manager.add_agent(config)
                return jsonify({"success": True, "config": data})
            except Exception as e:
                return jsonify({"success": False, "error": str(e)})
        
        @self.app.route('/api/config/models', methods=['GET'])
        def get_config_models():
            """获取配置的模型列表"""
            models = self.config_manager.models
            return jsonify({
                "models": {name: {
                    "name": config.name,
                    "provider": config.provider,
                    "model_name": config.model_name
                } for name, config in models.items()}
            })
        
        @self.app.route('/api/tasks', methods=['POST'])
        def create_task():
            """创建任务"""
            if not self.collaboration_manager:
                return jsonify({"error": "Collaboration manager not initialized"}), 400
            
            try:
                data = request.json
                description = data.get('description', '')
                assigned_to = data.get('assigned_to')
                
                task = self.collaboration_manager.task_coordinator.create_task(
                    description, 
                    assigned_to
                )
                
                return jsonify({
                    "success": True,
                    "task": {
                        "id": task.id,
                        "description": task.description,
                        "status": task.status,
                        "assigned_to": task.assigned_to
                    }
                })
            except Exception as e:
                return jsonify({"success": False, "error": str(e)})
        
        @self.app.route('/api/sessions', methods=['POST'])
        def create_session():
            """创建协作会话"""
            if not self.collaboration_manager:
                return jsonify({"error": "Collaboration manager not initialized"}), 400
            
            try:
                data = request.json
                mode = data.get('mode', 'collaborative')
                participants = data.get('participants', [])
                
                from ..managers.collaboration import CollaborationMode
                mode_enum = CollaborationMode(mode)
                
                session = self.collaboration_manager.create_session(
                    mode=mode_enum,
                    participants=participants
                )
                
                return jsonify({
                    "success": True,
                    "session": {
                        "id": session.id,
                        "mode": session.mode.value,
                        "participants": session.participants,
                        "status": session.status
                    }
                })
            except Exception as e:
                return jsonify({"success": False, "error": str(e)})
        
        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            """健康检查"""
            return jsonify({
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "agents_count": len(self.agent_manager.agents)
            })
    
    def run(self, host: str = "0.0.0.0", port: int = 8000, debug: bool = False):
        """运行 Web 服务器"""
        self.app.run(host=host, port=port, debug=debug)
