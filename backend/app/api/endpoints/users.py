from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import CurrentUser, require_admin
from app.api.deps.query import Paging
from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.user import UserActiveRequest, UserListData, UserOut
from app.services.user_service import UserService

router = APIRouter(prefix="/admin/users", tags=["admin-users"])


@router.get("", response_model=ApiResponse[UserListData])
async def list_users(
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_admin),
    paging: Paging = Depends(),
    username: str | None = Query(None, max_length=64, description="用户名模糊匹配，不传则不限"),
    is_active: bool | None = Query(None, description="按是否启用筛选，不传则不限"),
) -> ApiResponse[UserListData]:
    svc = UserService()
    u = (username or "").strip() or None
    data = await svc.list_users(
        db,
        page=paging.page,
        size=paging.size,
        username=u,
        is_active=is_active,
    )
    return ApiResponse(data=data)


@router.patch("/{user_id}/active", response_model=ApiResponse[UserOut])
async def set_user_active(
    user_id: int,
    payload: UserActiveRequest,
    db: AsyncSession = Depends(get_db),
    actor: CurrentUser = Depends(require_admin),
) -> ApiResponse[UserOut]:
    svc = UserService()
    data = await svc.set_active(
        db,
        user_id,
        payload.is_active,
        actor_user_id=actor.user_id,
    )
    return ApiResponse(data=data)


@router.delete("/{user_id}", response_model=ApiResponse[Any])
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    actor: CurrentUser = Depends(require_admin),
) -> ApiResponse[Any]:
    svc = UserService()
    await svc.delete_user(
        db,
        user_id,
        actor_user_id=actor.user_id,
        actor_username=actor.username,
    )
    return ApiResponse(data=None)
