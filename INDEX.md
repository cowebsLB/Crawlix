# Crawlix — Project Index

Local-first **desktop** SEO workstation: crawl, audit, keywords/SERP, citations/NAP, integrations (stubs), and reports — data stays in a **SQLite** database under a directory you control.

|                |                                                                                                                                                                                                                 |
|----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Repository** | [github.com/cowebsLB/Crawlix](https://github.com/cowebsLB/Crawlix)                                                                                                       |
| **License**    | MIT — see [LICENSE](LICENSE); **PyQt6** is GPL for distribution unless you use a commercial Qt license or switch to **PySide6** — see [SECURITY.md](SECURITY.md)         |
| **Version**    | `0.1.0` (see [pyproject.toml](pyproject.toml))                                                                                                                           |

---

## Features (Current Scope)

- First-run **wizard** (data directory, master password, politeness, disclaimers) and daily **unlock**
- **Projects** with SQLite + **Alembic** migrations
- **Crawl** (polite BFS, robots, queue, pages + gzipped HTML)
- **Audit** on crawled pages (scores + issues JSON)
- **Keywords** and **SERP** snapshot (demo fetch path; methodology and legal notes in README); **project targeting** (`seo_context_json`) drives **template keyword suggestions** by site type and country
- **Crawl snapshots** (per-crawl graph snapshots + diff/overview helpers) and **dashboard action hub** (next steps, attention surfaces)
- **Inspector / saved views** pattern on Dashboard, Crawl, Audit, SERP, and Citations (**persisted view state** where implemented)
- **Citations** (built-in YAML seed and placeholder docs)
- **Local**, **Integrations**, **Reports** (sample export), **Settings** (theme, politeness copy)
- **Job dock** (table + log), **inline progress** on long-running pages, **GitHub** update check

---

## Setup and Run

Short path: **[docs/setup.md](docs/setup.md)**  
Quick public blurb: **[README.md](README.md)**

```bash
pip install -e ".[dev]"
python -m crawlix
```

---

## Tech Stack

| Area                | Choice                                              |
|---------------------|----------------------------------------------------|
| UI                  | PyQt6, Matplotlib (Qt backend)                     |
| Persistence         | SQLAlchemy 2, SQLite, Alembic                      |
| HTTP / crawl        | httpx, selectolax                                  |
| Security / secrets  | Argon2 password hashing; TLS verification on by default |
| Quality             | pytest, ruff                                       |

---

## Documentation Map

### Getting Started

| Document                              | Purpose                                                      |
|----------------------------------------|--------------------------------------------------------------|
| [README.md](README.md)                 | Install, politeness table, legal note, tests, packaging pointer |
| [docs/setup.md](docs/setup.md)         | Dev install, run commands, first launch, data directory      |
| [CONTRIBUTING.md](CONTRIBUTING.md)     | Dev commands, migrations, i18n, PR checklist                 |
| [SECURITY.md](SECURITY.md)             | Threats, TLS, secrets, desktop distribution notes            |

### Architecture and Product

| Document                                       | Purpose                                                     |
|------------------------------------------------|-------------------------------------------------------------|
| [docs/architecture.md](docs/architecture.md)    | Layers, data flow, configuration                            |
| [docs/roadmap-phases.md](docs/roadmap-phases.md)| Phased delivery mirror (MVP through ship)                   |
| [docs/known-limitations.md](docs/known-limitations.md) | Honest scope gaps and deferred items                 |
| [docs/next-refactors-and-risks.md](docs/next-refactors-and-risks.md) | MainWindow split plan, SSRF/DNS, link counts, action hub v2 |
| [docs/changelog.md](docs/changelog.md)          | Notable changes (lightweight; expand at release time)        |

### User Experience

| Document                                              | Purpose                                   |
|------------------------------------------------------|-------------------------------------------|
| [docs/user-guide/README.md](docs/user-guide/README.md)| User guide index (journeys + planned chapters)|
| [docs/user-guide/journeys.md](docs/user-guide/journeys.md) | Journey catalog **J1–J14**             |
| [docs/ui/overview.md](docs/ui/overview.md)              | Shell layout, navigation, job dock    |
| [docs/ui/glossary.md](docs/ui/glossary.md)              | UI / i18n glossary                    |
| [docs/ui/theme-and-progress.md](docs/ui/theme-and-progress.md)| Themes, contrast, Fusion, job and task progress |
| [docs/ui/design-tokens.md](docs/ui/design-tokens.md)      | Color / density / motion semantics (signature UI) |
| [docs/ui/full-ui-redesign-backlog.md](docs/ui/full-ui-redesign-backlog.md)| Full UI redesign backlog (shell, tokens, pages, a11y) |
| [docs/ui/interaction-contracts.md](docs/ui/interaction-contracts.md)| Tables, inspector, actions — behavioral contracts |
| [docs/ui/dashboard-action-model.md](docs/ui/dashboard-action-model.md)| Dashboard action hub routing and priorities |
| [docs/ui/issue-taxonomy-and-priority.md](docs/ui/issue-taxonomy-and-priority.md)| Severity vs priority for insights |
| [docs/ui/milestone-checklists.md](docs/ui/milestone-checklists.md)| Milestone acceptance checklists         |

### Domain Modules

| Document                                                    | Purpose                                        |
|-------------------------------------------------------------|------------------------------------------------|
| [docs/citation-placeholders.md](docs/citation-placeholders.md) | Citation YAML placeholder rules             |
| [docs/local-pack-roadmap.md](docs/local-pack-roadmap.md)         | Local / GBP-oriented roadmap                 |
| [docs/keywords-targeting-and-templates.md](docs/keywords-targeting-and-templates.md) | Project targeting JSON, site-type packs, Keywords tab workflow |
| [docs/packaging.md](docs/packaging.md)                           | PyInstaller and cross-platform packaging notes|

### Operations

| Document                                               | Purpose                                              |
|--------------------------------------------------------|------------------------------------------------------|
| [docs/WorkLog-4-5-2026.md](docs/WorkLog-4-5-2026.md)   | Daily worklog — **4 May 2026** (current day file)    |
| [docs/WorkLog-3-5-2026.md](docs/WorkLog-3-5-2026.md)   | Daily worklog — 3 May 2026 (prior; linked from 4 May file)|

### Planning (Reference)

| Document                                                               | Purpose                                           |
|------------------------------------------------------------------------|---------------------------------------------------|
| [.cursor/plans/crawlix_pure_python_plan_ffdcc41d.plan.md](.cursor/plans/crawlix_pure_python_plan_ffdcc41d.plan.md) | Master product / technical plan (read-only spec) |
| [.cursor/plans/crawlix_ui_ux_shell_d5eb977f.plan.md](.cursor/plans/crawlix_ui_ux_shell_d5eb977f.plan.md)         | UI shell notes                                   |

---

## Repository Layout (High Level)

```plaintext
src/crawlix/          Application package (UI, workers, services, db)
alembic/              Database migrations
resources/            Default YAML (e.g. citation sources)
tests/                pytest suite
docs/                 All markdown documentation (this map)
```

---

## See Also

- **Tests:** `pytest tests/ -q`
- **Lint:** `ruff check src tests`
