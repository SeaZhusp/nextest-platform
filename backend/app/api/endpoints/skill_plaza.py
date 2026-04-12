"""技能广场（只读，登录用户）。"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import CurrentUser, get_current_user
from app.api.deps.query import Paging
from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.skill import SkillPlazaDetailOut, SkillPlazaListData
from app.services.skill_service import SkillService

router = APIRouter(prefix="/skill-plaza", tags=["skill-plaza"])


@router.get("", response_model=ApiResponse[SkillPlazaListData])
async def list_skill_plaza(
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
    paging: Paging = Depends(),
    q: str | None = Query(None, max_length=200, description="搜索名称、skill_id、描述"),
) -> ApiResponse[SkillPlazaListData]:
    svc = SkillService()
    data = await svc.list_plaza(
        db,
        page=paging.page,
        size=paging.size,
        q=(q or "").strip() or None,
    )
    return ApiResponse(data=data)


@router.get("/{skill_id}", response_model=ApiResponse[SkillPlazaDetailOut])
async def get_skill_plaza_detail(
    skill_id: str,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
) -> ApiResponse[SkillPlazaDetailOut]:
    svc = SkillService()
    data = await svc.get_plaza_detail(db, skill_id=skill_id.strip())
    return ApiResponse(data=data)
