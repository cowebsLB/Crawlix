"""App shell composition helpers (full frame lives in MainWindow until further extraction)."""

from __future__ import annotations

# Re-export shell widgets for a single import path.
from crawlix.ui.shell.job_center import JobCenter
from crawlix.ui.shell.nav_rail import NavRailColumn
from crawlix.ui.shell.page_host import PageHost
from crawlix.ui.shell.top_bar import TopCommandStrip

__all__ = (
    "JobCenter",
    "NavRailColumn",
    "PageHost",
    "TopCommandStrip",
)
