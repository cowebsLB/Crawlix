from pathlib import Path

from alembic import command
from alembic.config import Config

from crawlix.paths import find_repo_root


def test_alembic_upgrade(tmp_path: Path) -> None:
    db = tmp_path / "t.db"
    root = find_repo_root()
    cfg = Config(str(root / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db.as_posix()}")
    command.upgrade(cfg, "head")
    assert db.exists()
