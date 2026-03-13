"""create payment methods table

Revision ID: d2e7f4c9a1b0
Revises: c4a8e9b2f1d3
Create Date: 2026-03-13 14:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "d2e7f4c9a1b0"
down_revision: Union[str, Sequence[str], None] = "c4a8e9b2f1d3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "payment_methods",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_payment_methods_id"), "payment_methods", ["id"], unique=False)
    op.create_index(op.f("ix_payment_methods_name"), "payment_methods", ["name"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_payment_methods_name"), table_name="payment_methods")
    op.drop_index(op.f("ix_payment_methods_id"), table_name="payment_methods")
    op.drop_table("payment_methods")
