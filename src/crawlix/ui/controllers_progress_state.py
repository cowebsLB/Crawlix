"""Progress-strip state resolution helpers."""

from __future__ import annotations

from collections.abc import Callable


def serp_progress_state_from_status(snapshot_status: str, tr: Callable[[str], str]) -> tuple[str, str]:
    status_l = str(snapshot_status or "").strip().lower()
    if status_l in {"degraded", "partial", "captcha", "empty", "blocked", "timeout"}:
        return ("degraded", tr("Completed with degraded data"))
    return ("success", tr("Completed"))


def citation_progress_state_from_summary(
    summary: dict[str, object], tr: Callable[[str], str]
) -> tuple[str, str]:
    if summary.get("cancelled"):
        return ("failure", tr("Cancelled"))
    http_err = int(summary.get("http_err", 0) or 0)
    skipped = int(summary.get("skipped_playwright", 0) or 0)
    if http_err > 0 or skipped > 0:
        return ("degraded", tr("Completed with warnings"))
    return ("success", tr("Completed"))
