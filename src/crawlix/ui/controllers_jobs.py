"""Job center helpers for table rows and top-strip status text."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class JobRowView:
    job_id: str
    job_type: str
    progress_pct: str
    status_text: str
    project_id: str
    status_variant: str


def job_status_variant(status: str) -> str:
    s = status.lower()
    if s in {"completed", "done", "success"}:
        return "success"
    if s in {"failed", "error", "cancelled"}:
        return "danger"
    if s in {"queued", "running"}:
        return "warning"
    return "neutral"


def top_jobs_badge_text(*, running: int, failed: int) -> tuple[str, str]:
    if running == 0 and failed == 0:
        return ("Jobs: idle", "neutral")
    if failed:
        return (f"Jobs: {running} running, {failed} failed", "danger")
    return (f"Jobs: {running} running", "warning")


def build_job_rows(jobs: Iterable[object]) -> list[JobRowView]:
    rows: list[JobRowView] = []
    for j in jobs:
        status = str(getattr(j, "status", "") or "")
        rows.append(
            JobRowView(
                job_id=str(getattr(j, "id", "")),
                job_type=str(getattr(j, "type", "")),
                progress_pct=f"{float(getattr(j, 'progress_pct', 0.0)):.0f}",
                status_text=status,
                project_id=str(getattr(j, "project_id", "")),
                status_variant=job_status_variant(status),
            )
        )
    return rows
