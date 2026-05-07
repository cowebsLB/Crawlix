from crawlix.ui.controllers_toolbar import (
    audit_results_toolbar_actions,
    audit_run_toolbar_actions,
    citations_history_toolbar_actions,
    citations_location_toolbar_actions,
    citations_matrix_toolbar_actions,
    citations_source_toolbar_actions,
    crawl_table_toolbar_actions,
    keywords_toolbar_actions,
    rank_toolbar_actions,
    reports_export_toolbar_actions,
    serp_toolbar_actions,
)


def test_keywords_toolbar_actions_order() -> None:
    assert [a.action_id for a in keywords_toolbar_actions()] == [
        "keywords_add",
        "keywords_refresh",
        "keywords_export",
    ]


def test_serp_toolbar_actions_include_view_controls() -> None:
    ids = [a.action_id for a in serp_toolbar_actions()]
    assert "serp_save_view" in ids
    assert "serp_load_view" in ids


def test_rank_and_citations_toolbar_actions_have_expected_ids() -> None:
    assert [a.action_id for a in rank_toolbar_actions()] == ["rank_refresh", "rank_export"]
    assert [a.action_id for a in citations_matrix_toolbar_actions()] == [
        "citations_run_matrix",
        "citations_refresh_all",
        "citations_save_view",
        "citations_load_view",
    ]
    assert [a.action_id for a in citations_source_toolbar_actions()] == [
        "citations_sources_refresh",
        "citations_sources_export_csv",
    ]
    assert [a.action_id for a in citations_location_toolbar_actions()] == ["citations_locations_refresh"]
    assert [a.action_id for a in citations_history_toolbar_actions()] == ["citations_history_refresh"]


def test_crawl_audit_reports_toolbar_action_ids() -> None:
    assert [a.action_id for a in crawl_table_toolbar_actions()] == [
        "crawl_refresh_table",
        "crawl_export_pages_csv",
        "crawl_export_links_csv",
    ]
    assert [a.action_id for a in audit_run_toolbar_actions()] == ["audit_run_crawled_pages"]
    assert [a.action_id for a in audit_results_toolbar_actions()] == [
        "audit_refresh_results",
        "audit_export_csv",
        "audit_export_json",
    ]
    assert [a.action_id for a in reports_export_toolbar_actions()] == ["reports_export_markdown"]
