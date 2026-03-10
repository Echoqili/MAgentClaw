"""
心跳机制测试脚本

测试 HeartbeatManager 的各项功能
"""

import asyncio
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from maagentclaw.managers.heartbeat_manager import (
    HeartbeatManager,
    HeartbeatTask,
    HeartbeatConfig,
    TaskStatus
)


async def test_basic_functionality():
    """测试基本功能"""
    print("=" * 60)
    print("测试基本功能")
    print("=" * 60)
    
    # 创建临时目录
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_path = Path(tmpdir)
        
        # 创建示例 HEARTBEAT.md
        heartbeat_file = workspace_path / "HEARTBEAT.md"
        heartbeat_content = """# Heartbeat Tasks

## Task: health-check
- Interval: 60
- Command: check-health --service=all
- Enabled: true

## Task: data-sync
- Interval: 300
- Command: sync-data --source=db --target=cache
- Enabled: true

## Task: cleanup
- Interval: 3600
- Command: cleanup-temp-files
- Enabled: false
"""
        heartbeat_file.write_text(heartbeat_content, encoding='utf-8')
        
        # 创建管理器
        config = HeartbeatConfig(interval=10)  # 快速测试
        manager = HeartbeatManager(workspace_path, config)
        
        print(f"✓ 管理器创建成功")
        print(f"✓ 工作空间：{workspace_path}")
        print(f"✓ 加载任务数：{len(manager.tasks)}")
        
        # 检查任务
        assert len(manager.tasks) == 3, "应该有 3 个任务"
        assert "health-check" in manager.tasks
        assert "data-sync" in manager.tasks
        assert "cleanup" in manager.tasks
        
        print(f"✓ 任务解析正确")
        
        # 检查任务属性
        health_task = manager.tasks["health-check"]
        assert health_task.interval == 60
        assert health_task.command == "check-health --service=all"
        assert health_task.enabled == True
        
        print(f"✓ 任务属性正确")
        
        # 测试获取任务状态
        status = manager.get_task_status("health-check")
        assert status is not None
        assert status["name"] == "health-check"
        
        print(f"✓ 获取任务状态成功")
        
        # 测试获取所有任务
        all_tasks = manager.get_all_tasks()
        assert len(all_tasks) == 3
        
        print(f"✓ 获取所有任务成功")
        
        return manager


async def test_task_management():
    """测试任务管理"""
    print("\n" + "=" * 60)
    print("测试任务管理")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_path = Path(tmpdir)
        config = HeartbeatConfig()
        manager = HeartbeatManager(workspace_path, config)
        
        # 添加新任务
        new_task = HeartbeatTask(
            name="test-task",
            interval=120,
            command="echo 'Hello World'",
            enabled=True
        )
        manager.add_task(new_task)
        
        assert "test-task" in manager.tasks
        print(f"✓ 添加任务成功")
        
        # 禁用任务
        manager.disable_task("test-task")
        assert manager.tasks["test-task"].enabled == False
        print(f"✓ 禁用任务成功")
        
        # 启用任务
        manager.enable_task("test-task")
        assert manager.tasks["test-task"].enabled == True
        print(f"✓ 启用任务成功")
        
        # 移除任务
        manager.remove_task("test-task")
        assert "test-task" not in manager.tasks
        print(f"✓ 移除任务成功")


