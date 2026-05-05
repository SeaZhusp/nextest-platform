from __future__ import annotations

from sqlalchemy import BigInteger, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import ModelBase
from app.models.project import Project


class ProjectModule(ModelBase):
    """项目模块（树形：parent_id 为空表示根；可供功能用例等挂载，可与后续 API 测试等共用同一棵树）。"""

    __tablename__ = "project_modules"
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "parent_id",
            "name",
            name="uq_project_modules_project_parent_name",
        ),
    )

    project_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        comment="所属项目",
    )
    parent_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("project_modules.id", ondelete="CASCADE"),
        index=True,
        nullable=True,
        comment="父模块 ID，根节点为空",
    )
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="模块名称（同级唯一）",
    )
    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="同级排序，越小越前",
    )
    description: Mapped[str | None] = mapped_column(
        String(2000),
        nullable=True,
        comment="模块说明",
    )

    project: Mapped[Project] = relationship("Project", foreign_keys=[project_id])
    parent: Mapped[ProjectModule | None] = relationship(
        "ProjectModule",
        foreign_keys=[parent_id],
        remote_side="ProjectModule.id",
        back_populates="children",
    )
    children: Mapped[list[ProjectModule]] = relationship(
        "ProjectModule",
        back_populates="parent",
        cascade="all, delete-orphan",
    )
    functional_cases: Mapped[list["FunctionalCase"]] = relationship(
        "FunctionalCase",
        back_populates="module",
        cascade="all, delete-orphan",
    )
