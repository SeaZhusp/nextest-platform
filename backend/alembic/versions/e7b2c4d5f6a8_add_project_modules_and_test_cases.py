"""add project_modules and functional_cases

Revision ID: e7b2c4d5f6a8
Revises: c4e8f1a2b3d5
Create Date: 2026-05-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e7b2c4d5f6a8"
down_revision: Union[str, Sequence[str], None] = "c4e8f1a2b3d5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "project_modules",
        sa.Column(
            "project_id",
            sa.BigInteger(),
            nullable=False,
            comment="所属项目",
        ),
        sa.Column(
            "parent_id",
            sa.BigInteger(),
            nullable=True,
            comment="父模块 ID，根节点为空",
        ),
        sa.Column("name", sa.String(length=200), nullable=False, comment="模块名称（同级唯一）"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0", comment="同级排序，越小越前"),
        sa.Column("description", sa.Text(), nullable=True, comment="模块说明"),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False, comment="数据库主键ID"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="创建时间",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="更新时间",
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True, comment="删除时间(软删除)"),
        sa.Column("deleted_by", sa.String(length=36), nullable=True, comment="删除人标识"),
        sa.ForeignKeyConstraint(["parent_id"], ["project_modules.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "parent_id", "name", name="uq_project_modules_project_parent_name"),
    )
    op.create_index(op.f("ix_project_modules_parent_id"), "project_modules", ["parent_id"], unique=False)
    op.create_index(op.f("ix_project_modules_project_id"), "project_modules", ["project_id"], unique=False)

    op.create_table(
        "functional_cases",
        sa.Column("project_id", sa.BigInteger(), nullable=False, comment="所属项目"),
        sa.Column("module_id", sa.BigInteger(), nullable=False, comment="所属模块（须属于同一项目，由业务层校验）"),
        sa.Column("case_no", sa.String(length=64), nullable=False, comment="项目内唯一编号（展示用）"),
        sa.Column("title", sa.String(length=500), nullable=False, comment="标题"),
        sa.Column("preconditions", sa.Text(), nullable=True, comment="前置条件"),
        sa.Column(
            "steps",
            sa.JSON(),
            nullable=False,
            comment="步骤（结构化 JSON，数组或对象，由 Pydantic schema 约束）",
        ),
        sa.Column("expected", sa.Text(), nullable=True, comment="预期结果"),
        sa.Column("priority", sa.String(length=32), nullable=True, comment="优先级（如 P0/P1 或自定义文案）"),
        sa.Column(
            "case_type",
            sa.String(length=32),
            nullable=False,
            comment="positive / negative / compatibility / scenario（见 TestCaseTypeEnum）",
        ),
        sa.Column(
            "source",
            sa.String(length=16),
            nullable=False,
            comment="ai / manual（见 TestCaseSourceEnum）",
        ),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0", comment="模块内排序"),
        sa.Column("created_by_id", sa.BigInteger(), nullable=False, comment="创建人"),
        sa.Column("updated_by_id", sa.BigInteger(), nullable=True, comment="最后更新人"),
        sa.Column(
            "agent_session_id",
            sa.BigInteger(),
            nullable=True,
            comment="可选：生成来源会话（conversations.id）",
        ),
        sa.Column(
            "agent_message_id",
            sa.BigInteger(),
            nullable=True,
            comment="可选：生成来源消息（conversation_messages.id）",
        ),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False, comment="数据库主键ID"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="创建时间",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="更新时间",
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True, comment="删除时间(软删除)"),
        sa.Column("deleted_by", sa.String(length=36), nullable=True, comment="删除人标识"),
        sa.ForeignKeyConstraint(["agent_message_id"], ["conversation_messages.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["agent_session_id"], ["conversations.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["module_id"], ["project_modules.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "case_no", name="uq_functional_cases_project_case_no"),
    )
    op.create_index(
        op.f("ix_functional_cases_agent_message_id"),
        "functional_cases",
        ["agent_message_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_functional_cases_agent_session_id"),
        "functional_cases",
        ["agent_session_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_functional_cases_created_by_id"),
        "functional_cases",
        ["created_by_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_functional_cases_module_id"),
        "functional_cases",
        ["module_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_functional_cases_project_id"),
        "functional_cases",
        ["project_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_functional_cases_project_id"), table_name="functional_cases")
    op.drop_index(op.f("ix_functional_cases_module_id"), table_name="functional_cases")
    op.drop_index(op.f("ix_functional_cases_created_by_id"), table_name="functional_cases")
    op.drop_index(op.f("ix_functional_cases_agent_session_id"), table_name="functional_cases")
    op.drop_index(op.f("ix_functional_cases_agent_message_id"), table_name="functional_cases")
    op.drop_table("functional_cases")
    op.drop_index(op.f("ix_project_modules_project_id"), table_name="project_modules")
    op.drop_index(op.f("ix_project_modules_parent_id"), table_name="project_modules")
    op.drop_table("project_modules")
