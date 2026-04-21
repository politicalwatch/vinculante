"""target_documents_date_nullable

Revision ID: fd9abedf0c7d
Revises: 4591690ce321
Create Date: 2026-04-20 14:16:06.221509

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fd9abedf0c7d'
down_revision: Union[str, Sequence[str], None] = '4591690ce321'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('target_documents', 'date',
               existing_type=sa.Date(),
               nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('target_documents', 'date',
               existing_type=sa.Date(),
               nullable=False)
