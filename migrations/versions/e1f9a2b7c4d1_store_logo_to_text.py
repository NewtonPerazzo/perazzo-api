"""store logo to text

Revision ID: e1f9a2b7c4d1
Revises: d2e7f4c9a1b0
Create Date: 2026-03-17 10:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e1f9a2b7c4d1"
down_revision: Union[str, Sequence[str], None] = "d2e7f4c9a1b0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "stores",
        "logo",
        existing_type=sa.String(length=500),
        type_=sa.Text(),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "stores",
        "logo",
        existing_type=sa.Text(),
        type_=sa.String(length=500),
        existing_nullable=True,
    )
