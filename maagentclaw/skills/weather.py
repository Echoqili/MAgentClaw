"""
内置技能 - 天气查询

查询天气信息（模拟）
"""

from datetime import datetime
from ..managers.skill_manager import BaseSkill, SkillMetadata, SkillConfig, SkillResult


class WeatherSkill(BaseSkill):
    """天气查询技能"""
    
    metadata = SkillMetadata(
        name="weather",
        version="1.0.0",
        description="查询天气信息",
        author="MAgentClaw Team",
        email="team@magentclaw.com",
        tags=["weather", "query", "information"],
        category="information"
    )
    
    config = SkillConfig(
        enabled=True,
        timeout=30
    )
    
    # 模拟天气数据
    MOCK_WEATHER = {
        "beijing": {"temp": 25, "condition": "Sunny", "humidity": 45},
        "shanghai": {"temp": 28, "condition": "Cloudy", "humidity": 60},
        "guangzhou": {"temp": 32, "condition": "Rainy", "humidity": 80},
        "shenzhen": {"temp": 31, "condition": "Partly Cloudy", "humidity": 70},
        "new york": {"temp": 22, "condition": "Clear", "humidity": 50},
        "london": {"temp": 18, "condition": "Rainy", "humidity": 75},
        "tokyo": {"temp": 26, "condition": "Sunny", "humidity": 55},
    }
    
    async def execute(self, city: str = "beijing") -> SkillResult:
        """查询天气"""
        city_lower = city.lower()
        
        # 查找天气信息
        weather_data = self.MOCK_WEATHER.get(city_lower)
        
        if weather_data:
            return SkillResult(
                success=True,
                data={
                    "city": city,
                    "temperature": weather_data["temp"],
                    "condition": weather_data["condition"],
                    "humidity": weather_data["humidity"],
                    "timestamp": datetime.now().isoformat()
                },
                metadata={
                    "source": "mock",
                    "city": city
                }
            )
        else:
            # 返回随机天气数据
            import random
            temp = random.randint(15, 35)
            conditions = ["Sunny", "Cloudy", "Rainy", "Partly Cloudy"]
            
            return SkillResult(
                success=True,
                data={
                    "city": city,
                    "temperature": temp,
                    "condition": random.choice(conditions),
                    "humidity": random.randint(30, 90),
                    "timestamp": datetime.now().isoformat(),
                    "note": "This is simulated data"
                },
                metadata={
                    "source": "simulated",
                    "city": city
                }
            )


# 自动注册
skill = WeatherSkill()
