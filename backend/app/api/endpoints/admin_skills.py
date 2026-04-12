"""技能目录管理（仅管理员）。"""

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import CurrentUser, require_admin
from app.api.deps.query import Paging
from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.skill import SkillAdminListData, SkillAdminOut, SkillCreate, SkillUpdate
from app.services.skill_service import SkillService

router = APIRouter(prefix="/admin/skills", tags=["admin-skills"])


@router.get("", response_model=ApiResponse[SkillAdminListData])
async def list_skills_admin(
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_admin),
    paging: Paging = Depends(),
    q: str | None = Query(None, max_length=200),
) -> ApiResponse[SkillAdminListData]:
    svc = SkillService()
    data = await svc.list_admin(
        db,
        page=paging.page,
        size=paging.size,
        q=(q or "").strip() or None,
    )
    return ApiResponse(data=data)


@router.post("", response_model=ApiResponse[SkillAdminOut])
async def create_skill_admin(
    body: SkillCreate,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_admin),
) -> ApiResponse[SkillAdminOut]:
    svc = SkillService()
    data = await svc.create_admin(db, body)
    return ApiResponse(data=data)


@router.put("/{record_id}", response_model=ApiResponse[SkillAdminOut])
async def update_skill_admin(
    record_id: int,
    body: SkillUpdate,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_admin),
) -> ApiResponse[SkillAdminOut]:
    svc = SkillService()
    data = await svc.update_admin(db, record_id, body)
    return ApiResponse(data=data)


@router.delete("/{record_id}", response_model=ApiResponse[Any])
async def delete_skill_admin(
    record_id: int,
    db: AsyncSession = Depends(get_db),
    actor: CurrentUser = Depends(require_admin),
) -> ApiResponse[Any]:
    svc = SkillService()
    await svc.delete_admin(db, record_id, deleted_by=actor.username)
    return ApiResponse(data=None)
