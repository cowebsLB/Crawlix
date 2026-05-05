"""Internal link counts scope to a single crawl job (default: latest completed)."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from crawlix.db.models import Base, Job, Page, PageLink, Project
from crawlix.services.analyzer.site_audit import (
    inbound_internal_counts,
    latest_completed_crawl_job_id,
    outbound_internal_counts,
)


def _session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)()


def test_latest_completed_crawl_job_picks_newest_finish() -> None:
    s = _session()
    p = Project(name="P", slug="p")
    s.add(p)
    s.commit()
    j_old = Job(
        project_id=p.id,
        type="crawl",
        status="completed",
        progress_pct=100.0,
        finished_at=datetime(2020, 1, 1, tzinfo=UTC),
    )
    j_new = Job(
        project_id=p.id,
        type="crawl",
        status="completed",
        progress_pct=100.0,
        finished_at=datetime(2022, 1, 1, tzinfo=UTC),
    )
    s.add_all([j_old, j_new])
    s.commit()
    assert latest_completed_crawl_job_id(s, p.id) == j_new.id


def test_inbound_default_uses_latest_crawl_job_only() -> None:
    s = _session()
    p = Project(name="P", slug="p2")
    s.add(p)
    s.commit()
    j1 = Job(
        project_id=p.id,
        type="crawl",
        status="completed",
        progress_pct=100.0,
        finished_at=datetime(2020, 1, 1, tzinfo=UTC),
    )
    j2 = Job(
        project_id=p.id,
        type="crawl",
        status="completed",
        progress_pct=100.0,
        finished_at=datetime(2021, 1, 1, tzinfo=UTC),
    )
    s.add_all([j1, j2])
    s.commit()
    page = Page(
        project_id=p.id,
        url_norm="https://ex.test/",
        crawl_job_id=j2.id,
    )
    s.add(page)
    s.commit()
    target = "https://ex.test/a"
    s.add(PageLink(from_page_id=page.id, to_url_norm=target, job_id=j1.id))
    s.add(PageLink(from_page_id=page.id, to_url_norm=target, job_id=j2.id))
    s.commit()

    got = inbound_internal_counts(s, p.id, [target])
    assert got.get(target) == 1

    got_old = inbound_internal_counts(s, p.id, [target], crawl_job_id=j1.id)
    assert got_old.get(target) == 1


def test_outbound_zeros_when_no_completed_crawl() -> None:
    s = _session()
    p = Project(name="P", slug="p3")
    s.add(p)
    s.commit()
    page = Page(project_id=p.id, url_norm="https://ex.test/x")
    s.add(page)
    s.commit()
    m = outbound_internal_counts(s, p.id, {page.id: page.url_norm})
    assert m.get(page.id) == 0
