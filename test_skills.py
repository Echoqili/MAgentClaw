"""
技能系统测试脚本

测试 SkillManager 的各项功能
"""

import asyncio
import tempfile
from pathlib import Path

# 添加项目路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from maagentclaw.managers.skill_manager import (
    SkillManager,
    SkillStatus,
    SkillConfig
)


async def test_skill_loading():
    """测试技能加载"""
    print("=" * 60)
    print("测试技能加载")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_path = Path(tmpdir)
        
        # 创建技能目录
        skills_dir = workspace_path / "skills"
        skills_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建管理器
        manager = SkillManager(workspace_path)
        
        print(f"✓ 管理器创建成功")
        print(f"✓ 工作空间：{workspace_path}")
        
        # 列出技能
        skills = manager.list_skills()
        print(f"✓ 加载技能数：{len(skills)}")
        
        for skill in skills:
            print(f"  - {skill['name']} v{skill['version']} ({skill['status']})")
        
        return manager


async def test_skill_execution():
    """测试技能执行"""
    print("\n" + "=" * 60)
    print("测试技能执行")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_path = Path(tmpdir)
        manager = SkillManager(workspace_path)
        
        # 测试 Hello World
        print("\n1. 测试 Hello World 技能:")
        result = manager.execute_skill("hello-world", name="Alice", greeting="Hi")
        print(f"   成功：{result.success}")
        print(f"   数据：{result.data}")
        
        # 测试计算器
        print("\n2. 测试计算器技能:")
        result = manager.execute_skill("calculator", expression="2 + 3 * 4")
        print(f"   成功：{result.success}")
        print(f"   表达式：{result.data['expression']}")
        print(f"   结果：{result.data['result']}")
        
        # 测试天气
        print("\n3. 测试天气技能:")
        result = manager.execute_skill("weather", city="Beijing")
        print(f"   成功：{result.success}")
        print(f"   城市：{result.data['city']}")
        print(f"   温度：{result.data['temperature']}°C")
        print(f"   天气：{result.data['condition']}")
        
        # 测试文件操作
        print("\n4. 测试文件操作技能:")
        test_file = workspace_path / "test.txt"
        result = manager.execute_skill(
            "file-operator",
            operation="write",
            path=str(test_file),
            content="Hello, World!"
        )
        print(f"   写入成功：{result.success}")
        print(f"   字节数：{result.data['bytes_written']}")
        
        # 读取文件
        result = manager.execute_skill(
            "file-operator",
            operation="read",
            path=str(test_file)
        )
        print(f"   读取成功：{result.success}")
        print(f"   内容：{result.data['content']}")


async def test_skill_management():
    """测试技能管理"""
    print("\n" + "=" * 60)
    print("测试技能管理")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_path = Path(tmpdir)
        manager = SkillManager(workspace_path)
        
        # 获取技能
        skill = manager.get_skill("hello-world")
        print(f"\n✓ 获取技能：{skill.metadata.name if skill else None}")
        
        # 禁用技能
        success = manager.disable_skill("hello-world")
        print(f"✓ 禁用技能：{success}")
        
        skill = manager.get_skill("hello-world")
        print(f"✓ 当前状态：{skill.status if skill else None}")
        
        # 启用技能
        success = manager.enable_skill("hello-world")
        print(f"✓ 启用技能：{success}")
        
        skill = manager.get_skill("hello-world")
        print(f"✓ 当前状态：{skill.status if skill else None}")


async def test_statistics():
    """测试统计信息"""
    print("\n" + "=" * 60)
    print("测试统计信息")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_path = Path(tmpdir)
        manager = SkillManager(workspace_path)
        
        # 执行一些技能
        manager.execute_skill("hello-world", name="Test")
        manager.execute_skill("calculator", expression="1+1")
        manager.execute_skill("weather", city="Shanghai")
        
        # 获取统计
        stats = manager.get_statistics()
        
        print(f"\n统计信息:")
        print(f"  - 总技能数：{stats['total_skills']}")
        print(f"  - 启用技能：{stats['enabled_skills']}")
        print(f"  - 禁用技能：{stats['disabled_skills']}")
        print(f"  - 总执行次数：{stats['total_executions']}")


async def test_error_handling():
    """测试错误处理"""
    print("\n" + "=" * 60)
    print("测试错误处理")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_path = Path(tmpdir)
        manager = SkillManager(workspace_path)
        
        # 测试不存在的技能
        print("\n1. 测试不存在的技能:")
        result = manager.execute_skill("non-existent-skill")
        print(f"   成功：{result.success}")
        print(f"   错误：{result.error}")
        
        # 测试禁用的技能
        print("\n2. 测试禁用的技能:")
        manager.disable_skill("hello-world")
        result = manager.execute_skill("hello-world")
        print(f"   成功：{result.success}")
        print(f"   错误：{result.error}")
        
        # 测试无效表达式
        print("\n3. 测试无效计算表达式:")
        result = manager.execute_skill("calculator", expression="2 + invalid")
        print(f"   成功：{result.success}")
        print(f"   错误：{result.error}")


async def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("技能系统测试套件")
    print("=" * 60)
    
    try:
        # 运行所有测试
        await test_skill_loading()
        await test_skill_execution()
        await test_skill_management()
        await test_statistics()
        await test_error_handling()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
