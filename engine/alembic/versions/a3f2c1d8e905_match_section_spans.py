"""match_section_spans

Revision ID: a3f2c1d8e905
Revises: 091e4fb15314
Create Date: 2026-04-22 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "a3f2c1d8e905"
down_revision: Union[str, None] = "091e4fb15314"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("matches", "section_start_at")
    op.drop_column("matches", "section_end_at")
    op.add_column("matches", sa.Column("section_spans", JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column("matches", "section_spans")
    op.add_column("matches", sa.Column("section_start_at", sa.Integer(), nullable=True))
    op.add_column("matches", sa.Column("section_end_at", sa.Integer(), nullable=True))
