"""add store whatsapp acceptance and category sort order

Revision ID: b1c2d3e4f5a6
Revises: a9d4e2b7c6f1
Create Date: 2026-03-18 20:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b1c2d3e4f5a6"
down_revision: Union[str, Sequence[str], None] = "a9d4e2b7c6f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "stores",
        sa.Column(
            "is_accepted_send_order_to_whatsapp",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )

    op.add_column(
        "categories",
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )
    op.execute(
        """
        WITH ranked AS (
          SELECT id, ROW_NUMBER() OVER (ORDER BY name ASC) AS rn
          FROM categories
        )
        UPDATE categories
        SET sort_order = ranked.rn
        FROM ranked
        WHERE categories.id = ranked.id
        """
    )


def downgrade() -> None:
    op.drop_column("categories", "sort_order")
    op.drop_column("stores", "is_accepted_send_order_to_whatsapp")

