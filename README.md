# Crawlix

Local-first desktop SEO and local-marketing workstation: **crawl**, **technical audit**, **keywords / SERP**, **citations / NAP**, optional **integrations** and **Ollama** — data stays on disk you control.

- **Doc index:** [INDEX.md](INDEX.md) (overview, tech stack, links to all docs)
- **Repo:** [github.com/cowebsLB/Crawlix](https://github.com/cowebsLB/Crawlix)
- **Journeys (J1–J14):** [docs/user-guide/journeys.md](docs/user-guide/journeys.md)
- **UI overview:** [docs/ui/overview.md](docs/ui/overview.md)
- **Roadmap / phases:** [docs/roadmap-phases.md](docs/roadmap-phases.md)

## Legal / automation

Automated access to third-party sites (including SERPs and directories) may violate their terms. Crawlix ships **conservative defaults** and explicit **disclaimers** in the first-run wizard. **You are responsible** for how you use the tool.

## Default rate limits (politeness)

These values are implemented in `crawlix.config.PolitenessDefaults` and should match in-app **Methodology** copy.

| Parameter | Default |
|-----------|---------|
| Min delay between requests to the **same host** | **3.0 s** + uniform **0–2 s** jitter (≈ **3–5 s**) |
| Max concurrent connections per same host | **1** |
| Max concurrent **different** hostnames (global) | **4** (Aggressive preset up to **8** with extra warning) |
| 429 / 5xx backoff | `sleep = min(60, 2**retry)` seconds, max **5** retries |
| Global outbound TCP cap | **4** simultaneous connections across crawl / SERP / citations |

## Install (development)

Requires **Python 3.11+** (CI targets 3.11 and 3.12).

```bash
pip install -e ".[dev]"
python -m alembic upgrade head   # optional; app runs migrations path on first launch
python -m crawlix                # or: crawlix (console script after install)
```

Full setup notes: [docs/setup.md](docs/setup.md).

## Database

- **SQLite** + **Alembic** migrations in `alembic/versions/`.
- **SQLCipher** for at-rest encryption is specified in the product plan; this repo currently uses **standard SQLite** for portability in early development. Production hardening should follow `SECURITY.md`.

## Tests

```bash
pytest tests/ -q
```

## Packaging (PyInstaller)

See [docs/packaging.md](docs/packaging.md) for triple-OS build notes, Playwright bundles, and Windows Authenticode expectations.

## License

MIT — see [LICENSE](LICENSE). **PyQt6** is GPL unless you use a commercial Qt license or switch to **PySide6 (LGPL)** for binaries; see `SECURITY.md` and the plan’s licensing section.
