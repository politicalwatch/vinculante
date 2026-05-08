"""section meta

Revision ID: c4e7f9a2b1d3
Revises: 083eff051b19
Create Date: 2026-05-07 17:00:25.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "c4e7f9a2b1d3"
down_revision: Union[str, None] = "083eff051b19"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("sections", sa.Column("meta", JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column("sections", "meta")
