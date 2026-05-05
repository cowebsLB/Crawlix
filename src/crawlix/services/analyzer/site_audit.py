"""Cross-page / crawl-graph SEO signals merged into per-page issue lists."""

from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Iterable
from urllib.parse import urlparse

from sqlalchemy import func
from sqlalchemy.orm import Session

from crawlix.db.models import Job, Page, PageLink
from crawlix.utils.urls import normalize_url


def _same_host(a: str, b: str) -> bool:
    return urlparse(a).netloc.lower() == urlparse(b).netloc.lower()


def latest_completed_crawl_job_id(session: Session, project_id: int) -> int | None:
    """Most recently finished crawl job for the project (used as default link-graph scope)."""
    row = (
        session.query(Job.id)
        .filter(Job.project_id == project_id, Job.type == "crawl", Job.status == "completed")
        .order_by(Job.finished_at.desc().nullslast(), Job.id.desc())
        .first()
    )
    return int(row[0]) if row else None


def _resolve_crawl_job_for_links(
    session: Session,
    project_id: int,
    crawl_job_id: int | None,
) -> int | None:
    """Pick PageLink.job_id filter: explicit crawl job, else latest completed crawl."""
    if crawl_job_id is not None:
        return int(crawl_job_id)
    return latest_completed_crawl_job_id(session, project_id)


def inbound_internal_counts(
    session: Session,
    project_id: int,
    url_norms: list[str],
    *,
    crawl_job_id: int | None = None,
) -> dict[str, int]:
    if not url_norms:
        return {}
    jid = _resolve_crawl_job_for_links(session, project_id, crawl_job_id)
    if jid is None:
        return {}
    rows = (
        session.query(PageLink.to_url_norm, func.count(PageLink.id))
        .join(Page, PageLink.from_page_id == Page.id)
        .filter(
            Page.project_id == project_id,
            PageLink.to_url_norm.in_(url_norms),
            PageLink.job_id == jid,
        )
        .group_by(PageLink.to_url_norm)
        .all()
    )
    return {str(r[0]): int(r[1]) for r in rows}


def outbound_internal_counts(
    session: Session,
    project_id: int,
    pages_by_id: dict[int, str],
    *,
    crawl_job_id: int | None = None,
) -> dict[int, int]:
    """Counts PageLink rows from each page to same-host targets (for one crawl job)."""
    if not pages_by_id:
        return {}
    jid = _resolve_crawl_job_for_links(session, project_id, crawl_job_id)
    if jid is None:
        return {int(pid): 0 for pid in pages_by_id}
    ids = list(pages_by_id.keys())
    rows = (
        session.query(PageLink.from_page_id, PageLink.to_url_norm)
        .join(Page, PageLink.from_page_id == Page.id)
        .filter(
            Page.project_id == project_id,
            PageLink.from_page_id.in_(ids),
            PageLink.job_id == jid,
        )
        .all()
    )
    out: dict[int, int] = {pid: 0 for pid in ids}
    for fid, to_u in rows:
        base = pages_by_id.get(int(fid))
        if base and _same_host(base, str(to_u)):
            out[int(fid)] += 1
    return out


def _norm_title(title: str | None) -> str:
    if not title:
        return ""
    return re.sub(r"\s+", " ", title.strip()).lower()


def _first_path_segment(url: str) -> str:
    path = urlparse(url).path or "/"
    segs = [s for s in path.strip("/").split("/") if s]
    return segs[0] if segs else ""


def cross_page_issues_for_batch(
    rows: Iterable[dict[str, object]],
    *,
    diverse_prefix_threshold: int = 4,
) -> dict[int, list[dict]]:
    """
    rows: dicts with keys page_id, url_norm, url_final (optional), title (optional), content_fp (optional str)
    Returns extra issues keyed by page_id.
    """
    rlist = list(rows)
    by_id: dict[int, dict[str, object]] = {int(r["page_id"]): r for r in rlist}

    title_to_pages: dict[str, list[int]] = defaultdict(list)
    final_to_pages: dict[str, list[int]] = defaultdict(list)
    title_fp_to_pages: dict[tuple[str, str], list[int]] = defaultdict(list)

    for r in rlist:
        pid = int(r["page_id"])
        tkey = _norm_title(str(r.get("title") or ""))
        if tkey:
            title_to_pages[tkey].append(pid)
        final_raw = r.get("url_final")
        ufn = normalize_url(str(final_raw)) if final_raw else normalize_url(str(r["url_norm"]))
        final_to_pages[ufn].append(pid)
        fp = str(r.get("content_fp") or "")
        if tkey and fp:
            title_fp_to_pages[(tkey, fp)].append(pid)

    extras: dict[int, list[dict]] = defaultdict(list)

    for tkey, pids in title_to_pages.items():
        if len(pids) < 2:
            continue
        others = sorted({by_id[p]["url_norm"] for p in pids})[:12]
        for pid in pids:
            extras[pid].append(
                {
                    "id": "duplicate_title_site",
                    "severity": "medium",
                    "category": "duplicates",
                    "message": "Same title text is used on multiple pages",
                    "evidence": {
                        "title": tkey[:200],
                        "other_urls": [
                            u for u in others if u != by_id[pid]["url_norm"]
                        ][:8],
                    },
                }
            )

    for ufn, pids in final_to_pages.items():
        norms = {normalize_url(str(by_id[p]["url_norm"])) for p in pids}
        if len(norms) < 2:
            continue
        urls = sorted(norms)[:12]
        for pid in pids:
            extras[pid].append(
                {
                    "id": "multiple_paths_same_destination",
                    "severity": "medium",
                    "category": "duplicates",
                    "message": "Several normalized URLs resolve to the same final URL",
                    "evidence": {
                        "final_url": ufn,
                        "alternate_paths": [
                            u for u in urls if u != by_id[pid]["url_norm"]
                        ][:8],
                    },
                }
            )

    for (_t, _fp), pids in title_fp_to_pages.items():
        if len(pids) < 2:
            continue
        sample_urls = sorted({str(by_id[p]["url_norm"]) for p in pids})[:10]
        for pid in pids:
            extras[pid].append(
                {
                    "id": "duplicate_title_and_body_fingerprint",
                    "severity": "low",
                    "category": "duplicates",
                    "message": "Same title and very similar body content fingerprint as other pages",
                    "evidence": {"urls": [u for u in sample_urls if u != by_id[pid]["url_norm"]][:6]},
                }
            )

    prefixes = [_first_path_segment(str(r["url_norm"])) for r in rlist]
    nonempty = [p for p in prefixes if p]
    distinct = len(set(nonempty))
    if distinct >= diverse_prefix_threshold:
        top = sorted(set(nonempty))[:15]
        for r in rlist:
            pid = int(r["page_id"])
            extras[pid].append(
                {
                    "id": "mixed_top_level_path_prefixes",
                    "severity": "low",
                    "category": "url_structure",
                    "message": "Site uses many different top-level URL path folders",
                    "evidence": {"distinct_prefix_count": distinct, "sample_prefixes": top},
                }
            )

    return extras
