"""add user plan fields

Revision ID: ab2c3d4e5f6a
Revises: aa1b2c3d4e5f
Create Date: 2026-04-30 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "ab2c3d4e5f6a"
down_revision: Union[str, Sequence[str], None] = "aa1b2c3d4e5f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("plan", sa.String(length=30), nullable=True))
    op.add_column("users", sa.Column("plan_started_at", sa.DateTime(timezone=True), nullable=True))

    op.execute("UPDATE users SET plan = 'free' WHERE plan IS NULL")
    op.execute("UPDATE users SET plan_started_at = COALESCE(created_at, now()) WHERE plan_started_at IS NULL")

    op.alter_column("users", "plan", nullable=False)
    op.alter_column("users", "plan_started_at", nullable=False)
    op.create_check_constraint(
        "ck_users_plan_valid",
        "users",
        "plan IN ('free', 'essential', 'pro')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_users_plan_valid", "users", type_="check")
    op.drop_column("users", "plan_started_at")
    op.drop_column("users", "plan")
