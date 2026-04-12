from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_llm_profile import UserLlmProfile
from app.repositories.base import BaseRepository


class UserLlmProfileRepository(BaseRepository[UserLlmProfile]):
    def __init__(self) -> None:
        super().__init__(UserLlmProfile)

    async def list_by_user_id(
        self,
        db: AsyncSession,
        user_id: int,
        *,
        active_only: bool = False,
    ) -> list[UserLlmProfile]:
        q = self._base_query().where(UserLlmProfile.user_id == user_id)
        if active_only:
            q = q.where(UserLlmProfile.is_active.is_(True))
        q = q.order_by(UserLlmProfile.created_at.desc())
        result = await db.execute(q)
        return list(result.scalars().all())


user_llm_profile_repository = UserLlmProfileRepository()
