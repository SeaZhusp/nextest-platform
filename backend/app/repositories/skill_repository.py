from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.skill import Skill
from app.repositories.base import BaseRepository


class SkillRepository(BaseRepository[Skill]):
    def __init__(self) -> None:
        super().__init__(Skill)

    async def get_by_skill_id(
        self,
        db: AsyncSession,
        skill_id: str,
        *,
        include_deleted: bool = False,
    ) -> Skill | None:
        q = select(Skill).where(Skill.skill_id == skill_id.strip())
        if not include_deleted:
            q = q.where(Skill.deleted_at.is_(None))
        result = await db.execute(q.limit(1))
        return result.scalar_one_or_none()

    async def list_plaza_candidates(
        self,
        db: AsyncSession,
        *,
        q: str | None,
    ) -> list[Skill]:
        stmt = select(Skill).where(
            Skill.deleted_at.is_(None),
            Skill.is_published.is_(True),
        )
        if q and q.strip():
            qq = f"%{q.strip()}%"
            stmt = stmt.where(
                or_(
                    Skill.name.like(qq),
                    Skill.skill_id.like(qq),
                    Skill.description.like(qq),
                )
            )
        stmt = stmt.order_by(Skill.sort_order.asc(), Skill.id.asc())
        rows = (await db.execute(stmt)).scalars().all()
        return list(rows)

    async def search_admin(
        self,
        db: AsyncSession,
        *,
        page: int,
        size: int,
        q: str | None,
    ) -> tuple[list[Skill], int]:
        stmt = select(Skill).where(Skill.deleted_at.is_(None))
        if q and q.strip():
            qq = f"%{q.strip()}%"
            stmt = stmt.where(
                or_(
                    Skill.name.like(qq),
                    Skill.skill_id.like(qq),
                    Skill.description.like(qq),
                )
            )
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await db.execute(count_stmt)).scalar_one()
        stmt = stmt.order_by(Skill.sort_order.asc(), Skill.id.desc())
        stmt = stmt.offset((page - 1) * size).limit(size)
        rows = (await db.execute(stmt)).scalars().all()
        return list(rows), int(total)

    async def increment_use_count(self, db: AsyncSession, skill_id: str) -> int:
        """目录中存在该 skill_id 且未删除时 use_count+1，返回受影响行数。"""
        sid = skill_id.strip()
        if not sid:
            return 0
        stmt = (
            update(Skill)
            .where(Skill.skill_id == sid, Skill.deleted_at.is_(None))
            .values(use_count=Skill.use_count + 1)
        )
        res = await db.execute(stmt)
        return int(res.rowcount or 0)
