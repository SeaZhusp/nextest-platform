from __future__ import annotations

from sqlalchemy import BigInteger, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import ModelBase
from app.models.user import User


class Project(ModelBase):
    """项目：用例等业务资产的一级容器。"""

    __tablename__ = "projects"

    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="项目名称",
    )
    description: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="项目描述",
    )
    owner_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
        comment="项目负责人用户 ID（与成员表中 role=owner 对应，由业务层保持一致）",
    )

    owner: Mapped[User] = relationship(foreign_keys=[owner_id])
    members: Mapped[list[ProjectMember]] = relationship(
        "ProjectMember",
        back_populates="project",
        cascade="all, delete-orphan",
    )


class ProjectMember(ModelBase):
    """项目成员：同一用户在同一项目仅一行；leader/tester 可多人。"""

    __tablename__ = "project_members"
    __table_args__ = (
        UniqueConstraint("project_id", "user_id", name="uq_project_members_project_user"),
    )

    project_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        comment="项目 ID",
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        comment="用户 ID",
    )
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="owner / leader / tester（见 ProjectMemberRoleEnum）",
    )

    project: Mapped[Project] = relationship("Project", back_populates="members")
    user: Mapped[User] = relationship(foreign_keys=[user_id])
