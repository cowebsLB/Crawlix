"""Polite BFS crawl — httpx + robots.txt + gzip storage."""

from __future__ import annotations

import random
import time
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx
from selectolax.parser import HTMLParser
from sqlalchemy.orm import Session

from crawlix.config import PRESETS, PolitenessDefaults
from crawlix.db.models import CrawledData, CrawlQueueItem, Job, Page, PageLink
from crawlix.services.net.backoff import sleep_for_retry
from crawlix.services.net.global_limiter import GlobalOutboundLimiter
from crawlix.services.net.ssrf import assert_url_safe_for_fetch
from crawlix.utils.gzip_util import gzip_bytes
from crawlix.utils.urls import normalize_url


def _same_host(a: str, b: str) -> bool:
    return urlparse(a).netloc.lower() == urlparse(b).netloc.lower()


def _politeness_delay(preset_name: str) -> None:
    p = PRESETS.get(preset_name, PolitenessDefaults())
    base = p.min_delay_same_host_s
    jitter = random.uniform(0, p.jitter_same_host_max_s)
    time.sleep(base + jitter)


def run_crawl_job(
    session: Session,
    job_id: int,
    *,
    client: httpx.Client,
    limiter: GlobalOutboundLimiter,
    cancel_check: Callable[[], bool],
    allow_private_ssrf: bool = False,
    on_progress: Callable[[float, str], None] | None = None,
) -> dict[str, Any]:
    job = session.get(Job, job_id)
    if not job or not job.payload_json:
        return {"error": "missing job"}
    payload = job.payload_json
    seeds: list[str] = payload.get("seed_urls") or []
    max_depth: int = int(payload.get("max_depth", 2))
    respect_robots: bool = bool(payload.get("respect_robots", True))
    preset = str(payload.get("politeness_preset", "conservative"))
    project_id = job.project_id

    robots_cache: dict[str, RobotFileParser] = {}

    def can_fetch(url: str) -> bool:
        if not respect_robots:
            return True
        base = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
        if base not in robots_cache:
            rp = RobotFileParser()
            try:
                with limiter:
                    r = client.get(f"{base}/robots.txt", timeout=10.0)
                if r.status_code == 200:
                    rp.parse(r.text.splitlines())
                else:
                    rp.parse([])
            except Exception:
                rp.parse([])
            robots_cache[base] = rp
        rp = robots_cache[base]
        try:
            return rp.can_fetch("*", url)
        except Exception:
            return True

    visited: set[str] = set()
    fetched = 0
    errors: list[str] = []

    pending = (
        session.query(CrawlQueueItem)
        .filter(CrawlQueueItem.job_id == job_id, CrawlQueueItem.state == "pending")
        .order_by(CrawlQueueItem.depth, CrawlQueueItem.id)
        .all()
    )

    if not pending and seeds:
        for s in seeds:
            nu = normalize_url(s)
            assert_url_safe_for_fetch(nu, allow_private=allow_private_ssrf)
            session.add(
                CrawlQueueItem(job_id=job_id, url_norm=nu, depth=0, state="pending")
            )
        session.commit()
        pending = (
            session.query(CrawlQueueItem)
            .filter(CrawlQueueItem.job_id == job_id, CrawlQueueItem.state == "pending")
            .all()
        )

    max(len(pending), 1)

    while pending:
        if cancel_check():
            job.status = "cancelled"
            session.commit()
            return {"cancelled": True, "fetched": fetched}

        item = pending[0]
        url = item.url_norm
        if url in visited:
            item.state = "skipped"
            session.commit()
            pending = (
                session.query(CrawlQueueItem)
                .filter(CrawlQueueItem.job_id == job_id, CrawlQueueItem.state == "pending")
                .all()
            )
            continue
        visited.add(url)

        if not can_fetch(url):
            item.state = "skipped"
            item.last_error = "robots.txt disallow"
            session.commit()
            pending = (
                session.query(CrawlQueueItem)
                .filter(CrawlQueueItem.job_id == job_id, CrawlQueueItem.state == "pending")
                .all()
            )
            continue

        _politeness_delay(preset)
        resp: httpx.Response | None = None
        for attempt in range(PolitenessDefaults.max_retries_429_5xx + 1):
            try:
                with limiter:
                    resp = client.get(url, timeout=30.0)
            except Exception as e:
                errors.append(str(e))
                if attempt >= PolitenessDefaults.max_retries_429_5xx:
                    item.state = "failed"
                    item.last_error = str(e)
                    session.commit()
                    resp = None
                    break
                sleep_for_retry(attempt)
                continue
            if resp.status_code in (429, 500, 502, 503, 504):
                if attempt >= PolitenessDefaults.max_retries_429_5xx:
                    item.state = "failed"
                    item.last_error = f"HTTP {resp.status_code}"
                    session.commit()
                    resp = None
                    break
                sleep_for_retry(attempt)
                continue
            break

        if resp is None:
            pending = (
                session.query(CrawlQueueItem)
                .filter(CrawlQueueItem.job_id == job_id, CrawlQueueItem.state == "pending")
                .all()
            )
            continue

        page = (
            session.query(Page)
            .filter(Page.project_id == project_id, Page.url_norm == url)
            .one_or_none()
        )
        now = datetime.now(UTC)
        if not page:
            page = Page(
                project_id=project_id,
                url_norm=url,
                url_final=str(resp.url),
                title=None,
                status_code=resp.status_code,
                content_type=resp.headers.get("content-type"),
                crawl_job_id=job_id,
                first_seen_at=now,
                last_crawled_at=now,
            )
            session.add(page)
            session.flush()
        else:
            page.url_final = str(resp.url)
            page.status_code = resp.status_code
            page.content_type = resp.headers.get("content-type")
            page.last_crawled_at = now
            page.crawl_job_id = job_id
        page.crawl_depth = item.depth

        body = resp.content or b""
        session.add(
            CrawledData(
                page_id=page.id,
                job_id=job_id,
                html_gzip=gzip_bytes(body),
                headers_json=dict(resp.headers),
                bytes_raw=len(body),
            )
        )

        item.state = "fetched"
        fetched += 1

        ctype = (resp.headers.get("content-type") or "").lower()
        if "html" in ctype and item.depth < max_depth:
            text = body.decode(resp.encoding or "utf-8", errors="ignore")
            tree = HTMLParser(text)
            tnode = tree.css_first("title")
            if tnode and tnode.text():
                page.title = tnode.text()[:1024]
            for node in tree.css("a[href]"):
                href = node.attributes.get("href")
                if not href:
                    continue
                next_u = normalize_url(urljoin(str(resp.url), href))
                try:
                    assert_url_safe_for_fetch(next_u, allow_private=allow_private_ssrf)
                except ValueError:
                    continue
                if not _same_host(url, next_u):
                    session.add(
                        PageLink(
                            from_page_id=page.id,
                            to_url_norm=next_u,
                            link_text=node.text()[:512] if node.text() else None,
                            nofollow="nofollow" in (node.attributes.get("rel") or "").lower(),
                            job_id=job_id,
                        )
                    )
                    continue
                session.add(
                    PageLink(
                        from_page_id=page.id,
                        to_url_norm=next_u,
                        link_text=node.text()[:512] if node.text() else None,
                        nofollow="nofollow" in (node.attributes.get("rel") or "").lower(),
                        job_id=job_id,
                    )
                )
                if next_u not in visited:
                    exists = (
                        session.query(CrawlQueueItem)
                        .filter(
                            CrawlQueueItem.job_id == job_id,
                            CrawlQueueItem.url_norm == next_u,
                        )
                        .first()
                    )
                    if not exists:
                        session.add(
                            CrawlQueueItem(
                                job_id=job_id,
                                url_norm=next_u,
                                depth=item.depth + 1,
                                state="pending",
                                parent_page_id=page.id,
                            )
                        )

        pending_n = (
            session.query(CrawlQueueItem)
            .filter(CrawlQueueItem.job_id == job_id, CrawlQueueItem.state == "pending")
            .count()
        )
        done_n = (
            session.query(CrawlQueueItem)
            .filter(CrawlQueueItem.job_id == job_id, CrawlQueueItem.state == "fetched")
            .count()
        )
        job.progress_pct = min(99.0, 100.0 * done_n / max(done_n + pending_n, 1))
        session.commit()
        if on_progress:
            try:
                tail = url if len(url) <= 72 else f"{url[:69]}…"
                on_progress(job.progress_pct, f"{fetched} fetched · {tail}")
            except Exception:
                pass

        pending = (
            session.query(CrawlQueueItem)
            .filter(CrawlQueueItem.job_id == job_id, CrawlQueueItem.state == "pending")
            .all()
        )

    job.progress_pct = 100.0
    job.status = "completed"
    job.finished_at = datetime.now(UTC)
    job.result_summary_json = {"fetched": fetched, "errors": errors[:20]}
    session.commit()
    if on_progress:
        try:
            on_progress(100.0, f"Complete ({fetched} pages)")
        except Exception:
            pass
    return {"fetched": fetched, "errors": errors}
