"""
Task Parser - 自然语言任务解析器

解析自然语言任务，识别意图和参数
"""

import asyncio
import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class IntentType(Enum):
    """意图类型"""
    TASK_EXECUTE = "task_execute"      # 执行任务
    QUERY_INFO = "query_info"          # 查询信息
    FILE操作 = "file_operation"         # 文件操作
    SCHEDULE = "schedule"               # 定时任务
    BROADCAST = "broadcast"             # 广播消息
    CHAT = "chat"                      # 闲聊
    UNKNOWN = "unknown"                 # 未知


@dataclass
class Intent:
    """意图"""
    type: IntentType
    confidence: float
    action: str
    entities: Dict[str, Any] = field(default_factory=dict)
    original_text: str = ""
    slots: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Action:
    """动作定义"""
    name: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    requires_confirmation: bool = False


class TaskParser:
    """自然语言任务解析器"""
    
    def __init__(self, execute_callback: Optional[Callable] = None):
        self.execute_callback = execute_callback
        
        # 意图模式
        self.intent_patterns = {
            IntentType.TASK_EXECUTE: [
                r"(帮我|帮我|请|能不能).*(做|执行|完成|处理)",
                r"(任务|工作).*(是|就是)",
                r"^(?!.*聊天).*(做|完成|执行)"
            ],
            IntentType.QUERY_INFO: [
                r"(帮我|帮我|请).*(查|找|看|了解)",
                r"(什么是|怎么|如何|为什么)",
                r"(多少|几个|哪些)"
            ],
            IntentType.FILE操作: [
                r"(打开|创建|删除|修改|读取|写入).*文件",
                r"(文件|文档|表格|图片)",
                r"(保存|导出|导入)"
            ],
            IntentType.SCHEDULE: [
                r"(定时|每天|每周|每月|到时候)",
                r"(提醒|闹钟|日程|会议)",
                r"^\d{1,2}点"
            ],
            IntentType.BROADCAST: [
                r"(通知|告诉|提醒).*(大家|所有人|全部)",
                r"(群发|广播)",
                r"(发布|公布)"
            ]
        }
        
        # 动作模板
        self.action_templates = {
            "打开文件": Action(
                name="open_file",
                description="打开文件",
                parameters={"path": ""}
            ),
            "创建文件": Action(
                name="create_file",
                description="创建新文件",
                parameters={"path": "", "content": ""}
            ),
            "删除文件": Action(
                name="delete_file",
                description="删除文件",
                parameters={"path": ""},
                requires_confirmation=True
            ),
            "读取内容": Action(
                name="read_file",
                description="读取文件内容",
                parameters={"path": ""}
            ),
            "写入内容": Action(
                name="write_file",
                description="写入文件内容",
                parameters={"path": "", "content": ""}
            ),
            "执行代码": Action(
                name="execute_code",
                description="执行代码",
                parameters={"code": ""}
            ),
            "搜索信息": Action(
                name="search",
                description="搜索信息",
                parameters={"query": ""}
            ),
            "发送消息": Action(
                name="send_message",
                description="发送消息",
                parameters={"to": "", "content": ""}
            ),
            "创建任务": Action(
                name="create_task",
                description="创建定时任务",
                parameters={"task": "", "schedule": ""}
            ),
            "查询状态": Action(
                name="query_status",
                description="查询状态",
                parameters={"target": ""}
            )
        }
    
    def parse(self, text: str) -> Intent:
        """解析文本，识别意图"""
        text = text.strip()
        
        # 1. 识别意图类型
        intent_type = self._recognize_intent(text)
        
        # 2. 提取实体
        entities = self._extract_entities(text)
        
        # 3. 识别动作
        action = self._recognize_action(text)
        
        # 4. 提取槽位
        slots = self._extract_slots(text, action)
        
        # 5. 计算置信度
        confidence = self._calculate_confidence(text, intent_type, action)
        
        return Intent(
            type=intent_type,
            confidence=confidence,
            action=action,
            entities=entities,
            original_text=text,
            slots=slots
        )
    
    def _recognize_intent(self, text: str) -> IntentType:
        """识别意图类型"""
        text_lower = text.lower()
        
        for intent_type, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return intent_type
        
        # 默认闲聊
        return IntentType.CHAT
    
    def _extract_entities(self, text: str) -> Dict[str, Any]:
        """提取实体"""
        entities = {}
        
        # 提取时间
        time_patterns = [
            (r"(\d{1,2})点(\d{1,2})分?", "time"),
            (r"(今天|明天|后天|昨天)", "date"),
            (r"(早上|上午|中午|下午|晚上)", "period"),
            (r"(周一|周二|周三|周四|周五|周六|周日)", "weekday")
        ]
        
        for pattern, entity_type in time_patterns:
            match = re.search(pattern, text)
            if match:
                entities[entity_type] = match.group(1)
        
        # 提取文件名
        file_patterns = [
            (r"['\"](.+?\.(?:txt|md|py|json|docx|xlsx|pptx))['\"]", "filename"),
            (r"(?:文件|文档)(?:叫|名|是)?(.+?)(?:\s|$)", "filename")
        ]
        
        for pattern, entity_type in file_patterns:
            match = re.search(pattern, text)
            if match:
                entities[entity_type] = match.group(1)
        
        # 提取数字
        number_patterns = [
            (r"(\d+)个", "count"),
            (r"(\d+)次", "times")
        ]
        
        for pattern, entity_type in number_patterns:
            match = re.search(pattern, text)
            if match:
                entities[entity_type] = int(match.group(1))
        
        return entities
    
    def _recognize_action(self, text: str) -> str:
        """识别动作"""
        action_keywords = {
            "打开文件": ["打开", "开启", "启动"],
            "创建文件": ["创建", "新建", "新建"],
            "删除文件": ["删除", "移除", "删掉"],
            "读取内容": ["读取", "查看", "看看"],
            "写入内容": ["写入", "写", "编辑"],
            "执行代码": ["运行", "执行", "跑"],
            "搜索信息": ["搜索", "查找", "找"],
            "发送消息": ["发送", "告诉", "通知"],
            "创建任务": ["创建任务", "添加任务", "安排"],
            "查询状态": ["查询", "看看", "状态"]
        }
        
        for action, keywords in action_keywords.items():
            if any(kw in text for kw in keywords):
                return action
        
        return "general_task"
    
    def _extract_slots(self, text: str, action: str) -> Dict[str, Any]:
        """提取槽位"""
        slots = {}
        
        if action not in self.action_templates:
            return slots
        
        template = self.action_templates[action]
        
        # 提取文件路径
        if "file" in action.lower():
            path_match = re.search(r"['\"](.+?)['\"]", text)
            if path_match:
                slots["path"] = path_match.group(1)
            else:
                # 尝试提取文件名
                filename_match = re.search(r"(?:叫|名|是)?(.+?)(?:\s|$)", text)
                if filename_match:
                    slots["path"] = filename_match.group(1).strip()
        
        # 提取代码
        if action == "执行代码":
            code_match = re.search(r"```(?:python)?\s*(.+?)```", text, re.DOTALL)
            if code_match:
                slots["code"] = code_match.group(1)
        
        # 提取查询内容
        if action == "搜索信息":
            query = text
            for kw in ["搜索", "查找", "找"]:
                query = query.replace(kw, "")
            slots["query"] = query.strip().strip("?").strip()
        
        # 提取消息内容
        if action == "发送消息":
            # 提取发送给谁
            to_match = re.search(r"(?:给|向|通知)(.+?)(?:说|告诉|发)", text)
            if to_match:
                slots["to"] = to_match.group(1).strip()
            
            # 提取内容
            content_match = re.search(r"(?:说|告诉|发)(.+)$", text)
            if content_match:
                slots["content"] = content_match.group(1).strip()
        
        return slots
    
    def _calculate_confidence(self, text: str, intent_type: IntentType, action: str) -> float:
        """计算置信度"""
        confidence = 0.5
        
        # 根据意图匹配程度加分
        for pattern in self.intent_patterns.get(intent_type, []):
            if re.search(pattern, text.lower()):
                confidence += 0.2
                break
        
        # 根据动作识别程度加分
        if action != "general_task":
            confidence += 0.2
        
        # 根据实体提取数量加分
        entities = self._extract_entities(text)
        confidence += min(len(entities) * 0.1, 0.2)
        
        return min(confidence, 1.0)
    
    async def execute_intent(self, intent: Intent) -> Dict[str, Any]:
        """执行解析后的意图"""
        if not self.execute_callback:
            return {
                "success": False,
                "error": "No execute callback configured"
            }
        
        # 构建执行参数
        params = {
            "intent": intent.type.value,
            "action": intent.action,
            "entities": intent.entities,
            "slots": intent.slots,
            "confidence": intent.confidence
        }
        
        try:
            result = await self.execute_callback(
                intent.original_text,
                params
            )
            
            return {
                "success": True,
                "intent": intent.type.value,
                "action": intent.action,
                "confidence": intent.confidence,
                "result": result
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def process(self, text: str) -> Dict[str, Any]:
        """处理文本"""
        # 1. 解析意图
        intent = self.parse(text)
        
        # 2. 如果置信度太低，使用 LLM
        if intent.confidence < 0.6 and self.execute_callback:
            try:
                prompt = f"""解析以下用户输入，识别意图和参数：
用户输入: {text}

请返回 JSON 格式：
{{
    "intent": "意图类型",
    "action": "动作名称",
    "entities": {{"实体": "值"}},
    "slots": {{"参数": "值"}},
    "confidence": 0.0-1.0
}}
"""
                result = await self.execute_callback(prompt, {})
                llm_intent = json.loads(result)
                
                # 更新 intent
                intent.type = IntentType(llm_intent.get("intent", "chat"))
                intent.action = llm_intent.get("action", intent.action)
                intent.entities.update(llm_intent.get("entities", {}))
                intent.slots.update(llm_intent.get("slots", {}))
                intent.confidence = llm_intent.get("confidence", intent.confidence)
                
            except Exception as e:
                print(f"LLM parsing error: {e}")
        
        # 3. 执行意图
        return await self.execute_intent(intent)


# 简化导入
__all__ = [
    "IntentType",
    "Intent",
    "Action",
    "TaskParser"
]
