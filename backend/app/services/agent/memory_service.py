"""智能体会话记忆：解析 session、读写消息（2.2.4 F1.11 / F1.13）。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Literal, cast
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import NotFoundException
from app.models.agent_session import AgentMessage, AgentSession
from app.repositories.agent_message_repository import agent_message_repository
from app.repositories.agent_session_repository import agent_session_repository
from app.schemas.agent import AgentHistoryMessageOut, AgentSessionMessagesData, TextPart
from app.services.agent.context import build_test_case_gen_llm_messages
from app.services.skill_service import SkillService


@dataclass
class ResolvedAgentSession:
    row: AgentSession
    session_uuid: UUID
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
    sid = (skill_id or "test_case_gen").strip() or "test_case_gen"
    if session_id is None:
        new_uuid = uuid4()
        # 新会话与首条用户输入同一次请求：用本轮 parts 直接作为标题（与即将写入的首条消息一致）
        initial_title = _title_from_first_user_input(parts or [])
        row = await agent_session_repository.create_for_user(
            db,
            session_uuid=str(new_uuid),
            user_id=user_id,
            skill_id=sid,
            title=initial_title,
        )
        await SkillService().record_new_agent_session(db, sid)
        return ResolvedAgentSession(row=row, session_uuid=new_uuid, is_new_session=True)

    su = str(session_id)
    row = await agent_session_repository.get_by_uuid_for_user(db, session_uuid=su, user_id=user_id)
    if row is None:
        raise NotFoundException("会话不存在或无权访问")
    if row.skill_id != sid:
        row.skill_id = sid
        await db.flush()
    return ResolvedAgentSession(row=row, session_uuid=session_id, is_new_session=False)


async def load_prior_messages(
    db: AsyncSession,
    *,
    agent_session_id: int,
) -> list[AgentMessage]:
    return await agent_message_repository.list_for_session(db, agent_session_id=agent_session_id)


def build_llm_messages_for_test_case_gen(
    *,
    prior_messages: list,
    current_user_text: str,
) -> list[dict]:
    return build_test_case_gen_llm_messages(
        prior_messages=prior_messages,
        current_user_text=current_user_text,
        max_rounds=settings.agent_context_max_rounds,
    )


def _title_from_first_user_input(parts: list[TextPart], *, max_len: int = 200) -> str:
    """首条用户输入作为标题，超长截断（与 agent_sessions.title 长度一致）。"""
    text = "\n".join(p.text for p in parts).strip()
    if not text:
        return ""
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


async def save_user_message(
    db: AsyncSession,
    *,
    agent_session_id: int,
    parts: list[TextPart],
) -> None:
    await agent_message_repository.create_message(
        db,
        agent_session_id=agent_session_id,
        role="user",
        content_json=_parts_to_content_json(parts),
    )
    await db.flush()
    await agent_session_repository.touch_updated_at(db, agent_session_id)


async def save_assistant_message(
    db: AsyncSession,
    *,
    agent_session_id: int,
    text: str,
) -> None:
    await agent_message_repository.create_message(
        db,
        agent_session_id=agent_session_id,
        role="assistant",
        content_json={"text": text},
    )
    await db.flush()
    await agent_session_repository.touch_updated_at(db, agent_session_id)


def assistant_persist_text_from_result(*, llm_raw_output: str | None, test_cases_dump: list[dict]) -> str:
    if llm_raw_output is not None and llm_raw_output.strip():
        return llm_raw_output
    return json.dumps(test_cases_dump, ensure_ascii=False)


async def list_session_messages_for_user(
    db: AsyncSession,
    *,
    user_id: int,
    session_uuid: UUID,
) -> AgentSessionMessagesData:
    row = await agent_session_repository.get_by_uuid_for_user(
        db,
        session_uuid=str(session_uuid),
        user_id=user_id,
    )
    if row is None:
        raise NotFoundException("会话不存在或无权访问")
    rows = await agent_message_repository.list_for_session(db, agent_session_id=row.id)
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
                created_at=m.created_at.isoformat() if m.created_at else "",
            )
        )
    return AgentSessionMessagesData(
        session_id=str(session_uuid),
        title=(row.title or "").strip(),
        skill_id=row.skill_id,
        messages=out,
    )
