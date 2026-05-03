"""App configuration: paths, politeness defaults, feature flags."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path


def default_data_dir() -> Path:
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
        return base / "Crawlix"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Crawlix"
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "crawlix"


@dataclass(frozen=True)
class PolitenessDefaults:
    """Pinned numeric defaults — duplicate table in README."""

    min_delay_same_host_s: float = 3.0
    jitter_same_host_max_s: float = 2.0
    max_concurrent_per_host: int = 1
    max_concurrent_hosts: int = 4
    aggressive_max_hosts: int = 8
    backoff_max_s: int = 60
    max_retries_429_5xx: int = 5
    global_outbound_tcp_cap: int = 4


CONSERVATIVE = PolitenessDefaults()
NORMAL = PolitenessDefaults(
    min_delay_same_host_s=1.5,
    jitter_same_host_max_s=1.5,
    max_concurrent_hosts=6,
)
AGGRESSIVE = PolitenessDefaults(
    min_delay_same_host_s=0.75,
    jitter_same_host_max_s=0.75,
    max_concurrent_hosts=8,
    aggressive_max_hosts=8,
)

PRESETS: dict[str, PolitenessDefaults] = {
    "conservative": CONSERVATIVE,
    "normal": NORMAL,
    "aggressive": AGGRESSIVE,
}

OLLAMA_DEFAULT_URL = "http://127.0.0.1:11434"
GITHUB_REPO_SLUG = "cowebsLB/Crawlix"

# Set CRAWLIX_PLAINTEXT_DB=1 for dev CI without SQLCipher native libs.
USE_PLAINTEXT_SQLITE = os.environ.get("CRAWLIX_PLAINTEXT_DB", "1") == "1"


def app_db_path(data_dir: Path) -> Path:
    return data_dir / "crawlix.db"
