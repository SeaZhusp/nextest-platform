from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.enums import TokenTypeEnum
from app.core.exceptions import AuthenticationException
from app.core.token import TokenManager
from app.db.session import get_db
from app.schemas.auth import (
    AuthSessionData,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenPairData,
)
from app.schemas.common import ApiResponse
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/login", response_model=ApiResponse[AuthSessionData])
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[AuthSessionData]:
    auth_service = AuthService()
    data = await auth_service.login(db, payload)
    return ApiResponse(data=data)


@router.post("/register", response_model=ApiResponse[AuthSessionData])
async def register(
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[AuthSessionData]:
    auth_service = AuthService()
    data = await auth_service.register(db, payload)
    return ApiResponse(data=data)


@router.post("/refresh", response_model=ApiResponse[TokenPairData])
def refresh_token(
    payload: RefreshTokenRequest,
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
    )
