from crawlix.ui.controllers_actions import resolve_dashboard_action


def test_resolve_jobs_action() -> None:
    route = resolve_dashboard_action("jobs")
    assert route.show_jobs is True
    assert route.nav_row is None


def test_resolve_nav_actions() -> None:
    cs = resolve_dashboard_action("crawl:start")
    assert cs.nav_row == 1
    assert cs.focus_crawl_seeds is True
    assert resolve_dashboard_action("crawl:other").nav_row == 1
    assert resolve_dashboard_action("crawl:other").focus_crawl_seeds is False
    r = resolve_dashboard_action("audit:page:12")
    assert r.nav_row == 2
    assert r.focus_audit_page_id == 12
    assert resolve_dashboard_action("keywords:open").nav_row == 3
    assert resolve_dashboard_action("citations:open").nav_row == 4


def test_resolve_audit_page_entity_fallback() -> None:
    r = resolve_dashboard_action("audit:page:xx", entity_id=99, entity_type="page")
    assert r.nav_row == 2
    assert r.focus_audit_page_id == 99


def test_unknown_action_noop() -> None:
    route = resolve_dashboard_action("unknown")
    assert route.show_jobs is False
    assert route.nav_row is None
