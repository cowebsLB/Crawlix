"""Background audit worker."""

from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.robotparser import RobotFileParser

import httpx
from PyQt6.QtCore import QRunnable
from selectolax.parser import HTMLParser
from sqlalchemy.orm import sessionmaker

from crawlix.db.models import CrawledData, Job, Page, SeoAudit
from crawlix.services.analyzer.audit import audit_html, content_fingerprint, score_from_issues
from crawlix.services.analyzer.robots_check import url_allowed_by_robots
from crawlix.services.analyzer.site_audit import (
    cross_page_issues_for_batch,
    inbound_internal_counts,
    outbound_internal_counts,
)
from crawlix.services.net.global_limiter import GlobalOutboundLimiter
from crawlix.utils.gzip_util import gunzip_bytes
from crawlix.workers.job_bus import JobBus

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine


def _title_from_html(html: str) -> str:
    if not html:
        return ""
    tree = HTMLParser(html)
    title_el = tree.css_first("title")
    if title_el and title_el.text():
        return title_el.text().strip()[:1024]
    return ""


def _headers_from_cd(cd: CrawledData | None) -> dict[str, str] | None:
    if not cd or not cd.headers_json:
        return None
    raw = cd.headers_json
    if isinstance(raw, dict):
        return {str(k): str(v) for k, v in raw.items()}
    return None


class AuditWorker(QRunnable):
    def __init__(self, job_id: int, engine: Engine, bus: JobBus) -> None:
        super().__init__()
        self.job_id = job_id
        self.engine = engine
        self.bus = bus

    def run(self) -> None:
        Session = sessionmaker(bind=self.engine, expire_on_commit=False)
        session = Session()
        client = httpx.Client(follow_redirects=True, verify=True)
        limiter = GlobalOutboundLimiter()
        robots_cache: dict[str, RobotFileParser] = {}
        try:
            job = session.get(Job, self.job_id)
            if not job or not job.payload_json:
                self.bus.failed.emit(self.job_id, "audit_bad_job", "missing payload")
                return
            page_ids: list[int] = job.payload_json.get("page_ids") or []
            if not page_ids:
                self.bus.failed.emit(self.job_id, "audit_no_pages", "no page_ids")
                return
            job.status = "running"
            session.commit()
            n = len(page_ids)

            def cancel_check() -> bool:
                session.expire_all()
                j = session.get(Job, self.job_id)
                return bool(j and j.cancel_requested)

            pages = session.query(Page).filter(Page.id.in_(page_ids)).all()
            if not pages:
                self.bus.failed.emit(self.job_id, "audit_no_pages", "no matching pages")
                return
            project_id = pages[0].project_id
            pages_by_id = {p.id: p.url_norm for p in pages}
            url_norms = [p.url_norm for p in pages]
            inbound_map = inbound_internal_counts(session, project_id, url_norms)
            outbound_map = outbound_internal_counts(session, project_id, pages_by_id)

            batch_rows: list[dict[str, object]] = []
            page_html: dict[int, str] = {}

            for pid in page_ids:
                page = session.get(Page, pid)
                if not page:
                    continue
                cd = (
                    session.query(CrawledData)
                    .filter(CrawledData.page_id == pid)
                    .order_by(CrawledData.fetched_at.desc())
                    .first()
                )
                html = ""
                if cd and cd.html_gzip:
                    html = gunzip_bytes(cd.html_gzip).decode("utf-8", errors="ignore")
                elif page.url_final:
                    with limiter:
                        r = client.get(page.url_final, timeout=30.0)
                    html = r.text
                page_html[pid] = html
                title = page.title or _title_from_html(html)
                fp = content_fingerprint(html) if html else ""
                batch_rows.append(
                    {
                        "page_id": pid,
                        "url_norm": page.url_norm,
                        "url_final": page.url_final,
                        "title": title,
                        "content_fp": fp,
                    }
                )

            extras_by_page = cross_page_issues_for_batch(batch_rows)

            for i, pid in enumerate(page_ids):
                if cancel_check():
                    job.status = "cancelled"
                    job.progress_pct = 100.0 * i / max(n, 1)
                    session.commit()
                    self.bus.finished.emit(self.job_id, {"cancelled": True, "audited": i})
                    return
                page = session.get(Page, pid)
                if not page:
                    continue
                html = page_html.get(pid, "")
                cd = (
                    session.query(CrawledData)
                    .filter(CrawledData.page_id == pid)
                    .order_by(CrawledData.fetched_at.desc())
                    .first()
                )
                fetch_url = page.url_final or page.url_norm
                robots_ok = True
                try:
                    with limiter:
                        robots_ok = url_allowed_by_robots(client, fetch_url, cache=robots_cache)
                except Exception:
                    robots_ok = True

                _score, onpage_issues, _cats2 = audit_html(
                    html,
                    page.url_norm,
                    url_final=page.url_final,
                    status_code=page.status_code,
                    response_headers=_headers_from_cd(cd),
                    robots_txt_blocked=not robots_ok,
                    outbound_internal=outbound_map.get(pid),
                    inbound_internal=inbound_map.get(page.url_norm, 0),
                    crawl_depth=page.crawl_depth,
                )
                merged = list(onpage_issues) + list(extras_by_page.get(pid, []))
                overall, cats = score_from_issues(merged)
                session.add(
                    SeoAudit(
                        page_id=pid,
                        job_id=self.job_id,
                        overall_score=overall,
                        category_scores_json=cats,
                        issues_json=merged,
                        recommendations_json=[],
                    )
                )
                job.progress_pct = 100.0 * (i + 1) / n
                session.commit()
                self.bus.progress.emit(self.job_id, job.progress_pct, f"page {pid}")
            job.status = "completed"
            job.progress_pct = 100.0
            session.commit()
            self.bus.finished.emit(self.job_id, {"audited": n})
        except Exception as e:
            self.bus.failed.emit(self.job_id, "audit_failed", str(e))
        finally:
            session.close()
            client.close()
