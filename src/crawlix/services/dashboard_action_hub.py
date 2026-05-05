from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from crawlix.db.models import Job, Page, SeoAudit
from crawlix.services.analyzer.insights import build_insights


@dataclass(frozen=True)
class NextActionItem:
    label: str
    reason: str
    target: str
    severity: str | None = None
    priority: str | None = None
    entity_type: str | None = None
    entity_id: int | None = None
    suggested_filter: dict[str, object] | None = None


@dataclass(frozen=True)
class DashboardActionHub:
    next_actions: list[NextActionItem]
    needs_attention: list[str]
    recent_outcomes: list[str]


def _job_state_line(job: Job) -> str:
    return f"#{job.id} {job.type} · {job.status}"


def build_dashboard_action_hub(session: Session, project_id: int) -> DashboardActionHub:
    needs_attention: list[str] = []
    recent_outcomes: list[str] = []
    next_actions: list[NextActionItem] = []

    jobs = list(
        session.execute(
            select(Job)
            .where(Job.project_id == project_id)
            .order_by(Job.id.desc())
            .limit(25)
        ).scalars()
    )
    for j in jobs:
        if j.status in ("failed", "cancelled"):
            needs_attention.append(_job_state_line(j))
        if j.status == "completed":
            recent_outcomes.append(_job_state_line(j))

    audits = session.execute(
        select(SeoAudit, Page)
        .join(Page, SeoAudit.page_id == Page.id)
        .where(Page.project_id == project_id)
        .order_by(SeoAudit.audited_at.desc())
        .limit(120)
    ).all()

    unresolved_now: list[tuple[int, str, str]] = []
    unresolved_soon: list[tuple[int, str, str]] = []
    for audit, page in audits:
        raw_issues = audit.issues_json if isinstance(audit.issues_json, list) else []
        insights = build_insights(raw_issues)
        for ins in insights:
            if ins.priority == "now":
                unresolved_now.append((page.id, page.url_norm, ins.summary))
            elif ins.priority == "soon":
                unresolved_soon.append((page.id, page.url_norm, ins.summary))

    for page_id, url_norm, summary in unresolved_now[:4]:
        next_actions.append(
            NextActionItem(
                label=f"Fix critical issue on page {page_id}",
                reason=f"{summary} · {url_norm[:72]}",
                target=f"audit:page:{page_id}",
                priority="now",
                entity_type="page",
                entity_id=page_id,
            )
        )
    if not next_actions:
        for page_id, url_norm, summary in unresolved_soon[:4]:
            next_actions.append(
                NextActionItem(
                    label=f"Address SEO issue on page {page_id}",
                    reason=f"{summary} · {url_norm[:72]}",
                    target=f"audit:page:{page_id}",
                    priority="soon",
                    entity_type="page",
                    entity_id=page_id,
                )
            )

    if not next_actions:
        running = [j for j in jobs if j.status in ("queued", "running")]
        if running:
            next_actions.append(
                NextActionItem(
                    label="Monitor active jobs",
                    reason=f"{len(running)} queued/running job(s)",
                    target="jobs",
                    entity_type="jobs",
                )
            )
        else:
            next_actions.append(
                NextActionItem(
                    label="Run crawl on seed URLs",
                    reason="No urgent issues detected from recent audits",
                    target="crawl:start",
                    entity_type="crawl",
                    suggested_filter={"apply_saved_crawl_view": True},
                )
            )

    if not recent_outcomes:
        recent_outcomes = [f"No completed jobs yet as of {datetime.now(UTC).date().isoformat()}"]
    if not needs_attention:
        needs_attention = ["No failed or cancelled jobs."]

    return DashboardActionHub(
        next_actions=next_actions,
        needs_attention=needs_attention[:8],
        recent_outcomes=recent_outcomes[:8],
    )
