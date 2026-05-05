"""Dashboard action routing helper."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DashboardActionRoute:
    nav_row: int | None = None
    show_jobs: bool = False


def resolve_dashboard_action(target: str) -> DashboardActionRoute:
    t = (target or "").strip().lower()
    if t == "jobs":
        return DashboardActionRoute(show_jobs=True)
    if t.startswith("crawl"):
        return DashboardActionRoute(nav_row=1)
    if t.startswith("audit"):
        return DashboardActionRoute(nav_row=2)
    if t.startswith("keywords"):
        return DashboardActionRoute(nav_row=3)
    if t.startswith("citations"):
        return DashboardActionRoute(nav_row=4)
    return DashboardActionRoute()
