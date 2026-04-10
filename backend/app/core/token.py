from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from app.constants.enums import TokenTypeEnum
from app.core.config import settings


class TokenManager:
    @staticmethod
    def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
        """创建访问令牌。"""
        expire = datetime.now(timezone.utc) + (
            expires_delta or timedelta(days=settings.jwt_access_token_expire_days)
        )
        payload = dict(data)
        payload.update({"exp": expire, "type": TokenTypeEnum.ACCESS.value})
        return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

    @staticmethod
    def create_refresh_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
        """创建刷新令牌。"""
        expire = datetime.now(timezone.utc) + (
            expires_delta or timedelta(days=settings.jwt_refresh_token_expire_days)
        )
        payload = dict(data)
        payload.update({"exp": expire, "type": TokenTypeEnum.REFRESH.value})
        return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

    @staticmethod
    def verify_token(
        token: str,
        token_type: TokenTypeEnum = TokenTypeEnum.ACCESS,
    ) -> dict[str, Any] | None:
        """验证令牌。"""
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret,
                algorithms=[settings.jwt_algorithm],
            )
            if payload.get("type") != token_type.value:
                return None

            exp = payload.get("exp")
            if exp is None:
                return None
            if datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
                return None
            return payload
        except jwt.PyJWTError:
            return None

    @staticmethod
    def refresh_access_token(refresh_token: str) -> str | None:
        """使用刷新令牌获取新的访问令牌。"""
        payload = TokenManager.verify_token(refresh_token, TokenTypeEnum.REFRESH)
        if not payload:
            return None

        access_data = {
            "sub": payload.get("sub"),
            "username": payload.get("username"),
            "user_id": payload.get("user_id"),
            "member_level": payload.get("member_level"),
            "role": payload.get("role"),
        }
        return TokenManager.create_access_token(access_data)

    @staticmethod
    def get_token_expiration(token: str) -> datetime | None:
        """获取令牌过期时间。"""
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret,
                algorithms=[settings.jwt_algorithm],
                options={"verify_exp": False},
            )
            exp = payload.get("exp")
            if exp is None:
                return None
            return datetime.fromtimestamp(exp, tz=timezone.utc)
        except jwt.PyJWTError:
            return None

    @staticmethod
    def is_token_expired(token: str) -> bool:
        """检查令牌是否过期。"""
        exp_time = TokenManager.get_token_expiration(token)
        if not exp_time:
            return True
        return exp_time < datetime.now(timezone.utc)


def create_access_token(subject: str, role: str) -> str:
    """兼容现有调用方式，创建 access token。"""
    expire_delta = timedelta(minutes=settings.access_token_expire_minutes)
    return TokenManager.create_access_token(
        data={"sub": subject, "role": role},
        expires_delta=expire_delta,
    )
