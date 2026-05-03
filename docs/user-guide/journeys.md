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
| **J7** | Rank over time | Runs → charts → export history | `rankings`, `serp_results` |
| **J8** | Citation / NAP | Golden NAP → sources → matrix job → export | `citation_checks`, `citation_sources` |
| **J9** | Integrations | Connect GSC/GA4 → sync → data in UI | `integration_accounts`, snapshots |
| **J10** | AI assist | Ollama action → timeout handling → `ai_cache` | `ai_cache` |
| **J11** | Reporting | Pick outputs → CSV/Markdown/PDF → handoff | exports, optional `reports` |
| **J12** | Update | Check update → verify checksum → confirm → install | temp, `settings` |
| **J13** | Maintenance | Retention purge → VACUUM → backup | DB file |
| **J14** | Uninstall / wipe | OS removal + optional delete all data | N/A |

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
