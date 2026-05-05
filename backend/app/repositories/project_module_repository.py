from sqlalchemy import and_, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project_module import ProjectModule
from app.repositories.base import BaseRepository


class ProjectModuleRepository(BaseRepository[ProjectModule]):
    def __init__(self) -> None:
        super().__init__(ProjectModule)

    async def list_by_project(
        self,
        db: AsyncSession,
        *,
        project_id: int,
    ) -> list[ProjectModule]:
        q = (
            self._base_query()
            .where(ProjectModule.project_id == project_id)
            .order_by(
                # MySQL 不支持 NULLS FIRST；用 CASE 把根节点（parent_id IS NULL）排在前面
                case((ProjectModule.parent_id.is_(None), 0), else_=1),
                ProjectModule.parent_id.asc(),
                ProjectModule.sort_order.asc(),
                ProjectModule.id.asc(),
            )
        )
        r = await db.execute(q)
        return list(r.scalars().all())

    async def get_by_id_in_project(
        self,
        db: AsyncSession,
        *,
        project_id: int,
        module_id: int,
    ) -> ProjectModule | None:
        r = await db.execute(
            self._base_query()
            .where(ProjectModule.project_id == project_id)
            .where(ProjectModule.id == module_id)
            .limit(1)
        )
        return r.scalar_one_or_none()

    async def find_active_by_name_under_parent(
        self,
        db: AsyncSession,
        *,
        project_id: int,
        parent_id: int | None,
        name: str,
        exclude_module_id: int | None = None,
    ) -> ProjectModule | None:
        conds = [
            ProjectModule.project_id == project_id,
            ProjectModule.name == name,
        ]
        if parent_id is None:
            conds.append(ProjectModule.parent_id.is_(None))
        else:
            conds.append(ProjectModule.parent_id == parent_id)
        if exclude_module_id is not None:
            conds.append(ProjectModule.id != exclude_module_id)
        r = await db.execute(self._base_query().where(and_(*conds)).limit(1))
        return r.scalar_one_or_none()

    async def max_sort_order_among_siblings(
        self,
        db: AsyncSession,
        *,
        project_id: int,
        parent_id: int | None,
    ) -> int | None:
        q = self._base_query().where(ProjectModule.project_id == project_id)
        if parent_id is None:
            q = q.where(ProjectModule.parent_id.is_(None))
        else:
            q = q.where(ProjectModule.parent_id == parent_id)
        q = q.order_by(ProjectModule.sort_order.desc()).limit(1)
        r = await db.execute(q)
        row = r.scalar_one_or_none()
        return int(row.sort_order) if row else None
