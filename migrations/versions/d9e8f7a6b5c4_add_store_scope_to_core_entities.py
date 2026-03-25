"""add store scope to core entities

Revision ID: d9e8f7a6b5c4
Revises: c1d2e3f4a5b6
Create Date: 2026-03-24 18:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "d9e8f7a6b5c4"
down_revision: Union[str, Sequence[str], None] = "c1d2e3f4a5b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("products", sa.Column("store_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("categories", sa.Column("store_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("payment_methods", sa.Column("store_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("delivery_methods", sa.Column("store_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("customers", sa.Column("store_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("orders", sa.Column("store_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("carts", sa.Column("store_id", postgresql.UUID(as_uuid=True), nullable=True))

    op.execute(
        """
        WITH first_store AS (
          SELECT id
          FROM stores
          ORDER BY created_at ASC
          LIMIT 1
        )
        UPDATE products
        SET store_id = (SELECT id FROM first_store)
        WHERE store_id IS NULL
        """
    )
    op.execute(
        """
        WITH first_store AS (
          SELECT id
          FROM stores
          ORDER BY created_at ASC
          LIMIT 1
        )
        UPDATE categories
        SET store_id = (SELECT id FROM first_store)
        WHERE store_id IS NULL
        """
    )
    op.execute(
        """
        WITH first_store AS (
          SELECT id
          FROM stores
          ORDER BY created_at ASC
          LIMIT 1
        )
        UPDATE payment_methods
        SET store_id = (SELECT id FROM first_store)
        WHERE store_id IS NULL
        """
    )
    op.execute(
        """
        WITH first_store AS (
          SELECT id
          FROM stores
          ORDER BY created_at ASC
          LIMIT 1
        )
        UPDATE delivery_methods
        SET store_id = (SELECT id FROM first_store)
        WHERE store_id IS NULL
        """
    )
    op.execute(
        """
        WITH first_store AS (
          SELECT id
          FROM stores
          ORDER BY created_at ASC
          LIMIT 1
        )
        UPDATE customers
        SET store_id = (SELECT id FROM first_store)
        WHERE store_id IS NULL
        """
    )
    op.execute(
        """
        UPDATE orders o
        SET store_id = c.store_id
        FROM customers c
        WHERE o.store_id IS NULL
          AND o.customer_id = c.id
        """
    )
    op.execute(
        """
        WITH first_store AS (
          SELECT id
          FROM stores
          ORDER BY created_at ASC
          LIMIT 1
        )
        UPDATE orders
        SET store_id = (SELECT id FROM first_store)
        WHERE store_id IS NULL
        """
    )
    op.execute(
        """
        WITH first_store AS (
          SELECT id
          FROM stores
          ORDER BY created_at ASC
          LIMIT 1
        )
        UPDATE carts
        SET store_id = (SELECT id FROM first_store)
        WHERE store_id IS NULL
        """
    )

    op.create_index(op.f("ix_products_store_id"), "products", ["store_id"], unique=False)
    op.create_index(op.f("ix_categories_store_id"), "categories", ["store_id"], unique=False)
    op.create_index(op.f("ix_payment_methods_store_id"), "payment_methods", ["store_id"], unique=False)
    op.create_index(op.f("ix_delivery_methods_store_id"), "delivery_methods", ["store_id"], unique=False)
    op.create_index(op.f("ix_customers_store_id"), "customers", ["store_id"], unique=False)
    op.create_index(op.f("ix_orders_store_id"), "orders", ["store_id"], unique=False)
    op.create_index(op.f("ix_carts_store_id"), "carts", ["store_id"], unique=False)

    op.create_foreign_key("fk_products_store_id", "products", "stores", ["store_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("fk_categories_store_id", "categories", "stores", ["store_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("fk_payment_methods_store_id", "payment_methods", "stores", ["store_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("fk_delivery_methods_store_id", "delivery_methods", "stores", ["store_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("fk_customers_store_id", "customers", "stores", ["store_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("fk_orders_store_id", "orders", "stores", ["store_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("fk_carts_store_id", "carts", "stores", ["store_id"], ["id"], ondelete="CASCADE")


def downgrade() -> None:
    op.drop_constraint("fk_carts_store_id", "carts", type_="foreignkey")
    op.drop_constraint("fk_orders_store_id", "orders", type_="foreignkey")
    op.drop_constraint("fk_customers_store_id", "customers", type_="foreignkey")
    op.drop_constraint("fk_delivery_methods_store_id", "delivery_methods", type_="foreignkey")
    op.drop_constraint("fk_payment_methods_store_id", "payment_methods", type_="foreignkey")
    op.drop_constraint("fk_categories_store_id", "categories", type_="foreignkey")
    op.drop_constraint("fk_products_store_id", "products", type_="foreignkey")

    op.drop_index(op.f("ix_carts_store_id"), table_name="carts")
    op.drop_index(op.f("ix_orders_store_id"), table_name="orders")
    op.drop_index(op.f("ix_customers_store_id"), table_name="customers")
    op.drop_index(op.f("ix_delivery_methods_store_id"), table_name="delivery_methods")
    op.drop_index(op.f("ix_payment_methods_store_id"), table_name="payment_methods")
    op.drop_index(op.f("ix_categories_store_id"), table_name="categories")
    op.drop_index(op.f("ix_products_store_id"), table_name="products")

    op.drop_column("carts", "store_id")
    op.drop_column("orders", "store_id")
    op.drop_column("customers", "store_id")
    op.drop_column("delivery_methods", "store_id")
    op.drop_column("payment_methods", "store_id")
    op.drop_column("categories", "store_id")
    op.drop_column("products", "store_id")
