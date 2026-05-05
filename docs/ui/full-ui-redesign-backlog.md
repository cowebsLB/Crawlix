# Crawlix full UI redesign backlog

**Scope:** presentation, workflow, and interaction only — **not** a backend rebuild.

**Related:** [design-tokens.md](design-tokens.md) (current semantics), [interaction-contracts.md](interaction-contracts.md), [dashboard-action-model.md](dashboard-action-model.md), [next-refactors-and-risks.md](../next-refactors-and-risks.md) (MainWindow strangulation), [roadmap-phases.md](../roadmap-phases.md) (delivery phases).

---

## 0. Redesign goal

**From:** “PyQt admin panel with SEO features”  
**To:** “local-first technical SEO analyst workstation”

**Tone:** forensic · technical · calm · precise · action-driven · data-dense but not cramped

---

## 1. New app shell

**Problem:** Left `QListWidget` nav, project combo row, stacked pages, and bottom job dock all live in `MainWindow` — fine for MVP, not final product feel.

**Target:** Desktop product frame:

- **Top Command Strip** — project / domain / global search / job status / settings  
- **Left Rail** — grouped workflow nav (collapsible, clean)  
- **Page Header + Command Bar + Workspace**  
- **Optional Job Center / Activity Drawer** at bottom

**Package:** `ui/shell/`

| Module | Role |
|--------|------|
| `ui/shell/app_shell.py` | Root layout composing rail + host + job strip |
| `ui/shell/nav_rail.py` | Grouped, collapsible navigation |
| `ui/shell/top_bar.py` | Command strip (identity, search, jobs, settings) |
| `ui/shell/job_center.py` | Global job surface / drawer |
| `ui/shell/page_host.py` | Consistent frame for page content |

**Must-have:** Real top bar · grouped nav · collapsible nav · global job indicator · project identity always visible · job center globally reachable · pages hosted in one frame.

### New nav grouping

| Group | Items |
|-------|--------|
| **Overview** | Dashboard |
| **Technical SEO** | Crawl, Audit |
| **Discovery** | Keywords / SERP, Citations, Local |
| **Output** | Reports |
| **System** | Integrations, Settings |

**Acceptance:** The app reads as **one product** before any click.

---

## 2. Replace MainWindow page construction

**Problem:** `MainWindow` imports services, workers, models, controllers, widgets, charts, settings, exporters — shell + pages + refresh + actions + orchestration.

**Target:** Thin host.

| Path | Role |
|------|------|
| `ui/main_window.py` | Creates shell, wires app services |
| `ui/pages/dashboard_page.py` | … |
| `ui/pages/crawl_page.py` | … |
| `ui/pages/audit_page.py` | … |
| `ui/pages/keywords_page.py` | … |
| `ui/pages/citations_page.py` | … |
| `ui/pages/local_page.py` | … |
| `ui/pages/integrations_page.py` | … |
| `ui/pages/reports_page.py` | … |
| `ui/pages/settings_page.py` | … |

**Pages own:** layout, page controls, signals, render methods, empty states, local interaction.  
**Controllers/services own:** queries, formatting, business rules, job routing.

**Acceptance:** `main_window.py` is not where “every widget goes to retire.”

---

## 3. New design system

**Problem:** QSS is global and theme loading exists, but styling is still widget-type-driven, not semantic.

**Target:** Semantic design system.

**Artifacts:**

- `docs/ui/design-tokens.md` — human-readable contract (extend; keep in sync with code)
- `src/crawlix/ui/design_tokens.py` — token map / constants for Python + QSS interpolation
- `src/crawlix/ui/styles/app_dark.qss` / `app_light.qss` — semantic rules

**Token categories (summary):**

- **Color:** `surface.*`, `border.*`, `text.*`, `accent.*`, `status.*`, `priority.*`
- **Spacing:** `space.2` … `space.32`
- **Radius:** `radius.sm` … `radius.pill`
- **Typography:** title.large, title.page, section.heading, body, body.small, metadata, mono
- **Elevation:** flat, raised, floating, overlay

**QSS rule:** Prefer `objectName` + dynamic properties (`variant`, `severity`, `role`) over ad hoc per-widget rules.

**Acceptance:** Redesign by editing tokens/QSS, not hunting 900 lines of widget setup.

---

## 4. New component library

**Problem:** `components.py` is thin (`InspectorPanel`, `ActionListPanel`).

**Target:** Shared library — **PageHeader**, **TopCommandBar**, **SectionCard**, **MetricCard**, **ActionCard**, **StatusPill**, **PriorityPill**, **SeverityPill**, **InsightCard**, **InspectorPanelV2**, **EmptyState**, **ErrorBanner**, **ProgressStrip**, **FilterBar**, **FilterChip**, **SavedViewPicker**, **DataGridToolbar**, **JobCard**, **MethodologyPanel**, **SettingsSection**.

**Acceptance:** Pages do not hand-build patterns that belong in components.

---

## 5. Layout system

**Problem:** `table_with_inspector_split` is only a horizontal splitter seed.

