"""target_document_stats

Revision ID: e3a9f2b1c847
Revises: bcb2c90c5497
Create Date: 2026-04-30 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision: str = 'e3a9f2b1c847'
down_revision: Union[str, Sequence[str], None] = 'bcb2c90c5497'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('target_documents', sa.Column('stats', JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column('target_documents', 'stats')
