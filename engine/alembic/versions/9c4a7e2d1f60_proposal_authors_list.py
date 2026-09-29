"""proposal_authors_list

Replaces proposals.author (one string, proponents joined by commas) with
proposals.authors (text[], one item per proponent).

Revision ID: 9c4a7e2d1f60
Revises: 5b8d1e3f9a27
Create Date: 2026-09-28 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY


# revision identifiers, used by Alembic.
revision: str = '9c4a7e2d1f60'
down_revision: Union[str, Sequence[str], None] = '5b8d1e3f9a27'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'proposals',
        sa.Column('authors', ARRAY(sa.String()), nullable=False, server_default='{}'),
    )
    op.execute(
        """
        UPDATE proposals
        SET authors = ARRAY(
            SELECT btrim(part)
            FROM unnest(string_to_array(author, ',')) WITH ORDINALITY AS t(part, n)
            WHERE btrim(part) <> ''
            ORDER BY n
        )
        WHERE author IS NOT NULL
        """
    )
    op.drop_column('proposals', 'author')


def downgrade() -> None:
    op.add_column('proposals', sa.Column('author', sa.String(), nullable=True))
    op.execute(
        """
        UPDATE proposals
        SET author = NULLIF(array_to_string(authors, ', '), '')
        """
    )
    op.drop_column('proposals', 'authors')
