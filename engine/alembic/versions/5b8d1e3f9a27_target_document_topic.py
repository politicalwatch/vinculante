"""target_document_topic

Revision ID: 5b8d1e3f9a27
Revises: c4e7f9a2b1d3
Create Date: 2026-09-28 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5b8d1e3f9a27'
down_revision: Union[str, Sequence[str], None] = 'c4e7f9a2b1d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('target_documents', sa.Column('topic', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('target_documents', 'topic')
