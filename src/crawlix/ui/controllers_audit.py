"""Audit page controller helpers."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from crawlix.db.models import Page, SeoAudit


def query_audit_results_rows(
    session: Session,
    project_id: int,
    *,
    limit: int = 200,
    prioritize_page_id: int | None = None,
) -> list[tuple[SeoAudit, Page]]:
    """
    Latest audits for a project (default cap 200). When ``prioritize_page_id`` is set,
    that page's most recent audit row is moved to the front if it exists (still capped).
    """
    stmt = (
        select(SeoAudit, Page)
        .join(Page, SeoAudit.page_id == Page.id)
        .where(Page.project_id == project_id)
        .order_by(SeoAudit.audited_at.desc())
        .limit(limit)
    )
    rows = list(session.execute(stmt).all())
    if prioritize_page_id is None:
        return rows
    pin_stmt = (
        select(SeoAudit, Page)
        .join(Page, SeoAudit.page_id == Page.id)
        .where(Page.project_id == project_id, Page.id == int(prioritize_page_id))
        .order_by(SeoAudit.audited_at.desc())
        .limit(1)
    )
    pin = session.execute(pin_stmt).first()
    if pin is None:
        return rows
    audit_pin: SeoAudit = pin[0]
    page_pin: Page = pin[1]
    rest = [r for r in rows if r[0].id != audit_pin.id]
    combined = [(audit_pin, page_pin)] + rest
    return combined[:limit]


def build_audit_row_meta(
    *,
    page_id: int,
    url_norm: str,
    issues: object,
    inbound: int,
    outbound: int,
) -> dict[str, object]:
    safe_issues = issues if isinstance(issues, list) else []
    return {
        "page_id": int(page_id),
        "url_norm": str(url_norm),
        "issues": safe_issues,
        "inbound": int(inbound),
        "outbound": int(outbound),
    }


def issue_count(issues: object) -> int:
    if isinstance(issues, list):
        return len(issues)
    return 0
