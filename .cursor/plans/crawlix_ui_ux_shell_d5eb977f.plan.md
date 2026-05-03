---
name: Crawlix UI UX Shell
overview: Ship a clear, consistent PyQt6 shell and information architecture so Crawlix stays navigable as features grow—documented in-repo and aligned with the master Crawlix spec.
todos:
  - id: ui-shell-layout
    content: "PyQt6: QMainWindow, sidebar nav, stacked pages, project switcher, status bar, Job dock (Jobs|Log)"
    status: pending
  - id: ui-first-run
    content: Implement 6-step wizard per master plan; persist choices to project/settings
    status: pending
  - id: ui-keywords-serp-page
    content: Single Keywords & SERP page with Keywords | SERP runs | Rankings tabs (placeholder content OK)
    status: pending
  - id: ui-patterns-qss
    content: Table/modal/job patterns + central QSS light/dark + semantic status colors
    status: pending
  - id: ui-docs
    content: Add docs/ui/overview.md, docs/ui/glossary.md; link from README
    status: pending
  - id: ui-i18n-strings
    content: Wrap shell and wizard strings in tr(); list glossary keys for translators
    status: pending
isProject: false
---

# Crawlix UI/UX shell (implementation slice)

Authoritative detail lives in the master product spec: [crawlix_pure_python_plan_ffdcc41d.plan.md](c:\Users\COWebs.lb\.cursor\plans\crawlix_pure_python_plan_ffdcc41d.plan.md) — section **UI/UX (PyQt6): shell, navigation, patterns, accessibility**.

## Goals

- **One mental model**: project-scoped work; long tasks visible in a **Job dock** (Jobs | Log); no duplicate “where do I run SERP?” entry points.
- **Predictable chrome**: menu bar, **project switcher** in the top bar, **sidebar** order fixed, **status bar** for connection/proxy/last error hint.
- **First-run**: **6-step wizard** (language, data dir + DB password, default politeness, optional proxy, optional SERP provider, sample vs empty project) — same order as master plan.

## Sidebar information architecture (locked)

1. Dashboard  
2. Crawl  
3. Audit  
4. **Keywords & SERP** (single page; **tabs**: Keywords | SERP runs | Rankings)  
5. Citations  
6. Local (stub / roadmap)  
7. Integrations  
8. Reports  
9. Settings  

## Interaction patterns (locked)

- **Tables**: sort, filter row, multi-select, bulk actions toolbar, empty states with one primary CTA.  
- **Modals**: wizard and destructive confirms; **non-modal panels** for “configure run” so users keep context.  
- **Jobs**: dock shows progress, ETA where applicable, **Cancel**; errors link to Log with copyable detail.  
- **Terminology**: glossary in UI spec + [`docs/ui/glossary.md`](docs/ui/glossary.md); all user-visible strings via `tr()` for i18n.

## Visual system

- **Semantic colors** only (success/warning/error/info); **central QSS** + light/dark; **Matplotlib** colors follow app theme.  
- **Baseline a11y**: focus visible, keyboard nav for shell + tables, minimum tap targets where touch applies.

## Documentation (repo)

- [`docs/ui/overview.md`](docs/ui/overview.md) — diagram: shell + sidebar + dock; screenshots when the app exists.  
- [`docs/ui/glossary.md`](docs/ui/glossary.md) — same terms as the terminology table in the master plan.  
- [`README.md`](README.md) — link to UI overview.

## Engineering touchpoints (when executing)

- Main window: `QMainWindow` + `QStackedWidget` (or equivalent) for sidebar pages; **Job dock** `QDockWidget`.  
- Reuse existing plan items: **Platform epic** (app shell, i18n), **Keywords/SERP epic** for the Keywords & SERP tabs content.

## Out of scope for this slice

- Pixel-perfect visual design system beyond semantic tokens + QSS.  
- Full Local/GBP UI (stub page only per master plan).
