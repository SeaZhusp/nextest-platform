from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.enums import TokenTypeEnum
from app.core.exceptions import AuthenticationException
from app.core.password import verify_password
from app.core.token import TokenManager
from app.db.session import get_db
from app.repositories.user import UserRepository
from app.schemas.auth import LoginRequest, RefreshTokenRequest, TokenData, TokenPairData
from app.schemas.common import ApiResponse

router = APIRouter()


@router.post("/login", response_model=ApiResponse[TokenData])
async def login(
    payload: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[TokenData]:
    user_repo = UserRepository()
    user = await user_repo.get_by_username(db, payload.username)
    if not user or not user.is_active:
        raise AuthenticationException("用户名或密码错误")
    if not verify_password(payload.password, user.password_hash):
        raise AuthenticationException("用户名或密码错误")

    token = TokenManager.create_access_token(
        {
            "sub": str(user.id),
            "user_id": user.id,
            "username": user.username,
            "role": user.role,
        }
    )
    return ApiResponse(
        data=TokenData(access_token=token),
        request_id=getattr(request.state, "request_id", None),
    )


@router.post("/refresh", response_model=ApiResponse[TokenPairData])
def refresh_token(
    payload: RefreshTokenRequest,
    request: Request,
) -> ApiResponse[TokenPairData]:
    access_token = TokenManager.refresh_access_token(payload.refresh_token)
    if not access_token:
        raise AuthenticationException("refresh token 无效或已过期")

    refresh_payload = TokenManager.verify_token(payload.refresh_token, TokenTypeEnum.REFRESH)
    if not refresh_payload:
        raise AuthenticationException("refresh token 无效或已过期")

    new_refresh_token = TokenManager.create_refresh_token(
        {
            "sub": refresh_payload.get("sub"),
            "username": refresh_payload.get("username"),
            "user_id": refresh_payload.get("user_id"),
            "member_level": refresh_payload.get("member_level"),
            "role": refresh_payload.get("role"),
        }
    )
    return ApiResponse(
        data=TokenPairData(
            access_token=access_token,
            refresh_token=new_refresh_token,
        ),
        request_id=getattr(request.state, "request_id", None),
    )
