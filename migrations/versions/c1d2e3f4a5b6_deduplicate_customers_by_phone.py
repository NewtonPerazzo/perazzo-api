"""deduplicate customers by phone

Revision ID: c1d2e3f4a5b6
Revises: a1b2c3d4e5f6
Create Date: 2026-03-20 23:50:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "c1d2e3f4a5b6"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Keep the newest customer per phone and re-link orders before deleting duplicates.
    op.execute(
        """
        WITH ranked AS (
            SELECT
                id,
                phone,
                created_at,
                ROW_NUMBER() OVER (
                    PARTITION BY phone
                    ORDER BY created_at DESC, id DESC
                ) AS rn
            FROM customers
            WHERE phone IS NOT NULL
              AND btrim(phone) <> ''
              AND phone <> '-'
        ),
        duplicates AS (
            SELECT id AS duplicate_id, phone
            FROM ranked
            WHERE rn > 1
        ),
        keepers AS (
            SELECT id AS keeper_id, phone
            FROM ranked
            WHERE rn = 1
        )
        UPDATE orders o
        SET customer_id = k.keeper_id
        FROM duplicates d
        JOIN keepers k ON k.phone = d.phone
        WHERE o.customer_id = d.duplicate_id
        """
    )

    op.execute(
        """
        DELETE FROM customers c
        USING (
            SELECT id
            FROM (
                SELECT
                    id,
                    ROW_NUMBER() OVER (
                        PARTITION BY phone
                        ORDER BY created_at DESC, id DESC
                    ) AS rn
                FROM customers
                WHERE phone IS NOT NULL
                  AND btrim(phone) <> ''
                  AND phone <> '-'
            ) ranked
            WHERE rn > 1
        ) d
        WHERE c.id = d.id
        """
    )


def downgrade() -> None:
    # Irreversible data cleanup.
    pass

