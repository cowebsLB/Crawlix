from crawlix.ui.controllers_progress_state import (
    citation_progress_state_from_summary,
    serp_progress_state_from_status,
)


def test_serp_progress_state_degraded_statuses() -> None:
    for status in ("degraded", "partial", "captcha", "empty", "blocked", "timeout"):
        state, text = serp_progress_state_from_status(status, lambda x: x)
        assert state == "degraded"
        assert text == "Completed with degraded data"


def test_serp_progress_state_success_for_normal_status() -> None:
    state, text = serp_progress_state_from_status("ok", lambda x: x)
    assert state == "success"
    assert text == "Completed"


def test_citation_progress_state_cancelled_has_failure_state() -> None:
    state, text = citation_progress_state_from_summary({"cancelled": True}, lambda x: x)
    assert state == "failure"
    assert text == "Cancelled"


def test_citation_progress_state_degraded_when_errors_or_skips() -> None:
    state1, _ = citation_progress_state_from_summary({"http_err": 2, "skipped_playwright": 0}, lambda x: x)
    state2, _ = citation_progress_state_from_summary({"http_err": 0, "skipped_playwright": 4}, lambda x: x)
    assert state1 == "degraded"
    assert state2 == "degraded"
