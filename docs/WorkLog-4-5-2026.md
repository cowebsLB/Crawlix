# Worklog — 4 May 2026

**Standing preference:** keep **committing and pushing** after substantive iterations, and **append the dated worklog** for each calendar day (this file for **4 May**; full detail for **3 May** remains in [`WorkLog-3-5-2026.md`](WorkLog-3-5-2026.md)).

---

## Carried from 3 May 2026 ([`WorkLog-3-5-2026.md`](WorkLog-3-5-2026.md))

Use the linked file for verbatim bullets and full context. Summary of what landed **3 May** (and is still authoritative there):

- **Docs hub:** [`INDEX.md`](../INDEX.md), [`docs/setup.md`](setup.md), [`docs/known-limitations.md`](known-limitations.md), [`docs/ui/theme-and-progress.md`](ui/theme-and-progress.md), [`docs/changelog.md`](changelog.md); [`README.md`](../README.md) + architecture / UI overview updates.
- **Theming & UX:** Fusion + QSS on `QApplication`, plain-text page headers, job progress on Crawl / Audit / SERP, `JobBus` `task_*` signals, `httpx` sync `close()` fix.
- **J1–J5:** Wizard, unlock, new project + slug, crawl/audit tables, CSV exports, job cancel, dashboard stats.
- **J6–J7 (first pass):** Keywords + SERP tabs, snapshot history; **Rank** tab initially charted **organic row counts** per snapshot (proxy).
- **J8 citations (UI):** Built-in sources / locations / check history tabs, CSV export, `seed_builtin_sources` on unlock.
- **Tests:** slug, exporters, citation placeholders (as added on those days).

Anything above is **not duplicated** here line-for-line; open **3 May** worklog for the full paper trail.

---

## Tasks completed (4 May 2026)

### Citation matrix + crawl / audit depth (same delivery)

- **`CitationMatrixWorker`:** `Job.type == "citation"`; locations × built-in `citation_sources`; `expand_template` + `httpx` + `GlobalOutboundLimiter`; `CitationCheck` rows; Nominatim pacing; gzip small bodies; cancel between cells.
- **Citations UI:** **Run citation matrix (HTTP)…**, progress/status, confirm dialog, `JobBus` wiring, completion counts.
- **`pages.crawl_depth`:** model + Alembic `c7e2a1b4f9d0`, BFS + Crawl **max depth** UI, pages CSV column, `robots_check`, `site_audit` link counts on Crawl/Audit tables, audit worker robots batching; `test_site_audit.py`.

### CI (Ruff)

- **GitHub Actions:** CI failed **Ruff** (E501, I001). Fixed long lines / import order in `audit.py`, `site_audit.py`, `main_window.py`, `audit_worker.py`, `test_audit.py`; `ruff check` green on `main`.

### J7 — real rankings

- **`ranking_from_serp`:** project **`default_domain`** vs organic URL host (subdomains), DuckDuckGo **`uddg=`** unwrap.
- **`fetch_serp_placeholder`:** persists **`Ranking`** per snapshot (`serp_result_id`, `position` or null, `degraded` when organics exist but no match).
- **Rank history UI:** keyword combo synced with SERP combos; Matplotlib plots **`rankings.position`**, inverted Y, `math.nan` gaps; `_refresh_serp_tab_lists` drives chart refresh.
- **Tests:** `tests/unit/test_ranking_from_serp.py`.

### Documentation touched this day

- [`docs/user-guide/journeys.md`](user-guide/journeys.md) (J7/J8 rows, master table), [`docs/changelog.md`](changelog.md), [`docs/architecture.md`](architecture.md), [`docs/ui/overview.md`](ui/overview.md), and iteration notes that were appended on **3 May** file for J7 — **canonical narrative for 4 May** is this file for the bullets above; changelog/journeys reflect shipped behavior.

### Keyword targeting & templates + doc pass

