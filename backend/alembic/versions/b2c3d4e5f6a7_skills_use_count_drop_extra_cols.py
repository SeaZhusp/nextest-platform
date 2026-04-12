"""skills: drop subtitle/detail_markdown/view/like; add use_count

Revision ID: b2c3d4e5f6a7
Revises: fe0ef7a60bcd
Create Date: 2026-04-12

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "fe0ef7a60bcd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("skills", "subtitle")
    op.drop_column("skills", "detail_markdown")
    op.drop_column("skills", "view_count")
    op.drop_column("skills", "like_count")
    op.add_column(
        "skills",
        sa.Column(
            "use_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="使用次数：智能体以该技能发起新会话时 +1",
        ),
    )
    op.alter_column("skills", "use_count", server_default=None)


def downgrade() -> None:
    op.drop_column("skills", "use_count")
    op.add_column(
        "skills",
        sa.Column("subtitle", sa.String(length=256), nullable=True, comment="副标题"),
    )
    op.add_column(
        "skills",
        sa.Column("detail_markdown", sa.Text(), nullable=True, comment="详情 Markdown"),
    )
    op.add_column(
        "skills",
        sa.Column("view_count", sa.Integer(), nullable=False, server_default="0", comment="详情浏览次数"),
    )
    op.add_column(
        "skills",
        sa.Column("like_count", sa.Integer(), nullable=False, server_default="0", comment="点赞数（预留）"),
    )
    op.alter_column("skills", "view_count", server_default=None)
    op.alter_column("skills", "like_count", server_default=None)
