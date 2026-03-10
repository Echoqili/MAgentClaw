"""
内置技能 - 代码生成

根据描述生成代码片段
"""

import re
from typing import Any, Dict, List, Optional
from ..managers.skill_manager import BaseSkill, SkillMetadata, SkillConfig, SkillResult


class CodeGeneratorSkill(BaseSkill):
    """代码生成技能"""

    metadata = SkillMetadata(
        name="code-generator",
        version="1.0.0",
        description="根据描述生成代码片段，支持多种语言",
        author="MAgentClaw Team",
        email="team@maagentclaw.com",
        tags=["code", "generate", "snippet", "utility"],
        category="utility"
    )

    config = SkillConfig(
        enabled=True,
        timeout=30
    )

    TEMPLATES = {
        "python": {
            "function": 'def {name}({params}):\n    """{docstring}"""\n    pass',
            "class": 'class {name}:\n    """{docstring}"""\n    \n    def __init__(self{init_params}):\n        pass',
            "async_function": 'async def {name}({params}):\n    """{docstring}"""\n    pass'
        },
        "javascript": {
            "function": 'function {name}({params}) {{\n    // {docstring}\n}}',
            "class": 'class {name} {{\n    constructor({init_params}) {{\n        // {docstring}\n    }}\n}}',
            "async_function": 'async function {name}({params}) {{\n    // {docstring}\n}}'
        },
        "typescript": {
            "function": 'function {name}({params}): void {{\n    // {docstring}\n}}',
            "class": 'class {name} {{\n    constructor(private {init_params}) {{\n        // {docstring}\n    }}\n}}'
        }
    }

    async def execute(
        self,
        language: str,
        template: str,
        params: Optional[Dict[str, Any]] = None
    ) -> SkillResult:
        """执行代码生成"""
        params = params or {}

        try:
            if language not in self.TEMPLATES:
                return SkillResult(
                    success=False,
                    error=f"Unsupported language: {language}"
                )

            if template not in self.TEMPLATES[language]:
                return SkillResult(
                    success=False,
                    error=f"Unknown template: {template}"
                )

            code = self.TEMPLATES[language][template].format(
                name=params.get("name", "myFunction"),
                params=params.get("params", ""),
                init_params=params.get("init_params", ""),
                docstring=params.get("docstring", "")
            )

            return SkillResult(
                success=True,
                data={
                    "language": language,
                    "template": template,
                    "code": code,
                    "name": params.get("name", "myFunction")
                }
            )

        except Exception as e:
            return SkillResult(
                success=False,
                error=str(e)
            )

    def get_supported_languages(self) -> List[str]:
        """获取支持的语言"""
        return list(self.TEMPLATES.keys())

    def get_templates(self, language: str) -> List[str]:
        """获取语言模板"""
        return list(self.TEMPLATES.get(language, {}).keys())


skill = CodeGeneratorSkill()
