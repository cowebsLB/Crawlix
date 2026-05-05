"""Tests for crawl snapshot diff and persistence."""

from pathlib import Path

from sqlalchemy.orm import sessionmaker

from crawlix.db.models import CrawlSnapshot, CrawlSnapshotPage, Job, Page, Project
from crawlix.db.session import init_db, make_engine
from crawlix.services.crawler.crawl_snapshots import (
    compute_snapshot_diff,
    format_crawl_diff_for_ui,
    persist_after_completed_crawl,
)


def test_compute_snapshot_diff() -> None:
    old_m = {
        "https://ex.com/a": {"title": "A", "status_code": 200, "url_final": "https://ex.com/a", "crawl_depth": 0},
        "https://ex.com/b": {"title": "B", "status_code": 200, "url_final": "https://ex.com/b", "crawl_depth": 1},
    }
    new_m = {
        "https://ex.com/a": {"title": "A2", "status_code": 404, "url_final": "https://ex.com/a", "crawl_depth": 0},
        "https://ex.com/c": {"title": "C", "status_code": 200, "url_final": "https://ex.com/c", "crawl_depth": 1},
    }
    d = compute_snapshot_diff(old_m, new_m)
    assert "https://ex.com/c" in d["added"]
    assert "https://ex.com/b" in d["removed"]
    assert "https://ex.com/a" in d["title_changed"]
    assert "https://ex.com/a" in d["status_changed"]
    assert d["final_changed"] == []
    assert d["depth_changed"] == []


def test_format_crawl_diff_for_ui_none() -> None:
    text = format_crawl_diff_for_ui(None)
    assert "two completed crawls" in text.lower()


def test_persist_and_prune(tmp_path: Path) -> None:
    db = tmp_path / "snap.db"
    engine = make_engine(db)
    init_db(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    s = Session()
    try:
        pr = Project(name="P", slug="snap-p", default_domain="ex.com")
        s.add(pr)
        s.commit()
        job = Job(project_id=pr.id, type="crawl", status="completed", progress_pct=100.0)
        s.add(job)
        s.commit()
        s.add_all(
            [
                Page(
                    project_id=pr.id,
                    url_norm="https://ex.com/u1",
                    url_final="https://ex.com/u1",
                    title="One",
                    status_code=200,
                    crawl_depth=0,
                ),
                Page(
                    project_id=pr.id,
                    url_norm="https://ex.com/u2",
                    url_final="https://ex.com/u2",
                    title="Two",
                    status_code=200,
                    crawl_depth=1,
                ),
            ]
        )
        s.commit()
        sid = persist_after_completed_crawl(s, pr.id, job.id)
        assert sid is not None
        s.commit()
        n = s.query(CrawlSnapshotPage).filter(CrawlSnapshotPage.snapshot_id == sid).count()
        assert n == 2
        assert s.get(CrawlSnapshot, sid).page_count == 2
    finally:
        s.close()
