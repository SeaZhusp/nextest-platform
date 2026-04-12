"""agent_sessions + agent_messages (2.2.4 会话与记忆)

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-04-12

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, Sequence[str], None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "agent_sessions",
        sa.Column("session_uuid", sa.String(length=36), nullable=False, comment="对外会话 ID（UUID 字符串）"),
        sa.Column("user_id", sa.BigInteger(), nullable=False, comment="所属用户"),
        sa.Column("skill_id", sa.String(length=64), nullable=False, comment="当前技能 ID"),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False, comment="数据库主键ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="更新时间"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True, comment="删除时间(软删除)"),
        sa.Column("deleted_by", sa.String(length=36), nullable=True, comment="删除人标识"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_agent_sessions_session_uuid"), "agent_sessions", ["session_uuid"], unique=True)
    op.create_index(op.f("ix_agent_sessions_user_id"), "agent_sessions", ["user_id"], unique=False)

    op.create_table(
        "agent_messages",
        sa.Column("agent_session_id", sa.BigInteger(), nullable=False, comment="所属会话主键"),
        sa.Column("role", sa.String(length=16), nullable=False, comment="user / assistant"),
        sa.Column("content_json", sa.JSON(), nullable=False, comment="用户：{parts:[...]}；助手：{text: 模型原文或等价 JSON 文本}"),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False, comment="数据库主键ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="更新时间"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True, comment="删除时间(软删除)"),
        sa.Column("deleted_by", sa.String(length=36), nullable=True, comment="删除人标识"),
        sa.ForeignKeyConstraint(["agent_session_id"], ["agent_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_agent_messages_agent_session_id"),
        "agent_messages",
        ["agent_session_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_agent_messages_agent_session_id"), table_name="agent_messages")
    op.drop_table("agent_messages")
    op.drop_index(op.f("ix_agent_sessions_user_id"), table_name="agent_sessions")
    op.drop_index(op.f("ix_agent_sessions_session_uuid"), table_name="agent_sessions")
    op.drop_table("agent_sessions")
