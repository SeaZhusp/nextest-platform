from datetime import datetime, timezone
from typing import Literal

from sqlalchemy import and_, exists, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.constants.enums import SortOrderEnum
from app.models.project import Project, ProjectMember
from app.models.user import User
from app.repositories.base import BaseRepository


Participation = Literal["all", "owned", "joined"]


class ProjectRepository(BaseRepository[Project]):
    def __init__(self) -> None:
        super().__init__(Project)

    @staticmethod
    def _member_exists(user_id: int):
        return exists(
            select(1).select_from(ProjectMember).where(
                ProjectMember.project_id == Project.id,
                ProjectMember.user_id == user_id,
                ProjectMember.deleted_at.is_(None),
            )
        )

    def _participation_filter(self, user_id: int, participation: Participation):
        m = self._member_exists(user_id)
        if participation == "owned":
            return Project.owner_id == user_id
        if participation == "joined":
            return and_(Project.owner_id != user_id, m)
        return or_(Project.owner_id == user_id, m)

    async def list_for_user(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        page: int,
        size: int,
        participation: Participation = "all",
        sort_by: str = "updated_at",
        order_by: SortOrderEnum = SortOrderEnum.DESC,
    ) -> tuple[list[Project], int]:
        cond = self._participation_filter(user_id, participation)
        query = (
            select(Project)
            .options(selectinload(Project.owner))
            .where(Project.deleted_at.is_(None))
            .where(cond)
        )

        count_stmt = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_stmt)).scalar_one()

        sort_field = self._resolve_sort_field(sort_by)
        query = query.order_by(
            sort_field.desc() if order_by == SortOrderEnum.DESC else sort_field.asc()
        )
        query = query.offset((page - 1) * size).limit(size)
        rows = (await db.execute(query)).scalars().all()
        return list(rows), int(total)

    async def get_accessible_by_id(
        self,
        db: AsyncSession,
        project_id: int,
        user_id: int,
    ) -> Project | None:
        m = self._member_exists(user_id)
        cond = or_(Project.owner_id == user_id, m)
        result = await db.execute(
            select(Project)
            .options(selectinload(Project.owner))
            .where(Project.id == project_id)
            .where(Project.deleted_at.is_(None))
            .where(cond)
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_member_row(
        self,
        db: AsyncSession,
        *,
        project_id: int,
        user_id: int,
    ) -> ProjectMember | None:
        result = await db.execute(
            select(ProjectMember)
            .where(ProjectMember.project_id == project_id)
            .where(ProjectMember.user_id == user_id)
            .where(ProjectMember.deleted_at.is_(None))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def soft_delete_members_by_project(
        self,
        db: AsyncSession,
        *,
        project_id: int,
        deleted_by: str | None,
    ) -> None:
        now = datetime.now(timezone.utc)
        await db.execute(
            update(ProjectMember)
            .where(ProjectMember.project_id == project_id)
            .where(ProjectMember.deleted_at.is_(None))
            .values(deleted_at=now, deleted_by=deleted_by)
        )


class ProjectMemberRepository(BaseRepository[ProjectMember]):
    def __init__(self) -> None:
        super().__init__(ProjectMember)

    async def list_active_with_users(
        self,
        db: AsyncSession,
        project_id: int,
    ) -> list[tuple[ProjectMember, User]]:
        r = await db.execute(
            select(ProjectMember, User)
            .join(User, User.id == ProjectMember.user_id)
            .where(ProjectMember.project_id == project_id)
            .where(ProjectMember.deleted_at.is_(None))
            .where(User.deleted_at.is_(None))
            .order_by(ProjectMember.id.asc())
        )
        return list(r.all())

    async def get_active_by_project_and_user(
        self,
        db: AsyncSession,
        *,
        project_id: int,
        user_id: int,
    ) -> ProjectMember | None:
        result = await db.execute(
            select(ProjectMember)
            .where(ProjectMember.project_id == project_id)
            .where(ProjectMember.user_id == user_id)
            .where(ProjectMember.deleted_at.is_(None))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def soft_delete_one(
        self,
        db: AsyncSession,
        *,
        project_id: int,
        member_user_id: int,
        deleted_by: str | None,
    ) -> ProjectMember | None:
        row = await self.get_active_by_project_and_user(
            db, project_id=project_id, user_id=member_user_id
        )
        if not row:
            return None
        now = datetime.now(timezone.utc)
        row.deleted_at = now
        row.deleted_by = deleted_by
        await db.flush()
        return row
