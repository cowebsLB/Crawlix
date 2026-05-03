# Known limitations

This document lists **intentional MVP gaps** and **deferred** items so expectations stay aligned with the codebase. The authoritative feature matrix remains the product plan under `.cursor/plans/`.

## Security and storage

- **SQLite is not encrypted at rest** in this repository path. **SQLCipher** (or equivalent) is specified for production hardening; see [SECURITY.md](../SECURITY.md) and the product plan until it lands.
- **Master password** unlocks the local database UI; recovery is **backup-only** if the password is lost.

## Desktop and licensing

- **PyQt6** is used under its license terms. Shipping binaries may require a **commercial Qt license** or migrating the UI to **PySide6 (LGPL)**. See [SECURITY.md](../SECURITY.md) and [README.md](../README.md).

## Crawl and network

- Crawl scope, cancel semantics, and disk caps are **MVP-level**; very large sites may need future caps, resumability, and storage policies from the roadmap.
- **robots.txt** and **politeness** defaults are conservative; aggressive presets are opt-in and still subject to remote site policy and law.

## SERP and third parties

- The bundled **SERP snapshot** path is a **demo-style** HTML fetch and parser. Production use should prefer **official APIs** where available; automated scraping may violate terms of service. Responsibility stays with the operator ([README.md](../README.md)).

## UI shell

- The **menu bar** is intentionally minimal today (e.g. File → Exit, Help → Check for updates). Additional menus from the design spec are phased in via [roadmap-phases.md](roadmap-phases.md).
- **Screenshots** in [docs/ui/overview.md](ui/overview.md) are not yet attached.

## Features “next” or stubbed

- **Citations matrix** job wiring and UI beyond YAML seed / placeholders — see in-app Citations copy and [citation-placeholders.md](citation-placeholders.md).
- **Local / GBP** depth — see [local-pack-roadmap.md](local-pack-roadmap.md).
- **Integrations** (GSC, GA4, etc.) — placeholder cards only.
- **Rank history** tab uses a **sample** chart until real ranking rows drive the plot.

## Architecture debt (acceptable for MVP)

- Some **session / query usage** still lives in `MainWindow` for speed of iteration. As features grow, prefer **thin presenters** + service facades so widgets stay free of raw SQL ([architecture.md](architecture.md)).
