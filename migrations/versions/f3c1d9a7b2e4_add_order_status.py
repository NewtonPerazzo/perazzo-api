"""add order status

Revision ID: f3c1d9a7b2e4
Revises: e1f9a2b7c4d1
Create Date: 2026-03-17 17:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f3c1d9a7b2e4"
down_revision: Union[str, Sequence[str], None] = "e1f9a2b7c4d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "orders",
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
    )
    op.create_index(op.f("ix_orders_status"), "orders", ["status"], unique=False)
    op.execute(
        """
        ALTER TABLE orders
        ADD CONSTRAINT ck_orders_status
        CHECK (status IN ('confirmed', 'canceled', 'preparing', 'in_transit', 'pending', 'deliveried'))
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE orders DROP CONSTRAINT IF EXISTS ck_orders_status")
    op.drop_index(op.f("ix_orders_status"), table_name="orders")
    op.drop_column("orders", "status")
