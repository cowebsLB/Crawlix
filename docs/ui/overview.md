# Crawlix UI overview

## Shell

- **Menu bar (MVP):** **File** → Exit; **View** → **Job dock** (show/hide); **Help** → Check for updates (additional menus from the spec are phased in via the roadmap).
- **Top bar:** **Project** combobox (required) — all job-backed actions use the selected project.
- **Sidebar:** Dashboard → Crawl → Audit → Keywords / SERP → Citations → Local → Integrations → Reports → Settings — each row uses **vector icons** (QPainter, theme **window text** color); matching **SVG sources** ship under `src/crawlix/resources/icons/` for design tweaks and packaging. The **menu** icon on the button above the list **collapses** the rail to icon-only (narrow) or **expands** it to icons + labels. State is persisted in `QSettings`. Loader: `crawlix.ui.svg_icons`.
- **Scroll vs. inputs:** Mouse wheel does **not** change **spin boxes** or **combo boxes** (application event filter) so scrolling a page does not bump filters or crawl depth.
- **Crawl layout:** The **pages table** and **Page details** pane use a horizontal splitter with a **wider details** default (~46% width, **min 400px** for the pane), persisted as `ui/crawl_lr_split`.
- **Content:** `QStackedWidget` — each stacked page body is wrapped in a **`QScrollArea`** (via `wrap_page_content`) so tall modules scroll; plain-text **title** + optional subtitle (no HTML headings in labels, for theme-safe contrast).
- **Job dock (bottom):** tabs **Jobs** (table: id, type, %, status, project) | **Log** (timestamped lines). **Hide / Show** next to the dock title (and **View → Job dock**) toggles the panel and gives vertical space back to the main splitter; last dock height is remembered when you show it again.
- **Inline progress:** **Crawl**, **Audit**, and **Keywords → SERP** show a **progress bar** and status text while the matching job runs; **Reports** export shows an indeterminate bar; **Check for updates** shows status text in the **status bar**.
- **Keywords stack:** **Keywords** tab lists phrases; **SERP snapshots** tab has a keyword picker, history table, and run button; **Rank history** has its own keyword picker and plots **`rankings`** position (vs project default domain) over snapshots.
- **Citations page:** tabbed **built-in sources** (YAML-seeded templates), **locations** for the project, **citation check** history; refresh + export built-in sources to CSV; **Run citation matrix (HTTP)** with inline progress (job type `citation`, cancellable from the job dock).
- **Status bar:** politeness preset label (and transient messages during update check).

## Dashboard & inspector (May 2026 stream)

- **Dashboard** emphasizes **next actions**, **needs attention**, and **recent outcomes**, backed by **`dashboard_action_hub`** and taxonomy-aware **`insights`** (see [dashboard-action-model.md](dashboard-action-model.md), [issue-taxonomy-and-priority.md](issue-taxonomy-and-priority.md)).
- **Audit**, **Crawl**, **SERP snapshots**, and **Citations** use a shared **table + inspector** split where applicable (**`page_sections.table_with_inspector_split`**); **saved views** persist key tab/search context (**`saved_views`**).
- **Design tokens** and **interaction contracts** are documented in [design-tokens.md](design-tokens.md) and [interaction-contracts.md](interaction-contracts.md).

## Theming

Dark/light **Fusion** + QSS on the whole application, persisted in settings. See [theme-and-progress.md](theme-and-progress.md).

## Screenshots

Add screenshots when the stable skin ships; link from `README.md` and this page.
