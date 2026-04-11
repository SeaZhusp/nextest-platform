from dataclasses import dataclass
from typing import Any

from fastapi import Depends, Header, Request

from app.constants.enums import TokenTypeEnum, UserRoleEnum
from app.core.exceptions import AuthenticationException, AuthorizationException
from app.core.token import TokenManager


@dataclass
class CurrentUser:
    user_id: str
    username: str
    user_type: str
    member_level: str | None = None
    raw_payload: dict[str, Any] | None = None


@dataclass
class AuthContext:
    user: CurrentUser | None
    request: Request


def _extract_bearer_token(authorization: str) -> str:
    if not authorization.startswith("Bearer "):
        raise AuthenticationException("请先登录（缺少 Bearer Token）")
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise AuthenticationException("无效认证，请重新登录")
    return token


def _build_current_user(payload: dict[str, Any]) -> CurrentUser:
    username = payload.get("username") or payload.get("sub")
    if not username:
        raise AuthenticationException("无效认证令牌")
    ut = payload.get("user_type") or payload.get("role")
    return CurrentUser(
        user_id=str(payload.get("user_id") or payload.get("sub") or ""),
        username=str(username),
        user_type=str(ut or UserRoleEnum.USER.value),
        member_level=payload.get("member_level"),
        raw_payload=payload,
    )


def get_current_user(authorization: str = Header(default="")) -> CurrentUser:
    token = _extract_bearer_token(authorization)
    payload = TokenManager.verify_token(token, TokenTypeEnum.ACCESS)
    if not payload:
        raise AuthenticationException("认证已过期或无效，请重新登录")
    return _build_current_user(payload)


def require_admin(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if user.user_type != UserRoleEnum.ADMIN.value:
        raise AuthorizationException("需要管理员权限")
    return user


def open_auth(request: Request) -> AuthContext:
    return AuthContext(user=None, request=request)


def user_auth(
    request: Request,
    user: CurrentUser = Depends(get_current_user),
) -> AuthContext:
    return AuthContext(user=user, request=request)


def admin_auth(
    request: Request,
    user: CurrentUser = Depends(require_admin),
) -> AuthContext:
    return AuthContext(user=user, request=request)
