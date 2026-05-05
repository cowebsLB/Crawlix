# User journey catalog (J1–J14)

Each journey maps to **tests**, **docs**, and **release checklists**. Keep in sync with the product capability matrix (A–J).

| ID | Journey | Happy path summary | Primary persistence |
|----|---------|-------------------|---------------------|
| **J1** | First launch | Install → wizard → data dir → master password → automation disclaimer → politeness → optional Ollama | `settings`, new DB |
| **J2** | Daily unlock | Start app → unlock DB → dashboard | session |
| **J3** | New project | Create project (name, domain) → optional location | `projects`, `locations` |
| **J4** | Site crawl | Configure crawl → job → results + export | `jobs`, `pages`, `crawled_data`, `page_links` |
| **J5** | On-page audit | URLs → audit job → scores + `issues_json` → export | `jobs`, `seo_audits` |
| **J6** | Keywords + SERP | Seeds → SERP snapshot → gzip HTML + parsed rows | `keywords`, `serp_results` |
| **J7** | Rank over time | SERP → domain match → `rankings` → chart → export (future) | `rankings`, `serp_results` |
| **J8** | Citation / NAP | Golden NAP → sources → matrix job → export | `citation_checks`, `citation_sources` |
| **J9** | Integrations | Connect GSC/GA4 → sync → data in UI | `integration_accounts`, snapshots |
| **J10** | AI assist | Ollama action → timeout handling → `ai_cache` | `ai_cache` |
| **J11** | Reporting | Pick outputs → CSV/Markdown/PDF → handoff | exports, optional `reports` |
| **J12** | Update | Check update → verify checksum → confirm → install | temp, `settings` |
| **J13** | Maintenance | Retention purge → VACUUM → backup | DB file |
| **J14** | Uninstall / wipe | OS removal + optional delete all data | N/A |

## J1–J5 in the current app

| Journey | Where it lives |
|---------|----------------|
| **J1** | First-run `QWizard` in `crawlix.ui.onboarding` — data dir, master password (Argon2), disclaimer checkbox, politeness preset, optional **Ollama URL + enable** persisted to `settings` (`ollama_base_url`, `ollama_enabled`). |
| **J2** | `UnlockDialog` on each launch when the DB exists; recovery copy explains backup-only reset. |
| **J3** | **File → New project…** opens `NewProjectDialog` — name, default domain, optional **primary `Location`** (NAP seed); slug collision handled via `crawlix.utils.slug.unique_project_slug`. |
| **J4** | **Crawl** page — queue job, live progress, **pages table**, **Export pages / links CSV**, **Job dock → Cancel selected job** (sets `jobs.cancel_requested`). |
| **J5** | **Audit** page — job over crawled pages, **results table**, **Export audits CSV/JSON**, cancel supported in `AuditWorker` between pages. |
| **Settings** | **Ollama** URL + enable can be edited after wizard (`Save Ollama settings`). |
| **Dashboard** | Project summary: page count, job count, audit count, last crawl timestamp. |

## J6–J7 in the current app

| Journey | Where it lives |
|---------|----------------|
| **J6** | **Keywords** tab: table of project keywords + refresh; **Project targeting (templates)** saves `projects.seo_context_json` (site type, country, brand, topic) and **Template keyword ideas** generates English phrase packs, deduped vs existing phrases, **Add checked to project**; **SERP snapshots** tab: keyword picker (`QComboBox`), run snapshot job, history table (fetched time, status, organic hit count). Storage: `keywords` (+ optional `tags_json`), `serp_results` + gzip HTML via `fetch_serp_placeholder`. |
| **J7** | **Rank history** tab: **keyword picker** + Matplotlib chart of **`rankings.position`** (1 = best) over time vs **project `default_domain`** (subdomain match; DuckDuckGo `uddg=` unwrap). One **`Ranking`** row per SERP snapshot from **`fetch_serp_placeholder`**; gaps (`NaN`) when the domain is not in the parsed organic set. |

## J8 in the current app

| Journey | Where it lives |
|---------|----------------|
| **J8** | **Citations** page: **Built-in sources** + CSV export; **Locations**; **Check history**. **Run citation matrix (HTTP)** queues job type `citation` — `CitationMatrixWorker` expands templates (`placeholders.expand_template`), runs HTTP checks (small bodies gzipped), skips `requires_playwright` rows, honors cancel. NAP-vs-page diff not implemented yet. |

## Doc chapters (suggested)

- `j1-first-launch.md` … `j14-uninstall.md` — one file per cluster as the product matures; see [README.md](README.md) in this folder for the user-guide index and status of those chapters.

## Failure highlights (test these)

- **J1:** Data dir permissions; SQLCipher/native driver missing.
- **J2:** Forgot password — only backup/recovery path documented.
- **J4:** robots disallow; rate limits; cancel mid-run; disk cap.
- **J6:** CAPTCHA/degraded; parser drift.
- **J8:** Blocked sources; JS-only listings.
- **J9:** Token expiry; revoked scopes.
- **J12:** Hash mismatch; offline; wrong architecture asset.
