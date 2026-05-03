# Worklog — 3 May 2026

## Tasks completed

- **Documentation hub:** Filled root [`INDEX.md`](../INDEX.md) with project overview, feature list, tech stack, setup pointers, and a complete map of all repository docs (including this worklog).
- **Worklog discipline:** Established this dated worklog entry for the session’s deliverables.
- **New docs:** Added [`docs/setup.md`](setup.md), [`docs/known-limitations.md`](known-limitations.md), [`docs/ui/theme-and-progress.md`](ui/theme-and-progress.md), and [`docs/changelog.md`](changelog.md) to cover setup, honest scope limits, UI theming/job progress behavior, and a lightweight changelog.
- **Doc maintenance:** Updated [`docs/architecture.md`](architecture.md) (workers, progress, SERP task path) and [`docs/ui/overview.md`](ui/overview.md) (shell and progress UX aligned with the current app). Updated [`README.md`](../README.md) to link `INDEX.md` and correct the run command to `python -m crawlix`.

### Earlier same-day / cumulative product work (reflected in codebase)

- **UI contrast and theming:** Application-wide **Fusion** style + **QSS** on `QApplication` before the main window so wizard, dialogs, and shell share one theme; expanded dark/light stylesheets for inputs, wizards, tables, and message boxes; replaced HTML heading labels with plain-text headers to avoid unreadable rich-text colors; wizard **Classic** style and unlock dialog sizing on Windows; theme persisted via settings + `QSettings` sync; rank chart colors follow dark/light.
- **HTTP client teardown:** Replaced incorrect **`httpx.Client.aclose()`** with **`close()`** in crawl worker, audit worker, and proxy manager (sync API).
- **Job progress UX:** **`JobBus`** extended with **`task_*`** signals for short UI tasks; **BFS crawl** reports progress via an optional callback; **CrawlWorker** emits starting/progress/finished; per-page **progress bars** and status text on **Crawl**, **Audit**, and **Keywords → SERP**; **SERP** moved to **`SerpWorker`** with a real **`Job`** row; **Reports** export and **Help → Check for updates** run on the thread pool with visible progress (status bar + indeterminate bar).
- **QSS:** Added **`QProgressBar`** styling in dark and light themes.

## Problems encountered

- **Readable UI on Windows:** Native wizard chrome mixed with partial styling caused low contrast (e.g. title bar text, password fields). Addressed by centralizing theme on the application and explicit QSS for common widgets.
- **`httpx` API mismatch:** `aclose` exists on async clients only; synchronous **`Client`** requires **`close()`**, which surfaced at crawl worker shutdown.

## Decisions made

- **INDEX at repo root** (`INDEX.md`) is the canonical **documentation map**; `README.md` stays the short public-facing intro and links into `INDEX.md` for depth.
- **SERP and light tasks** use a **`serp` job type** plus **`SimpleTaskWorker`** for non-persisted tasks (export, updates) so the UI stays responsive without blocking the Qt event loop.
- **Changelog** lives under **`docs/changelog.md`** for now (no separate root `CHANGELOG.md` unless release automation requires it).

## Next steps

- Per-journey chapters under `docs/user-guide/` (see [`journeys.md`](user-guide/journeys.md) “Doc chapters”) as flows stabilize.
- Screenshots in [`docs/ui/overview.md`](ui/overview.md) when the visual design is frozen.
- Optional root `CHANGELOG.md` mirroring `docs/changelog.md` if you want GitHub Releases to pick it up automatically.
