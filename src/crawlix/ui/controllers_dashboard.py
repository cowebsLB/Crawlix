"""Dashboard presentation controller helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from crawlix.db.models import Job, Page, SeoAudit
from crawlix.services.dashboard_action_hub import DashboardActionHub, build_dashboard_action_hub


@dataclass(frozen=True)
class DashboardSummary:
    pages: int
    jobs: int
    audits: int
    last_crawl: str


def load_dashboard_summary(session: Session, project_id: int, *, never_label: str = "never") -> DashboardSummary:
    n_pages = int(session.scalar(select(func.count()).select_from(Page).where(Page.project_id == project_id)) or 0)
    n_jobs = int(session.scalar(select(func.count()).select_from(Job).where(Job.project_id == project_id)) or 0)
    n_audits = int(
        session.scalar(
            select(func.count())
            .select_from(SeoAudit)
            .join(Page, SeoAudit.page_id == Page.id)
            .where(Page.project_id == project_id)
        )
        or 0
    )
    last_c = session.scalar(select(func.max(Page.last_crawled_at)).where(Page.project_id == project_id))
    last_s = last_c.isoformat() if isinstance(last_c, datetime) else never_label
    return DashboardSummary(pages=n_pages, jobs=n_jobs, audits=n_audits, last_crawl=last_s)


def load_dashboard_action_hub(session: Session, project_id: int) -> DashboardActionHub:
    return build_dashboard_action_hub(session, project_id)


def format_dashboard_summary_line(summary: DashboardSummary) -> str:
    return (
        f"Pages: {summary.pages} · Jobs (all types): {summary.jobs} · "
        f"Audits: {summary.audits} · Last page crawl: {summary.last_crawl}"
    )
