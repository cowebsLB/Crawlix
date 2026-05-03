"""Background audit worker."""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx
from PyQt6.QtCore import QRunnable
from sqlalchemy.orm import sessionmaker

from crawlix.db.models import CrawledData, Job, Page, SeoAudit
from crawlix.services.analyzer.audit import audit_html
from crawlix.services.net.global_limiter import GlobalOutboundLimiter
from crawlix.utils.gzip_util import gunzip_bytes
from crawlix.workers.job_bus import JobBus

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine


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
                score, issues, cats = audit_html(html, page.url_norm)
                session.add(
                    SeoAudit(
                        page_id=pid,
                        job_id=self.job_id,
                        overall_score=score,
                        category_scores_json=cats,
                        issues_json=issues,
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
