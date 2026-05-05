# Changelog

All notable changes to this project are documented in this file. Format follows a lightweight [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) style.

## [Unreleased]

### Added

- **Crawl snapshots:** Tables **`crawl_snapshots`** / **`crawl_snapshot_pages`** (Alembic **`d4f8a2c1b0e3`**); BFS persists a snapshot after a completed crawl; services **`crawl_overview`**, **`crawl_snapshots`** (diff + formatting) support Crawl/Dashboard insights. Tests: `tests/unit/test_crawl_overview.py`, `tests/unit/test_crawl_snapshots.py`.
- **Keyword targeting & templates:** **`projects.seo_context_json`** (Alembic **`e5a1c2d3b4f0`**) stores **`site_type`**, **`primary_country_code`**, **`brand_name`**, **`primary_topic`** (+ reserved **`language`**). **Keywords** tab — save targeting, generate phrase suggestions from site-type packs (merge with first **Location** + project defaults), add checked rows as **`keywords`** with **`tags_json`** marking template source. Service: **`crawlix.services.keywords.templates`**. Tests: **`tests/unit/test_keyword_templates.py`**. Docs: [keywords-targeting-and-templates.md](keywords-targeting-and-templates.md).
- **Citations (J8):** **Citations** page — built-in sources (YAML → DB), **locations (NAP)**, **check history**; **Export built-in sources CSV**; **Run citation matrix** (`Job.type == citation`, **`CitationMatrixWorker`**). Unlock runs **`seed_builtin_sources`** for older DBs.
- **Crawl / audit depth:** Optional **`crawl_depth`** on **`pages`** (Alembic **`c7e2a1b4f9d0`**); BFS depth; Crawl **max depth** UI; **`robots_check`** / **`site_audit`** link counts on Crawl and Audit tables.
- **Keywords / SERP / rank (J6–J7):** **`ranking_from_serp`** persists **`rankings`**; **Rank history** plots **`rankings.position`** (shared keyword combos with SERP).
- **Dashboard & inspector milestone (May 2026):** **`dashboard_action_hub`**, taxonomy-backed **`services.analyzer.insights`**, **`inspector_presenter`**, **`saved_views`** (persisted Crawl/SERP/Citations context); reusable **`InspectorPanel`** / **`ActionListPanel`**, **`inspector_logic`**, **`page_sections.table_with_inspector_split`**; UI controllers **`controllers_dashboard`**, **`controllers_inspector`**, **`controllers_inspector_secondary`**, **`controllers_crawl`**, **`controllers_actions`**, **`controllers_audit`**, **`controllers_serp`**, **`controllers_citations`**. Process docs: [design-tokens.md](ui/design-tokens.md), [interaction-contracts.md](ui/interaction-contracts.md), [dashboard-action-model.md](ui/dashboard-action-model.md), [issue-taxonomy-and-priority.md](ui/issue-taxonomy-and-priority.md), [milestone-checklists.md](ui/milestone-checklists.md).
- **Navigation assets:** Vector-drawn sidebar icons (**`svg_icons`**); **`src/crawlix/resources/icons/*.svg`** packaged via setuptools **`package-data`**.
- **Docs hub:** root **[INDEX.md](../INDEX.md)**; **[docs/setup.md](setup.md)**; **[docs/known-limitations.md](known-limitations.md)**; **[docs/ui/theme-and-progress.md](docs/ui/theme-and-progress.md)**; worklogs **[WorkLog-4-5-2026.md](WorkLog-4-5-2026.md)** / **[WorkLog-3-5-2026.md](WorkLog-3-5-2026.md)**.
- **`JobBus`** **`task_*`** signals; **`SerpWorker`**; **`SimpleTaskWorker`**; **`run_crawl_job(..., on_progress=...)`** crawl progress callback.

### Changed

- **Shell UX:** Stacked pages wrapped in **`QScrollArea`** (**`wrap_page_content`**); **collapsible sidebar** ( **`QSettings`** **`ui/nav_collapsed`** ); **togglable job dock** (**View → Job dock**, **`ui/job_dock_hidden`**, **`ui/job_dock_last_height`**).
- **Crawl layout:** Horizontal splitter defaults (**`ui/crawl_lr_split`**), wider **Page details** pane.
- **Inputs:** Application **`wheel_guard`** blocks mouse-wheel from changing **`QSpinBox`** / **`QComboBox`** values while scrolling.
- **Theme:** Fusion + QSS on **`QApplication`** before windows; refreshed **`app_dark.qss`** / **`app_light.qss`** toward design-token semantics.
- **README** documents **`python -m crawlix`** and links **INDEX.md**.

### Fixed

- **CI (Ruff):** Line length / import order on audited modules so **`ruff check src tests`** passes on Actions.
- **CI (Ubuntu):** Removed unused **`pytest-qt`** from dev deps so headless runners do not load the Qt GUI plugin.
- **`httpx.Client` lifecycle:** synchronous clients use **`close()`**, not **`aclose()`** (crawl, audit, proxy manager).
- **Tests (Windows / Qt):** **`test_svg_icons`** checks the raster API is exposed without building a headless **`QIcon`** (some **Python 3.14** + **PyQt6** + **Windows** combinations crash in **`QPixmap`** paths). When **pytest-qt** is present, **`qt_api = pyqt6`** in **`pyproject.toml`** keeps the Qt binding aligned with the app. See [known-limitations.md](known-limitations.md).
