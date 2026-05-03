# Crawlix roadmap (calendar mirror)

This file mirrors the **Delivery phasing (milestones)** section of the product plan. **Scope and J/epic mapping are authoritative in that plan**; this document adds **dates**, **owners**, **release tags**, and **checklists** only.

## How to use

| Column | Fill when |
|--------|-----------|
| Target | Quarter or date after spec freeze |
| Owner | DRI for the phase exit |
| Release tag | Semver tag when the phase ships to users |
| Test checklist | Same **J** ids as the plan — no extra scope without updating the master spec |

## MVP

**Definition:** through **Phase 3** — unlock app, create project, crawl, technical audit, export (CSV/Markdown). **J1–J5**.

## Phase table

| Phase | Codename | Target | Owner | Release tag | Primary epics | Journeys | Exit checklist |
|-------|----------|--------|-------|-------------|---------------|----------|----------------|
| 1 | Foundation | TBD | TBD | v0.1.0 | epic-platform, epic-network (skeleton) | J1, J2, J3 | Wizard, unlock, project CRUD, job dock, settings shell |
| 2 | Crawl | TBD | TBD | v0.2.0 | epic-crawl-audit, epic-network | J4 | Robots, politeness, pages + export |
| 3 | Audit | TBD | TBD | v0.3.0 | epic-crawl-audit | J5 | Issues JSON, scores, export |
| 4 | Keywords | TBD | TBD | v0.4.0 | epic-keywords-serp | J6 | SERP snapshot, gzip HTML, methodology copy |
| 5 | Rank | TBD | TBD | v0.5.0 | epic-keywords-serp | J7 | Rankings + Matplotlib charts |
| 6 | Citations | TBD | TBD | v0.6.0 | epic-citations-local | J8 | NAP matrix, source packs |
| 7 | Integrations | TBD | TBD | v0.7.0 | epic-integrations | J9 | GSC/GA4/Bing behind flags |
| 8 | AI | TBD | TBD | v0.8.0 | epic-ai-collab | J10 | Ollama, cache, timeouts |
| 9 | Reports | TBD | TBD | v0.9.0 | epic-platform, epic-ai-collab | J11 | Cross-module export |
| 10 | Ship | TBD | TBD | v1.0.0 | epic-ship | J12–J14 | PyInstaller, Windows signing, updater checksums, SECURITY.md gate |
| 11+ | Depth | TBD | TBD | v1.x | epic-gbp-reviews-links | Extend J4–J11 | GBP/reviews/links per spec |

## Parallel tracks (non-blocking)

- **SECURITY.md**, **CONTRIBUTING.md**, **docs/user-guide/** — start Phase 1; tighten each release.
- **i18n / RTL** — `tr()` from Phase 1; RTL smoke by Phase 3.
- **SQLCipher spike** — complete before large crawl HTML at scale (Phase 2); if slipped, cap crawl size in dev until encryption lands.

## Hard dependencies (ordering)

1. Phase 2 before 3 (audit consumes crawl or manual URLs).
2. Phase 4 before 5 (rank needs SERP storage).
3. Phase 6 after stable ProxyManager + cancel (Phases 2–4).
4. Phase 7 after Phase 1 DB/token patterns.
5. Phase 10: Windows Authenticode before broad Windows marketing.

## CI / manual gate (per release)

- [ ] `pytest` green on **Python 3.11 and 3.12** (add `pytest-qt` + headless Qt/EGL deps in CI only when GUI smoke tests land)
- [ ] `alembic upgrade head` on fresh DB
- [ ] Journeys listed for the phase: smoke manual pass
- [ ] No `verify=False` in tree; grep for accidental secrets
