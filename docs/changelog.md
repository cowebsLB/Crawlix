# Changelog

All notable changes to this project are documented in this file. Format follows a lightweight [Keep a Changelog](https://keepachangelog.com/) style.

## [Unreleased]

### Added

- Root **[INDEX.md](../INDEX.md)** as the documentation hub linking all docs.
- **[docs/setup.md](setup.md)** — install, run, migrations, first launch.
- **[docs/known-limitations.md](known-limitations.md)** — scope and deferred items.
- **[docs/ui/theme-and-progress.md](ui/theme-and-progress.md)** — theming and job progress behavior.
- **Daily worklog** — [WorkLog-3-5-2026.md](WorkLog-3-5-2026.md).
- **Inline job progress** — per-page progress bars and status text for Crawl, Audit, and SERP; indeterminate progress for Markdown export; status-bar text for “Check for updates”.
- **`JobBus` task signals** — `task_progress`, `task_finished`, `task_failed` for work that does not map to a persisted `Job` row (or for lightweight tasks).
- **`SerpWorker`** — background SERP snapshot with a `Job` row of type `serp`.
- **`SimpleTaskWorker`** — generic callable runner for export and update checks.
- **Crawl progress callbacks** — `run_crawl_job(..., on_progress=...)` for GUI-friendly percentage and status without coupling BFS to Qt.

### Fixed

- **`httpx.Client` lifecycle** — use **`close()`** instead of nonexistent **`aclose()`** on synchronous clients (crawl worker, audit worker, proxy manager).

### Changed

- **Application theme** — Fusion style + stylesheet applied on **`QApplication`** before windows are shown so setup wizard and dialogs match the main shell.
- **README** — documents `python -m crawlix` and links **INDEX.md**.
