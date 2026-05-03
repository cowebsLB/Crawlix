"""QRunnable crawl worker."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import httpx
from PyQt6.QtCore import QRunnable
from sqlalchemy.orm import sessionmaker

from crawlix.db.models import Job
from crawlix.services.crawler.bfs import run_crawl_job
from crawlix.services.net.global_limiter import GlobalOutboundLimiter
from crawlix.workers.job_bus import JobBus

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine


class CrawlWorker(QRunnable):
    def __init__(
        self,
        job_id: int,
        engine: Engine,
        bus: JobBus,
        *,
        job_key: str,
    ) -> None:
        super().__init__()
        self.job_id = job_id
        self.engine = engine
        self.bus = bus
        self.job_key = job_key

    def run(self) -> None:
        Session = sessionmaker(bind=self.engine, expire_on_commit=False)
        session = Session()
        client = httpx.Client(follow_redirects=True, verify=True)
        limiter = GlobalOutboundLimiter()
        try:
            job = session.get(Job, self.job_id)
            if job:
                job.status = "running"
                job.started_at = job.started_at or datetime.now(UTC)
                session.commit()
            cancel = False

            def cancel_check() -> bool:
                nonlocal cancel
                session.expire_all()
                j = session.get(Job, self.job_id)
                return bool(j and j.cancel_requested)

            self.bus.progress.emit(self.job_id, 0.0, "starting")

            def on_progress(pct: float, msg: str) -> None:
                self.bus.progress.emit(self.job_id, pct, msg)

            summary = run_crawl_job(
                session,
                self.job_id,
                client=client,
                limiter=limiter,
                cancel_check=cancel_check,
                on_progress=on_progress,
            )
            self.bus.finished.emit(self.job_id, summary)
        except Exception as e:
            self.bus.failed.emit(self.job_id, "crawl_failed", str(e))
        finally:
            session.close()
            client.close()
