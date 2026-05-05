"""Dashboard action routing helper."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DashboardActionRoute:
    nav_row: int | None = None
    show_jobs: bool = False
    focus_audit_page_id: int | None = None
    focus_crawl_seeds: bool = False


def resolve_dashboard_action(
    target: str,
    *,
    entity_id: int | None = None,
    entity_type: str | None = None,
) -> DashboardActionRoute:
    raw = (target or "").strip()
    t = raw.lower()

    if t == "jobs":
        return DashboardActionRoute(show_jobs=True)

    if t == "crawl:start" or t.startswith("crawl:start"):
        return DashboardActionRoute(nav_row=1, focus_crawl_seeds=True)

    if t.startswith("audit:page:"):
        suffix = raw[len("audit:page:") :].strip()
        focus_pid: int | None = None
        try:
            focus_pid = int(suffix)
        except ValueError:
            focus_pid = None
        if focus_pid is None and entity_type == "page" and entity_id is not None:
            focus_pid = int(entity_id)
        return DashboardActionRoute(nav_row=2, focus_audit_page_id=focus_pid)

    if t.startswith("crawl"):
        return DashboardActionRoute(nav_row=1)
    if t.startswith("audit"):
        return DashboardActionRoute(nav_row=2)
    if t.startswith("keywords"):
        return DashboardActionRoute(nav_row=3)
    if t.startswith("citations"):
        return DashboardActionRoute(nav_row=4)
    return DashboardActionRoute()
