"""智能体编排：校验后的请求进入技能执行（阶段一）。"""

from typing import cast
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.agent import AgentChatAckData, AgentChatRequest, TextPart
from app.schemas.llm_invoke import LlmInvokeConfig
from app.services.skill.base import SkillContext
from app.services.skill.executor import execute_skill
from app.services.skill_service import SkillService


async def process_agent_chat(
    payload: AgentChatRequest,
    llm_config: LlmInvokeConfig | None,
    db: AsyncSession,
) -> AgentChatAckData:
    assert payload.parts is not None
    is_new_session = payload.session_id is None
    session_id = payload.session_id or uuid4()
    user_text = "\n".join(p.text for p in payload.parts)
    skill_id = (payload.skill_id or "test_case_gen").strip() or "test_case_gen"

    if is_new_session:
        await SkillService().record_new_agent_session(db, skill_id)

    ctx = SkillContext(
        user_text=user_text,
        session_id=str(session_id),
        skill_id=skill_id,
        llm_config=llm_config,
    )
    result = await execute_skill(skill_id, ctx)

    return AgentChatAckData(
        session_id=str(session_id),
        skill_id=skill_id,
        parts=cast(list[TextPart], payload.parts),
        test_cases=result.test_cases,
    )
