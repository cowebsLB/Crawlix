# Next refactors and risks (engineering backlog)

Prioritized technical debt and hardening work identified after the dashboard / controller extraction milestone. This is **not** the phased product roadmap ([roadmap-phases.md](roadmap-phases.md)); it is **implementation leverage** and **correctness** follow-ups.

For the **full UI redesign** (shell, tokens, components, per-page UX), see **[ui/full-ui-redesign-backlog.md](ui/full-ui-redesign-backlog.md)**.

---

## 1. MainWindow remains the coordination hub

Controllers and helpers (`ui/controllers_*`, `inspector_*`, `page_sections`, `saved_views`) reduced coupling, but **`main_window.py`** still orchestrates too much in one place: DB bootstrap, first-run / unlock, page construction, navigation, job dock, `QSettings`, project reload, crawl UI, dashboard UI, charts, workers, exporters, and models.

**Not wrong for an MVP**, but it is the **highest-leverage refactor target** next.

**Suggested strangulation order** (one slice at a time — no big-bang rewrite):

| Extract | Responsibility |
|--------|----------------|
| **AppBootstrap** / **Unlock flow** | Wizard, master password, first DB open |
| **ShellWindow** | Stacked pages container, **nav** + **job dock** chrome only |
| **ProjectContextController** | Current project id, reload, title, dirty signals |
| **Page factories** | `CrawlPage`, `AuditPage`, `KeywordsPage`, `CitationsPage` (build + wire table/inspector) |
| **JobDockController** | Job table, log, visibility, height settings |

Keep peeling responsibilities into focused modules until `MainWindow` is mostly composition.

---

## 2. SSRF: DNS + redirect hops

**Implemented:** `services/net/ssrf.py` resolves hostnames (short timeout, bounded thread pool, ~60s positive cache). **Any** resolved **A/AAAA** that maps to private / loopback / link-local / reserved / multicast blocks the fetch unless **`allow_private`**. **`httpx_event_hooks_ssrf`** is attached to app **httpx** clients so **each outgoing request URL** (including every **redirect** hop) is checked.

**Still worth doing later:** negative DNS caching, per-host rate limits, optional DNS-over-TLS if threat model requires it.

---

## 3. Crawl BFS — removed dead expression

**Resolved in tree:** `run_crawl_job` contained `max(len(pending), 1)` with no assignment or consumer — a no-op left behind during iteration refactors. It has been **removed** from `services/crawler/bfs.py`.

If progress denominator logic is needed later, introduce a named variable (e.g. **estimated queue depth**) and wire it to **`on_progress`** explicitly.

---

## 4. PageLink counts — scoped to crawl job

**Implemented:** **`inbound_internal_counts`** / **`outbound_internal_counts`** filter **`PageLink.job_id`**. Default scope is **`latest_completed_crawl_job_id`** for the project; pass **`crawl_job_id=`** for an explicit crawl. **Audit worker** uses the single **`page.crawl_job_id`** when all audited pages share one crawl; otherwise it falls back to latest completed crawl.

**Optional next:** tie counts to a **selected crawl snapshot** in the UI when the user picks a snapshot for comparison (same job id as snapshot source).

---

## 5. Dashboard action hub — richer `NextActionItem`

**Partially implemented:** **`NextActionItem`** now includes optional **`severity`**, **`priority`**, **`entity_type`**, **`entity_id`**, **`suggested_filter`**. The hub sets **`priority`**, **`entity_type`**, and **`entity_id`** for audit and fallback actions. **Run selected action** navigates and, for **`audit:page:`** / entity **`page`**, focuses the **Audit** table row and inspector.

**Next upgrade:** add **`severity`** on actions from the insight taxonomy; optional **Crawl** table **row** focus when stable page keys exist in the grid.

See also [dashboard-action-model.md](ui/dashboard-action-model.md) (decode runner, **`crawl:start`**, partial crawl filters).
