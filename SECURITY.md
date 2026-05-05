# Security policy

## Supported versions

We ship security fixes for the **latest minor** on the active release branch. Older versions may not receive backports.

## Reporting a vulnerability

Please email the maintainers (see GitHub profile / repo contacts) with:

- Description and impact
- Steps to reproduce
- Suggested fix (optional)

Do not file public issues for undisclosed critical vulnerabilities until a fix is released.

## Threat model (summary)

- **Local-first:** data lives in a SQLite file under the user’s chosen data directory (see QSettings key `data_dir` bootstrap + encrypted DB roadmap).
- **No telemetry** in the product default: no third-party crash reporting.
- **Outbound HTTPS:** user-initiated crawls, SERP fetches, citation checks, optional GitHub Releases update checks, optional Ollama on `127.0.0.1`, optional OAuth integrations.
- **SSRF:** private / loopback / link-local targets are **blocked** for literal IPs and for **hostnames after DNS resolution** (all resolved A/AAAA addresses must be “public” unless **`allow_private`**). Results are cached briefly. Outbound **httpx** clients use **request event hooks** (`httpx_event_hooks_ssrf`) so **each redirect hop** is checked when **follow_redirects** is enabled. Intranet crawls use **`allow_private_ssrf`** in the job payload / future UI opt-in.
- **TLS:** `httpx` uses certificate verification; **do not** set `verify=False` in production code paths.
- **Proxies:** unknown proxies are a **TLS MITM** risk — document for users; credentials must not appear in logs or debug bundles.
- **Updates:** installers must pass **checksum verification** before apply; user confirmation required; see `crawlix.services.updater.github_releases`.
- **Playwright:** warn users not to log into **personal accounts** inside automated browser profiles (supporting doc: user guide).

## PyQt6 / GPL

Shipping binaries that link PyQt6 may impose **GPL v3** obligations. Review Riverbank Computing licensing or consider **PySide6** before wide binary distribution.

## SQLCipher

Encrypted SQLite is a **product requirement** for production agency use. Track driver packaging (PyInstaller on Windows/macOS/Linux) and Alembic compatibility in the roadmap.
