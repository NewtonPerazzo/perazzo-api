"""create customers and refactor orders customer fields

Revision ID: a7c6f0b8d1e2
Revises: 9b6d1d4a2f7e
Create Date: 2026-03-07 16:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "a7c6f0b8d1e2"
down_revision: Union[str, Sequence[str], None] = "9b6d1d4a2f7e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "customers",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("phone", sa.String(length=30), nullable=False),
        sa.Column("address", sa.String(length=255), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_customers_id"), "customers", ["id"], unique=False)

    op.execute(
        """
        INSERT INTO customers (id, name, phone, address, email, created_at)
        SELECT DISTINCT customer_id, customer_name, customer_phone, customer_address, customer_email, created_at
        FROM orders
        ON CONFLICT (id) DO NOTHING
        """
    )

    op.create_foreign_key(
        "fk_orders_customer_id_customers",
        "orders",
        "customers",
        ["customer_id"],
        ["id"],
    )

    op.add_column("orders", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")))

    op.drop_column("orders", "customer_name")
    op.drop_column("orders", "customer_phone")
    op.drop_column("orders", "customer_address")
    op.drop_column("orders", "customer_email")


def downgrade() -> None:
    op.add_column("orders", sa.Column("customer_email", sa.String(length=255), nullable=True))
    op.add_column("orders", sa.Column("customer_address", sa.String(length=255), nullable=True))
    op.add_column("orders", sa.Column("customer_phone", sa.String(length=30), nullable=False, server_default=""))
    op.add_column("orders", sa.Column("customer_name", sa.String(length=120), nullable=False, server_default=""))

    op.execute(
        """
        UPDATE orders
        SET customer_name = customers.name,
            customer_phone = customers.phone,
            customer_address = customers.address,
            customer_email = customers.email
        FROM customers
        WHERE orders.customer_id = customers.id
        """
    )

    op.drop_column("orders", "updated_at")
    op.drop_constraint("fk_orders_customer_id_customers", "orders", type_="foreignkey")
    op.drop_index(op.f("ix_customers_id"), table_name="customers")
    op.drop_table("customers")
