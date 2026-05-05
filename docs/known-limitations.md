# Known limitations

This document lists **intentional MVP gaps** and **deferred** items so expectations stay aligned with the codebase. The authoritative feature matrix remains the product plan under `.cursor/plans/`.

## Security and storage

- **SQLite is not encrypted at rest** in this repository path. **SQLCipher** (or equivalent) is specified for production hardening; see [SECURITY.md](../SECURITY.md) and the product plan until it lands.
- **Master password** unlocks the local database UI; recovery is **backup-only** if the password is lost.

## Desktop and licensing

- **PyQt6** is used under its license terms. Shipping binaries may require a **commercial Qt license** or migrating the UI to **PySide6 (LGPL)**. See [SECURITY.md](../SECURITY.md) and [README.md](../README.md).
- On **Windows**, some **Python 3.14** builds with the current **PyQt6** wheels can hit **native crashes** in `QPixmap` raster paths (e.g. `fill`, `QPainter` on a pixmap, `QPixmap.fromImage`). The app and tests avoid relying on a headless `QIcon` raster round-trip in CI; if the desktop build misbehaves, try **Python 3.11–3.13** or a fresh **PyQt6** install until the stack stabilizes.

## Crawl and network

- Crawl scope, cancel semantics, and disk caps are **MVP-level**; very large sites may need future caps, resumability, and storage policies from the roadmap.
- **robots.txt** and **politeness** defaults are conservative; aggressive presets are opt-in and still subject to remote site policy and law.

## SERP and third parties

- The bundled **SERP snapshot** path is a **demo-style** HTML fetch and parser. Production use should prefer **official APIs** where available; automated scraping may violate terms of service. Responsibility stays with the operator ([README.md](../README.md)).

## UI shell

- The **menu bar** is intentionally minimal today (e.g. File → Exit, Help → Check for updates). Additional menus from the design spec are phased in via [roadmap-phases.md](roadmap-phases.md).
- **Screenshots** in [docs/ui/overview.md](ui/overview.md) are not yet attached.

## Features “next” or stubbed

- **Keyword template suggestions** — English packs only (`language` in `seo_context_json` is reserved); **New project** wizard does not set targeting yet (Keywords tab only); keyword table does not surface `tags_json` / “from template” in the grid. Detail: [keywords-targeting-and-templates.md](keywords-targeting-and-templates.md).
- **Citations matrix** job wiring and UI beyond YAML seed / placeholders — see in-app Citations copy and [citation-placeholders.md](citation-placeholders.md).
- **Local / GBP** depth — see [local-pack-roadmap.md](local-pack-roadmap.md).
- **Integrations** (GSC, GA4, etc.) — placeholder cards only.

## Architecture debt (acceptable for MVP)

- Some **session / query usage** still lives in `MainWindow` for coordination; presentation and row-meta shaping increasingly live in **`ui/controllers_*`** modules and **`inspector_*` helpers** ([architecture.md](architecture.md)). Prefer thin presenters + facades as new surfaces are added. **Next split targets** (bootstrap, shell, project context, page factories, job dock) are outlined in [next-refactors-and-risks.md](next-refactors-and-risks.md).
- **Internal link counts** default to the **latest completed crawl job** (`PageLink.job_id`). Pass **`crawl_job_id=…`** to `inbound_internal_counts` / `outbound_internal_counts` for a specific crawl. **`allow_private_ssrf`** only affects network fetch policy, not link math.
