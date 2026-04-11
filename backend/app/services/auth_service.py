from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.enums import UserRoleEnum
from app.core.exceptions import AuthenticationException, ConflictException
from app.core.password import hash_password, verify_password
from app.core.token import TokenManager
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.auth import AuthSessionData, LoginRequest, RegisterRequest, UserPublic


def user_to_public(user: User) -> UserPublic:
    return UserPublic(
        id=int(user.id),
        username=user.username,
        email=user.email,
        nickname=user.nickname,
        phone=user.phone,
        user_type=user.user_type,
        is_active=user.is_active,
        last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
        created_at=user.created_at.isoformat() if user.created_at else "",
        updated_at=user.updated_at.isoformat() if user.updated_at else "",
    )


def build_session_for_user(user: User) -> AuthSessionData:
    base_claims = {
        "sub": str(user.id),
        "user_id": user.id,
        "username": user.username,
        "user_type": user.user_type,
    }
    access_token = TokenManager.create_access_token(base_claims)
    refresh_token = TokenManager.create_refresh_token(base_claims)
    return AuthSessionData(
        access_token=access_token,
        refresh_token=refresh_token,
        user_info=user_to_public(user),
    )


class AuthService:
    def __init__(self) -> None:
        self._users = UserRepository()

    async def login(self, db: AsyncSession, payload: LoginRequest) -> AuthSessionData:
        user = await self._users.get_by_username(db, payload.username.strip())
        if not user or not user.is_active:
            raise AuthenticationException("用户名或密码错误")
        if not verify_password(payload.password, user.password):
            raise AuthenticationException("用户名或密码错误")

        user.last_login_at = datetime.now(timezone.utc)
        await db.flush()
        await db.commit()
        await db.refresh(user)
        return build_session_for_user(user)

    async def register(self, db: AsyncSession, payload: RegisterRequest) -> AuthSessionData:
        if await self._users.get_by_username(db, payload.username.strip()):
            raise ConflictException("用户名已被注册")

        user = await self._users.create(
            db,
            {
                "username": payload.username.strip(),
                "nickname": payload.nickname,
                "email": None,
                "password": hash_password(payload.password),
                "user_type": UserRoleEnum.USER.value,
                "is_active": True,
            },
        )
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            raise ConflictException("用户名已被注册") from None

        await db.refresh(user)
        return build_session_for_user(user)
