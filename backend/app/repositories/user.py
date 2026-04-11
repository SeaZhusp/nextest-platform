from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.enums import SortOrderEnum
from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self):
        super().__init__(User)

    async def get_by_username(self, db: AsyncSession, username: str) -> User | None:
        result = await db.execute(
            select(User)
            .where(User.deleted_at.is_(None))
            .where(User.username == username)
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, db: AsyncSession, email: str) -> User | None:
        result = await db.execute(
            select(User)
            .where(User.deleted_at.is_(None))
            .where(User.email == email)
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_by_phone(self, db: AsyncSession, phone: str) -> User | None:
        result = await db.execute(
            select(User)
            .where(User.deleted_at.is_(None))
            .where(User.phone == phone)
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def search_paginated(
        self,
        db: AsyncSession,
        *,
        page: int,
        size: int,
        sort_by: str = "created_at",
        order_by: SortOrderEnum = SortOrderEnum.DESC,
        username: str | None = None,
        is_active: bool | None = None,
    ) -> tuple[list[User], int]:
        query = select(User).where(User.deleted_at.is_(None))
        if is_active is not None:
            query = query.where(User.is_active == is_active)
        if username:
            u = username.strip()
            if u:
                query = query.where(User.username.contains(u))

        count_stmt = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_stmt)).scalar_one()

        sort_field = self._resolve_sort_field(sort_by)
        query = query.order_by(
            sort_field.desc() if order_by == SortOrderEnum.DESC else sort_field.asc()
        )
        query = query.offset((page - 1) * size).limit(size)
        rows = (await db.execute(query)).scalars().all()
        return list(rows), int(total)
