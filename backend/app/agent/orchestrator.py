"""智能体编排：校验后的请求进入技能执行；包含会话持久化与多轮上下文。"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.executor import execute_plan_steps
from app.agent.input_normalizer import normalize_agent_input
from app.agent.memory_service import (
    assistant_persist_text_from_result,
    build_llm_messages_for_test_case_gen,
    load_prior_messages,
    resolve_agent_session,
    save_assistant_message,
    save_user_message,
)
from app.agent.planner import plan_for_chat
from app.agent.policies import resolve_execution_policy
from app.api.deps.auth import CurrentUser
from app.schemas.agent import AgentChatAckData, AgentChatRequest
from app.schemas.llm_invoke import LlmInvokeConfig
from app.contracts.skill import SkillContext
from app.agent.skills.executor import execute_skill


async def process_agent_chat(
    payload: AgentChatRequest,
    llm_config: LlmInvokeConfig | None,
    db: AsyncSession,
    *,
    user_id: int,
    user: CurrentUser | None = None,
) -> AgentChatAckData:
    normalized = normalize_agent_input(payload)
    skill_id = normalized.skill_id
    parts = normalized.text_parts
    user_text = normalized.user_text

    resolved = await resolve_agent_session(
        db,
        user_id=user_id,
        session_id=payload.session_id,
        skill_id=skill_id,
        parts=parts,
    )
    prior = await load_prior_messages(db, conversation_id=resolved.row.id)

    await save_user_message(db, conversation_id=resolved.row.id, parts=parts)
    await db.commit()

    llm_messages = None
    if skill_id == "test_case_gen":
        llm_messages = build_llm_messages_for_test_case_gen(
            prior_messages=prior,
            current_user_text=user_text,
        )

    ctx = SkillContext(
        user_text=user_text,
        session_id=str(resolved.conversation_uuid),
        skill_id=skill_id,
        llm_config=llm_config,
        llm_chat_messages=llm_messages,
        input_artifacts=[a.model_dump() for a in normalized.artifacts],
    )
    steps = plan_for_chat(normalized)
    result, exec_result = await execute_plan_steps(
        steps=steps,
        call_skill=execute_skill,
        skill_id=skill_id,
        ctx=ctx,
        policy=resolve_execution_policy(skill_id, user=user),
    )

    dump = [c.model_dump() for c in result.test_cases]
    asst_text = assistant_persist_text_from_result(
        llm_raw_output=result.llm_raw_output,
        test_cases_dump=dump,
    )
    await save_assistant_message(
        db,
        conversation_id=resolved.row.id,
        text=asst_text,
        skill_id=skill_id,
        execution=exec_result.model_dump(),
    )
    await db.commit()

    return AgentChatAckData(
        session_id=str(resolved.conversation_uuid),
        skill_id=skill_id,
        parts=parts,
        test_cases=result.test_cases,
    )

