"""
MAgentClaw 完整自动化测试套件

测试所有核心模块：心跳、技能、工具、渠道、编排器、任务解析、调度器等
"""

import asyncio
import sys
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

# 导入待测模块
from maagentclaw.managers.heartbeat_manager import (
    HeartbeatManager, HeartbeatTask, HeartbeatConfig, TaskStatus
)
from maagentclaw.managers.skill_manager import (
    SkillManager, SkillMetadata, SkillConfig, SkillResult, BaseSkill
)
from maagentclaw.managers.tool_manager import (
    ToolManager, ToolMetadata, ToolConfig, ToolResult, ToolPermission
)
from maagentclaw.tasks.task_parser import TaskParser, IntentType
from maagentclaw.tasks.enhanced_scheduler import (
    EnhancedScheduler, ScheduleType, CronExpression, ScheduleTemplates
)
from maagentclaw.agents.multi_agent_orchestrator import (
    MultiAgentOrchestrator, AgentMode, AgentRole, SubAgent, TaskStatus as AgentTaskStatus
)


class TestResult:
    """测试结果"""
    def __init__(self, name: str):
        self.name = name
        self.passed = False
        self.error = None
        self.duration = 0
    
    def __str__(self):
        status = "✅ PASS" if self.passed else "❌ FAIL"
        return f"{status} | {self.name} | {self.duration:.3f}s"
    
    def __repr__(self):
        return self.__str__()


class TestSuite:
    """测试套件"""
    def __init__(self, name: str):
        self.name = name
        self.results = []
    
    def add_result(self, result: TestResult):
        self.results.append(result)
    
    def print_summary(self):
        print("\n" + "=" * 70)
        print(f"📊 {self.name} 测试结果")
        print("=" * 70)
        
        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed)
        
        for result in self.results:
            print(result)
        
        print("-" * 70)
        print(f"总计: {len(self.results)} | ✅ 通过: {passed} | ❌ 失败: {failed}")
        
        if failed > 0:
            print("\n❌ 失败的测试:")
            for r in self.results:
                if not r.passed:
                    print(f"  - {r.name}: {r.error}")
        
        print("=" * 70)
        
        return failed == 0


async def test_heartbeat_basic():
    """测试心跳基础功能"""
    result = TestResult("心跳 - 基础功能")
    start = datetime.now()
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            
            # 创建 HEARTBEAT.md
            heartbeat_file = workspace / "HEARTBEAT.md"
            heartbeat_file.write_text("""# Heartbeat Tasks
## Task: test-task
- Interval: 60
- Command: test-command
- Enabled: true
""", encoding='utf-8')
            
            # 创建配置
            config = HeartbeatConfig(interval=1)
            
            # 创建管理器
            manager = HeartbeatManager(workspace, config)
            
            # 验证任务加载
            assert len(manager.tasks) == 1, "应该加载 1 个任务"
            assert "test-task" in manager.tasks, "任务名称应该正确"
            
            # 验证任务属性
            task = manager.tasks["test-task"]
            assert task.interval == 60, "间隔应该是 60"
            assert task.enabled == True, "应该启用"
            assert task.command == "test-command", "命令应该正确"
            
            # 测试任务管理
            manager.enable_task("test-task")
            assert manager.tasks["test-task"].enabled == True
            
            manager.disable_task("test-task")
            assert manager.tasks["test-task"].enabled == False
            
            # 测试获取状态
            status = manager.get_task_status("test-task")
            assert status["name"] == "test-task"
            
            # 测试统计
            stats = manager.get_statistics()
            assert stats["total_tasks"] == 1
            
            result.passed = True
            
    except Exception as e:
        result.error = str(e)
    
    result.duration = (datetime.now() - start).total_seconds()
    return result


async def test_heartbeat_execution():
    """测试心跳执行"""
    result = TestResult("心跳 - 执行测试")
    start = datetime.now()
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            
            # 创建 HEARTBEAT.md
            heartbeat_file = workspace / "HEARTBEAT.md"
            heartbeat_file.write_text("""# Heartbeat Tasks
## Task: quick-task
- Interval: 2
- Command: quick-command
- Enabled: true
""", encoding='utf-8')
            
            # 执行回调
            execution_count = 0
            async def executor(command, metadata):
                nonlocal execution_count
                execution_count += 1
                await asyncio.sleep(0.1)
            
            # 创建管理器
            config = HeartbeatConfig(interval=1, suppress_duplicates=False)
            manager = HeartbeatManager(workspace, config, executor)
            
            # 启动心跳
            await manager.start()
            
            # 等待执行
            await asyncio.sleep(5)
            
            # 停止心跳
            await manager.stop()
            
            # 验证执行次数
            assert execution_count >= 1, f"至少执行 1 次，实际 {execution_count}"
            
            result.passed = True
            
    except Exception as e:
        result.error = str(e)
    
    result.duration = (datetime.now() - start).total_seconds()
    return result


