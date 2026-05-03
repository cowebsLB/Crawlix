# Setup and first run

## Requirements

- **Python 3.11+** (project allows `<3.15`; CI typically uses 3.11 / 3.12).
- Windows, macOS, or Linux with a desktop session (PyQt6 GUI).

## Development install

From the repository root:

```bash
pip install -e ".[dev]"
```

This installs Crawlix in editable mode plus **pytest** and **ruff**.

## Database migrations

The app runs **Alembic** upgrades on startup against your configured database file. You can also apply migrations manually:

```bash
python -m alembic upgrade head
```

## Run the application

**Recommended (works from any CWD once installed):**

```bash
python -m crawlix
```

**Console script** (after install):

```bash
crawlix
```

> **Note:** Use `python -m crawlix`, not `python -m crawlix.main` — the package exposes [`crawlix/__main__.py`](../src/crawlix/__main__.py).

## First launch

1. If no database exists yet, the **first-run wizard** collects:
   - Data directory (where the SQLite file and blobs live).
   - Master password (Argon2 hash stored in `settings`).
   - Politeness preset and automation disclaimer acknowledgment.
2. On subsequent launches, **Unlock** validates the master password before opening the shell.

Data directory preference is stored in **Qt `QSettings`** (`COWEBS` / `Crawlix`, key `data_dir`) and mirrored in the database `settings` table where applicable.

## Verify install

```bash
ruff check src tests
pytest tests/ -q
```

## Packaging

For frozen binaries and signing expectations, see [packaging.md](packaging.md).
