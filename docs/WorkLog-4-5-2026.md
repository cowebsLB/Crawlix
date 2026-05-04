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
