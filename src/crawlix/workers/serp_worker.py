"""Background SERP snapshot worker."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import httpx
from PyQt6.QtCore import QRunnable
from sqlalchemy.orm import sessionmaker

from crawlix.db.models import Job
from crawlix.services.scraper.serp_service import fetch_serp_placeholder
from crawlix.workers.job_bus import JobBus

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine


class SerpWorker(QRunnable):
    def __init__(self, job_id: int, engine: Engine, bus: JobBus) -> None:
        super().__init__()
        self.job_id = job_id
        self.engine = engine
        self.bus = bus

    def run(self) -> None:
        Session = sessionmaker(bind=self.engine, expire_on_commit=False)
        session = Session()
        client = httpx.Client(follow_redirects=True, verify=True, timeout=60.0)
        try:
            job = session.get(Job, self.job_id)
            if not job or not job.payload_json:
                self.bus.failed.emit(self.job_id, "serp_bad_job", "missing job or payload")
                return
            kid = job.payload_json.get("keyword_id")
            if not kid:
                self.bus.failed.emit(self.job_id, "serp_bad_payload", "missing keyword_id")
                return
            job.status = "running"
            job.started_at = job.started_at or datetime.now(UTC)
            session.commit()
            self.bus.progress.emit(self.job_id, 15.0, "fetching HTML")
            rid = fetch_serp_placeholder(session, int(kid), client=client)
            job = session.get(Job, self.job_id)
            if job:
                job.status = "completed"
                job.progress_pct = 100.0
                job.finished_at = datetime.now(UTC)
                job.result_summary_json = {"serp_result_id": rid, "type": "serp"}
                session.commit()
            self.bus.progress.emit(self.job_id, 100.0, "snapshot stored")
            self.bus.finished.emit(self.job_id, {"serp_result_id": rid, "type": "serp"})
        except Exception as e:
            job = session.get(Job, self.job_id)
            if job:
                job.status = "failed"
                job.error_text = str(e)
                job.finished_at = datetime.now(UTC)
                session.commit()
            self.bus.failed.emit(self.job_id, "serp_failed", str(e))
        finally:
            session.close()
            client.close()
