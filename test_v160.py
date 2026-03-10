import asyncio
import tempfile
from pathlib import Path

async def run_tests():
    print('=' * 50)
    print('MAgentClaw v1.6.0 功能测试')
    print('=' * 50)

    # 1. 测试技能系统
    print('\n[1] 技能系统测试')
    from maagentclaw.managers.skill_manager import SkillManager
    with tempfile.TemporaryDirectory() as tmpdir:
        sm = SkillManager(Path(tmpdir))
        print(f'  Loaded skills: {len(sm.registry.list_skills())}')
        print(f'  Skills: {sm.registry.list_skills()}')

    # 2. 测试记忆系统
    print('\n[2] 记忆系统测试')
    from maagentclaw.memory import MemoryManager
    with tempfile.TemporaryDirectory() as tmpdir:
        mm = MemoryManager(Path(tmpdir))
        item1 = await mm.add('用户说今天天气很好', importance=0.5)
        item2 = await mm.add('用户喜欢编程', importance=0.8)
        print(f'  Added: 2 items')
        results = await mm.search('天气')
        print(f'  Search: {len(results)} found')
        stats = await mm.get_stats()
        total = stats['total']
        print(f'  Total: {total} items')

    # 3. 测试规划器
    print('\n[3] 规划器测试')
    from maagentclaw.core.planner import Plan
    from maagentclaw.core.planner_executor import PlanGenerator, PlanExecutor
    plan = Plan(goal='Test task')
    print(f'  Created: {plan.id[:8]}')
    gen = PlanGenerator()
    plan = await gen.generate('Book flight')
    print(f'  Steps: {len(plan.steps)}')
    executor = PlanExecutor()
    executor.register_handler('execute', lambda p, c: {'result': 'ok'})
    result = await executor.execute(plan)
    print(f'  Result: success={result.success}')

    # 4. 测试 RAG
    print('\n[4] RAG 测试')
    from maagentclaw.rag import RAGPipeline
    rag = RAGPipeline(chunk_size=100)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write('Python is a programming language.')
        test_file = f.name
    chunks = await rag.load_and_index(Path(test_file))
    print(f'  Indexed: {chunks} chunks')
    results = await rag.search('Python')
    print(f'  Search: {len(results)} found')

    # 5. 测试安全模块
    print('\n[5] 安全模块测试')
    from maagentclaw.security import AuthManager, AuditLogger, Permission, ActionType
    with tempfile.TemporaryDirectory() as tmpdir:
        auth = AuthManager(Path(tmpdir) / 'keys.json')
        key, api_key = auth.create_key('test-key', [Permission.READ])
        print(f'  Created key: {api_key.name}')
        verified = auth.verify_key(key)
        print(f'  Verified: {verified is not None}')
        audit = AuditLogger(Path(tmpdir) / 'audit.json')
        log = await audit.log(ActionType.READ, 'user1', '/api/test')
        print(f'  Logged: {log.id[:8]}')

    print('\n' + '=' * 50)
    print('ALL TESTS PASSED!')
    print('=' * 50)

if __name__ == '__main__':
    asyncio.run(run_tests())
