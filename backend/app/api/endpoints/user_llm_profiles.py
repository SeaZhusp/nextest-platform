from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import CurrentUser, get_current_user
from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.user_llm_profile import (
    LlmConnectionTestRequest,
    LlmConnectionTestResult,
    UserLlmProfileActivePatch,
    UserLlmProfileCreate,
    UserLlmProfileDetailOut,
    UserLlmProfileListResponse,
    UserLlmProfileOut,
    UserLlmProfileUpdate,
)
from app.services import user_llm_profile_service as llm_profile_svc

router = APIRouter(prefix="/user/llm-profiles", tags=["user-llm-profiles"])


@router.get("", response_model=ApiResponse[UserLlmProfileListResponse])
async def list_my_profiles(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
    active_only: bool = Query(False, description="为 true 时仅返回已启用的配置（智能体下拉用）"),
) -> ApiResponse[UserLlmProfileListResponse]:
    uid = int(user.user_id)
    data = await llm_profile_svc.list_profiles(db, uid, active_only=active_only)
    return ApiResponse(data=data)


@router.post("/test", response_model=ApiResponse[LlmConnectionTestResult])
async def test_connection_payload(
    payload: LlmConnectionTestRequest,
    _user: CurrentUser = Depends(get_current_user),
) -> ApiResponse[LlmConnectionTestResult]:
    """使用表单中的地址 / 模型 / Key 测试连通性（保存前）。"""
    data = await llm_profile_svc.test_llm_connection_payload(payload)
    return ApiResponse(data=data)


@router.get("/{profile_id}", response_model=ApiResponse[UserLlmProfileDetailOut])
async def get_my_profile(
    profile_id: int,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> ApiResponse[UserLlmProfileDetailOut]:
    uid = int(user.user_id)
    data = await llm_profile_svc.get_profile_detail(db, uid, profile_id)
    return ApiResponse(data=data)


@router.post("", response_model=ApiResponse[UserLlmProfileOut])
async def create_my_profile(
    payload: UserLlmProfileCreate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> ApiResponse[UserLlmProfileOut]:
    uid = int(user.user_id)
    data = await llm_profile_svc.create_profile(db, uid, payload)
    return ApiResponse(data=data)


@router.patch("/{profile_id}", response_model=ApiResponse[UserLlmProfileOut])
async def patch_my_profile(
    profile_id: int,
    payload: UserLlmProfileUpdate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> ApiResponse[UserLlmProfileOut]:
    uid = int(user.user_id)
    data = await llm_profile_svc.update_profile(db, uid, profile_id, payload)
    return ApiResponse(data=data)


@router.patch("/{profile_id}/active", response_model=ApiResponse[UserLlmProfileOut])
async def patch_profile_active(
    profile_id: int,
    payload: UserLlmProfileActivePatch,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> ApiResponse[UserLlmProfileOut]:
    uid = int(user.user_id)
    data = await llm_profile_svc.set_profile_active(db, uid, profile_id, payload.is_active)
    return ApiResponse(data=data)


@router.delete("/{profile_id}", response_model=ApiResponse[None])
async def delete_my_profile(
    profile_id: int,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> ApiResponse[None]:
    uid = int(user.user_id)
    await llm_profile_svc.delete_profile(
        db, uid, profile_id, deleted_by=user.user_id
    )
    return ApiResponse(data=None)


@router.post("/{profile_id}/test", response_model=ApiResponse[LlmConnectionTestResult])
async def test_connection_saved(
    profile_id: int,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> ApiResponse[LlmConnectionTestResult]:
    """使用已保存的配置测试连通性。"""
    uid = int(user.user_id)
    data = await llm_profile_svc.test_llm_connection_by_id(db, uid, profile_id)
    return ApiResponse(data=data)
