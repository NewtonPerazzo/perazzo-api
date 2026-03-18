"""add delivery methods and neighborhood

Revision ID: b7a1c9d3e5f2
Revises: f3c1d9a7b2e4
Create Date: 2026-03-17 21:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "b7a1c9d3e5f2"
down_revision: Union[str, Sequence[str], None] = "f3c1d9a7b2e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "delivery_methods",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("price", sa.Float(), nullable=False, server_default="0"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_delivery_methods_id"), "delivery_methods", ["id"], unique=False)
    op.create_index(op.f("ix_delivery_methods_name"), "delivery_methods", ["name"], unique=False)

    op.add_column("customers", sa.Column("neighborhood", sa.String(length=120), nullable=True))
    op.add_column("orders", sa.Column("delivery_method_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index(op.f("ix_orders_delivery_method_id"), "orders", ["delivery_method_id"], unique=False)
    op.create_foreign_key(
        "fk_orders_delivery_method_id",
        "orders",
        "delivery_methods",
        ["delivery_method_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_orders_delivery_method_id", "orders", type_="foreignkey")
    op.drop_index(op.f("ix_orders_delivery_method_id"), table_name="orders")
    op.drop_column("orders", "delivery_method_id")
    op.drop_column("customers", "neighborhood")

    op.drop_index(op.f("ix_delivery_methods_name"), table_name="delivery_methods")
    op.drop_index(op.f("ix_delivery_methods_id"), table_name="delivery_methods")
    op.drop_table("delivery_methods")