**Target:** Page templates:

- **ActionWorkspacePage** — dashboard-like (header, action cards, metrics, recent activity)
- **DataInspectorPage** — Crawl, Audit, SERP, Citations (header, command bar, summary strip, filter bar, grid + inspector)
- **SettingsPageLayout** — settings nav + panel
- **StubPageLayout** — roadmap cards, disabled previews, docs link

**Acceptance:** Major pages share the same visual grammar.

---

## 6. Dashboard redesign

**Target:** True **Action Hub** — `PageHeader`, hero **Next Best Action**, health metrics, **Needs Attention**, **Recent Outcomes**, **Quick Start** (crawl, audit, keyword, citation matrix), failed jobs with direct actions.

Replace passive list piles with **ActionCard**; hide passive chrome unless tied to an action.

**Acceptance:** Answers **“What do I do next?”** — not “here are stats, good luck.”

---

## 7. Crawl page redesign

**Target:** Flagship workflow — `PageHeader`, `CommandBar`, `ProgressStrip`, metric strip, `FilterBar`, main split **DataGrid + InspectorPanelV2**.

Command bar: seeds, max depth, run, refresh, export. Metrics: pages, unique finals, dup clusters, HTTP errors, depth stats. Filters: search, HTTP, depth, dup finals, in/out bounds, saved view, reset.

**Acceptance:** Crawl feels like the primary workflow page.

---

## 8. Audit page redesign

**Target:** Prioritized triage — summary cards, issue filters, grid + inspector; inspector shows structured issue cards (problem, why, evidence, fix, actions).

**Acceptance:** Answers **“What matters most and why?”**

---

## 9. Keywords / SERP redesign

**Target:** Research workspace — sub-nav: Keywords, SERP Snapshots, Rank History. Targeting profile card (edit/save), template suggestions as cards/chips, methodology panel for SERP limitations, improved rank chart (tokens, empty state, degraded markers).

**Acceptance:** Feels like a research module, not forms in an alley.

---

## 10. Citations redesign

**Target:** Matrix monitoring — overview cards, command bar, tabs (Matrix Overview, Locations, Sources, Check History), grids per tab, inspector with location/source identity and recommended next step.

**Acceptance:** Citation health and failures visible immediately.

---

## 11. Local page redesign

**Target:** Roadmap preview — scope banner, feature preview cards, checklist, docs link (GBP checklist, pack evidence, reviews, NAP, official tools).

**Acceptance:** Stub feels intentional, not an empty room.

---

## 12. Integrations redesign

**Target:** Provider connection center — cards (GSC, GA4, Bing, Ollama, Proxy) with status, description, last sync, permissions, configure, docs.

**Acceptance:** Clear what is connected, planned, and what data each provides.

---

## 13. Reports redesign

**Target:** Report builder UX — type selector, included modules, preview, export actions, recent exports; types (audit summary, crawl health, citation/NAP, keyword/rank, full project); formats Markdown, CSV bundle, HTML; PDF later.

**Acceptance:** Communicates future workflow before full generation exists.

---

## 14. Settings redesign

**Target:** Control center — sidebar or tabs: Appearance, Workspace, Data & storage, Network & politeness, Proxy, AI/Ollama, Security, Updates, Locale, Advanced (with retention, purge, VACUUM/ANALYZE, updater channel, checksum status, i18n/RTL notes per existing plans).

**Acceptance:** Structured system panel, not “miscellaneous stuff.”

---

## 15. Onboarding redesign

**Target:** Trustworthy flow — Welcome → Data location → Security → Automation responsibility → Network politeness → AI/Ollama → Review & finish. Improvements: browse for data folder, storage copy, honest password/SQLCipher messaging, politeness as visual cards with “recommended” on conservative preset, Ollama optional, final review screen.

**Acceptance:** First launch builds trust.

---

## 16. Dialog redesign

**Dialogs:** NewProject, Unlock, citation matrix confirm, exports, migration required, update available, error details.

**Improvements:** Inline validation, clear titles, primary/destructive styling, copyable technical details, narrow focus. **New Project:** identity, domain, optional location, review; **country dropdown** instead of free-text ISO.

**Acceptance:** Fewer message-box spikes; clearer destructive actions.

---

## 17. Data grid system

**Target:** **DataGridPanel** — toolbar, filter row, column visibility, saved view picker, table, pagination/limit notice, empty state, context menu, status footer. Standard behaviors: sort, select, multi-select where useful, copy cells/URL, open URL, tooltips, row height, numeric alignment, status chips.

**Acceptance:** Tables look and behave consistently unless there is a deliberate exception.

---

## 18. Inspector system v2

**Target:** Analyst-grade surface — entity header, status chips, primary problem, insight stack, evidence, recommendation, related rows, actions (not only `insights_to_plain_text()`).

**Acceptance:** Inspector explains the row like an analyst.

---

## 19. Empty states

**Target:** Every empty table/page — icon, title, explanation, primary action, secondary docs/action. Cover: no project, no crawl, no audits, no keywords, SERP, rank history, citations, jobs, integrations, reports.

