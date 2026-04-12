"""agent_sessions: display title for history list / rename

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-04-12

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, Sequence[str], None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "agent_sessions",
        sa.Column(
            "title",
            sa.String(length=200),
            nullable=False,
            server_default="新会话",
            comment="展示名称；可重命名；首轮用户输入后可自动摘要为标题",
        ),
    )
    op.alter_column("agent_sessions", "title", server_default=None)


def downgrade() -> None:
    op.drop_column("agent_sessions", "title")
