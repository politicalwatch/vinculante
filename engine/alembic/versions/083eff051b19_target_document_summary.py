"""target_document_summary

Revision ID: 083eff051b19
Revises: e3a9f2b1c847
Create Date: 2026-05-05 09:25:02.143331

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '083eff051b19'
down_revision: Union[str, Sequence[str], None] = 'e3a9f2b1c847'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('target_documents', sa.Column('summary', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('target_documents', 'summary')
