from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.enums import SortOrderEnum
from app.core.exceptions import ValidationException
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import UserListData, UserOut


def user_to_out(user: User) -> UserOut:
    return UserOut(
        id=int(user.id),
        username=user.username,
        nickname=user.nickname,
        email=user.email,
        phone=user.phone,
        user_type=user.user_type,
        is_active=user.is_active,
        last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
        created_at=user.created_at.isoformat() if user.created_at else "",
        updated_at=user.updated_at.isoformat() if user.updated_at else "",
    )


class UserService:
    def __init__(self) -> None:
        self._users = UserRepository()

    async def list_users(
        self,
        db: AsyncSession,
        *,
        page: int,
        size: int,
        username: str | None,
        is_active: bool | None = None,
    ) -> UserListData:
        records, total = await self._users.search_paginated(
            db,
            page=page,
            size=size,
            sort_by="created_at",
            order_by=SortOrderEnum.DESC,
            username=username,
            is_active=is_active,
        )
        return UserListData(
            items=[user_to_out(u) for u in records],
            total=total,
            page=page,
            size=size,
        )

    def _parse_actor_id(self, actor_user_id: str) -> int:
        try:
            return int(actor_user_id)
        except (TypeError, ValueError) as e:
            raise ValidationException("无效的操作者身份") from e

    async def set_active(
        self,
        db: AsyncSession,
        user_id: int,
        is_active: bool,
        *,
        actor_user_id: str,
    ) -> UserOut:
        actor_id = self._parse_actor_id(actor_user_id)
        if not is_active and user_id == actor_id:
            raise ValidationException("不能禁用自己的账号")
        await self._users.require_by_id(db, user_id)
        user = await self._users.update(db, user_id, {"is_active": is_active})
        await db.commit()
        await db.refresh(user)
        return user_to_out(user)

    async def delete_user(
        self,
        db: AsyncSession,
        user_id: int,
        *,
        actor_user_id: str,
        actor_username: str,
    ) -> None:
        actor_id = self._parse_actor_id(actor_user_id)
        if user_id == actor_id:
            raise ValidationException("不能删除自己的账号")
        await self._users.soft_delete(db, user_id, deleted_by=actor_username)
        await db.commit()
