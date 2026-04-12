from __future__ import annotations

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_session import AgentSession
from app.repositories.base import BaseRepository


class AgentSessionRepository(BaseRepository[AgentSession]):
    def __init__(self) -> None:
        super().__init__(AgentSession)

    async def get_by_uuid_for_user(
        self,
        db: AsyncSession,
        *,
        session_uuid: str,
        user_id: int,
    ) -> AgentSession | None:
        q = self._base_query().where(
            AgentSession.session_uuid == session_uuid,
            AgentSession.user_id == user_id,
        )
        r = await db.execute(q.limit(1))
        return r.scalar_one_or_none()

    async def create_for_user(
        self,
        db: AsyncSession,
        *,
        session_uuid: str,
        user_id: int,
        skill_id: str,
        title: str | None = None,
    ) -> AgentSession:
        # 新建会话标题为空，首条用户消息写入后由 memory_service 写入摘要标题
        tt = (title if title is not None else "").strip()[:200]
        return await self.create(
            db,
            {
                "session_uuid": session_uuid,
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
    ) -> tuple[list[AgentSession], int]:
        filt = (
            AgentSession.user_id == user_id,
            AgentSession.deleted_at.is_(None),
        )
        total = int(
            (
                await db.execute(
                    select(func.count()).select_from(AgentSession).where(*filt)
                )
            ).scalar_one()
            or 0
        )
        stmt = (
            select(AgentSession)
            .where(*filt)
            .order_by(AgentSession.updated_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        rows = (await db.execute(stmt)).scalars().all()
        return list(rows), total

    async def touch_updated_at(self, db: AsyncSession, session_id: int) -> None:
        await db.execute(
            update(AgentSession)
            .where(AgentSession.id == session_id, AgentSession.deleted_at.is_(None))
            .values(updated_at=func.now())
        )
        await db.flush()


agent_session_repository = AgentSessionRepository()
