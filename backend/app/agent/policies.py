"""Execution policy guards for lightweight planning runtime."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.agent.types import PlanStep
from app.api.deps.auth import CurrentUser
from app.core.config import settings
from app.core.exceptions import ValidationException


class ExecutionPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_steps: int = Field(..., ge=1)
    max_tool_calls: int = Field(..., ge=1)
    step_timeout_seconds: float = Field(..., gt=0.0)
    step_retry_times: int = Field(default=0, ge=0)
    total_timeout_seconds: float = Field(..., gt=0.0)


def default_execution_policy() -> ExecutionPolicy:
    return ExecutionPolicy(
        max_steps=settings.agent_max_plan_steps,
        max_tool_calls=settings.agent_max_tool_calls,
        step_timeout_seconds=settings.agent_step_timeout_seconds,
        step_retry_times=settings.agent_step_retry_times,
        total_timeout_seconds=settings.agent_total_timeout_seconds,
    )


def _apply_overrides(base: ExecutionPolicy, overrides: dict[str, Any]) -> ExecutionPolicy:
    if not overrides:
        return base
    data = base.model_dump()
    for k, v in overrides.items():
        if k in data:
            data[k] = v
    return ExecutionPolicy.model_validate(data)


def resolve_execution_policy(skill_id: str, user: CurrentUser | None = None) -> ExecutionPolicy:
    base = default_execution_policy()
    if skill_id == "test_case_gen":
        base = ExecutionPolicy(
            max_steps=base.max_steps,
            max_tool_calls=base.max_tool_calls,
            step_timeout_seconds=settings.agent_step_timeout_seconds_test_case_gen,
            step_retry_times=base.step_retry_times,
            total_timeout_seconds=base.total_timeout_seconds,
        )

    # Apply JSON overrides: default -> role -> member_level -> skill -> skill+role
    raw = settings.agent_policy_overrides_json or {}
    if isinstance(raw, dict):
        base = _apply_overrides(base, raw.get("default") if isinstance(raw.get("default"), dict) else {})
        if user is not None:
            role = (user.user_type or "").strip()
            if role:
                role_map = raw.get("roles")
                if isinstance(role_map, dict) and isinstance(role_map.get(role), dict):
                    base = _apply_overrides(base, role_map[role])
            ml = (user.member_level or "").strip()
            if ml:
                ml_map = raw.get("member_levels")
                if isinstance(ml_map, dict) and isinstance(ml_map.get(ml), dict):
                    base = _apply_overrides(base, ml_map[ml])

        skills_map = raw.get("skills")
        if isinstance(skills_map, dict) and isinstance(skills_map.get(skill_id), dict):
            base = _apply_overrides(base, skills_map[skill_id])

        if user is not None:
            role = (user.user_type or "").strip()
            skill_roles = raw.get("skill_roles")
            if role and isinstance(skill_roles, dict):
                s = skill_roles.get(skill_id)
                if isinstance(s, dict) and isinstance(s.get(role), dict):
                    base = _apply_overrides(base, s[role])

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

