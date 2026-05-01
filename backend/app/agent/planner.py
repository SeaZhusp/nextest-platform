"""Lightweight planner for current single-skill execution flow."""

from app.agent.types import NormalizedAgentInput, PlanStep


def plan_for_chat(normalized: NormalizedAgentInput) -> list[PlanStep]:
    return [
        PlanStep(
            step_id="call_skill",
            type="call_skill",
            name="执行技能",
            payload={"skill_id": normalized.skill_id},
            depends_on=[],
        ),
        PlanStep(
            step_id="respond",
            type="respond",
            name="组装响应结果",
            payload={},
            depends_on=["call_skill"],
        ),
    ]

