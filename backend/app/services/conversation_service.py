"""会话列表与重命名（产品化历史入口）。"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ValidationException
from app.repositories.conversation_repository import conversation_repository
from app.schemas.agent import AgentSessionListData, AgentSessionSummaryOut


async def list_my_conversations(
    db: AsyncSession,
    *,
    user_id: int,
    page: int,
    size: int,
) -> AgentSessionListData:
    rows, total = await conversation_repository.list_for_user(
        db, user_id=user_id, page=page, size=size
    )
    items = [
        AgentSessionSummaryOut(
            session_id=r.conversation_uuid,
            title=(r.title or "").strip(),
            skill_id=r.skill_id,
            updated_at=r.updated_at.isoformat() if r.updated_at else "",
        )
        for r in rows
    ]
    return AgentSessionListData(items=items, total=total, page=page, size=size)


async def rename_conversation(
    db: AsyncSession,
    *,
    user_id: int,
    conversation_uuid: UUID,
    title: str,
) -> AgentSessionSummaryOut:
    t = title.strip()
    if not t:
        raise ValidationException("标题不能为空")
    if len(t) > 200:
        raise ValidationException("标题不能超过 200 个字符")
    row = await conversation_repository.get_by_uuid_for_user(
        db, conversation_uuid=str(conversation_uuid), user_id=user_id
    )
    if row is None:
        raise NotFoundException("会话不存在或无权访问")
    row = await conversation_repository.update(db, int(row.id), {"title": t})
    await db.commit()
    await db.refresh(row)
    return AgentSessionSummaryOut(
        session_id=row.conversation_uuid,
        title=row.title,
        skill_id=row.skill_id,
        updated_at=row.updated_at.isoformat() if row.updated_at else "",
    )


async def delete_conversation(
    db: AsyncSession,
    *,
    user_id: int,
    conversation_uuid: UUID,
) -> None:
    row = await conversation_repository.get_by_uuid_for_user(
        db, conversation_uuid=str(conversation_uuid), user_id=user_id
    )
    if row is None:
        raise NotFoundException("会话不存在或无权访问")
    await conversation_repository.hard_delete_with_messages(db, conversation_id=int(row.id))
    await db.commit()
