"""author_nullable

Revision ID: 4591690ce321
Revises: 4e7074d7beea
Create Date: 2026-04-20 14:00:52.770961

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4591690ce321'
down_revision: Union[str, Sequence[str], None] = '4e7074d7beea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('proposals', 'author',
               existing_type=sa.VARCHAR(),
               nullable=True)
    op.alter_column('proposals', 'author_type',
               existing_type=sa.VARCHAR(),
               nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('proposals', 'author_type',
               existing_type=sa.VARCHAR(),
               nullable=False)
    op.alter_column('proposals', 'author',
               existing_type=sa.VARCHAR(),
               nullable=False)
