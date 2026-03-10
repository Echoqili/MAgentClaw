"""
内置技能 - Hello World

最简单的示例技能
"""

from ..managers.skill_manager import BaseSkill, SkillMetadata, SkillConfig, SkillResult


class HelloWorldSkill(BaseSkill):
    """Hello World 技能"""
    
    metadata = SkillMetadata(
        name="hello-world",
        version="1.0.0",
        description="简单的问候技能",
        author="MAgentClaw Team",
        email="team@maagentclaw.com",
        tags=["greeting", "example", "basic"],
        category="communication"
    )
    
    config = SkillConfig(
        enabled=True,
        timeout=10
    )
    
    async def execute(self, name: str = "World", greeting: str = "Hello") -> SkillResult:
        """执行问候"""
        message = f"{greeting}, {name}!"
        
        return SkillResult(
            success=True,
            data={"message": message},
            metadata={
                "name": name,
                "greeting": greeting
            }
        )


# 自动注册
skill = HelloWorldSkill()
