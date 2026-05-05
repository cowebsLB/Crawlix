"""add seo_context_json to projects

Revision ID: e5a1c2d3b4f0
Revises: d4f8a2c1b0e3
Create Date: 2026-05-04

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e5a1c2d3b4f0"
down_revision: Union[str, None] = "d4f8a2c1b0e3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("seo_context_json", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("projects", "seo_context_json")