- **Product:** `projects.seo_context_json` (Alembic `e5a1c2d3b4f0`) — `site_type`, `primary_country_code`, `brand_name`, `primary_topic`, default `language`; merge with first **Location** and project name/domain in `crawlix.services.keywords.templates`. **Keywords** tab: save targeting, generate suggestions, add checked phrases as `Keyword` rows with `tags_json` (`source: template`, `site_type`).
- **Quality:** `tests/unit/test_keyword_templates.py`; Ruff clean on touched modules (`_pack_local` unused locals removed).
- **Docs:** New [`docs/keywords-targeting-and-templates.md`](keywords-targeting-and-templates.md); [`INDEX.md`](../INDEX.md) feature line + doc map; [`docs/changelog.md`](changelog.md); [`docs/user-guide/journeys.md`](user-guide/journeys.md) J6 row; [`docs/architecture.md`](architecture.md) UI row.

---

## Problems encountered

- **CI Ruff:** line length and import-order failures on Windows/Ubuntu matrix until wrapped / isort-aligned.
- **Ranking UX:** older SERP snapshots have no **`rankings`** rows until a new snapshot is run after this release (documented in UI copy and journeys).

## Decisions made

- **Worklog split by calendar day:** **3 May** = [`WorkLog-3-5-2026.md`](WorkLog-3-5-2026.md); **4 May** = this file; cross-link at top of each.
- **J7 v1:** one **`Ranking`** per SERP snapshot; domain = **`projects.default_domain`** only (multi-domain / competitors deferred to “J7 depth” in Next steps).

## Next steps

- Per-journey chapters under `docs/user-guide/` (see [`journeys.md`](user-guide/journeys.md)).
- Screenshots in [`docs/ui/overview.md`](ui/overview.md) when the UI is stable.
- **J7 depth:** extra match domains, manual override, rank CSV export.
- **J8 depth:** NAP vs crawl diff; Playwright for `requires_playwright` citation sources.
- Optional: bump GitHub Actions (`checkout` / `setup-python`) when addressing Node 20 deprecation warnings.

### UI/UX rework implementation (5 May 2026, milestone stream)

- **Visual personality + foundations:** updated app light/dark QSS toward the new signature (calm neutral surfaces, sharper action accent), and documented the token/interaction model in:
  - `docs/ui/design-tokens.md`
  - `docs/ui/interaction-contracts.md`
  - `docs/ui/issue-taxonomy-and-priority.md`
  - `docs/ui/dashboard-action-model.md`
  - `docs/ui/milestone-checklists.md`

- **Issue intelligence foundation:** added `crawlix.services.analyzer.insights` with canonical taxonomy mapping, `InspectorInsight` contract, confidence derivation, and explicit **severity != priority** scoring.

- **Dashboard action hub:** added `crawlix.services.dashboard_action_hub` and rewired Dashboard into an action-first model (`next actions`, `needs attention`, `recent outcomes`) with task routing hooks.

- **Saved views:** added `crawlix.ui.saved_views` and integrated persisted view behavior for Crawl, SERP keyword/rank state, and Citations tab context.

- **Inspector differentiator rollout:**
  - Audit: persistent right inspector with prioritized insights.
  - Crawl: contextual pseudo-issues + recommendations in details panel.
  - SERP snapshots: persistent inspector with context/risk hints.
  - Citations check history: persistent inspector with status/HTTP risk interpretation.

- **Refactor increments (MainWindow de-risking):**
  - Added reusable components in `crawlix.ui.components` (`InspectorPanel`, `ActionListPanel`).
  - Added shared split helper in `crawlix.ui.page_sections`.
  - Extracted pure inspector decision helpers to `crawlix.ui.inspector_logic`.
  - Extracted UI controller helpers:
    - `crawlix.ui.controllers_dashboard`
    - `crawlix.ui.controllers_inspector`

- **Tests added/updated:**
  - `tests/unit/test_insights_taxonomy.py`
  - `tests/unit/test_saved_views.py`
  - `tests/unit/test_inspector_logic.py`
  - `tests/unit/test_dashboard_controller.py`
  - `tests/unit/test_inspector_controller.py`

