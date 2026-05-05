"""add crawl_snapshots and crawl_snapshot_pages

Revision ID: d4f8a2c1b0e3
Revises: c7e2a1b4f9d0
Create Date: 2026-05-04

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d4f8a2c1b0e3"
down_revision: Union[str, None] = "c7e2a1b4f9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "crawl_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("crawl_job_id", sa.Integer(), sa.ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column("page_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_crawl_snapshots_project_id", "crawl_snapshots", ["project_id"])
    op.create_index("ix_crawl_snapshots_job_id", "crawl_snapshots", ["crawl_job_id"])

    op.create_table(
        "crawl_snapshot_pages",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "snapshot_id",
            sa.Integer(),
            sa.ForeignKey("crawl_snapshots.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("url_norm", sa.String(length=2048), nullable=False),
        sa.Column("url_final", sa.String(length=2048), nullable=True),
        sa.Column("title", sa.String(length=1024), nullable=True),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("crawl_depth", sa.Integer(), nullable=True),
        sa.UniqueConstraint("snapshot_id", "url_norm", name="uq_crawl_snapshot_pages_snapshot_url"),
    )
    op.create_index("ix_crawl_snapshot_pages_snapshot_id", "crawl_snapshot_pages", ["snapshot_id"])


def downgrade() -> None:
    op.drop_index("ix_crawl_snapshot_pages_snapshot_id", table_name="crawl_snapshot_pages")
    op.drop_table("crawl_snapshot_pages")
    op.drop_index("ix_crawl_snapshots_job_id", table_name="crawl_snapshots")
    op.drop_index("ix_crawl_snapshots_project_id", table_name="crawl_snapshots")
    op.drop_table("crawl_snapshots")
