from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_session import AgentMessage
from app.repositories.base import BaseRepository


class AgentMessageRepository(BaseRepository[AgentMessage]):
    def __init__(self) -> None:
        super().__init__(AgentMessage)

    async def list_for_session(
        self,
        db: AsyncSession,
        *,
        agent_session_id: int,
    ) -> list[AgentMessage]:
        q = (
            self._base_query()
            .where(AgentMessage.agent_session_id == agent_session_id)
            .order_by(AgentMessage.id.asc())
        )
        rows = (await db.execute(q)).scalars().all()
        return list(rows)

    async def create_message(
        self,
        db: AsyncSession,
        *,
        agent_session_id: int,
        role: str,
        content_json: dict[str, Any],
    ) -> AgentMessage:
        return await self.create(
            db,
            {
                "agent_session_id": agent_session_id,
                "role": role,
                "content_json": content_json,
            },
        )

agent_message_repository = AgentMessageRepository()
