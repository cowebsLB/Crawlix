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

## Iteration — same day (keywords / SERP / rank + housekeeping)

- **Standing preference (user):** keep **committing and pushing** after substantive iterations, and **append this worklog** each time so the paper trail stays on one dated file (`WorkLog-3-5-2026.md`) until the calendar day changes.
- **J6–J7 (UI):** **Keywords** tab — table of project keywords (id, phrase, locale, device, archived) + **Refresh** + refresh after add. **SERP snapshots** tab — **keyword picker** (`QComboBox`), **Refresh lists**, history table (snapshot id, keyword, fetched time, status, organic row count), validation that the selected keyword belongs to the current project and is not archived. **Rank history** tab — Matplotlib chart rebuilt from **organic URL counts per SERP snapshot** (oldest→newest index), empty-state copy when no data; **Refresh chart** button; chart colors follow theme and **rebuild on theme save** and **after successful SERP job**.
- **Docs:** [`docs/user-guide/journeys.md`](user-guide/journeys.md) — restored full **J1–J14** rows in the master table; removed duplicate/misplaced rows under the J1–J5 map; added **J6–J7 in the current app** mapping.

## Iteration — J8 citations UI

- **Citations page:** Tabbed UI — **built-in sources** table + refresh + CSV export of templates; **locations** for current project; **citation check** history (up to 500 rows) with joins. **`seed_builtin_sources`** also runs after **unlock** so older DB files get YAML-backed rows without wiping data.
- **Local page:** Expanded placeholder copy — checklist direction and pointer to `docs/local-pack-roadmap.md`.
- **Tests:** `export_builtin_citation_sources_csv` covered in `tests/unit/test_exporters.py`.
- **Docs:** [`docs/user-guide/journeys.md`](user-guide/journeys.md) — **J8 in the current app**; [`docs/changelog.md`](changelog.md); [`docs/architecture.md`](architecture.md) / [`docs/ui/overview.md`](ui/overview.md) aligned with citations export.

## Iteration — citation matrix job (J8)

- **`CitationMatrixWorker`** (`src/crawlix/workers/citation_worker.py`): `Job.type == "citation"`; Cartesian product of project **locations** × enabled **built-in** `citation_sources`; **`expand_template`**; **`httpx`** + **`GlobalOutboundLimiter`**; **`CitationCheck`** rows (OK / error / skipped); **Nominatim** ~1.1s spacing; gzip bodies ≤120KB; **cancel** between cells.
- **UI:** **Run citation matrix (HTTP)…** on Citations page, progress + status, confirmation dialog with counts; **`JobBus`** wired like SERP; completion summary (OK / errors / Playwright skipped).
- **Tests:** `tests/unit/test_citation_placeholders.py` for template expansion.

### Bundled same commit (crawl / audit)

- **`pages.crawl_depth`**, Alembic migration, BFS + Crawl UI max depth, CSV export column, **`robots_check`**, **`site_audit`** inbound/outbound counts on Crawl and Audit tables, audit worker robots batching; tests `test_site_audit.py`.

## Iteration — CI (Ruff) green

- **GitHub Actions:** Latest **`CI`** runs on `main` failed the **Ruff** step (E501 line length, I001 import order). Fixed by wrapping long strings / dicts, splitting **`site_audit`** import in **`audit_worker`**, **`ruff check --fix`** on **`audit_worker`**, and **`analyzer` → `citations`** import order in **`main_window`**.

## Iteration — J7 real rankings

- **`ranking_from_serp`:** hostname / subdomain match to **`projects.default_domain`**, DuckDuckGo **`uddg=`** unwrap, **`compute_rank_for_project_domain`**.
- **`fetch_serp_placeholder`:** after **`SerpResult`** flush, inserts **`Ranking`** (`serp_result_id`, `position` or null, `degraded` when organic rows exist but no domain match).
- **UI:** **Rank history** keyword **`QComboBox`** (kept in sync with SERP keyword combos via **`_refresh_serp_keyword_combo`**); chart uses **`rankings`** ordered by **`tracked_at`**, **`invert_yaxis`**, **`math.nan`** for misses; **`_refresh_serp_tab_lists`** ends with chart rebuild.
- **Tests:** `tests/unit/test_ranking_from_serp.py`.

## Next steps

- Per-journey chapters under `docs/user-guide/` (see [`journeys.md`](user-guide/journeys.md) “Doc chapters”) as flows stabilize.
- Screenshots in [`docs/ui/overview.md`](ui/overview.md) when the visual design is frozen.
- Optional root `CHANGELOG.md` mirroring `docs/changelog.md` if you want GitHub Releases to pick it up automatically.
- **J7 depth:** multi-property / competitor URLs; manual rank override; export rank CSV.
- **J8 depth:** optional **NAP diff** vs crawled page; **Playwright** path for `requires_playwright` sources when policy allows.
