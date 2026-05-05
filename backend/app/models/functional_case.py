from __future__ import annotations

from typing import Any

from sqlalchemy import BigInteger, ForeignKey, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import ModelBase
from app.models.project_module import ProjectModule
from app.models.project import Project
from app.models.user import User


class FunctionalCase(ModelBase):
    """功能用例（归属项目 + 模块；无乐观锁；可选关联对话追溯来源）。"""

    __tablename__ = "functional_cases"
    __table_args__ = (
        UniqueConstraint("project_id", "case_no", name="uq_functional_cases_project_case_no"),
    )

    project_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        comment="所属项目",
    )
    module_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("project_modules.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
        comment="所属模块（须属于同一项目，由业务层校验）",
    )
    case_no: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="项目内唯一编号（展示用）",
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="标题",
    )
    preconditions: Mapped[str | None] = mapped_column(
        String(2000),
        nullable=True,
        comment="前置条件",
    )
    steps: Mapped[Any] = mapped_column(
        JSON,
        nullable=False,
        comment="步骤（结构化 JSON，数组或对象，由 Pydantic schema 约束）",
    )
    expected: Mapped[str | None] = mapped_column(
        String(2000),
        nullable=True,
        comment="预期结果",
    )
    priority: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
        comment="优先级（如 P0/P1 或自定义文案）",
    )
    case_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="positive / negative / compatibility / scenario（见 TestCaseTypeEnum）",
    )
    source: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        comment="ai / manual（见 TestCaseSourceEnum）",
    )
    created_by_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
        comment="创建人",
    )
    updated_by_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="最后更新人",
    )
    agent_session_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("conversations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="可选：生成来源会话（conversations.id）",
    )
    agent_message_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("conversation_messages.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="可选：生成来源消息（conversation_messages.id）",
    )

    project: Mapped[Project] = relationship("Project", foreign_keys=[project_id])
    module: Mapped[ProjectModule] = relationship(
        "ProjectModule",
        back_populates="functional_cases",
        foreign_keys=[module_id],
    )
    created_by: Mapped[User] = relationship(
        User,
        foreign_keys=[created_by_id],
    )
    updated_by: Mapped[User | None] = relationship(
        User,
        foreign_keys=[updated_by_id],
    )
