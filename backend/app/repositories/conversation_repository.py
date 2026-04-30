from __future__ import annotations

from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation, ConversationMessage
from app.repositories.base import BaseRepository


class ConversationRepository(BaseRepository[Conversation]):
    def __init__(self) -> None:
        super().__init__(Conversation)

    async def get_by_uuid_for_user(
        self,
        db: AsyncSession,
        *,
        conversation_uuid: str,
        user_id: int,
    ) -> Conversation | None:
        q = self._base_query().where(
            Conversation.conversation_uuid == conversation_uuid,
            Conversation.user_id == user_id,
        )
        r = await db.execute(q.limit(1))
        return r.scalar_one_or_none()

    async def create_for_user(
        self,
        db: AsyncSession,
        *,
        conversation_uuid: str,
        user_id: int,
        skill_id: str,
        title: str | None = None,
    ) -> Conversation:
        tt = (title if title is not None else "").strip()[:200]
        return await self.create(
            db,
            {
                "conversation_uuid": conversation_uuid,
                "user_id": user_id,
                "skill_id": skill_id.strip() or "test_case_gen",
                "title": tt,
            },
        )

    async def list_for_user(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        page: int,
        size: int,
    ) -> tuple[list[Conversation], int]:
        filt = (
            Conversation.user_id == user_id,
            Conversation.deleted_at.is_(None),
        )
        total = int(
            (
                await db.execute(
                    select(func.count()).select_from(Conversation).where(*filt)
                )
            ).scalar_one()
            or 0
        )
        stmt = (
            select(Conversation)
            .where(*filt)
            .order_by(Conversation.updated_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        rows = (await db.execute(stmt)).scalars().all()
        return list(rows), total

    async def touch_updated_at(self, db: AsyncSession, conversation_id: int) -> None:
        await db.execute(
            update(Conversation)
            .where(Conversation.id == conversation_id, Conversation.deleted_at.is_(None))
            .values(updated_at=func.now())
        )
        await db.flush()

    async def list_messages(
        self,
        db: AsyncSession,
        *,
        conversation_id: int,
    ) -> list[ConversationMessage]:
        stmt = (
            select(ConversationMessage)
            .where(
                ConversationMessage.deleted_at.is_(None),
                ConversationMessage.conversation_id == conversation_id,
            )
            .order_by(ConversationMessage.id.asc())
        )
        rows = (await db.execute(stmt)).scalars().all()
        return list(rows)

    async def create_message(
        self,
        db: AsyncSession,
        *,
        conversation_id: int,
        role: str,
        content_json: dict[str, Any],
    ) -> ConversationMessage:
        msg = ConversationMessage(
            conversation_id=conversation_id,
            role=role,
            content_json=content_json,
        )
        db.add(msg)
        await db.flush()
        await db.refresh(msg)
        return msg


conversation_repository = ConversationRepository()
