"""
MAgentClaw 简化版自动化测试套件

测试所有核心模块的基本功能
"""

import asyncio
import sys
import tempfile
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

# 测试结果收集
test_results = []
passed = 0
failed = 0


def log_test(name, passed_test, error=None):
    """记录测试结果"""
    global passed, failed
    if passed_test:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name}: {error}")


async def test_heartbeat_manager():
    """测试心跳管理器"""
    print("\n📋 测试心跳管理器...")
    
    from maagentclaw.managers.heartbeat_manager import (
        HeartbeatManager, HeartbeatTask, HeartbeatConfig, TaskStatus
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        
        # 创建 HEARTBEAT.md
        heartbeat_file = workspace / "HEARTBEAT.md"
        heartbeat_file.write_text("""# Heartbeat Tasks

## Task: health-check
- Interval: 60
- Command: check-health
- Enabled: true

## Task: data-sync
- Interval: 300
- Command: sync-data
- Enabled: true
""", encoding='utf-8')
        
        # 创建管理器
        config = HeartbeatConfig(interval=1)
        manager = HeartbeatManager(workspace, config)
        
        # 测试任务加载
        log_test("任务加载", len(manager.tasks) >= 1, 
                f"期望 >=1, 实际 {len(manager.tasks)}")
        
        # 测试获取任务
        task = manager.get_task_status("health-check")
        log_test("获取任务", task is not None)
        
        # 测试添加任务
        new_task = HeartbeatTask(
            name="test-task",
            interval=60,
            command="test",
            enabled=True
        )
        manager.add_task(new_task)
        log_test("添加任务", "test-task" in manager.tasks)
        
        # 测试启用/禁用
        manager.disable_task("test-task")
        log_test("禁用任务", manager.tasks["test-task"].enabled == False)
        
        manager.enable_task("test-task")
        log_test("启用任务", manager.tasks["test-task"].enabled == True)
        
        # 测试统计
        stats = manager.get_statistics()
        log_test("统计功能", "total_tasks" in stats)


async def test_skill_manager():
    """测试技能管理器"""
    print("\n📋 测试技能管理器...")
    
    from maagentclaw.managers.skill_manager import SkillManager
    
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        manager = SkillManager(workspace)
        
        # 测试加载
        skills = manager.list_skills()
        log_test("技能加载", len(skills) >= 1,
                f"期望 >=1, 实际 {len(skills)}")
        
        # 测试执行 hello-world
        if "hello-world" in [s["name"] for s in skills]:
            result = manager.execute_skill("hello-world", name="Test")
            log_test("执行问候", result.success == True, 
                    result.error if not result.success else None)
        
        # 测试执行 calculator
        if "calculator" in [s["name"] for s in skills]:
            result = manager.execute_skill("calculator", expression="2+3*4")
            log_test("执行计算", result.success == True and result.data.get("result") == 14,
                    f"结果: {result.data if result.success else result.error}")
        
        # 测试执行 weather
        if "weather" in [s["name"] for s in skills]:
            result = manager.execute_skill("weather", city="Beijing")
            log_test("执行天气", result.success == True and "temperature" in result.data,
                    result.error if not result.success else None)
        
        # 测试统计
        stats = manager.get_statistics()
        log_test("技能统计", "total_skills" in stats)


async def test_tool_manager():
    """测试工具管理器"""
    print("\n📋 测试工具管理器...")
    
    from maagentclaw.managers.tool_manager import ToolManager
    
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        manager = ToolManager(workspace)
        
        # 测试加载
        tools = manager.list_tools()
        log_test("工具加载", len(tools) >= 1,
                f"期望 >=1, 实际 {len(tools)}")
        
        # 测试执行 json-processor
        if "json-processor" in [t["name"] for t in tools]:
            result = await manager.execute_tool(
                "json-processor",
                {"operation": "format", "json_string": '{"name":"test"}'}
            )
            log_test("JSON格式化", result.success == True,
                    result.error if not result.success else None)
        
        # 测试执行 text-processor
        if "text-processor" in [t["name"] for t in tools]:
            result = await manager.execute_tool(
                "text-processor",
                {"operation": "uppercase", "text": "hello"}
            )
            log_test("文本处理", result.success == True and result.data.get("result") == "HELLO",
                    result.error if not result.success else None)
        
        # 测试执行 word_count
        if "text-processor" in [t["name"] for t in tools]:
            result = await manager.execute_tool(
                "text-processor",
                {"operation": "word_count", "text": "hello world test"}
            )
            log_test("词数统计", result.success == True and result.data.get("word_count") == 3,
                    result.error if not result.success else None)


async def test_task_parser():
    """测试任务解析器"""
    print("\n📋 测试任务解析器...")
    
    from maagentclaw.tasks.task_parser import TaskParser, IntentType
    
    parser = TaskParser()
    
    # 测试意图识别
    intent = parser.parse("帮我打开文件 test.txt")
    log_test("文件操作识别", intent.type == IntentType.FILE操作)
    
    intent = parser.parse("搜索 AI 新闻")
    log_test("搜索识别", intent.action == "搜索信息" or intent.type == IntentType.QUERY_INFO)
    
    # 测试解析
    intent = parser.parse("每天下午3点提醒我")
    log_test("定时任务", intent.type == IntentType.SCHEDULE)
    
    # 测试置信度
    intent = parser.parse("hello")
    log_test("置信度", intent.confidence > 0)


async def test_enhanced_scheduler():
    """测试增强调度器"""
    print("\n📋 测试增强调度器...")
    
    from maagentclaw.tasks.enhanced_scheduler import (
        EnhancedScheduler, ScheduleType, CronExpression
    )
    
    # 测试 Cron 解析
    cron = CronExpression.parse("0 9 * * 1-5")
    log_test("Cron解析", cron.minute == "0" and cron.hour == "9")
    
    # 测试匹配
    test_time = datetime(2026, 3, 10, 9, 0, 0)  # 周二
    log_test("Cron匹配", cron.matches(test_time) == True)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        scheduler = EnhancedScheduler(workspace)
        
        # 测试添加任务
        task_id = scheduler.add_task(
            name="test-task",
            command="test-command",
            schedule_type=ScheduleType.INTERVAL,
            interval_seconds=60
        )
        log_test("添加任务", task_id is not None)
        
        # 测试列表
        tasks = scheduler.list_tasks()
        log_test("任务列表", len(tasks) >= 1)
        
        # 测试启用/禁用
        scheduler.disable_task(task_id)
        task = scheduler.get_task(task_id)
        log_test("禁用任务", task.enabled == False)
        
        # 测试统计
        stats = scheduler.get_statistics()
        log_test("调度统计", "total_tasks" in stats)


async def test_multi_agent_orchestrator():
    """测试多智能体编排器"""
    print("\n📋 测试多智能体编排器...")
    
    from maagentclaw.agents.multi_agent_orchestrator import (
        MultiAgentOrchestrator, AgentMode, SubAgent, AgentRole
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        orchestrator = MultiAgentOrchestrator(workspace)
        
        # 测试默认 Agent
        agents = orchestrator.list_agents()
        log_test("默认Agent", len(agents) >= 4,
                f"期望 >=4, 实际 {len(agents)}")
        
        # 测试添加自定义 Agent
        custom = SubAgent(
            id="custom",
            name="Custom",
            role=AgentRole.SPECIALIST,
            description="Test"
        )
        orchestrator.register_agent(custom)
        log_test("注册Agent", len(orchestrator.list_agents()) >= 5)
        
        # 测试会话
        thread_id = await orchestrator.create_session("user1", AgentMode.SESSION)
        log_test("创建会话", thread_id is not None)
        
        # 测试统计
        stats = orchestrator.get_statistics()
        log_test("编排器统计", "total_agents" in stats)


async def test_permission_system():
    """测试权限系统"""
    print("\n📋 测试权限系统...")
    
    from maagentclaw.managers.tool_manager import ToolManager, ToolPermission
    
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        manager = ToolManager(workspace)
        
        # 测试设置权限
        manager.set_user_permissions("user1", [ToolPermission.READ])
        perms = manager.get_user_permissions("user1")
        log_test("设置权限", ToolPermission.READ in perms)
        
        # 测试执行历史
        await manager.execute_tool(
            "json-processor",
            {"operation": "validate", "json_string": "{}"}
        )
        history = manager.get_execution_history()
        log_test("执行历史", len(history) >= 1)


async def main():
    """主函数"""
    print("=" * 60)
    print("🚀 MAgentClaw 自动化测试套件 v1.5.0")
    print("=" * 60)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    global passed, failed
    
    # 运行所有测试
    await test_heartbeat_manager()
    await test_skill_manager()
    await test_tool_manager()
    await test_task_parser()
    await test_enhanced_scheduler()
    await test_multi_agent_orchestrator()
    await test_permission_system()
    
    # 打印总结
    print("\n" + "=" * 60)
    print(f"📊 测试总结")
    print("=" * 60)
    print(f"  ✅ 通过: {passed}")
    print(f"  ❌ 失败: {failed}")
    print(f"  📈 总计: {passed + failed}")
    
    if failed == 0:
        print("\n🎉 所有测试通过！")
    else:
        print(f"\n💥 {failed} 个测试失败")
    
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
