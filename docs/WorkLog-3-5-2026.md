# Worklog — 3 May 2026

**Continued on:** [`WorkLog-4-5-2026.md`](WorkLog-4-5-2026.md) — work from **4 May 2026** onward is logged there (this file stays the full record for **3 May**).

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

## Iteration — same day (keywords / SERP / rank + housekeeping)

- **Standing preference (user):** keep **committing and pushing** after substantive iterations, and **append the dated worklog** each time; after **4 May** use [`WorkLog-4-5-2026.md`](WorkLog-4-5-2026.md) (see link at top of this file).
- **J6–J7 (UI):** **Keywords** tab — table of project keywords (id, phrase, locale, device, archived) + **Refresh** + refresh after add. **SERP snapshots** tab — **keyword picker** (`QComboBox`), **Refresh lists**, history table (snapshot id, keyword, fetched time, status, organic row count), validation that the selected keyword belongs to the current project and is not archived. **Rank history** tab — Matplotlib chart rebuilt from **organic URL counts per SERP snapshot** (oldest→newest index), empty-state copy when no data; **Refresh chart** button; chart colors follow theme and **rebuild on theme save** and **after successful SERP job**.
- **Docs:** [`docs/user-guide/journeys.md`](user-guide/journeys.md) — restored full **J1–J14** rows in the master table; removed duplicate/misplaced rows under the J1–J5 map; added **J6–J7 in the current app** mapping.

## Iteration — J8 citations UI

- **Citations page:** Tabbed UI — **built-in sources** table + refresh + CSV export of templates; **locations** for current project; **citation check** history (up to 500 rows) with joins. **`seed_builtin_sources`** also runs after **unlock** so older DB files get YAML-backed rows without wiping data.
- **Local page:** Expanded placeholder copy — checklist direction and pointer to `docs/local-pack-roadmap.md`.
- **Tests:** `export_builtin_citation_sources_csv` covered in `tests/unit/test_exporters.py`.
- **Docs:** [`docs/user-guide/journeys.md`](user-guide/journeys.md) — **J8 in the current app**; [`docs/changelog.md`](changelog.md); [`docs/architecture.md`](architecture.md) / [`docs/ui/overview.md`](ui/overview.md) aligned with citations export.

## Next steps (as of end of 3 May)

- Continued on **4 May** — see [`WorkLog-4-5-2026.md`](WorkLog-4-5-2026.md) for citation matrix, crawl depth / site audit bundle, CI Ruff fix, **J7 real rankings**, and updated next steps.
