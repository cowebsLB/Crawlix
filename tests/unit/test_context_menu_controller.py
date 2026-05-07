from crawlix.ui.controllers_context_menu import (
    crawl_context_menu_actions,
    keywords_context_menu_actions,
    rank_context_menu_actions,
    serp_context_menu_actions,
)


def test_keywords_context_menu_actions_match_expected_order() -> None:
    actions = keywords_context_menu_actions()
    assert [a.action_id for a in actions] == ["keywords_refresh", "keywords_export_csv"]


def test_serp_context_menu_actions_include_run_and_export() -> None:
    actions = serp_context_menu_actions()
    ids = [a.action_id for a in actions]
    assert "serp_run" in ids
    assert "serp_export_csv" in ids


def test_rank_and_crawl_actions_defined() -> None:
    assert [a.action_id for a in rank_context_menu_actions()] == ["rank_refresh", "rank_export_csv"]
    assert [a.action_id for a in crawl_context_menu_actions()] == ["crawl_audit_selected"]
