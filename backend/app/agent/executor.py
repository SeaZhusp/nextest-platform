"""Step executor with basic trace collection."""

from __future__ import annotations

import asyncio
import time

from app.agent.policies import ExecutionPolicy, validate_plan_against_policy
from app.agent.types import ExecutionResult, ExecutionTrace, PlanStep
from app.contracts.skill import SkillContext, SkillRunResult


async def execute_plan_steps(
    *,
    steps: list[PlanStep],
    call_skill,
    skill_id: str,
    ctx: SkillContext,
    policy: ExecutionPolicy,
) -> tuple[SkillRunResult, ExecutionResult]:
    validate_plan_against_policy(steps, policy)
    traces: list[ExecutionTrace] = []
    last_skill_result: SkillRunResult | None = None

    async def _run() -> tuple[SkillRunResult, ExecutionResult]:
        nonlocal last_skill_result
        for step in steps:
            started = time.perf_counter()
            try:
                if step.type == "call_skill":
                    for attempt in range(policy.step_retry_times + 1):
                        try:
                            last_skill_result = await asyncio.wait_for(
                                call_skill(skill_id, ctx),
                                timeout=policy.step_timeout_seconds,
                            )
                            break
                        except Exception:  # noqa: PERF203
                            if attempt >= policy.step_retry_times:
                                raise
                    retry_suffix = (
                        f", retries={policy.step_retry_times}" if policy.step_retry_times > 0 else ""
                    )
                    traces.append(
                        ExecutionTrace(
                            step_id=step.step_id,
                            status="succeeded",
                            duration_ms=int((time.perf_counter() - started) * 1000),
                            output_summary=f"generated={len(last_skill_result.test_cases)}{retry_suffix}",
                        )
                    )
                else:
                    traces.append(
                        ExecutionTrace(
                            step_id=step.step_id,
                            status="succeeded",
                            duration_ms=int((time.perf_counter() - started) * 1000),
                            output_summary="noop",
                        )
                    )
            except Exception as e:
                traces.append(
                    ExecutionTrace(
                        step_id=step.step_id,
                        status="failed",
                        duration_ms=int((time.perf_counter() - started) * 1000),
                        error=str(e),
                    )
                )
                return (
                    last_skill_result or SkillRunResult(),
                    ExecutionResult(status="failed", traces=traces, outputs={}),
                )

        if last_skill_result is None:
            return SkillRunResult(), ExecutionResult(status="failed", traces=traces, outputs={})

        return (
            last_skill_result,
            ExecutionResult(
                status="succeeded",
                traces=traces,
                outputs={"test_case_count": len(last_skill_result.test_cases)},
            ),
        )

    try:
        return await asyncio.wait_for(_run(), timeout=policy.total_timeout_seconds)
    except TimeoutError:
        traces.append(
            ExecutionTrace(
                step_id="__policy_total_timeout__",
                status="failed",
                duration_ms=int(policy.total_timeout_seconds * 1000),
                error="total_timeout",
                output_summary="execution timed out by policy",
            )
        )
        return SkillRunResult(), ExecutionResult(status="failed", traces=traces, outputs={})

