from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessException, NotFoundException, ValidationException
from app.models.user_llm_profile import UserLlmProfile
from app.repositories.user_llm_profile_repository import user_llm_profile_repository
from app.schemas.llm_invoke import LlmInvokeConfig
from app.schemas.user_llm_profile import (
    LlmConnectionTestRequest,
    LlmConnectionTestResult,
    UserLlmProfileCreate,
    UserLlmProfileDetailOut,
    UserLlmProfileListResponse,
    UserLlmProfileOut,
    UserLlmProfileUpdate,
)
from app.llm.client import chat_completion_content


def _key_last4(api_key: str) -> str:
    s = api_key.strip()
    if len(s) <= 4:
        return s
    return s[-4:]


def _mask_api_key(api_key: str) -> str:
    s = (api_key or "").strip()
    if not s:
        return "••••"
    if s.startswith("sk-"):
        return "sk-" + "•" * 8
    if len(s) <= 8:
        return "•" * min(8, len(s))
    return s[:3] + "•" * 6 + s[-4:]


def _row_to_out(row: UserLlmProfile) -> UserLlmProfileOut:
    return UserLlmProfileOut(
        id=int(row.id),
        provider=row.provider,
        display_name=row.display_name,
        api_base=row.api_base,
        model_name=row.model_name,
        key_last4=row.key_last4,
        api_key_masked=_mask_api_key(row.api_key),
        is_active=bool(row.is_active),
    )


def _row_to_detail(row: UserLlmProfile) -> UserLlmProfileDetailOut:
    base = _row_to_out(row)
    return UserLlmProfileDetailOut(**base.model_dump(), api_key=row.api_key)


async def list_profiles(
    db: AsyncSession,
    user_id: int,
    *,
    active_only: bool = False,
) -> UserLlmProfileListResponse:
    rows = await user_llm_profile_repository.list_by_user_id(
        db, user_id, active_only=active_only
    )
    return UserLlmProfileListResponse(items=[_row_to_out(r) for r in rows])


async def get_profile_detail(
    db: AsyncSession,
    user_id: int,
    profile_id: int,
) -> UserLlmProfileDetailOut:
    row = await user_llm_profile_repository.get_by_id(db, profile_id)
    if row is None or row.user_id != user_id:
        raise NotFoundException("模型配置不存在")
    return _row_to_detail(row)


async def create_profile(db: AsyncSession, user_id: int, payload: UserLlmProfileCreate) -> UserLlmProfileOut:
    row = UserLlmProfile(
        user_id=user_id,
        provider=payload.provider.strip().lower()[:32],
        display_name=(payload.display_name or "").strip() or payload.model_name.strip(),
        api_base=payload.api_base.strip().rstrip("/"),
        model_name=payload.model_name.strip(),
        api_key=payload.api_key.strip(),
        key_last4=_key_last4(payload.api_key),
        is_active=payload.is_active,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return _row_to_out(row)


async def update_profile(
    db: AsyncSession,
    user_id: int,
    profile_id: int,
    payload: UserLlmProfileUpdate,
) -> UserLlmProfileOut:
    row = await user_llm_profile_repository.get_by_id(db, profile_id)
    if row is None or row.user_id != user_id:
        raise NotFoundException("模型配置不存在")

    data = payload.model_dump(exclude_unset=True)
    if "provider" in data and data["provider"] is not None:
        row.provider = str(data["provider"]).strip().lower()[:32]
    if "display_name" in data and data["display_name"] is not None:
        row.display_name = str(data["display_name"]).strip()
    if "api_base" in data and data["api_base"] is not None:
        row.api_base = str(data["api_base"]).strip().rstrip("/")
    if "model_name" in data and data["model_name"] is not None:
        row.model_name = str(data["model_name"]).strip()
    if "api_key" in data and data["api_key"] is not None:
        ak = str(data["api_key"]).strip()
        if not ak:
            raise ValidationException("API Key 不能为空")
        row.api_key = ak
        row.key_last4 = _key_last4(ak)
    if "is_active" in data and data["is_active"] is not None:
        row.is_active = bool(data["is_active"])

    await db.commit()
    await db.refresh(row)
    return _row_to_out(row)


async def set_profile_active(
    db: AsyncSession,
    user_id: int,
    profile_id: int,
    is_active: bool,
) -> UserLlmProfileOut:
    return await update_profile(
        db,
        user_id,
        profile_id,
        UserLlmProfileUpdate(is_active=is_active),
    )


async def delete_profile(
    db: AsyncSession,
    user_id: int,
    profile_id: int,
    *,
    deleted_by: str | None,
) -> None:
    row = await user_llm_profile_repository.get_by_id(db, profile_id)
    if row is None or row.user_id != user_id:
        raise NotFoundException("模型配置不存在")
    await user_llm_profile_repository.soft_delete(db, profile_id, deleted_by=deleted_by)


async def test_llm_connection_payload(req: LlmConnectionTestRequest) -> LlmConnectionTestResult:
    cfg = LlmInvokeConfig(
        api_base=req.api_base.strip().rstrip("/"),
        api_key=req.api_key.strip(),
        model=req.model_name.strip(),
        temperature=0.0,
    )
    try:
        await chat_completion_content(
            [{"role": "user", "content": "ping"}],
            config=cfg,
        )
    except Exception as e:
        raise BusinessException(
            message="连接失败",
            details={"reason": str(e)},
        ) from e
    return LlmConnectionTestResult(ok=True, message="连接成功")


async def test_llm_connection_by_id(
    db: AsyncSession,
    user_id: int,
    profile_id: int,
) -> LlmConnectionTestResult:
    row = await user_llm_profile_repository.get_by_id(db, profile_id)
    if row is None or row.user_id != user_id:
        raise NotFoundException("模型配置不存在")
    req = LlmConnectionTestRequest(
        api_base=row.api_base,
        model_name=row.model_name,
        api_key=row.api_key,
    )
    return await test_llm_connection_payload(req)
