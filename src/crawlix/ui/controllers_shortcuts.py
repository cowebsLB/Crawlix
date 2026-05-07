"""Keyboard shortcut definitions for the desktop shell."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class ShortcutSpec:
    key: str
    description: str


SHORTCUT_SPECS: dict[str, ShortcutSpec] = {
    "focus_search": ShortcutSpec("Ctrl+F", "Focus current page search"),
    "refresh_page": ShortcutSpec("F5", "Refresh current page"),
    "toggle_jobs": ShortcutSpec("Ctrl+J", "Toggle Job Center"),
    "focus_project": ShortcutSpec("Ctrl+L", "Focus project switcher"),
    "export_view": ShortcutSpec("Ctrl+E", "Export current view"),
    "run_primary": ShortcutSpec("Ctrl+R", "Run primary page action"),
    "open_settings": ShortcutSpec("Ctrl+,", "Open Settings"),
    "help_shortcuts": ShortcutSpec("F1", "Show keyboard shortcuts"),
}


def keywords_primary_action_id(tab_index: int) -> str:
    if tab_index == 0:
        return "keywords_add"
    if tab_index == 1:
        return "serp_run"
    return "rank_refresh"


def keywords_export_action_id(tab_index: int) -> str | None:
    if tab_index == 0:
        return "keywords_export_csv"
    if tab_index == 1:
        return "serp_export_csv"
    if tab_index == 2:
        return "rank_export_csv"
    return "keywords_export_csv"


def citations_primary_action_id(tab_index: int) -> str:
    if tab_index == 0:
        return "citations_refresh_sources"
    if tab_index == 1:
        return "citations_refresh_locations"
    return "citations_refresh_checks"


def citations_export_action_id(tab_index: int) -> str | None:
    if tab_index == 0:
        return "citations_export_sources_csv"
    return None


def focus_target_id_for_page(
    slug: str, *, keywords_tab_index: int | None = None, citations_tab_index: int | None = None
) -> str:
    if slug == "keywords":
        idx = 0 if keywords_tab_index is None else keywords_tab_index
        if idx == 0:
            return "keywords_input"
        if idx == 1:
            return "serp_keyword_combo"
        return "rank_keyword_combo"
    if slug == "citations":
        idx = 0 if citations_tab_index is None else citations_tab_index
        if idx == 0:
            return "citations_sources_table"
        if idx == 1:
            return "citations_locations_table"
        return "citations_checks_table"
    defaults = {
        "crawl": "crawl_search",
        "audit": "audit_search",
        "dashboard": "dashboard_actions",
    }
    return defaults.get(slug, "project_switcher")


def primary_action_id_for_page(
    slug: str, *, keywords_tab_index: int | None = None, citations_tab_index: int | None = None
) -> str | None:
    if slug == "keywords":
        return keywords_primary_action_id(0 if keywords_tab_index is None else keywords_tab_index)
    if slug == "citations":
        return citations_primary_action_id(0 if citations_tab_index is None else citations_tab_index)
    defaults = {
        "dashboard": "dashboard_run_selected",
        "crawl": "crawl_start",
        "audit": "audit_start",
    }
    return defaults.get(slug)


def export_action_id_for_page(
    slug: str, *, keywords_tab_index: int | None = None, citations_tab_index: int | None = None
) -> str | None:
    if slug == "keywords":
        return keywords_export_action_id(0 if keywords_tab_index is None else keywords_tab_index)
    if slug == "citations":
        return citations_export_action_id(0 if citations_tab_index is None else citations_tab_index)
    defaults = {
        "crawl": "crawl_export_pages_csv",
        "audit": "audit_export_csv",
        "reports": "reports_export_markdown",
    }
    return defaults.get(slug)


def refresh_action_id_for_page(slug: str) -> str | None:
    defaults = {
        "dashboard": "dashboard_refresh",
        "crawl": "crawl_refresh_table",
        "audit": "audit_refresh_results",
        "keywords": "keywords_refresh_lists",
        "citations": "citations_refresh_all",
    }
    return defaults.get(slug)


def no_action_message_key(action_kind: str, slug: str) -> str:
    if action_kind == "export":
        if slug == "keywords":
            return "no_export_keywords_tab"
        if slug == "citations":
            return "no_export_citations_tab"
        return "no_export_page"
    if action_kind == "refresh":
        return "no_refresh_page"
    if action_kind == "primary":
        return "no_primary_page"
    return "no_action_generic"


def shortcuts_help_text(tr: Callable[[str], str]) -> str:
    title = tr("Keyboard shortcuts")
    lines = [title, "-" * len(title)]
    order = (
        "focus_search",
        "refresh_page",
        "toggle_jobs",
        "focus_project",
        "export_view",
        "run_primary",
        "open_settings",
        "help_shortcuts",
    )
    for key in order:
        spec = SHORTCUT_SPECS[key]
        lines.append(f"{spec.key}  -  {tr(spec.description)}")
    return "\n".join(lines)
