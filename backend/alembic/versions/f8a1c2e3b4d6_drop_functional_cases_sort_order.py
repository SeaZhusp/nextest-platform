"""drop functional_cases.sort_order

Revision ID: f8a1c2e3b4d6
Revises: e7b2c4d5f6a8
Create Date: 2026-05-04

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f8a1c2e3b4d6"
down_revision: Union[str, Sequence[str], None] = "e7b2c4d5f6a8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("functional_cases", "sort_order")


def downgrade() -> None:
    op.add_column(
        "functional_cases",
        sa.Column(
            "sort_order",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="模块内排序",
        ),
    )
