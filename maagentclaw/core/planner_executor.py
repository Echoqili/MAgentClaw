import json
import re
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from .planner import Plan, PlanStep, PlanResult, PlanStatus, StepStatus


class PlanGenerator:
    """计划生成器 - 使用 LLM 生成执行计划"""

    def __init__(self, llm_callback: Optional[Callable] = None):
        self.llm_callback = llm_callback

    async def generate(
        self,
        goal: str,
        context: Optional[Dict[str, Any]] = None,
        max_steps: int = 10
    ) -> Plan:
        """生成执行计划"""
        plan = Plan(goal=goal, context=context or {})

        if self.llm_callback:
            plan = await self._generate_with_llm(plan, max_steps)
        else:
            plan = self._generate_simple(plan, goal)

        return plan

    async def _generate_with_llm(self, plan: Plan, max_steps: int) -> Plan:
        """使用 LLM 生成计划"""
        prompt = self._build_prompt(plan.goal, plan.context, max_steps)

        try:
            response = await self.llm_callback(
                prompt,
                system="你是一个任务规划专家，根据用户目标生成详细的执行计划。"
            )

            steps = self._parse_llm_response(response)
            plan.steps = steps
            plan.description = f"Generated {len(steps)} steps for: {plan.goal}"

        except Exception as e:
            print(f"LLM planning failed: {e}")
            plan = self._generate_simple(plan, plan.goal)

        return plan

    def _generate_simple(self, plan: Plan, goal: str) -> Plan:
        """简单计划生成 - 基于规则"""
        step = PlanStep(
            description=f"Execute: {goal}",
            action="execute",
            params={"goal": goal}
        )
        plan.steps.append(step)
        plan.description = f"Single step: {goal}"
        return plan

    def _build_prompt(self, goal: str, context: Dict[str, Any], max_steps: int) -> str:
        """构建 LLM 提示"""
        context_str = ""
        if context:
            context_str = f"\nContext: {json.dumps(context, ensure_ascii=False)}"

        return f"""请为以下目标生成执行计划：

目标: {goal}
{context_str}

要求:
1. 将目标分解为 {max_steps} 个以内的具体步骤
2. 每个步骤应该清晰、可执行
3. 步骤之间如有依赖关系需明确标注
4. 输出格式为 JSON 数组，每个元素包含:
   - description: 步骤描述
   - action: 执行动作
   - params: 动作参数
   - dependencies: 依赖步骤ID列表(可选)

请直接输出 JSON，不要其他内容。"""

    def _parse_llm_response(self, response: str) -> List[PlanStep]:
        """解析 LLM 响应"""
        try:
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                steps_data = json.loads(json_match.group())

                steps = []
                for i, step_data in enumerate(steps_data):
                    step = PlanStep(
                        description=step_data.get("description", ""),
                        action=step_data.get("action", "execute"),
                        params=step_data.get("params", {}),
                        dependencies=step_data.get("dependencies", [])
                    )
                    steps.append(step)

                return steps

        except Exception as e:
            print(f"Failed to parse LLM response: {e}")

        return [PlanStep(description=response, action="execute")]


class PlanExecutor:
    """计划执行器"""

    def __init__(self):
        self.action_handlers: Dict[str, Callable] = {}

    def register_handler(self, action: str, handler: Callable) -> None:
        """注册动作处理器"""
        self.action_handlers[action] = handler

    async def execute(
        self,
        plan: Plan,
        context: Optional[Dict[str, Any]] = None,
        on_step_complete: Optional[Callable] = None
    ) -> PlanResult:
        """执行计划"""
        import time
        start_time = time.time()

        plan.context.update(context or {})
        plan.status = PlanStatus.IN_PROGRESS

        executed_count = 0

        while True:
            next_step = plan.get_next_step()

            if not next_step:
                break

            next_step.status = StepStatus.RUNNING
            next_step.started_at = datetime.now()
            plan.current_step = plan.steps.index(next_step)

            try:
                result = await self._execute_step(next_step, plan.context)
                next_step.result = result
                next_step.status = StepStatus.COMPLETED
                next_step.completed_at = datetime.now()

                executed_count += 1

                if on_step_complete:
                    await on_step_complete(next_step, result)

            except Exception as e:
                next_step.error = str(e)
                next_step.status = StepStatus.FAILED
                next_step.completed_at = datetime.now()

                plan.status = PlanStatus.FAILED
                return PlanResult(
                    success=False,
                    plan=plan,
                    error=str(e),
                    executed_steps=executed_count,
                    duration=time.time() - start_time
                )

        plan.status = PlanStatus.COMPLETED
        plan.completed_at = datetime.now()

        completed_steps = plan.get_completed_steps()
        final_result = None
        if completed_steps:
            final_result = completed_steps[-1].result

        return PlanResult(
            success=True,
            plan=plan,
            final_result=final_result,
            executed_steps=executed_count,
            duration=time.time() - start_time
        )

    async def _execute_step(self, step: PlanStep, context: Dict[str, Any]) -> Any:
        """执行单个步骤"""
        handler = self.action_handlers.get(step.action)

        if handler:
            return await handler(step.params, context)

        return {"message": f"Action '{step.action}' not implemented, skipping"}

    async def resume(self, plan: Plan) -> PlanResult:
        """恢复执行失败的计划"""
        failed_step = None
        for step in plan.steps:
            if step.status == StepStatus.FAILED:
                failed_step = step
                break

        if failed_step:
            failed_step.status = StepStatus.PENDING
            failed_step.error = None

        return await self.execute(plan, plan.context)
