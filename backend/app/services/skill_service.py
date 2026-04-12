from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ValidationException
from app.models.skill import Skill
from app.repositories.skill_repository import SkillRepository
from app.schemas.skill import (
    SkillAdminListData,
    SkillAdminOut,
    SkillCreate,
    SkillPlazaDetailOut,
    SkillPlazaItemOut,
    SkillPlazaListData,
    SkillUpdate,
)
from app.services.skill.registry import get_skill_registry


def _registry_has(skill_id: str) -> bool:
    return skill_id in set(get_skill_registry().list_skill_ids())


def _tags(row: Skill) -> list[str]:
    if row.capability_tags is None:
        return []
    if isinstance(row.capability_tags, list):
        return [str(x) for x in row.capability_tags]
    return []


def _to_plaza_item(row: Skill) -> SkillPlazaItemOut:
    return SkillPlazaItemOut(
        id=int(row.id),
        skill_id=row.skill_id,
        name=row.name,
        description=row.description or "",
        capability_tags=_tags(row),
        icon_key=row.icon_key,
        is_published=row.is_published,
        sort_order=row.sort_order,
        use_count=int(row.use_count or 0),
        runtime_available=_registry_has(row.skill_id),
    )


def _to_admin_out(row: Skill) -> SkillAdminOut:
    return SkillAdminOut(
        id=int(row.id),
        skill_id=row.skill_id,
        name=row.name,
        description=row.description or "",
        capability_tags=_tags(row),
        icon_key=row.icon_key,
        is_published=row.is_published,
        sort_order=row.sort_order,
        use_count=int(row.use_count or 0),
        runtime_available=_registry_has(row.skill_id),
        created_at=row.created_at.isoformat() if row.created_at else "",
        updated_at=row.updated_at.isoformat() if row.updated_at else "",
    )


class SkillService:
    def __init__(self) -> None:
        self._repo = SkillRepository()

    async def record_new_agent_session(self, db: AsyncSession, skill_id: str) -> None:
        """技能目录中存在该 skill_id 时，将使用次数 +1 并提交。"""
        n = await self._repo.increment_use_count(db, skill_id)
        if n:
            await db.commit()

    async def list_plaza(
        self,
        db: AsyncSession,
        *,
        page: int,
        size: int,
        q: str | None,
    ) -> SkillPlazaListData:
        candidates = await self._repo.list_plaza_candidates(db, q=q)
        total = len(candidates)
        offset = (page - 1) * size
        page_rows = candidates[offset : offset + size]
        items = [_to_plaza_item(r) for r in page_rows]
        return SkillPlazaListData(items=items, total=total, page=page, size=size)

    async def get_plaza_detail(
        self,
        db: AsyncSession,
        *,
        skill_id: str,
    ) -> SkillPlazaDetailOut:
        row = await self._repo.get_by_skill_id(db, skill_id)
        if not row or not row.is_published:
            raise NotFoundException("技能不存在或未上架")
        return SkillPlazaDetailOut.model_validate(_to_plaza_item(row))

    async def list_admin(
        self,
        db: AsyncSession,
        *,
        page: int,
        size: int,
        q: str | None,
    ) -> SkillAdminListData:
        rows, total = await self._repo.search_admin(db, page=page, size=size, q=q)
        return SkillAdminListData(
            items=[_to_admin_out(r) for r in rows],
            total=total,
            page=page,
            size=size,
        )

    async def create_admin(
        self,
        db: AsyncSession,
        payload: SkillCreate,
    ) -> SkillAdminOut:
        existing = await self._repo.get_by_skill_id(db, payload.skill_id)
        if existing:
            raise ValidationException(f"技能 ID 已存在: {payload.skill_id}")
        data = {
            "skill_id": payload.skill_id.strip(),
            "name": payload.name.strip(),
            "description": payload.description or "",
            "capability_tags": payload.capability_tags or [],
            "icon_key": payload.icon_key,
            "is_published": payload.is_published,
            "sort_order": payload.sort_order,
            "use_count": 0,
        }
        row = await self._repo.create(db, data)
        await db.commit()
        await db.refresh(row)
        return _to_admin_out(row)

    async def update_admin(
        self,
        db: AsyncSession,
        record_id: int,
        payload: SkillUpdate,
    ) -> SkillAdminOut:
        row = await self._repo.require_by_id(db, record_id)
        update_data: dict = {}
        if payload.skill_id is not None:
            sid = payload.skill_id.strip()
            other = await self._repo.get_by_skill_id(db, sid)
            if other and other.id != row.id:
                raise ValidationException(f"技能 ID 已存在: {sid}")
            update_data["skill_id"] = sid
        if payload.name is not None:
            update_data["name"] = payload.name.strip()
        if payload.description is not None:
            update_data["description"] = payload.description
        if payload.capability_tags is not None:
            update_data["capability_tags"] = payload.capability_tags
        if payload.icon_key is not None:
            update_data["icon_key"] = payload.icon_key or None
        if payload.is_published is not None:
            update_data["is_published"] = payload.is_published
        if payload.sort_order is not None:
            update_data["sort_order"] = payload.sort_order
        if not update_data:
            return _to_admin_out(row)
        row = await self._repo.update(db, record_id, update_data)
        await db.commit()
        await db.refresh(row)
        return _to_admin_out(row)

    async def delete_admin(
        self,
        db: AsyncSession,
        record_id: int,
        *,
        deleted_by: str,
    ) -> None:
        await self._repo.soft_delete(db, record_id, deleted_by=deleted_by)
        await db.commit()
