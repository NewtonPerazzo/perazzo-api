"""add order observation

Revision ID: a9d4e2b7c6f1
Revises: b7a1c9d3e5f2
Create Date: 2026-03-18 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a9d4e2b7c6f1'
down_revision: Union[str, Sequence[str], None] = 'b7a1c9d3e5f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('orders', sa.Column('observation', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('orders', 'observation')
