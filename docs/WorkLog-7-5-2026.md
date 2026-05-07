# Worklog — 7 May 2026

**Continues from:** [`WorkLog-4-5-2026.md`](WorkLog-4-5-2026.md) (all prior milestones and cumulative notes stay there).

---

## Tasks completed

- **Released previous sprint batch:** committed and pushed the UI foundation + hardening stream to `main` (SSRF hooks, dashboard action routing, crawl link-count scoping, tokenized theme base, shell scaffolding, docs/tests sync).
- **Started the new-day UX slice:** improved the top command strip in `MainWindow` with:
  - current project identity label,
  - disabled global search placeholder,
  - live jobs health badge (`idle`, `running`, `failed` counts),
  - direct Settings shortcut button.
- **Job visibility polish:** wired top-strip jobs badge updates into `_refresh_job_table` so users can see global background state without opening Job Center.
- **Project context clarity:** top-strip project identity now updates on project reload and project selection changes.
- **Grouped workflow rail:** navigation now renders section headings (**Overview**, **Technical SEO**, **Discovery**, **Output**, **System**) with safe slug→row/page mapping. Dashboard action routing and Settings shortcut now navigate by slug, so grouped headings do not break page targeting.
- **Component baseline:** added reusable `PageHeader` in `crawlix.ui.components` and switched `MainWindow` page header factory to consume it (first step toward replacing ad hoc per-page title blocks).
- **SectionCard foundation:** added semantic `SectionCard` component (`QFrame#SectionCard`) and migrated Dashboard summary from `QGroupBox` to `SectionCard`. `ActionListPanel` now extends `SectionCard`, moving dashboard cards toward the new design grammar without behavior changes.
- **Empty states (first migration):** added reusable `EmptyState` component and rewired the **Local** page from a generic placeholder `QGroupBox` into an intentional roadmap-preview surface with clear scope text and direct “Open local roadmap” action.
- **System/output page polish:** migrated **Integrations** provider placeholder and **Reports** shell to semantic cards (`SectionCard`) and added a reports preview `EmptyState`, while preserving the existing sample Markdown export workflow.
- **FilterBar start (Crawl):** introduced reusable `FilterBar` component and migrated Crawl “Table filters” into it (same controls, no behavior changes). Added active-filter summary text (`none` vs active filter list) so current data slice is visible at a glance.
- **FilterBar rollout (Audit):** added an Audit `FilterBar` with URL search, max-score threshold, and min-issues controls. Applied filters in `_refresh_audit_results_table` with active-filter summary text to make triage context explicit.
- **DataGridToolbar start (Crawl + Audit):** added reusable `DataGridToolbar` component and migrated Crawl/Audit action rows (refresh + exports) to shared semantic toolbar cards, preserving existing handlers and behavior.
- **DataGridToolbar expansion (Citations):** migrated citations **Built-in sources** and **Check history** action rows to `DataGridToolbar` for consistent table-action grammar across modules.
- **StatusPill baseline:** added reusable `StatusPill` component + tokenized QSS variants and applied it to the top command-strip jobs indicator (neutral/warning/danger state by queue/failure counts).
- **StatusPill in data grid:** citations check-history **Status** column now renders semantic `StatusPill` widgets (success/warning/danger/neutral mapping) while preserving raw status text in table items for sorting/data consistency.
- **Keywords/SERP toolbar consistency:** migrated Keywords and SERP action rows to shared `DataGridToolbar` cards (add/refresh, refresh/run/save/load actions) with existing handlers unchanged.
- **SERP status semantics:** SERP snapshots **Status** column now uses `StatusPill` rendering with success/warning/danger mapping while retaining raw status text items for sort/data behavior.
- **Methodology trust panels:** added reusable `MethodologyPanel` component and applied it to SERP snapshot and Citations pages so limitations/interpretation guidance is visible inline (calm, explicit, action-supportive wording).
- **Three-change pass cadence:** switched to batching 2–3 focused UI improvements per pass for steadier progress.
- **Keywords card migration:** converted **Project targeting** to `SectionCard`; converted **Template keyword ideas** to `MethodologyPanel` + `DataGridToolbar` actions (`Generate suggestions`, `Add checked`) without changing logic.
- **Settings card migration:** converted **Appearance** and **Ollama** groups to `SectionCard`, and converted crawler politeness note to a `MethodologyPanel` trust surface.
- **Citations layout cards:** converted **Locations (NAP)** and **Check history** wrappers from `QGroupBox` to `SectionCard` while preserving existing table and refresh behavior.
- **Rank actions toolbar:** migrated Rank history refresh row to `DataGridToolbar` (`Refresh chart`) for action-row consistency with Crawl/Audit/Citations/Keywords/SERP.
- **SectionCard wrapper sweep:** converted **Keywords**, **Rank history**, and Citations **Matrix job** wrappers from `QGroupBox` to `SectionCard` with existing controls/handlers unchanged.
- **SectionCard wrapper sweep (continued):** converted Crawl **Run crawl**, Audit **Run**, and SERP **SERP snapshot** wrappers from `QGroupBox` to `SectionCard` while preserving all existing actions and behavior.
- **SectionCard foundation:** added semantic `SectionCard` component (`QFrame#SectionCard`) and migrated Dashboard summary from `QGroupBox` to `SectionCard`. `ActionListPanel` now extends `SectionCard`, moving dashboard cards toward the new design grammar without behavior changes.

## Problems encountered

- No blockers in this slice; changes were scoped to UI composition and status surfacing.

## Decisions made

- Keep this day focused on **incremental shell UX improvements** instead of broad page extraction, so behavior remains stable while the redesign track advances.
- Continue following the staged redesign order: shell chrome -> shared components -> page-level visual rewrites.

## Next steps

- Introduce first shared components from backlog (`PageHeader`, `SectionCard`, `EmptyState`) and migrate one page at a time.
- Start Crawl page visual grammar pass (`CommandBar` + `MetricStrip` + unified `FilterBar`) while preserving existing backend flow.
- Add keyboard shortcut pass for the new shell chrome (`Ctrl+J`, `Ctrl+,`, `Ctrl+F`) and document help overlay baseline.
