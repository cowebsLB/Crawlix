"""Run Alembic migrations against a concrete SQLite path."""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config

from crawlix.paths import find_repo_root


def upgrade_database(db_path: Path) -> None:
    root = find_repo_root()
    ini = root / "alembic.ini"
    cfg = Config(str(ini))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path.as_posix()}")
    command.upgrade(cfg, "head")
