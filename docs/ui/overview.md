# Crawlix UI overview

## Shell

- **Menu bar (MVP):** **File** → Exit; **Help** → Check for updates (additional menus from the spec are phased in via the roadmap).
- **Top bar:** **Project** combobox (required) — all job-backed actions use the selected project.
- **Sidebar:** Dashboard → Crawl → Audit → Keywords & SERP → Citations → Local → Integrations → Reports → Settings.
- **Content:** `QStackedWidget` — each page uses a **plain-text title** + optional subtitle (no HTML headings in labels, for theme-safe contrast).
- **Job dock (bottom):** tabs **Jobs** (table: id, type, %, status, project) | **Log** (timestamped lines).
- **Inline progress:** **Crawl**, **Audit**, and **Keywords → SERP** show a **progress bar** and status text while the matching job runs; **Reports** export shows an indeterminate bar; **Check for updates** shows status text in the **status bar**.
- **Keywords stack:** **Keywords** tab lists phrases in a table; **SERP snapshots** tab has a keyword picker, snapshot history table, and run button; **Rank history** plots SERP-derived activity (organic row counts) until real `rankings` data exists.
- **Citations page:** tabbed **built-in sources** (YAML-seeded templates), **locations** for the project, **citation check** history; refresh + export built-in sources to CSV.
- **Status bar:** politeness preset label (and transient messages during update check).

## Theming

Dark/light **Fusion** + QSS on the whole application, persisted in settings. See [theme-and-progress.md](theme-and-progress.md).

## Screenshots

Add screenshots when the stable skin ships; link from `README.md` and this page.
