from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.constants.enums import UserRoleEnum
from app.models.base import ModelBase


class User(ModelBase):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
        comment="用户名",
    )
    nickname: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="昵称/姓名",
    )
    email: Mapped[str | None] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=True,
        comment="邮箱",
    )
    phone: Mapped[str | None] = mapped_column(
        String(20),
        unique=True,
        index=True,
        nullable=True,
        comment="手机号",
    )
    password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="密码哈希",
    )
    user_type: Mapped[str] = mapped_column(
        "user_type",
        String(20),
        nullable=False,
        default=UserRoleEnum.USER.value,
        comment="用户类型",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="是否启用",
    )
    last_login_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="最后登录时间",
    )
