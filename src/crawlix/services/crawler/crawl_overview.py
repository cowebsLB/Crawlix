"""Aggregate stats and duplicate-final-URL grouping for the Crawl UI."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from urllib.parse import urlparse

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from crawlix.db.models import Page


def effective_final_url(p: Page) -> str:
    return ((p.url_final or p.url_norm or "").strip()) or ""


def duplicate_final_counts(pages: Iterable[Page]) -> dict[str, int]:
    """Map normalized final URL → number of page rows sharing that final."""
    c: Counter[str] = Counter()
    for p in pages:
        k = effective_final_url(p)
        if k:
            c[k] += 1
    return dict(c)


def duplicate_cluster_count(pages: Iterable[Page]) -> int:
    """How many distinct final URLs are shared by more than one discovered URL (row)."""
    return sum(1 for _k, n in duplicate_final_counts(pages).items() if n > 1)


def path_segment_counts(pages: Iterable[Page], *, max_segments: int = 40) -> list[tuple[str, int]]:
    """
    First path segment of each page's url_norm (e.g. /html/..., /pages/...), with counts.
    """
    c: Counter[str] = Counter()
    for p in pages:
        u = (p.url_norm or "").strip()
        if not u:
            continue
        if "://" not in u:
            u = "https://" + u
        path = urlparse(u).path or "/"
        parts = [x for x in path.split("/") if x]
        seg = f"/{parts[0]}/" if parts else "/"
        c[seg] += 1
    out = sorted(c.items(), key=lambda x: (-x[1], x[0]))
    return out[:max_segments]


def http_error_count(pages: Iterable[Page]) -> int:
    return sum(1 for p in pages if p.status_code is not None and p.status_code >= 400)


def crawl_summary_metrics(pages: list[Page]) -> dict[str, float | int]:
    """Compute summary numbers for the crawl bar (single pass over ``pages``)."""
    n = len(pages)
    finals = {effective_final_url(p) for p in pages if effective_final_url(p)}
    dup_clusters = duplicate_cluster_count(pages)
    depths = [p.crawl_depth for p in pages if p.crawl_depth is not None]
    max_d = max(depths) if depths else 0
    avg_d = sum(depths) / len(depths) if depths else 0.0
    err = http_error_count(pages)
    return {
        "pages": n,
        "unique_final_urls": len(finals),
        "duplicate_clusters": dup_clusters,
        "max_depth": int(max_d),
        "avg_depth": round(avg_d, 2),
        "http_errors": err,
    }


def final_key_sql_expr():
    """SQL expression: trimmed coalesced final URL key used for duplicate grouping."""
    return func.nullif(func.trim(func.coalesce(Page.url_final, Page.url_norm)), "")


def fetch_crawl_dashboard_stats(session: Session, project_id: int) -> dict[str, float | int]:
    """Project-wide crawl summary for the overview bar (all stored pages)."""
    fk = final_key_sql_expr()
    w = Page.project_id == project_id

    pages_total = session.scalar(select(func.count()).select_from(Page).where(w)) or 0
    unique_final = (
        session.scalar(select(func.count(func.distinct(fk))).select_from(Page).where(w, fk.isnot(None))) or 0
    )
    dup_q = select(fk).where(w, fk.isnot(None)).group_by(fk).having(func.count(Page.id) > 1)
    dup_clusters = len(session.execute(dup_q).all())

    max_depth = session.scalar(select(func.max(Page.crawl_depth)).where(w))
    avg_depth = session.scalar(select(func.avg(Page.crawl_depth)).where(w))
    http_errors = (
        session.scalar(
            select(func.count())
            .select_from(Page)
            .where(w, Page.status_code.isnot(None), Page.status_code >= 400)
        )
        or 0
    )

    return {
        "pages": int(pages_total),
        "unique_final_urls": int(unique_final),
        "duplicate_clusters": int(dup_clusters),
        "max_depth": int(max_depth or 0),
        "avg_depth": round(float(avg_depth or 0.0), 2),
        "http_errors": int(http_errors),
    }


def fetch_duplicate_final_sizes(session: Session, project_id: int) -> dict[str, int]:
    """Per final-key row counts for the whole project (for duplicate column)."""
    fk = final_key_sql_expr()
    stmt = select(fk, func.count(Page.id)).where(Page.project_id == project_id, fk.isnot(None)).group_by(fk)
    return {str(k): int(v) for k, v in session.execute(stmt).all() if k}


def path_segment_lines_from_norms(url_norms: Iterable[str], *, max_segments: int = 40) -> list[tuple[str, int]]:
    """Like ``path_segment_counts`` but from bare URL strings (no ORM rows)."""
    from types import SimpleNamespace

    pages = (SimpleNamespace(url_norm=u) for u in url_norms)
    return path_segment_counts(pages, max_segments=max_segments)


def normalization_hints(url_norm: str, url_final: str | None, *, dup_group_size: int = 1) -> str:
    """Short hints for the crawl detail panel (canonical / extension patterns)."""
    lines: list[str] = []
    fn = (url_final or "").strip()
    un = (url_norm or "").strip()
    un_l = un.lower()
    if fn:
        fn_l = fn.lower()
        if un_l.endswith((".html", ".htm")) and not fn_l.endswith((".html", ".htm")):
            lines.append("Discovered URL uses an .html/.htm path; final URL is a cleaner path.")
        if un_l.rstrip("/") != fn_l.rstrip("/") and un_l.replace("/index.html", "/") != fn_l.rstrip("/"):
            lines.append("Original URL differs from final URL (redirect or rewrite).")
    if dup_group_size > 1:
        lines.append(
            f"This final URL is shared by {dup_group_size} discovered URLs — pick one canonical and consolidate."
        )
    if not lines:
        return ""
    return "\n".join(lines)


def format_internal_link_insights(
    pages: list[tuple[int, str, int | None]],
    in_map: dict[str, int],
    out_map: dict[int, int],
    *,
    top_n: int = 8,
    high_outbound_threshold: int = 80,
    deep_depth_min: int = 2,
    weak_inbound_max: int = 1,
) -> str:
    """
    Human-readable internal-link intelligence for the Crawl tab.

    ``pages`` is ``(page_id, url_norm, crawl_depth)`` for the analyzed set (typically whole project).
    """
    if not pages:
        return "Internal links: no pages yet."
    lines: list[str] = ["Internal link intelligence (same-host in/out edges):"]
    zero_in_urls = [url for pid, url, _d in pages if in_map.get(url, 0) == 0]
    lines.append(f"• Pages with 0 internal inbound links: {len(zero_in_urls)}")
    low_in = [url for pid, url, _d in pages if 1 <= in_map.get(url, 0) <= 3]
    lines.append(f"• Pages with 1–3 internal inbound links: {len(low_in)}")
    by_in = sorted(((in_map.get(url, 0), url) for _pid, url, _d in pages), reverse=True)
    lines.append(f"• Top {top_n} pages by internal inbound count:")
    for cnt, url in by_in[:top_n]:
        short = url if len(url) <= 76 else f"{url[:73]}…"
        lines.append(f"    {cnt:4d}  {short}")
    by_out = sorted(((out_map.get(pid, 0), url) for pid, url, _d in pages), reverse=True)
    lines.append(f"• Top {top_n} pages by internal outbound count:")
    for cnt, url in by_out[:top_n]:
        short = url if len(url) <= 76 else f"{url[:73]}…"
        lines.append(f"    {cnt:4d}  {short}")
    high_out = [
        (pid, url, out_map.get(pid, 0))
        for pid, url, _d in pages
        if out_map.get(pid, 0) >= high_outbound_threshold
    ]
    lines.append(
        f"• Pages with ≥{high_outbound_threshold} internal outbound links: {len(high_out)}"
        + (" (see table filters)" if high_out else "")
    )
    deep_weak = [
        url
        for pid, url, d in pages
        if d is not None
        and int(d) >= deep_depth_min
        and in_map.get(url, 0) <= weak_inbound_max
    ]
    lines.append(
        f"• Deep pages (depth ≥ {deep_depth_min}) with inbound ≤ {weak_inbound_max}: {len(deep_weak)}"
    )
    if deep_weak:
        for url in deep_weak[:top_n]:
            short = url if len(url) <= 76 else f"{url[:73]}…"
            lines.append(f"    {short}")
        if len(deep_weak) > top_n:
            lines.append(f"    … +{len(deep_weak) - top_n} more")
    return "\n".join(lines)
