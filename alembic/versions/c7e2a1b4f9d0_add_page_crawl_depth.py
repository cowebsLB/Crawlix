"""add crawl_depth to pages

Revision ID: c7e2a1b4f9d0
Revises: 9b949aa9c11d
Create Date: 2026-05-04

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c7e2a1b4f9d0"
down_revision: Union[str, None] = "9b949aa9c11d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("pages", sa.Column("crawl_depth", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("pages", "crawl_depth")
