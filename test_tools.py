"""
工具系统测试脚本

测试 ToolManager 的各项功能
"""

import asyncio
import tempfile
from pathlib import Path

# 添加项目路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from maagentclaw.managers.tool_manager import (
    ToolManager,
    ToolStatus,
    ToolPermission
)


async def test_tool_loading():
    """测试工具加载"""
    print("=" * 60)
    print("测试工具加载")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_path = Path(tmpdir)
        
        # 创建管理器
        manager = ToolManager(workspace_path)
        
        print(f"✓ 管理器创建成功")
        print(f"✓ 工作空间：{workspace_path}")
        
        # 列出工具
        tools = manager.list_tools()
        print(f"✓ 加载工具数：{len(tools)}")
        
        for tool in tools:
            print(f"  - {tool['name']} v{tool['version']} ({tool['category']})")
        
        return manager


async def test_tool_execution():
    """测试工具执行"""
    print("\n" + "=" * 60)
    print("测试工具执行")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_path = Path(tmpdir)
        manager = ToolManager(workspace_path)
        
        # 测试 JSON 处理器
        print("\n1. 测试 JSON 处理器:")
        result = await manager.execute_tool(
            "json-processor",
            {"operation": "format", "json_string": '{"name":"Alice","age":30}'}
        )
        print(f"   成功：{result.success}")
        if result.success:
            print(f"   格式化结果:\n{result.data['formatted']}")
        
        # 测试文本处理
        print("\n2. 测试文本处理器:")
        result = await manager.execute_tool(
            "text-processor",
            {"operation": "word_count", "text": "Hello World! This is a test."}
        )
        print(f"   成功：{result.success}")
        print(f"   词数：{result.data['word_count']}")
        print(f"   字符数：{result.data['char_count']}")
        
        # 测试网络搜索（模拟）
        print("\n3. 测试网络搜索:")
        result = await manager.execute_tool(
            "web-search",
            {"query": "python tutorial", "num_results": 3}
        )
        print(f"   成功：{result.success}")
        print(f"   查询：{result.data['query']}")
        print(f"   结果数：{result.data['total']}")
        if result.data['results']:
            print(f"   第一个结果：{result.data['results'][0]['title']}")
        
        # 测试代码执行
        print("\n4. 测试代码执行:")
        code = """
x = 10
y = 20
print(f"Sum: {x + y}")
result = x * y
"""
        result = await manager.execute_tool(
            "code-executor",
            {"code": code}
        )
        print(f"   成功：{result.success}")
        if result.success:
            print(f"   输出：{result.data['stdout'].strip()}")
            print(f"   变量：{result.data['variables']}")


async def test_permission_system():
    """测试权限系统"""
    print("\n" + "=" * 60)
    print("测试权限系统")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_path = Path(tmpdir)
        manager = ToolManager(workspace_path)
        
        # 设置用户权限
        user_id = "test-user"
        
        # 普通用户权限
        manager.set_user_permissions(
            user_id,
            [ToolPermission.READ, ToolPermission.EXECUTE]
        )
        
        print(f"\n✓ 设置用户权限：{[p.value for p in manager.get_user_permissions(user_id)]}")
        
        # 尝试执行需要 NETWORK 权限的工具
        print(f"\n1. 测试权限检查（应该失败）:")
        result = await manager.execute_tool(
            "web-search",
            {"query": "test"},
            user_id=user_id
        )
        print(f"   结果：{result.success}")
        print(f"   错误：{result.error}")
        
        # 添加 NETWORK 权限
        manager.set_user_permissions(
            user_id,
            [ToolPermission.READ, ToolPermission.EXECUTE, ToolPermission.NETWORK]
        )
        
        print(f"\n✓ 更新用户权限")
        
        # 再次尝试
        print(f"\n2. 测试权限检查（应该成功）:")
        result = await manager.execute_tool(
            "web-search",
            {"query": "test"},
            user_id=user_id
        )
        print(f"   结果：{result.success}")


async def test_statistics():
    """测试统计信息"""
    print("\n" + "=" * 60)
    print("测试统计信息")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_path = Path(tmpdir)
        manager = ToolManager(workspace_path)
        
        # 执行一些工具
        await manager.execute_tool("json-processor", {"operation": "validate", "json_string": '{}'})
        await manager.execute_tool("text-processor", {"operation": "uppercase", "text": "test"})
        await manager.execute_tool("web-search", {"query": "python"})
        
        # 获取统计
        stats = manager.get_statistics()
        
        print(f"\n统计信息:")
        print(f"  - 总工具数：{stats['total_tools']}")
        print(f"  - 启用工具：{stats['enabled_tools']}")
        print(f"  - 总执行次数：{stats['total_executions']}")
        print(f"  - 分类：{stats['categories']}")


async def test_error_handling():
    """测试错误处理"""
    print("\n" + "=" * 60)
    print("测试错误处理")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_path = Path(tmpdir)
        manager = ToolManager(workspace_path)
        
        # 测试不存在的工具
        print("\n1. 测试不存在的工具:")
        result = await manager.execute_tool("non-existent-tool", {})
        print(f"   成功：{result.success}")
        print(f"   错误：{result.error}")
        
        # 测试无效的 JSON
        print("\n2. 测试无效的 JSON:")
        result = await manager.execute_tool(
            "json-processor",
            {"operation": "format", "json_string": "invalid json"}
        )
        print(f"   成功：{result.success}")
        print(f"   错误：{result.error}")
        
        # 测试危险的代码
        print("\n3. 测试危险的代码:")
        result = await manager.execute_tool(
            "code-executor",
            {"code": "import os; os.system('ls')"}
        )
        print(f"   成功：{result.success}")
        print(f"   错误：{result.error}")


async def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("工具系统测试套件")
    print("=" * 60)
    
    try:
        # 运行所有测试
        await test_tool_loading()
        await test_tool_execution()
        await test_permission_system()
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
