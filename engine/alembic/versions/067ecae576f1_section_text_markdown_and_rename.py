"""section_text_markdown_and_rename

Revision ID: 067ecae576f1
Revises: a3f2c1d8e905
Create Date: 2026-04-28 08:22:00.566812

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '067ecae576f1'
down_revision: Union[str, Sequence[str], None] = 'a3f2c1d8e905'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('sections', sa.Column('text_markdown', sa.String(), nullable=True))
    op.alter_column('sections', 'plain_text', new_column_name='clear_language')


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('sections', 'clear_language', new_column_name='plain_text')
    op.drop_column('sections', 'text_markdown')
