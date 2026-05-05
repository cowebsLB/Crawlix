from crawlix.ui.controllers_actions import resolve_dashboard_action


def test_resolve_jobs_action() -> None:
    route = resolve_dashboard_action("jobs")
    assert route.show_jobs is True
    assert route.nav_row is None


def test_resolve_nav_actions() -> None:
    assert resolve_dashboard_action("crawl:start").nav_row == 1
    assert resolve_dashboard_action("audit:page:12").nav_row == 2
    assert resolve_dashboard_action("keywords:open").nav_row == 3
    assert resolve_dashboard_action("citations:open").nav_row == 4


def test_unknown_action_noop() -> None:
    route = resolve_dashboard_action("unknown")
    assert route.show_jobs is False
    assert route.nav_row is None