- **Validation:** repeated compile + unit-test runs for new modules and touched flows passed (noting known environment-level pytest process exit artifact seen previously in this workstation).

- **Docs/architecture/changelog updates:** appended architecture/changelog entries after each implementation batch to keep the paper trail current with refactor boundaries.

### UI refactor task batch (5 May 2026, follow-up)

- Extracted secondary inspector text builders to `crawlix.ui.controllers_inspector_secondary`:
  - SERP snapshot inspector composition
  - Citation check inspector composition
- Rewired `MainWindow` to consume controller outputs instead of composing SERP/Citation inspector text inline.
- Kept Crawl pseudo-issue logic in `ui/inspector_logic` and reduced inline UI decision code in `MainWindow`.
- Added unit coverage in `tests/unit/test_inspector_secondary_controller.py`.
- Validation for this batch: compile + targeted inspector/controller tests passed.

### UI refactor task batch (5 May 2026, crawl controller extraction)

- Added `crawlix.ui.controllers_crawl` to centralize crawl detail/inspector text composition.
- Rewired `MainWindow._update_crawl_detail_panel` to use controller output instead of inline pseudo-issue and insight assembly.
- Removed now-redundant direct insight/presenter imports from `MainWindow` for crawl details.
- Added unit coverage in `tests/unit/test_crawl_controller.py`.
- Validation for this batch: compile + targeted crawl/inspector tests passed.

### UI refactor task batch (5 May 2026, dashboard action routing extraction)

- Added `crawlix.ui.controllers_actions` with normalized dashboard target routing (`resolve_dashboard_action`).
- Rewired `MainWindow._run_selected_dashboard_action` to use controller routes instead of inline target parsing.
- Added unit coverage in `tests/unit/test_actions_controller.py`.
- Validation for this batch: compile + controller tests passed.

### UI refactor task batch (5 May 2026, audit controller extraction)

- Added `crawlix.ui.controllers_audit` for audit row-meta assembly and issue-count normalization.
- Rewired audit table refresh in `MainWindow` to use controller helpers (`build_audit_row_meta`, `issue_count`).
- Added unit coverage in `tests/unit/test_audit_controller.py`.
- Validation for this batch: compile + audit/controller tests passed.

### UI refactor task batch (5 May 2026, SERP controller extraction)

- Added `crawlix.ui.controllers_serp` for SERP organic-row counting and snapshot row-meta shaping.
- Rewired SERP snapshot table refresh in `MainWindow` to use controller helpers (`serp_organic_count`, `build_serp_row_meta`).
- Added unit coverage in `tests/unit/test_serp_controller.py`.
- Validation for this batch: compile + SERP/inspector/dashboard controller tests passed.

### UI refactor task batch (5 May 2026, citations controller extraction)

- Added `crawlix.ui.controllers_citations` for URL/error clipping and citation check row-meta shaping.
- Rewired citation check history refresh in `MainWindow` to use controller helpers (`clipped_url`, `clipped_error`, `build_citation_check_row_meta`).
- Added unit coverage in `tests/unit/test_citations_controller.py`.
- Validation for this batch: compile + citations/inspector/audit-controller tests passed.

### Documentation sync (commit to `main`)

- **INDEX.md** — features + documentation map for **design tokens**, **interaction contracts**, **dashboard action model**, **issue taxonomy**, **milestone checklists**; crawl snapshots / dashboard / inspector called out in features.
- **docs/changelog.md** — consolidated **`[Unreleased]`** (Added / Changed / Fixed) for snapshots, keyword targeting, inspector milestone, shell UX, theme, CI.
- **docs/architecture.md** — fixed **`table_with_inspector_split`** reference; inspector/controller bullets unchanged in substance.
- **docs/known-limitations.md** — removed stale “sample rank chart” line; clarified **MainWindow** vs **controllers** debt.
- **docs/ui/overview.md** — Dashboard / inspector / saved-views subsection.
- **docs/user-guide/README.md** — links to UI process docs.