**Acceptance:** No blank dead zones.

---

## 20. Error and degraded states

**Target:** **ErrorBanner**, **ErrorDetailsDialog**, **DegradedStateCard**, **RetryAction**, **CopyDetailsButton**; SERP/citations specials (CAPTCHA, consent, blocked, timeout, Playwright, empty parse, parser degraded).

**Acceptance:** Calm, clear, actionable.

---

## 21. Loading and progress

**Target:** Shared **ProgressStrip** — states queued / running / completed / failed / cancelled / degraded; used on crawl, audit, SERP, citations matrix, reports export, global job center; cancel + “view job” + short message.

**Acceptance:** User always knows system state.

---

## 22. Saved views redesign

**Target:** **SavedViewPicker** — `View: [Default ▾] [Save] [Reset]`, active filter chips, built-in views for Crawl, Audit, Citations as listed in spec.

**Acceptance:** Saved views are visible workflow, not a hidden convenience.

---

## 23. Filter UX redesign

**Target:** Consistent **FilterBar** — search, dropdowns, boolean chips, active summary, reset all, save view, filter count.

**Acceptance:** User knows what slice of data they are viewing.

---

## 24. Table context actions

**Target:** Consistent right-click menus per domain (Crawl, Audit, SERP, Citations) as specified (inspect, copy, open, audit, filter by dup/path/issue, export, etc.).

**Acceptance:** Right-click is useful everywhere.

---

## 25. Keyboard navigation

**Target:** Ctrl+F search · F5 refresh · Ctrl+J Job Center · Ctrl+L project · Ctrl+E export · Ctrl+R primary action (when safe) · Esc clear transient · F1 help · Ctrl+, settings (align with existing UX notes).

**Acceptance:** Power users avoid mouse gymnastics.

---

## 26. Accessibility

**Required:** Visible focus rings · logical tab order · keyboard table interaction · non-color-only severity · high contrast · reduced motion · SR labels where possible · contrast checks · font scaling tolerance.

**Manual checklist:** Keyboard to primary actions, crawl without mouse, inspect audit row without mouse, job center toggle, warnings readable in light/dark, severity distinguishable without color.

**Acceptance:** Keyboard + high contrast + “4 AM tired user” usable.

---

## 27. Motion and interaction feedback

**Target:** Subtle motion for inspector update, job transitions, sidebar collapse, error reveal, selection, action card hover — **no** decorative noise, pulsing, or crypto-aesthetic fluff. Reduced motion must disable equivalents.

**Acceptance:** Alive, not hyperactive.

---

## 28. Light / dark / high-contrast modes

**Target:** Parity across tables, buttons, inputs, disabled, selected rows, inspector, errors, charts, dialogs, wizard, job center.

**Acceptance:** Light mode not a neglected stepchild.

---

## 29. Chart redesign

**Target:** Colors from tokens · empty state · degraded markers · date axis · later: tooltip points, export image · latest/best/worst rank cards.

**Acceptance:** Charts feel integrated.

---

## 30. Methodology and trust surfaces

**Target:** Methodology panels for SERP, citations, crawler politeness, robots, AI/Ollama (later).

**Acceptance:** Honest limitations build trust.

---

## 31. Copywriting and labels

**Target:** Clear, short, calm, specific, action-oriented — avoid dumps, ambiguous labels, fake certainty. Example: primary label **“Run SERP snapshot”** with limitations in methodology panel, not in the button.

**Acceptance:** Sounds like a calm analyst, not a debug console.

---

## 32. Responsive resizing

**Target:** Healthy behavior at 1200×800, 1366×768, 1440×900, 1920×1080, high DPI — minimize fixed heights, intentional splitters, persist + reset layout, tables vs inspector balance, inspector collapse on narrow widths, cards wrap.

**Acceptance:** No horizontal chaos on laptop sizes.

---

## 33. Visual hierarchy rules

**Every page:** one primary action · one main workspace · one supporting inspector/context · quieter secondary actions · rare, clear danger actions.

**Ban:** same-size everything · everything bordered · everything in `QGroupBox` · identical button colors · giant dumps · blank tables.

**Acceptance:** The eye knows where to go first.

---

## Suggested implementation order (engineering)

1. **Design tokens + QSS split** (`design_tokens.py`, `app_dark.qss` / `app_light.qss`) while keeping current theme load path working.  
2. **`ui/shell/`** + thin `main_window` delegating to **page_host** (existing widgets moved, behavior unchanged).  
3. **Page modules** strangling out of `main_window` per [next-refactors-and-risks.md](../next-refactors-and-risks.md).  
4. **Components** (PageHeader, SectionCard, EmptyState, ProgressStrip) then **DataGridPanel** + **InspectorPanelV2**.  
5. **Per-page polish** in priority order: Dashboard → Crawl → Audit → Keywords → Citations → Settings → rest.

This order matches **foundation → shell → pages → density** and avoids a big-bang UI rewrite.
