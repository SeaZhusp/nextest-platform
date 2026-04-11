"""rename users.role to user_type

Revision ID: b7c3f91a2d84
Revises: 65026c057079
Create Date: 2026-04-11

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b7c3f91a2d84"
down_revision: Union[str, Sequence[str], None] = "65026c057079"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "users",
        "role",
        new_column_name="user_type",
        existing_type=sa.String(length=20),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "users",
        "user_type",
        new_column_name="role",
        existing_type=sa.String(length=20),
        existing_nullable=False,
    )
