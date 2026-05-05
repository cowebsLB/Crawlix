"""Background citation matrix worker — one HTTP check per (location × built-in source)."""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import httpx
from PyQt6.QtCore import QRunnable
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from crawlix.db.models import CitationCheck, CitationSource, Job, Location
from crawlix.services.citations.placeholders import LocationFields, expand_template
from crawlix.services.net.global_limiter import GlobalOutboundLimiter
from crawlix.services.net.ssrf import httpx_event_hooks_ssrf
from crawlix.utils.gzip_util import gzip_bytes
from crawlix.workers.job_bus import JobBus

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine

_CITATION_UA = "Crawlix/0.1 (local SEO tool; +https://github.com/cowebsLB/Crawlix)"


def _location_fields(loc: Location) -> LocationFields:
    return LocationFields(
        business_name=loc.business_name,
        city=loc.city,
        region=loc.region,
        postal_code=loc.postal_code,
        country_code=loc.country_code,
        primary_phone_e164=loc.primary_phone_e164,
    )


class CitationMatrixWorker(QRunnable):
    def __init__(self, job_id: int, engine: Engine, bus: JobBus) -> None:
        super().__init__()
        self.job_id = job_id
        self.engine = engine
        self.bus = bus

    def run(self) -> None:
        Session = sessionmaker(bind=self.engine, expire_on_commit=False)
        session = Session()
        client = httpx.Client(
            follow_redirects=True,
            verify=True,
            timeout=30.0,
            event_hooks=httpx_event_hooks_ssrf(allow_private=False),
        )
        limiter = GlobalOutboundLimiter()
        try:
            job = session.get(Job, self.job_id)
            if not job or job.type != "citation":
                self.bus.failed.emit(self.job_id, "citation_bad_job", "missing job or wrong type")
                return
            project_id = job.project_id
            locs = (
                session.execute(
                    select(Location).where(Location.project_id == project_id).order_by(Location.id.asc())
                )
                .scalars()
                .all()
            )
            if not locs:
                self.bus.failed.emit(self.job_id, "citation_no_locations", "no locations for project")
                return
            srcs = (
                session.execute(
                    select(CitationSource)
                    .where(
                        CitationSource.is_builtin.is_(True),
                        CitationSource.project_id.is_(None),
                        CitationSource.enabled.is_(True),
                    )
                    .order_by(CitationSource.sort_order, CitationSource.id)
                )
                .scalars()
                .all()
            )
            if not srcs:
                self.bus.failed.emit(self.job_id, "citation_no_sources", "no enabled built-in sources")
                return

            job.status = "running"
            job.started_at = job.started_at or datetime.now(UTC)
            session.commit()

            total = len(locs) * len(srcs)
            http_ok = 0
            http_err = 0
            skipped_pw = 0

            def cancel_check() -> bool:
                session.expire_all()
                j = session.get(Job, self.job_id)
                return bool(j and j.cancel_requested)

            idx = 0
            for loc in locs:
                lf = _location_fields(loc)
                for src in srcs:
                    if cancel_check():
                        job = session.get(Job, self.job_id)
                        if job:
                            job.status = "cancelled"
                            job.progress_pct = 100.0 * idx / max(total, 1)
                            job.finished_at = datetime.now(UTC)
                            job.result_summary_json = {
                                "type": "citation",
                                "cancelled": True,
                                "written": idx,
                                "http_ok": http_ok,
                                "http_err": http_err,
                                "skipped_playwright": skipped_pw,
                            }
                            session.commit()
                        self.bus.finished.emit(
                            self.job_id,
                            {
                                "type": "citation",
                                "cancelled": True,
                                "written": idx,
                                "http_ok": http_ok,
                                "skipped_playwright": skipped_pw,
                            },
                        )
                        return

                    idx += 1
                    short = f"{loc.label} · {src.name}"
                    self.bus.progress.emit(self.job_id, 100.0 * idx / max(total, 1), short)

                    if src.requires_playwright:
                        try:
                            req_url = expand_template(src.template_url, lf)
                            err_t = "skipped: requires_playwright"
                        except ValueError as e:
                            req_url = None
                            err_t = str(e)
                        session.add(
                            CitationCheck(
                                location_id=loc.id,
                                source_id=src.id,
                                job_id=self.job_id,
                                requested_url=req_url,
                                final_url=None,
                                http_status=None,
                                fetched_at=datetime.now(UTC),
                                status="skipped",
                                error_text=err_t,
                                playwright_used=False,
                            )
                        )
                        skipped_pw += 1
                        job = session.get(Job, self.job_id)
                        if job:
                            job.progress_pct = 100.0 * idx / max(total, 1)
                        session.commit()
                        continue

                    try:
                        req_url = expand_template(src.template_url, lf)
                    except ValueError as e:
                        session.add(
                            CitationCheck(
                                location_id=loc.id,
                                source_id=src.id,
                                job_id=self.job_id,
                                requested_url=None,
                                final_url=None,
                                http_status=None,
                                fetched_at=datetime.now(UTC),
                                status="error",
                                error_text=str(e),
                                playwright_used=False,
                            )
                        )
                        http_err += 1
                        job = session.get(Job, self.job_id)
                        if job:
                            job.progress_pct = 100.0 * idx / max(total, 1)
                        session.commit()
                        continue

                    html_gzip: bytes | None = None
                    final_url: str | None = None
                    http_status: int | None = None
                    status = "ok"
                    err_text: str | None = None
                    try:
                        headers = {"User-Agent": _CITATION_UA}
                        if "nominatim.openstreetmap.org" in req_url:
                            headers["User-Agent"] = (
                                "Crawlix/0.1 (citation check; contact: https://github.com/cowebsLB/Crawlix)"
                            )
                        with limiter:
                            resp = client.get(req_url, headers=headers, timeout=25.0)
                        http_status = resp.status_code
                        final_url = str(resp.url)
                        if resp.status_code >= 400:
                            status = "error"
                            err_text = f"HTTP {resp.status_code}"
                            http_err += 1
                        else:
                            http_ok += 1
                            raw = resp.content
                            if len(raw) <= 120_000:
                                html_gzip = gzip_bytes(raw)
                        if "nominatim.openstreetmap.org" in req_url:
                            time.sleep(1.1)
                    except httpx.HTTPError as e:
                        status = "error"
                        err_text = str(e)
                        http_err += 1

                    session.add(
                        CitationCheck(
                            location_id=loc.id,
                            source_id=src.id,
                            job_id=self.job_id,
                            requested_url=req_url,
                            final_url=final_url,
                            http_status=http_status,
                            fetched_at=datetime.now(UTC),
                            status=status,
                            error_text=err_text,
                            playwright_used=False,
                            response_html_gzip=html_gzip,
                        )
                    )
                    job = session.get(Job, self.job_id)
                    if job:
                        job.progress_pct = 100.0 * idx / max(total, 1)
                    session.commit()

            job = session.get(Job, self.job_id)
            if job:
                job.status = "completed"
                job.progress_pct = 100.0
                job.finished_at = datetime.now(UTC)
                job.result_summary_json = {
                    "type": "citation",
                    "written": idx,
                    "http_ok": http_ok,
                    "http_err": http_err,
                    "skipped_playwright": skipped_pw,
                }
                session.commit()
            self.bus.finished.emit(
                self.job_id,
                {
                    "type": "citation",
                    "written": idx,
                    "http_ok": http_ok,
                    "http_err": http_err,
                    "skipped_playwright": skipped_pw,
                },
            )
        except Exception as e:
            job = session.get(Job, self.job_id)
            if job:
                job.status = "failed"
                job.error_text = str(e)
                job.finished_at = datetime.now(UTC)
                session.commit()
            self.bus.failed.emit(self.job_id, "citation_failed", str(e))
        finally:
            session.close()
            client.close()
