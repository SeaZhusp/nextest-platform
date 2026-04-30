"""Execution policy guards for lightweight planning runtime."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.agent.types import PlanStep
from app.core.config import settings
from app.core.exceptions import ValidationException


class ExecutionPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_steps: int = Field(..., ge=1)
    max_tool_calls: int = Field(..., ge=1)
    step_timeout_seconds: float = Field(..., gt=0.0)
    step_retry_times: int = Field(default=0, ge=0)


def default_execution_policy() -> ExecutionPolicy:
    return ExecutionPolicy(
        max_steps=settings.agent_max_plan_steps,
        max_tool_calls=settings.agent_max_tool_calls,
        step_timeout_seconds=settings.agent_step_timeout_seconds,
        step_retry_times=settings.agent_step_retry_times,
    )


def resolve_execution_policy(skill_id: str) -> ExecutionPolicy:
    base = default_execution_policy()
    if skill_id == "test_case_gen":
        return ExecutionPolicy(
            max_steps=base.max_steps,
            max_tool_calls=base.max_tool_calls,
            step_timeout_seconds=settings.agent_step_timeout_seconds_test_case_gen,
            step_retry_times=base.step_retry_times,
        )
    return base


def validate_plan_against_policy(steps: list[PlanStep], policy: ExecutionPolicy) -> None:
    if len(steps) > policy.max_steps:
        raise ValidationException(
            f"计划步数超限：{len(steps)} > {policy.max_steps}"
        )
    tool_calls = sum(1 for s in steps if s.type == "call_skill")
    if tool_calls > policy.max_tool_calls:
        raise ValidationException(
            f"工具调用步数超限：{tool_calls} > {policy.max_tool_calls}"
        )

