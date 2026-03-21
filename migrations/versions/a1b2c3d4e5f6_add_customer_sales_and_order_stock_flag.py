"""add customer sales counters and order stock flag

Revision ID: a1b2c3d4e5f6
Revises: f8a9b0c1d2e3
Create Date: 2026-03-20 13:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "f8a9b0c1d2e3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "customers",
        sa.Column("delivered_orders_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )
    op.add_column(
        "customers",
        sa.Column("delivered_total_spent", sa.Float(), nullable=False, server_default=sa.text("0")),
    )
    op.add_column(
        "orders",
        sa.Column("is_stock_reduced", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )


def downgrade() -> None:
    op.drop_column("orders", "is_stock_reduced")
    op.drop_column("customers", "delivered_total_spent")
    op.drop_column("customers", "delivered_orders_count")

