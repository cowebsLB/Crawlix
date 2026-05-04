# Crawlix UI overview

## Shell

- **Menu bar (MVP):** **File** → Exit; **Help** → Check for updates (additional menus from the spec are phased in via the roadmap).
- **Top bar:** **Project** combobox (required) — all job-backed actions use the selected project.
- **Sidebar:** Dashboard → Crawl → Audit → Keywords & SERP → Citations → Local → Integrations → Reports → Settings.
- **Content:** `QStackedWidget` — each page uses a **plain-text title** + optional subtitle (no HTML headings in labels, for theme-safe contrast).
- **Job dock (bottom):** tabs **Jobs** (table: id, type, %, status, project) | **Log** (timestamped lines).
- **Inline progress:** **Crawl**, **Audit**, and **Keywords → SERP** show a **progress bar** and status text while the matching job runs; **Reports** export shows an indeterminate bar; **Check for updates** shows status text in the **status bar**.
- **Keywords stack:** **Keywords** tab lists phrases; **SERP snapshots** tab has a keyword picker, history table, and run button; **Rank history** has its own keyword picker and plots **`rankings`** position (vs project default domain) over snapshots.
- **Citations page:** tabbed **built-in sources** (YAML-seeded templates), **locations** for the project, **citation check** history; refresh + export built-in sources to CSV; **Run citation matrix (HTTP)** with inline progress (job type `citation`, cancellable from the job dock).
- **Status bar:** politeness preset label (and transient messages during update check).

## Theming

Dark/light **Fusion** + QSS on the whole application, persisted in settings. See [theme-and-progress.md](theme-and-progress.md).

## Screenshots

Add screenshots when the stable skin ships; link from `README.md` and this page.
