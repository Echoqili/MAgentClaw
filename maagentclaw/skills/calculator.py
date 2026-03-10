"""
内置技能 - 计算器

执行基本数学计算
"""

import re
from ..managers.skill_manager import BaseSkill, SkillMetadata, SkillConfig, SkillResult


class CalculatorSkill(BaseSkill):
    """计算器技能"""
    
    metadata = SkillMetadata(
        name="calculator",
        version="1.0.0",
        description="执行基本数学计算",
        author="MAgentClaw Team",
        email="team@maagentclaw.com",
        tags=["math", "calculation", "utility"],
        category="utility"
    )
    
    config = SkillConfig(
        enabled=True,
        timeout=10
    )
    
    async def execute(self, expression: str) -> SkillResult:
        """执行计算"""
        try:
            # 安全检查：只允许数字和基本运算符
            if not re.match(r'^[\d+\-*/().\s]+$', expression):
                return SkillResult(
                    success=False,
                    error="Invalid expression. Only numbers and +, -, *, /, (, ) are allowed."
                )
            
            # 执行计算
            result = eval(expression)
            
            return SkillResult(
                success=True,
                data={
                    "expression": expression,
                    "result": result
                },
                metadata={
                    "type": "calculation"
                }
            )
            
        except Exception as e:
            return SkillResult(
                success=False,
                error=f"Calculation error: {str(e)}"
            )


# 自动注册
skill = CalculatorSkill()
