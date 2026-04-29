"""add cart secret

Revision ID: aa1b2c3d4e5f
Revises: d9e8f7a6b5c4
Create Date: 2026-04-28
"""

from alembic import op
import sqlalchemy as sa


revision = "aa1b2c3d4e5f"
down_revision = "d9e8f7a6b5c4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("carts", sa.Column("cart_secret", sa.String(length=128), nullable=True))
    op.create_index("ix_carts_cart_secret", "carts", ["cart_secret"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_carts_cart_secret", table_name="carts")
    op.drop_column("carts", "cart_secret")
