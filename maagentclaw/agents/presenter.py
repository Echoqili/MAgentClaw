"""
展示员Agent (Presenter Agent)

负责将系统处理结果以清晰、结构化、用户友好的方式进行呈现
参考"三郡六县制"：如同古代的"郡守"或"县令"，负责向百姓展示政令
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import re


class OutputFormat(Enum):
    """输出格式"""
    MARKDOWN = "markdown"
    HTML = "html"
    JSON = "json"
    PLAIN_TEXT = "plain_text"
    TABLE = "table"
    CARD = "card"


class PresentationStyle(Enum):
    """展示风格"""
    FORMAL = "formal"       # 正式
    CASUAL = "casual"       # 随意
    TECHNICAL = "technical"  # 技术
    BUSINESS = "business"   # 商务
    EDUCATIONAL = "educational"  # 教育


@dataclass
class PresentationConfig:
    """展示配置"""
    name: str = "presenter"
    role: str = "结果展示员"
    
    # 输出设置
    default_format: OutputFormat = OutputFormat.MARKDOWN
    default_style: PresentationStyle = PresentationStyle.FORMAL
    
    # 展示选项
    include_summary: bool = True
    include_details: bool = True
    include_metadata: bool = True
    max_depth: int = 3
    
    # 格式化选项
    code_highlight: bool = True
    emoji_enabled: bool = True
    table_border: bool = True
    
    # 角色定义
    goal: str = "以清晰、结构化的方式呈现信息"
    backstory: str = """你是一位专业的内容展示专家，擅长将复杂的信息
    以简洁美观的方式呈现。你精通各种文档格式，
    能够根据不同的场景和受众选择最合适的展示方式。"""
    responsibilities: List[str] = field(default_factory=lambda: [
        "格式化输出内容",
        "生成结构化展示",
        "创建可视化图表",
        "优化用户体验",
        "适配不同终端"
    ])


@dataclass
class PresentationSection:
    """展示区块"""
    title: str = ""
    content: Any = None
    content_type: str = "text"  # text, code, table, list, chart, image
    collapsible: bool = False
    order: int = 0


@dataclass
class PresentationResult:
    """展示结果"""
    title: str = ""
    summary: str = ""
    sections: List[PresentationSection] = field(default_factory=list)
    
    format: OutputFormat = OutputFormat.MARKDOWN
    style: PresentationStyle = PresentationStyle.FORMAL
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


class PresenterAgent:
    """展示员Agent
    
    如同古代的"郡守"或"县令"，负责将处理结果以最佳方式呈现给用户
    展示员负责将系统输出转换为用户友好的格式
    """
    
    def __init__(self, config: Optional[PresentationConfig] = None):
        self.config = config or PresentationConfig()
        self.presentation_history: List[PresentationResult] = []
    
    async def initialize(self) -> bool:
        """初始化展示员"""
        return True
    
    async def present(
        self,
        data: Any,
        title: str = "",
        format: Optional[OutputFormat] = None,
        style: Optional[PresentationStyle] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> PresentationResult:
        """展示数据"""
        result = PresentationResult(
            title=title,
            format=format or self.config.default_format,
            style=style or self.config.default_style
        )
        
        options = options or {}
        
        # 1. 生成摘要
        if self.config.include_summary:
            result.summary = self._generate_summary(data)
        
        # 2. 结构化数据
        sections = self._structure_data(data, options)
        result.sections = sections
        
        # 3. 根据格式渲染
        rendered = await self._render(result, format or self.config.default_format)
        result.metadata["rendered"] = rendered
        
        # 保存到历史
        self.presentation_history.append(result)
        
        return result
    
    def _generate_summary(self, data: Any) -> str:
        """生成摘要"""
        if isinstance(data, dict):
            keys = list(data.keys())
            if len(keys) <= 3:
                return f"包含 {len(keys)} 个字段: {', '.join(keys)}"
            else:
                return f"包含 {len(keys)} 个字段，其中主要字段包括: {', '.join(keys[:3])} 等"
        
        elif isinstance(data, list):
            return f"包含 {len(data)} 个项目"
        
        elif isinstance(data, str):
            words = data.split()
            return f"包含 {len(words)} 个字的内容"
        
        return "数据摘要"
    
    def _structure_data(
        self,
        data: Any,
        options: Dict[str, Any]
    ) -> List[PresentationSection]:
        """结构化数据"""
        sections = []
        
        if isinstance(data, dict):
            # 字典类型
            sections.extend(self._structure_dict(data, options))
        
        elif isinstance(data, list):
            # 列表类型
            sections.extend(self._structure_list(data, options))
        
        elif isinstance(data, str):
            # 字符串类型
            sections.append(PresentationSection(
                title="内容",
                content=data,
                content_type="text"
            ))
        
        else:
            # 其他类型
            sections.append(PresentationSection(
                title="数据",
                content=str(data),
                content_type="text"
            ))
        
        return sections
    
    def _structure_dict(
        self,
        data: Dict,
        options: Dict[str, Any]
    ) -> List[PresentationSection]:
        """结构化字典数据"""
        sections = []
        
        depth = options.get("depth", 0)
        max_depth = self.config.max_depth
        
        if depth > max_depth:
            return [PresentationSection(
                title="数据",
                content=str(data)[:100] + "...",
                content_type="text"
            )]
        
        # 主要信息
        main_keys = ["result", "status", "message", "data", "content", "output"]
        main_data = {k: data[k] for k in main_keys if k in data}
        
        if main_data:
            sections.append(PresentationSection(
                title="结果",
                content=main_data,
                content_type="json",
                order=0
            ))
        
        # 其他信息
        other_keys = [k for k in data.keys() if k not in main_keys]
        if other_keys:
            other_data = {k: data[k] for k in other_keys}
            sections.append(PresentationSection(
                title="详细信息",
                content=other_data,
                content_type="json",
                order=1
            ))
        
        return sections
    
    def _structure_list(
        self,
        data: List,
        options: Dict[str, Any]
    ) -> List[PresentationSection]:
        """结构化列表数据"""
        sections = []
        
        if not data:
            return [PresentationSection(
                title="列表",
                content="无数据",
                content_type="text"
            )]
        
        # 列表概览
        sections.append(PresentationSection(
            title=f"列表 ({len(data)} 项)",
            content=f"共 {len(data)} 个项目",
            content_type="text"
        ))
        
        # 如果是字典列表，显示表格
        if data and isinstance(data[0], dict):
            sections.append(PresentationSection(
                title="数据表格",
                content=data,
                content_type="table"
            ))
        
        return sections
    
    async def _render(
        self,
        result: PresentationResult,
        format: OutputFormat
    ) -> str:
        """渲染为指定格式"""
        if format == OutputFormat.MARKDOWN:
            return await self._render_markdown(result)
        elif format == OutputFormat.HTML:
            return await self._render_html(result)
        elif format == OutputFormat.JSON:
            return await self._render_json(result)
        elif format == OutputFormat.PLAIN_TEXT:
            return await self._render_plain_text(result)
        elif format == OutputFormat.TABLE:
            return await self._render_table(result)
        else:
            return str(result.sections)
    
    async def _render_markdown(self, result: PresentationResult) -> str:
        """渲染为 Markdown"""
        lines = []
        
        # 标题
        if result.title:
            lines.append(f"# {result.title}")
            lines.append("")
        
        # 摘要
        if result.summary:
            lines.append(f"> {result.summary}")
            lines.append("")
        
        # 各个区块
        for section in result.sections:
            if section.title:
                lines.append(f"## {section.title}")
                lines.append("")
            
            content = section.content
            
            if section.content_type == "text":
                lines.append(str(content))
            
            elif section.content_type == "code":
                lang = section.content.get("language", "")
                code = section.content.get("code", str(content))
                lines.append(f"```{lang}")
                lines.append(code)
                lines.append("```")
            
            elif section.content_type == "json":
                if isinstance(content, dict):
                    lines.append("```json")
                    lines.append(json.dumps(content, ensure_ascii=False, indent=2))
                    lines.append("```")
                else:
                    lines.append(str(content))
            
            elif section.content_type == "table":
                lines.extend(self._render_table_content(content))
            
            elif section.content_type == "list":
                for item in content:
                    lines.append(f"- {item}")
            
            lines.append("")
        
        return "\n".join(lines)
    
    def _render_table_content(self, data: List) -> List[str]:
        """渲染表格内容"""
        if not data or not isinstance(data[0], dict):
            return [str(item) for item in data]
        
        # 获取所有键
        keys = list(data[0].keys())
        
        # 表头
        lines = ["| " + " | ".join(keys) + " |"]
        
        # 分隔符
        lines.append("| " + " | ".join(["---"] * len(keys)) + " |")
        
        # 数据行
        for row in data:
            values = [str(row.get(k, "")) for k in keys]
            lines.append("| " + " | ".join(values) + " |")
        
        return lines
    
    async def _render_html(self, result: PresentationResult) -> str:
        """渲染为 HTML"""
        html = ['<!DOCTYPE html>', '<html>', '<head>',
                '<meta charset="utf-8">',
                '<title>' + result.title + '</title>',
                '<style>body{font-family:Arial,sans-serif;margin:20px}',
                '.section{margin:20px 0}', '.title{color:#333}',
                'table{border-collapse:collapse;width:100%}',
                'th,td{border:1px solid #ddd;padding:8px;text-align:left}',
                'th{background:#f5f5f5}</style>',
                '</head>', '<body>']
        
        if result.title:
            html.append(f'<h1>{result.title}</h1>')
        
        if result.summary:
            html.append(f'<blockquote>{result.summary}</blockquote>')
        
        for section in result.sections:
            if section.title:
                html.append(f'<div class="section"><h2>{section.title}</h2>')
            
            if section.content_type == "table":
                html.append('<table>')
                if isinstance(section.content, list) and section.content:
                    keys = list(section.content[0].keys())
                    html.append('<thead><tr>')
                    for k in keys:
                        html.append(f'<th>{k}</th>')
                    html.append('</tr></thead><tbody>')
                    for row in section.content:
                        html.append('<tr>')
                        for k in keys:
                            html.append(f'<td>{row.get(k,"")}</td>')
                        html.append('</tr>')
                    html.append('</tbody></table>')
            else:
                html.append(f'<pre>{section.content}</pre>')
            
            if section.title:
                html.append('</div>')
        
        html.extend(['</body>', '</html>'])
        return '\n'.join(html)
    
    async def _render_json(self, result: PresentationResult) -> str:
        """渲染为 JSON"""
        output = {
            "title": result.title,
            "summary": result.summary,
            "sections": []
        }
        
        for section in result.sections:
            output["sections"].append({
                "title": section.title,
                "content": section.content,
                "type": section.content_type
            })
        
        return json.dumps(output, ensure_ascii=False, indent=2)
    
    async def _render_plain_text(self, result: PresentationResult) -> str:
        """渲染为纯文本"""
        lines = []
        
        if result.title:
            lines.append("=" * len(result.title))
            lines.append(result.title)
            lines.append("=" * len(result.title))
        
        if result.summary:
            lines.append(result.summary)
            lines.append("")
        
        for section in result.sections:
            if section.title:
                lines.append(f"\n[{section.title}]")
                lines.append("-" * len(section.title))
            
            content = section.content
            if isinstance(content, dict):
                for k, v in content.items():
                    lines.append(f"  {k}: {v}")
            elif isinstance(content, list):
                for item in content:
                    lines.append(f"  - {item}")
            else:
                lines.append(f"  {content}")
        
        return "\n".join(lines)
    
    async def _render_table(self, result: PresentationResult) -> str:
        """渲染为表格"""
        # 查找表格数据
        table_data = None
        for section in result.sections:
            if section.content_type == "table":
                table_data = section.content
                break
        
        if not table_data:
            return await self._render_markdown(result)
        
        return "\n".join(self._render_table_content(table_data))
    
    async def create_dashboard(
        self,
        widgets: List[Dict[str, Any]]
    ) -> str:
        """创建仪表板"""
        return await self._render_html(PresentationResult(
            title="仪表板",
            sections=[
                PresentationSection(
                    title=w.get("title", "Widget"),
                    content=w.get("data", {}),
                    content_type=w.get("type", "text")
                )
                for w in widgets
            ]
        ))
    
    async def create_card(
        self,
        title: str,
        content: Any,
        actions: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """创建卡片"""
        return await self._render_html(PresentationResult(
            title=title,
            sections=[
                PresentationSection(
                    title="内容",
                    content=content,
                    content_type="text"
                )
            ]
        ))
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取展示统计"""
        return {
            "total": len(self.presentation_history),
            "by_format": self._count_by_format(),
            "by_style": self._count_by_style()
        }
    
    def _count_by_format(self) -> Dict[str, int]:
        counts = {fmt.value: 0 for fmt in OutputFormat}
        for p in self.presentation_history:
            counts[p.format.value] += 1
        return counts
    
    def _count_by_style(self) -> Dict[str, int]:
        counts = {style.value: 0 for style in PresentationStyle}
        for p in self.presentation_history:
            counts[p.style.value] += 1
        return counts
