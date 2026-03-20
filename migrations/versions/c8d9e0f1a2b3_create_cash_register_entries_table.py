"""create cash register entries table

Revision ID: c8d9e0f1a2b3
Revises: b1c2d3e4f5a6
Create Date: 2026-03-18 23:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "c8d9e0f1a2b3"
down_revision: Union[str, Sequence[str], None] = "b1c2d3e4f5a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "cash_register_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("store_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("entry_type", sa.String(length=10), nullable=False),
        sa.Column("name", sa.String(length=140), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("payment_method", sa.String(length=60), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("occurred_on", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_cash_register_entries_id"), "cash_register_entries", ["id"], unique=False)
    op.create_index(op.f("ix_cash_register_entries_store_id"), "cash_register_entries", ["store_id"], unique=False)
    op.create_index(op.f("ix_cash_register_entries_entry_type"), "cash_register_entries", ["entry_type"], unique=False)
    op.create_index(op.f("ix_cash_register_entries_occurred_on"), "cash_register_entries", ["occurred_on"], unique=False)
    op.execute(
        """
        ALTER TABLE cash_register_entries
        ADD CONSTRAINT ck_cash_register_entries_type
        CHECK (entry_type IN ('entry', 'expense'))
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE cash_register_entries DROP CONSTRAINT IF EXISTS ck_cash_register_entries_type")
    op.drop_index(op.f("ix_cash_register_entries_occurred_on"), table_name="cash_register_entries")
    op.drop_index(op.f("ix_cash_register_entries_entry_type"), table_name="cash_register_entries")
    op.drop_index(op.f("ix_cash_register_entries_store_id"), table_name="cash_register_entries")
    op.drop_index(op.f("ix_cash_register_entries_id"), table_name="cash_register_entries")
    op.drop_table("cash_register_entries")

