"""Helpers for dashboard follow-up actions after page routing."""

from __future__ import annotations

from dataclasses import dataclass

from crawlix.ui.controllers_actions import DashboardActionRoute


@dataclass(frozen=True)
class DashboardPostNavPlan:
    focus_audit_page_id: int | None = None
    apply_saved_crawl_view: bool = False
    crawl_filter: dict[str, object] | None = None
    focus_crawl_seeds: bool = False


def build_dashboard_post_nav_plan(
    route: DashboardActionRoute,
    suggested_filter: dict[str, object] | None,
) -> DashboardPostNavPlan:
    if route.focus_audit_page_id is not None:
        return DashboardPostNavPlan(focus_audit_page_id=int(route.focus_audit_page_id))
    if route.focus_crawl_seeds:
        use_saved = bool(suggested_filter and suggested_filter.get("apply_saved_crawl_view"))
        crawl_filter = None if use_saved else suggested_filter
        return DashboardPostNavPlan(
            apply_saved_crawl_view=use_saved,
            crawl_filter=crawl_filter,
            focus_crawl_seeds=True,
        )
    return DashboardPostNavPlan()
