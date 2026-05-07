from crawlix.ui.controllers_actions import DashboardActionRoute
from crawlix.ui.controllers_dashboard_routes import build_dashboard_post_nav_plan


def test_post_nav_plan_prefers_audit_focus() -> None:
    route = DashboardActionRoute(nav_row=2, focus_audit_page_id=123)
    plan = build_dashboard_post_nav_plan(route, {"apply_saved_crawl_view": True})
    assert plan.focus_audit_page_id == 123
    assert not plan.focus_crawl_seeds


def test_post_nav_plan_uses_saved_crawl_view_flag() -> None:
    route = DashboardActionRoute(nav_row=1, focus_crawl_seeds=True)
    plan = build_dashboard_post_nav_plan(route, {"apply_saved_crawl_view": True, "depth_filter": "deep"})
    assert plan.focus_crawl_seeds
    assert plan.apply_saved_crawl_view
    assert plan.crawl_filter is None


def test_post_nav_plan_uses_partial_filter_when_not_saved_view() -> None:
    route = DashboardActionRoute(nav_row=1, focus_crawl_seeds=True)
    suggested = {"depth_filter": "deep", "dup_only": True}
    plan = build_dashboard_post_nav_plan(route, suggested)
    assert plan.focus_crawl_seeds
    assert not plan.apply_saved_crawl_view
    assert plan.crawl_filter == suggested