async def test_skills_loading():
    """测试技能加载"""
    result = TestResult("技能 - 加载测试")
    start = datetime.now()
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            
            # 创建管理器
            manager = SkillManager(workspace)
            
            # 验证内置技能
            skills = manager.list_skills()
            assert len(skills) >= 4, f"应该至少有 4 个内置技能，实际 {len(skills)}"
            
            # 验证技能名称
            skill_names = [s["name"] for s in skills]
            assert "hello-world" in skill_names, "应该有 hello-world 技能"
            
            result.passed = True
            
    except Exception as e:
        result.error = str(e)
    
    result.duration = (datetime.now() - start).total_seconds()
    return result


async def test_skills_execution():
    """测试技能执行"""
    result = TestResult("技能 - 执行测试")
    start = datetime.now()
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            manager = SkillManager(workspace)
            
            # 测试 Hello World
            res = manager.execute_skill("hello-world", name="Test", greeting="Hi")
            assert res.success == True, "应该成功"
            assert "Hi, Test!" in res.data["message"], "消息应该正确"
            
            # 测试计算器
            res = manager.execute_skill("calculator", expression="2+3*4")
            assert res.success == True, "应该成功"
            assert res.data["result"] == 14, "结果应该是 14"
            
            # 测试天气
            res = manager.execute_skill("weather", city="Beijing")
            assert res.success == True, "应该成功"
            assert "temperature" in res.data, "应该包含温度"
            
            # 测试文件操作
            test_file = workspace / "test.txt"
            res = manager.execute_skill("file-operator", operation="write", 
                                        path=str(test_file), content="Hello")
            assert res.success == True, "写入应该成功"
            
            res = manager.execute_skill("file-operator", operation="read", 
                                        path=str(test_file))
            assert res.success == True, "读取应该成功"
            assert res.data["content"] == "Hello", "内容应该正确"
            
            result.passed = True
            
    except Exception as e:
        result.error = str(e)
    
    result.duration = (datetime.now() - start).total_seconds()
    return result


async def test_tools_loading():
    """测试工具加载"""
    result = TestResult("工具 - 加载测试")
    start = datetime.now()
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            manager = ToolManager(workspace)
            
            # 验证内置工具
            tools = manager.list_tools()
            assert len(tools) >= 5, f"应该至少有 5 个内置工具，实际 {len(tools)}"
            
            # 验证工具名称
            tool_names = [t["name"] for t in tools]
            assert "json-processor" in tool_names, "应该有 json-processor"
            assert "text-processor" in tool_names, "应该有 text-processor"
            
            result.passed = True
            
    except Exception as e:
        result.error = str(e)
    
    result.duration = (datetime.now() - start).total_seconds()
    return result


async def test_tools_execution():
    """测试工具执行"""
    result = TestResult("工具 - 执行测试")
    start = datetime.now()
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            manager = ToolManager(workspace)
            
            # 测试 JSON 处理
            res = await manager.execute_tool(
                "json-processor",
                {"operation": "format", "json_string": '{"name":"Alice"}'}
            )
            assert res.success == True, "应该成功"
            
            # 测试文本处理
            res = await manager.execute_tool(
                "text-processor",
                {"operation": "uppercase", "text": "hello"}
            )
            assert res.success == True, "应该成功"
            assert res.data["result"] == "HELLO", "应该转大写"
            
            # 测试词数统计
            res = await manager.execute_tool(
                "text-processor",
                {"operation": "word_count", "text": "Hello World Test"}
            )
            assert res.success == True, "应该成功"
            assert res.data["word_count"] == 3, "应该是 3 个词"
            
            result.passed = True
            
    except Exception as e:
        result.error = str(e)
    
    result.duration = (datetime.now() - start).total_seconds()
    return result


async def test_task_parser():
    """测试任务解析器"""
    result = TestResult("任务解析器")
    start = datetime.now()
    
    try:
        parser = TaskParser()
        
        # 测试意图识别
        intent = parser.parse("帮我打开文件 test.txt")
        assert intent.type == IntentType.FILE操作, f"应该是文件操作，实际 {intent.type}"
        
        intent = parser.parse("搜索 AI 新闻")
        assert intent.action in ["搜索信息", "general_task"], f"动作应该是搜索，实际 {intent.action}"
        
        intent = parser.parse("每天下午3点提醒我开会")
        assert intent.type == IntentType.SCHEDULE, f"应该是定时任务，实际 {intent.type}"
        
        # 测试实体提取
        intent = parser.parse("打开文件 'test.txt'")
        assert "test.txt" in intent.slots.get("path", ""), "应该提取文件名"
        
        # 测试置信度
        intent = parser.parse("帮我做这件事")
        assert intent.confidence > 0, "应该有置信度"
        
        result.passed = True
        
    except Exception as e:
        result.error = str(e)
    
    result.duration = (datetime.now() - start).total_seconds()
    return result


