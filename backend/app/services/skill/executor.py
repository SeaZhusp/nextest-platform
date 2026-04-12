"""技能唯一执行入口（2.2.2 F1.4）。"""

from app.core.exceptions import NotFoundException
from app.services.skill.base import SkillContext, SkillRunResult
from app.services.skill.registry import get_skill_registry


async def execute_skill(skill_id: str, ctx: SkillContext) -> SkillRunResult:
    reg = get_skill_registry()
    skill = reg.get(skill_id)
    if skill is None:
        raise NotFoundException(f"未知技能: {skill_id}")
    return await skill.run(ctx)
