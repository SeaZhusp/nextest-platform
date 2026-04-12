"""智能体编排：校验后的请求进入技能执行（阶段一）；2.2.4 起持久化会话与多轮上下文。"""

from typing import cast

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.agent import AgentChatAckData, AgentChatRequest, TextPart
from app.schemas.llm_invoke import LlmInvokeConfig
from app.services.agent.memory_service import (
    assistant_persist_text_from_result,
    build_llm_messages_for_test_case_gen,
    load_prior_messages,
    resolve_agent_session,
    save_assistant_message,
    save_user_message,
)
from app.services.skill.base import SkillContext
from app.services.skill.executor import execute_skill


async def process_agent_chat(
    payload: AgentChatRequest,
    llm_config: LlmInvokeConfig | None,
    db: AsyncSession,
    *,
    user_id: int,
) -> AgentChatAckData:
    assert payload.parts is not None
    skill_id = (payload.skill_id or "test_case_gen").strip() or "test_case_gen"
    parts = cast(list[TextPart], payload.parts)
    user_text = "\n".join(p.text for p in parts)

    resolved = await resolve_agent_session(
        db,
        user_id=user_id,
        session_id=payload.session_id,
        skill_id=skill_id,
        parts=parts,
    )
    prior = await load_prior_messages(db, agent_session_id=resolved.row.id)

    await save_user_message(db, agent_session_id=resolved.row.id, parts=parts)
    await db.commit()

    llm_messages = None
    if skill_id == "test_case_gen":
        llm_messages = build_llm_messages_for_test_case_gen(
            prior_messages=prior,
            current_user_text=user_text,
        )

    ctx = SkillContext(
        user_text=user_text,
        session_id=str(resolved.session_uuid),
        skill_id=skill_id,
        llm_config=llm_config,
        llm_chat_messages=llm_messages,
    )
    result = await execute_skill(skill_id, ctx)

    dump = [c.model_dump() for c in result.test_cases]
    asst_text = assistant_persist_text_from_result(
        llm_raw_output=result.llm_raw_output,
        test_cases_dump=dump,
    )
    await save_assistant_message(db, agent_session_id=resolved.row.id, text=asst_text)
    await db.commit()

    return AgentChatAckData(
        session_id=str(resolved.session_uuid),
        skill_id=skill_id,
        parts=parts,
        test_cases=result.test_cases,
    )