async def test_cron_expression():
    """测试 Cron 表达式"""
    result = TestResult("Cron 表达式")
    start = datetime.now()
    
    try:
        # 测试解析
        cron = CronExpression.parse("0 0 * * *")
        assert cron.minute == "0", "分钟应该是 0"
        assert cron.hour == "0", "小时应该是 0"
        assert cron.day_of_month == "*", "日期应该是任意"
        
        # 测试匹配
        test_time = datetime(2026, 3, 10, 0, 0, 0)
        assert cron.matches(test_time) == True, "应该匹配"
        
        test_time = datetime(2026, 3, 10, 0, 1, 0)
        assert cron.matches(test_time) == False, "不应该匹配"
        
        # 测试范围
        cron2 = CronExpression.parse("0 9 * * 1-5")
        test_time = datetime(2026, 3, 10, 9, 0, 0)  # 周二
        assert cron2.matches(test_time) == True, "工作日早上应该匹配"
        
        result.passed = True
        
    except Exception as e:
        result.error = str(e)
    
    result.duration = (datetime.now() - start).total_seconds()
    return result


async def test_scheduler():
    """测试调度器"""
    result = TestResult("调度器")
    start = datetime.now()
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            
            # 创建调度器
            scheduler = EnhancedScheduler(workspace)
            
            # 添加间隔任务
            task_id = scheduler.add_task(
                name="test-interval",
                command="test-command",
                schedule_type=ScheduleType.INTERVAL,
                interval_seconds=60
            )
            assert task_id is not None, "应该返回任务 ID"
            
            # 添加 Cron 任务
            task_id2 = scheduler.add_task(
                name="test-cron",
                command="cron-command",
                schedule_type=ScheduleType.CRON,
                cron_expression="0 0 * * *"
            )
            
            # 验证任务列表
            tasks = scheduler.list_tasks()
            assert len(tasks) == 2, f"应该有 2 个任务，实际 {len(tasks)}"
            
            # 测试启用/禁用
            scheduler.enable_task(task_id)
            task = scheduler.get_task(task_id)
            assert task.enabled == True, "应该启用"
            
            scheduler.disable_task(task_id)
            task = scheduler.get_task(task_id)
            assert task.enabled == False, "应该禁用"
            
            # 测试统计
            stats = scheduler.get_statistics()
            assert stats["total_tasks"] == 2, "统计应该正确"
            
            result.passed = True
            
    except Exception as e:
        result.error = str(e)
    
    result.duration = (datetime.now() - start).total_seconds()
    return result


async def test_multi_agent():
    """测试多智能体编排器"""
    result = TestResult("多智能体编排器")
    start = datetime.now()
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            
            # 创建编排器
            orchestrator = MultiAgentOrchestrator(workspace)
            
            # 验证默认 Agent
            agents = orchestrator.list_agents()
            assert len(agents) >= 4, f"应该有 4 个默认 Agent，实际 {len(agents)}"
            
            # 验证 Agent 名称
            agent_names = [a["id"] for a in agents]
            assert "coordinator" in agent_names, "应该有 coordinator"
            assert "planner" in agent_names, "应该有 planner"
            assert "executor" in agent_names, "应该有 executor"
            
            # 测试注册自定义 Agent
            custom_agent = SubAgent(
                id="custom-agent",
                name="Custom Agent",
                role=AgentRole.SPECIALIST,
                description="Custom test agent",
                instructions="You are a test agent."
            )
            orchestrator.register_agent(custom_agent)
            
            agents = orchestrator.list_agents()
            assert len(agents) == 5, "应该有 5 个 Agent"
            
            # 测试会话创建
            thread_id = await orchestrator.create_session("test-user", AgentMode.SESSION)
            assert thread_id is not None, "应该返回会话 ID"
            
            # 测试统计
            stats = orchestrator.get_statistics()
            assert "total_agents" in stats, "应该有统计信息"
            
            result.passed = True
            
    except Exception as e:
        result.error = str(e)
    
    result.duration = (datetime.now() - start).total_seconds()
    return result