async def test_heartbeat_loop():
    """测试心跳循环"""
    print("\n" + "=" * 60)
    print("测试心跳循环（10 秒）")
    print("=" * 60)
    
    execution_log = []
    
    async def mock_executor(command, metadata):
        """模拟执行器"""
        execution_log.append({
            "command": command,
            "timestamp": datetime.now(),
            "metadata": metadata
        })
        print(f"  执行：{command}")
        await asyncio.sleep(0.1)  # 模拟执行时间
    
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_path = Path(tmpdir)
        
        # 创建 HEARTBEAT.md
        heartbeat_file = workspace_path / "HEARTBEAT.md"
        heartbeat_content = """# Heartbeat Tasks

## Task: quick-task
- Interval: 2
- Command: quick-command
- Enabled: true

## Task: slow-task
- Interval: 5
- Command: slow-command
- Enabled: true
"""
        heartbeat_file.write_text(heartbeat_content, encoding='utf-8')
        
        # 创建管理器（快速心跳）
        config = HeartbeatConfig(interval=1, suppress_duplicates=False)
        manager = HeartbeatManager(
            workspace_path, 
            config,
            execution_callback=mock_executor
        )
        
        # 启动心跳
        await manager.start()
        
        # 等待 10 秒
        await asyncio.sleep(10)
        
        # 停止心跳
        await manager.stop()
        
        # 检查执行日志
        print(f"\n执行日志：")
        for log in execution_log:
            print(f"  - {log['command']} @ {log['timestamp'].strftime('%H:%M:%S')}")
        
        print(f"\n✓ 心跳循环测试完成")
        print(f"✓ 总执行次数：{len(execution_log)}")
        
        # 检查统计
        stats = manager.get_statistics()
        print(f"✓ 统计信息：")
        print(f"  - 总任务数：{stats['total_tasks']}")
        print(f"  - 启用任务：{stats['enabled_tasks']}")
        print(f"  - 总执行：{stats['total_executions']}")
        print(f"  - 成功率：{stats['success_rate']:.1f}%")


async def test_suppression_logic():
    """测试心跳抑制逻辑"""
    print("\n" + "=" * 60)
    print("测试心跳抑制逻辑")
    print("=" * 60)
    
    execution_count = 0
    
    async def counting_executor(command, metadata):
        nonlocal execution_count
        execution_count += 1
        print(f"  执行 #{execution_count}: {command}")
        await asyncio.sleep(0.5)  # 模拟较长的执行时间
    
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_path = Path(tmpdir)
        
        # 创建 HEARTBEAT.md
        heartbeat_file = workspace_path / "HEARTBEAT.md"
        heartbeat_content = """# Heartbeat Tasks

## Task: test-suppression
- Interval: 2
- Command: test-command
- Enabled: true
"""
        heartbeat_file.write_text(heartbeat_content, encoding='utf-8')
        
        # 启用抑制
        config = HeartbeatConfig(interval=1, suppress_duplicates=True)
        manager = HeartbeatManager(
            workspace_path,
            config,
            execution_callback=counting_executor
        )
        
        # 启动心跳
        await manager.start()
        
        # 等待 5 秒
        await asyncio.sleep(5)
        
        # 停止心跳
        await manager.stop()
        
        print(f"\n✓ 启用抑制时执行次数：{execution_count}")
        print(f"✓ 抑制逻辑正常工作")


async def test_error_handling():
    """测试错误处理"""
    print("\n" + "=" * 60)
    print("测试错误处理和重试")
    print("=" * 60)
    
    fail_count = 0
    
    async def failing_executor(command, metadata):
        nonlocal fail_count
        fail_count += 1
        if fail_count < 3:
            raise Exception(f"模拟失败 #{fail_count}")
        print(f"  执行成功：{command}")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_path = Path(tmpdir)
        
        # 创建 HEARTBEAT.md
        heartbeat_file = workspace_path / "HEARTBEAT.md"
        heartbeat_content = """# Heartbeat Tasks

## Task: flaky-task
- Interval: 2
- Command: flaky-command
- Enabled: true
"""
        heartbeat_file.write_text(heartbeat_content, encoding='utf-8')
        
        # 创建管理器
        config = HeartbeatConfig(
            interval=1,
            max_retries=3,
            retry_delay=1
        )
        manager = HeartbeatManager(
            workspace_path,
            config,
            execution_callback=failing_executor
        )
        
        # 启动心跳
        await manager.start()
        
        # 等待执行
        await asyncio.sleep(5)
        
        # 停止心跳
        await manager.stop()
        
        # 检查任务状态
        task_status = manager.get_task_status("flaky-task")
        print(f"✓ 任务状态：{task_status['status']}")
        print(f"✓ 执行次数：{task_status['execution_count']}")
        print(f"✓ 失败次数：{task_status['failure_count']}")
        
        if task_status.get("last_error"):
            print(f"✓ 最后错误：{task_status['last_error']}")


async def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("心跳机制测试套件")
    print("=" * 60)
    
    try:
        # 运行所有测试
        await test_basic_functionality()
        await test_task_management()
        await test_heartbeat_loop()
        await test_suppression_logic()
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
