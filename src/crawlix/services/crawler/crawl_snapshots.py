"""Persist per-crawl page snapshots and diff consecutive runs."""

from __future__ import annotations

from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from crawlix.db.models import CrawlSnapshot, CrawlSnapshotPage, Page

KEEP_SNAPSHOTS_PER_PROJECT = 10
MAX_SNAPSHOT_PAGE_ROWS = 15_000


def persist_after_completed_crawl(session: Session, project_id: int, crawl_job_id: int) -> int | None:
    """
    Copy current ``Page`` rows into a new ``CrawlSnapshot`` (after a successful crawl).
    Drops older snapshots beyond ``KEEP_SNAPSHOTS_PER_PROJECT``.
    """
    pages = list(
        session.scalars(
            select(Page).where(Page.project_id == project_id).order_by(Page.id.asc()).limit(MAX_SNAPSHOT_PAGE_ROWS)
        ).all()
    )
    if not pages:
        return None
    snap = CrawlSnapshot(
        project_id=project_id,
        crawl_job_id=crawl_job_id,
        page_count=len(pages),
    )
    session.add(snap)
    session.flush()
    for p in pages:
        t = p.title
        if t and len(t) > 1024:
            t = t[:1024]
        session.add(
            CrawlSnapshotPage(
                snapshot_id=snap.id,
                url_norm=p.url_norm,
                url_final=p.url_final,
                title=t,
                status_code=p.status_code,
                crawl_depth=p.crawl_depth,
            )
        )
    ids = list(
        session.scalars(
            select(CrawlSnapshot.id)
            .where(CrawlSnapshot.project_id == project_id)
            .order_by(CrawlSnapshot.id.desc())
        ).all()
    )
    for sid in ids[KEEP_SNAPSHOTS_PER_PROJECT:]:
        session.execute(delete(CrawlSnapshot).where(CrawlSnapshot.id == sid))
    return snap.id


def _row_dict(r: CrawlSnapshotPage) -> dict[str, Any]:
    return {
        "url_norm": r.url_norm,
        "url_final": (r.url_final or "").strip() or None,
        "title": r.title,
        "status_code": r.status_code,
        "crawl_depth": r.crawl_depth,
    }


def load_snapshot_page_map(session: Session, snapshot_id: int) -> dict[str, dict[str, Any]]:
    rows = session.scalars(select(CrawlSnapshotPage).where(CrawlSnapshotPage.snapshot_id == snapshot_id)).all()
    return {r.url_norm: _row_dict(r) for r in rows}


def diff_latest_two_snapshots(session: Session, project_id: int) -> dict[str, Any] | None:
    """Compare the two newest snapshots for a project. Returns None if fewer than two exist."""
    ids = list(
        session.scalars(
            select(CrawlSnapshot.id)
            .where(CrawlSnapshot.project_id == project_id)
            .order_by(CrawlSnapshot.id.desc())
            .limit(2)
        ).all()
    )
    if len(ids) < 2:
        return None
    new_id, old_id = ids[0], ids[1]
    old_m = load_snapshot_page_map(session, old_id)
    new_m = load_snapshot_page_map(session, new_id)
    return compute_snapshot_diff(old_m, new_m, old_snapshot_id=old_id, new_snapshot_id=new_id)


def compute_snapshot_diff(
    old_m: dict[str, dict[str, Any]],
    new_m: dict[str, dict[str, Any]],
    *,
    old_snapshot_id: int = 0,
    new_snapshot_id: int = 0,
) -> dict[str, Any]:
    old_keys = set(old_m)
    new_keys = set(new_m)
    added = sorted(new_keys - old_keys)
    removed = sorted(old_keys - new_keys)
    title_changed: list[str] = []
    status_changed: list[str] = []
    final_changed: list[str] = []
    depth_changed: list[str] = []
    for u in old_keys & new_keys:
        o, n = old_m[u], new_m[u]
        if (o.get("title") or "") != (n.get("title") or ""):
            title_changed.append(u)
        if o.get("status_code") != n.get("status_code"):
            status_changed.append(u)
        if (o.get("url_final") or "") != (n.get("url_final") or ""):
            final_changed.append(u)
        if o.get("crawl_depth") != n.get("crawl_depth"):
            depth_changed.append(u)
    return {
        "old_snapshot_id": old_snapshot_id,
        "new_snapshot_id": new_snapshot_id,
        "added": added,
        "removed": removed,
        "title_changed": title_changed,
        "status_changed": status_changed,
        "final_changed": final_changed,
        "depth_changed": depth_changed,
    }


def format_crawl_diff_for_ui(diff: dict[str, Any] | None, *, max_show: int = 14) -> str:
    """Plain-text summary for the Crawl tab."""
    if not diff:
        return (
            "Crawl diff: run at least two completed crawls to compare this crawl vs the previous snapshot "
            "(URLs, titles, HTTP status, final URL, depth)."
        )
    lines: list[str] = []
    lines.append(
        f"Crawl diff (snapshot #{diff.get('old_snapshot_id')} → #{diff.get('new_snapshot_id')}):"
    )

    def block(label: str, urls: list[str]) -> None:
        if not urls:
            lines.append(f"• {label}: 0")
            return
        lines.append(f"• {label}: {len(urls)}")
        for u in urls[:max_show]:
            short = u if len(u) <= 88 else f"{u[:85]}…"
            lines.append(f"    {short}")
        if len(urls) > max_show:
            lines.append(f"    … +{len(urls) - max_show} more")

    block("New URLs (discovered)", diff.get("added") or [])
    block("Removed URLs (gone from crawl set)", diff.get("removed") or [])
    block("Title changed", diff.get("title_changed") or [])
    block("HTTP status changed", diff.get("status_changed") or [])
    block("Final URL changed", diff.get("final_changed") or [])
    block("Crawl depth changed", diff.get("depth_changed") or [])
    return "\n".join(lines)
