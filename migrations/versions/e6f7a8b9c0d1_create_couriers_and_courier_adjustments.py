"""create couriers and courier adjustments

Revision ID: e6f7a8b9c0d1
Revises: d4e5f6a7b8c9
Create Date: 2026-03-19 20:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "e6f7a8b9c0d1"
down_revision: Union[str, Sequence[str], None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "couriers",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("address", sa.String(length=255), nullable=True),
        sa.Column("store_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_couriers_id"), "couriers", ["id"], unique=False)
    op.create_index(op.f("ix_couriers_store_id"), "couriers", ["store_id"], unique=False)

    op.create_table(
        "courier_adjustments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("adjustment_type", sa.String(length=12), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("payment_method", sa.String(length=60), nullable=True),
        sa.Column("note", sa.String(length=255), nullable=True),
        sa.Column("occurred_on", sa.Date(), nullable=False),
        sa.Column("store_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("courier_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["courier_id"], ["couriers.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_courier_adjustments_courier_id"), "courier_adjustments", ["courier_id"], unique=False)
    op.create_index(op.f("ix_courier_adjustments_id"), "courier_adjustments", ["id"], unique=False)
    op.create_index(op.f("ix_courier_adjustments_store_id"), "courier_adjustments", ["store_id"], unique=False)

    op.add_column("orders", sa.Column("courier_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index(op.f("ix_orders_courier_id"), "orders", ["courier_id"], unique=False)
    op.create_foreign_key(
        "fk_orders_courier_id_couriers",
        "orders",
        "couriers",
        ["courier_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_orders_courier_id_couriers", "orders", type_="foreignkey")
    op.drop_index(op.f("ix_orders_courier_id"), table_name="orders")
    op.drop_column("orders", "courier_id")

    op.drop_index(op.f("ix_courier_adjustments_store_id"), table_name="courier_adjustments")
    op.drop_index(op.f("ix_courier_adjustments_id"), table_name="courier_adjustments")
    op.drop_index(op.f("ix_courier_adjustments_courier_id"), table_name="courier_adjustments")
    op.drop_table("courier_adjustments")

    op.drop_index(op.f("ix_couriers_store_id"), table_name="couriers")
    op.drop_index(op.f("ix_couriers_id"), table_name="couriers")
    op.drop_table("couriers")

