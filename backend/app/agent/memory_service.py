"""智能体会话记忆：解析 session、读写消息。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Literal, cast
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.context import build_test_case_gen_llm_messages
from app.core.config import settings
from app.core.exceptions import NotFoundException
from app.models.conversation import Conversation, ConversationMessage
from app.repositories.conversation_repository import conversation_repository
from app.schemas.agent import (
    AgentExecutionOut,
    AgentExecutionSummaryOut,
    AgentHistoryMessageOut,
    AgentSessionMessagesData,
    TextPart,
)
from app.services.skill_service import SkillService


@dataclass
class ResolvedAgentSession:
    row: Conversation
    conversation_uuid: UUID
    is_new_session: bool


def _parts_to_content_json(parts: list[TextPart]) -> dict:
    return {"parts": [p.model_dump() for p in parts]}


async def resolve_agent_session(
    db: AsyncSession,
    *,
    user_id: int,
    session_id: UUID | None,
    skill_id: str,
    parts: list[TextPart] | None = None,
) -> ResolvedAgentSession:
    # skill_id is validated at outer boundary (input normalizer).
    sid = skill_id.strip()
    if session_id is None:
        new_uuid = uuid4()
        initial_title = _title_from_first_user_input(parts or [])
        row = await conversation_repository.create_for_user(
            db,
            conversation_uuid=str(new_uuid),
            user_id=user_id,
            skill_id=sid,
            title=initial_title,
        )
        await SkillService().record_new_agent_session(db, sid)
        return ResolvedAgentSession(row=row, conversation_uuid=new_uuid, is_new_session=True)

    su = str(session_id)
    row = await conversation_repository.get_by_uuid_for_user(db, conversation_uuid=su, user_id=user_id)
    if row is None:
        raise NotFoundException("会话不存在或无权访问")
    if row.skill_id != sid:
        row.skill_id = sid
        await db.flush()
    return ResolvedAgentSession(row=row, conversation_uuid=session_id, is_new_session=False)


async def load_prior_messages(
    db: AsyncSession,
    *,
    conversation_id: int,
) -> list[ConversationMessage]:
    return await conversation_repository.list_messages(db, conversation_id=conversation_id)


def build_llm_messages_for_test_case_gen(
    *,
    prior_messages: list[ConversationMessage],
    current_user_text: str,
) -> list[dict]:
    return build_test_case_gen_llm_messages(
        prior_messages=prior_messages,
        current_user_text=current_user_text,
        max_rounds=settings.agent_context_max_rounds,
    )


def _title_from_first_user_input(parts: list[TextPart], *, max_len: int = 200) -> str:
    text = "\n".join(p.text for p in parts).strip()
    if not text:
        return ""
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


async def save_user_message(
    db: AsyncSession,
    *,
    conversation_id: int,
    parts: list[TextPart],
) -> None:
    await conversation_repository.create_message(
        db,
        conversation_id=conversation_id,
        role="user",
        content_json=_parts_to_content_json(parts),
    )
    await db.flush()
    await conversation_repository.touch_updated_at(db, conversation_id)


async def save_assistant_message(
    db: AsyncSession,
    *,
    conversation_id: int,
    text: str,
    execution: dict | None = None,
) -> None:
    content_json: dict = {"text": text}
    if execution is not None:
        content_json["execution"] = execution
    await conversation_repository.create_message(
        db,
        conversation_id=conversation_id,
        role="assistant",
        content_json=content_json,
    )
    await db.flush()
    await conversation_repository.touch_updated_at(db, conversation_id)


def assistant_persist_text_from_result(*, llm_raw_output: str | None, test_cases_dump: list[dict]) -> str:
    if llm_raw_output is not None and llm_raw_output.strip():
        return llm_raw_output
    return json.dumps(test_cases_dump, ensure_ascii=False)


async def list_session_messages_for_user(
    db: AsyncSession,
    *,
    user_id: int,
    conversation_uuid: UUID,
) -> AgentSessionMessagesData:
    row = await conversation_repository.get_by_uuid_for_user(
        db,
        conversation_uuid=str(conversation_uuid),
        user_id=user_id,
    )
    if row is None:
        raise NotFoundException("会话不存在或无权访问")
    rows = await conversation_repository.list_messages(db, conversation_id=row.id)
    out: list[AgentHistoryMessageOut] = []
    for m in rows:
        role_raw = (m.role or "").strip()
        role: Literal["user", "assistant"] = (
            cast(Literal["user", "assistant"], role_raw)
            if role_raw in ("user", "assistant")
            else "user"
        )
        out.append(
            AgentHistoryMessageOut(
                id=int(m.id),
                role=role,
                content_json=dict(m.content_json) if isinstance(m.content_json, dict) else {},
                execution=_parse_execution_from_content_json(m.content_json),
                created_at=m.created_at.isoformat() if m.created_at else "",
            )
        )
    return AgentSessionMessagesData(
        session_id=str(conversation_uuid),
        title=(row.title or "").strip(),
        skill_id=row.skill_id,
        messages=out,
    )


async def get_execution_summary_for_user(
    db: AsyncSession,
    *,
    user_id: int,
    conversation_uuid: UUID,
) -> AgentExecutionSummaryOut:
    row = await conversation_repository.get_by_uuid_for_user(
        db,
        conversation_uuid=str(conversation_uuid),
        user_id=user_id,
    )
    if row is None:
        raise NotFoundException("会话不存在或无权访问")
    rows = await conversation_repository.list_messages(db, conversation_id=row.id)

    assistant_rows = [m for m in rows if (m.role or "").strip() == "assistant"]
    executions: list[AgentExecutionOut] = []
    for m in assistant_rows:
        ex = _parse_execution_from_content_json(m.content_json)
        if ex is not None:
            executions.append(ex)

    succeeded = sum(1 for e in executions if e.status == "succeeded")
    failed = sum(1 for e in executions if e.status == "failed")
    total_duration_ms = 0
    last_status = executions[-1].status if executions else None
    for e in executions:
        for t in e.traces:
            total_duration_ms += int(t.duration_ms or 0)

    return AgentExecutionSummaryOut(
        session_id=str(conversation_uuid),
        total_assistant_messages=len(assistant_rows),
        total_executions=len(executions),
        succeeded=succeeded,
        failed=failed,
        total_duration_ms=total_duration_ms,
        last_status=last_status,
    )


def _parse_execution_from_content_json(content_json: object) -> AgentExecutionOut | None:
    if not isinstance(content_json, dict):
        return None
    raw = content_json.get("execution")
    if not isinstance(raw, dict):
        return None
    try:
        return AgentExecutionOut.model_validate(raw)
    except Exception:
        return None

