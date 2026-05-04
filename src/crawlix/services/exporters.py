"""CSV/JSON export helpers for J4–J5 (pages, links, audits) and J8 (citation sources)."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from crawlix.db.models import CitationSource, Page, PageLink, SeoAudit


def export_pages_csv(session: Session, project_id: int, path: Path) -> int:
    rows = (
        session.execute(
            select(Page).where(Page.project_id == project_id).order_by(Page.url_norm.asc())
        )
        .scalars()
        .all()
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(
            ["id", "url_norm", "url_final", "title", "status_code", "crawl_depth", "last_crawled_at"]
        )
        for p in rows:
            w.writerow(
                [
                    p.id,
                    p.url_norm,
                    p.url_final or "",
                    p.title or "",
                    p.status_code if p.status_code is not None else "",
                    p.crawl_depth if p.crawl_depth is not None else "",
                    p.last_crawled_at.isoformat() if p.last_crawled_at else "",
                ]
            )
    return len(rows)


def export_page_links_csv(session: Session, project_id: int, path: Path) -> int:
    q = (
        select(PageLink, Page.url_norm.label("from_url"))
        .join(Page, PageLink.from_page_id == Page.id)
        .where(Page.project_id == project_id)
        .order_by(Page.url_norm.asc(), PageLink.to_url_norm.asc())
    )
    rows = session.execute(q).all()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["from_page_id", "from_url", "to_url_norm", "link_text", "nofollow"])
        for pl, from_url in rows:
            w.writerow(
                [
                    pl.from_page_id,
                    from_url,
                    pl.to_url_norm,
                    pl.link_text or "",
                    pl.nofollow,
                ]
            )
    return len(rows)


def export_seo_audits_csv(session: Session, project_id: int, path: Path) -> int:
    q = (
        select(SeoAudit, Page.url_norm)
        .join(Page, SeoAudit.page_id == Page.id)
        .where(Page.project_id == project_id)
        .order_by(SeoAudit.audited_at.desc())
    )
    rows = session.execute(q).all()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "audit_id",
                "page_id",
                "url_norm",
                "overall_score",
                "issues_count",
                "audited_at",
            ]
        )
        for audit, url_norm in rows:
            issues = audit.issues_json or []
            w.writerow(
                [
                    audit.id,
                    audit.page_id,
                    url_norm,
                    audit.overall_score if audit.overall_score is not None else "",
                    len(issues) if isinstance(issues, list) else "",
                    audit.audited_at.isoformat() if audit.audited_at else "",
                ]
            )
    return len(rows)


def export_seo_audits_json(session: Session, project_id: int, path: Path) -> int:
    q = (
        select(SeoAudit, Page.url_norm)
        .join(Page, SeoAudit.page_id == Page.id)
        .where(Page.project_id == project_id)
        .order_by(SeoAudit.audited_at.desc())
    )
    rows = session.execute(q).all()
    out: list[dict[str, Any]] = []
    for audit, url_norm in rows:
        out.append(
            {
                "id": audit.id,
                "page_id": audit.page_id,
                "url_norm": url_norm,
                "job_id": audit.job_id,
                "overall_score": audit.overall_score,
                "category_scores_json": audit.category_scores_json,
                "issues_json": audit.issues_json,
                "recommendations_json": audit.recommendations_json,
                "audited_at": audit.audited_at.isoformat() if audit.audited_at else None,
            }
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    return len(out)


def export_builtin_citation_sources_csv(session: Session, path: Path) -> int:
    """Export global built-in citation templates (YAML-backed rows in DB)."""
    rows = (
        session.execute(
            select(CitationSource)
            .where(CitationSource.is_builtin.is_(True), CitationSource.project_id.is_(None))
            .order_by(CitationSource.sort_order, CitationSource.id)
        )
        .scalars()
        .all()
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "id",
                "name",
                "template_url",
                "region_tags_json",
                "requires_playwright",
                "enabled",
                "pack_version",
                "sort_order",
            ]
        )
        for src in rows:
            tags = src.region_tags
            tags_cell = json.dumps(tags, ensure_ascii=False) if tags is not None else ""
            w.writerow(
                [
                    src.id,
                    src.name,
                    src.template_url,
                    tags_cell,
                    int(src.requires_playwright),
                    int(src.enabled),
                    src.pack_version,
                    src.sort_order,
                ]
            )
    return len(rows)
