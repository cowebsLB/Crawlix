from types import SimpleNamespace

from crawlix.ui.controllers_jobs import build_job_rows, job_status_variant, top_jobs_badge_text


def test_job_status_variant_mapping() -> None:
    assert job_status_variant("completed") == "success"
    assert job_status_variant("failed") == "danger"
    assert job_status_variant("running") == "warning"
    assert job_status_variant("unknown_state") == "neutral"


def test_top_jobs_badge_text() -> None:
    assert top_jobs_badge_text(running=0, failed=0) == ("Jobs: idle", "neutral")
    assert top_jobs_badge_text(running=3, failed=0) == ("Jobs: 3 running", "warning")
    assert top_jobs_badge_text(running=2, failed=1) == ("Jobs: 2 running, 1 failed", "danger")


def test_build_job_rows_shapes_values() -> None:
    jobs = [
        SimpleNamespace(id=12, type="crawl", progress_pct=44.9, status="running", project_id=5),
        SimpleNamespace(id=13, type="audit", progress_pct=100.0, status="completed", project_id=5),
    ]
    rows = build_job_rows(jobs)
    assert len(rows) == 2
    assert rows[0].job_id == "12"
    assert rows[0].progress_pct == "45"
    assert rows[0].status_variant == "warning"
    assert rows[1].status_variant == "success"
