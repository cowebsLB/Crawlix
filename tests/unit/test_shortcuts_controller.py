from crawlix.ui.controllers_shortcuts import (
    SHORTCUT_SPECS,
    citations_export_action_id,
    citations_primary_action_id,
    export_action_id_for_page,
    focus_target_id_for_page,
    keywords_export_action_id,
    keywords_primary_action_id,
    no_action_message_key,
    primary_action_id_for_page,
    refresh_action_id_for_page,
    shortcuts_help_text,
)


def test_shortcut_keys_are_unique() -> None:
    keys = [spec.key for spec in SHORTCUT_SPECS.values()]
    assert len(keys) == len(set(keys))


def test_shortcuts_help_text_includes_core_entries() -> None:
    text = shortcuts_help_text(lambda value: value)
    assert "Keyboard shortcuts" in text
    assert "Ctrl+F  -  Focus current page search" in text
    assert "Ctrl+,  -  Open Settings" in text
    assert "F1  -  Show keyboard shortcuts" in text


def test_keywords_tab_action_mapping() -> None:
    assert keywords_primary_action_id(0) == "keywords_add"
    assert keywords_primary_action_id(1) == "serp_run"
    assert keywords_primary_action_id(2) == "rank_refresh"
    assert keywords_export_action_id(0) == "keywords_export_csv"
    assert keywords_export_action_id(1) == "serp_export_csv"
    assert keywords_export_action_id(2) == "rank_export_csv"


def test_citations_tab_action_mapping() -> None:
    assert citations_primary_action_id(0) == "citations_refresh_sources"
    assert citations_primary_action_id(1) == "citations_refresh_locations"
    assert citations_primary_action_id(2) == "citations_refresh_checks"
    assert citations_export_action_id(0) == "citations_export_sources_csv"
    assert citations_export_action_id(1) is None


def test_page_level_focus_and_action_resolution() -> None:
    assert focus_target_id_for_page("keywords", keywords_tab_index=1) == "serp_keyword_combo"
    assert focus_target_id_for_page("citations", citations_tab_index=2) == "citations_checks_table"
    assert focus_target_id_for_page("crawl") == "crawl_search"
    assert primary_action_id_for_page("keywords", keywords_tab_index=2) == "rank_refresh"
    assert primary_action_id_for_page("dashboard") == "dashboard_run_selected"
    assert export_action_id_for_page("reports") == "reports_export_markdown"
    assert refresh_action_id_for_page("keywords") == "keywords_refresh_lists"
    assert refresh_action_id_for_page("settings") is None


def test_no_action_message_key_routing() -> None:
    assert no_action_message_key("export", "keywords") == "no_export_keywords_tab"
    assert no_action_message_key("export", "citations") == "no_export_citations_tab"
    assert no_action_message_key("refresh", "settings") == "no_refresh_page"
    assert no_action_message_key("primary", "settings") == "no_primary_page"