async def test_permission_system():
    """测试权限系统"""
    result = TestResult("权限系统")
    start = datetime.now()
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            manager = ToolManager(workspace)
            
            # 设置用户权限
            manager.set_user_permissions("user1", [ToolPermission.READ])
            
            # 验证权限
            perms = manager.get_user_permissions("user1")
            assert ToolPermission.READ in perms, "应该有 READ 权限"
            
            # 测试权限检查 - 无权限
            tool = manager.get_tool("code-executor")  # 需要 ADMIN 权限
            assert manager.check_permission("user1", tool) == False, "user1 没有 ADMIN 权限"
            
            # 添加权限
            manager.set_user_permissions("user1", 
                [ToolPermission.READ, ToolPermission.EXECUTE, ToolPermission.ADMIN])
            
            # 验证权限检查 - 有权限
            assert manager.check_permission("user1", tool) == True, "user1 有 ADMIN 权限"
            
            # 测试执行历史
            await manager.execute_tool("json-processor", {"operation": "validate", "json_string": "{}"})
            history = manager.get_execution_history()
            assert len(history) >= 1, "应该有执行历史"
            
            result.passed = True
            
    except Exception as e:
        result.error = str(e)
    
    result.duration = (datetime.now() - start).total_seconds()
    return result


async def test_statistics():
    """测试统计功能"""
    result = TestResult("统计功能")
    start = datetime.now()
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            
            # 测试心跳统计
            config = HeartbeatConfig(interval=1)
            heartbeat_mgr = HeartbeatManager(workspace, config)
            
            stats = heartbeat_mgr.get_statistics()
            assert "total_tasks" in stats, "应该有任务统计"
            
            # 测试技能统计
            skill_mgr = SkillManager(workspace)
            stats = skill_mgr.get_statistics()
            assert "total_skills" in stats, "应该有技能统计"
            
            # 测试工具统计
            tool_mgr = ToolManager(workspace)
            await tool_mgr.execute_tool("text-processor", {"operation": "uppercase", "text": "test"})
            stats = tool_mgr.get_statistics()
            assert "total_tools" in stats, "应该有工具统计"
            assert stats["total_executions"] >= 1, "应该有执行次数"
            
            result.passed = True
            
    except Exception as e:
        result.error = str(e)
    
    result.duration = (datetime.now() - start).total_seconds()
    return result


async def test_error_handling():
    """测试错误处理"""
    result = TestResult("错误处理")
    start = datetime.now()
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            
            # 测试不存在的技能
            skill_mgr = SkillManager(workspace)
            res = skill_mgr.execute_skill("non-existent")
            assert res.success == False, "不存在的技能应该失败"
            
            # 测试禁用的技能
            skill_mgr.disable_skill("hello-world")
            res = skill_mgr.execute_skill("hello-world")
            assert res.success == False, "禁用的技能应该失败"
            
            # 测试无效 JSON
            tool_mgr = ToolManager(workspace)
            res = await tool_mgr.execute_tool(
                "json-processor",
                {"operation": "format", "json_string": "invalid"}
            )
            assert res.success == False, "无效 JSON 应该失败"
            
            # 测试任务不存在
            scheduler = EnhancedScheduler(workspace)
            status = scheduler.get_task_status("non-existent")
            assert status is None, "不存在的任务应该返回 None"
            
            result.passed = True
            
    except Exception as e:
        result.error = str(e)
    
    result.duration = (datetime.now() - start).total_seconds()
    return result


async def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 70)
    print("🚀 MAgentClaw 自动化测试套件")
    print("=" * 70)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    suite = TestSuite("MAgentClaw 核心模块测试")
    
    # 定义测试
    tests = [
        test_heartbeat_basic,
        test_heartbeat_execution,
        test_skills_loading,
        test_skills_execution,
        test_tools_loading,
        test_tools_execution,
        test_task_parser,
        test_cron_expression,
        test_scheduler,
        test_multi_agent,
        test_permission_system,
        test_statistics,
        test_error_handling,
    ]
    
    # 运行测试
    for test in tests:
        try:
            result = await test()
            suite.add_result(result)
        except Exception as e:
            result = TestResult(test.__name__)
            result.error = str(e)
            suite.add_result(result)
        
        # 打印进度
        print(f"  ✓ {test.__name__}")
    
    # 打印总结
    success = suite.print_summary()
    
    return success


def main():
    """主函数"""
    success = asyncio.run(run_all_tests())
    
    if success:
        print("\n🎉 所有测试通过！")
        sys.exit(0)
    else:
        print("\n💥 部分测试失败！")
        sys.exit(1)


if __name__ == "__main__":
    main()
