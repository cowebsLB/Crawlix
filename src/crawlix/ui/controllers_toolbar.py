"""Toolbar action definitions for page-level UI builders."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ToolbarActionDef:
    action_id: str
    label: str
    variant: str = "primary"


def keywords_toolbar_actions() -> tuple[ToolbarActionDef, ...]:
    return (
        ToolbarActionDef("keywords_add", "Add keyword"),
        ToolbarActionDef("keywords_refresh", "Refresh table", "secondary"),
        ToolbarActionDef("keywords_export", "Export CSV", "secondary"),
    )


def serp_toolbar_actions() -> tuple[ToolbarActionDef, ...]:
    return (
        ToolbarActionDef("serp_refresh_lists", "Refresh lists", "secondary"),
        ToolbarActionDef("serp_run", "Run SERP snapshot"),
        ToolbarActionDef("serp_export", "Export snapshots CSV", "secondary"),
        ToolbarActionDef("serp_save_view", "Save view", "secondary"),
        ToolbarActionDef("serp_load_view", "Load view", "secondary"),
    )


def rank_toolbar_actions() -> tuple[ToolbarActionDef, ...]:
    return (
        ToolbarActionDef("rank_refresh", "Refresh chart", "secondary"),
        ToolbarActionDef("rank_export", "Export rank CSV", "secondary"),
    )


def citations_matrix_toolbar_actions() -> tuple[ToolbarActionDef, ...]:
    return (
        ToolbarActionDef("citations_run_matrix", "Run citation matrix (HTTP)…"),
        ToolbarActionDef("citations_refresh_all", "Refresh all tabs", "secondary"),
        ToolbarActionDef("citations_save_view", "Save view", "secondary"),
        ToolbarActionDef("citations_load_view", "Load view", "secondary"),
    )


def citations_source_toolbar_actions() -> tuple[ToolbarActionDef, ...]:
    return (
        ToolbarActionDef("citations_sources_refresh", "Refresh list"),
        ToolbarActionDef("citations_sources_export_csv", "Export CSV…", "secondary"),
    )


def citations_location_toolbar_actions() -> tuple[ToolbarActionDef, ...]:
    return (
        ToolbarActionDef("citations_locations_refresh", "Refresh locations"),
    )


def citations_history_toolbar_actions() -> tuple[ToolbarActionDef, ...]:
    return (
        ToolbarActionDef("citations_history_refresh", "Refresh history"),
    )


def crawl_table_toolbar_actions() -> tuple[ToolbarActionDef, ...]:
    return (
        ToolbarActionDef("crawl_refresh_table", "Refresh table"),
        ToolbarActionDef("crawl_export_pages_csv", "Export pages CSV…", "secondary"),
        ToolbarActionDef("crawl_export_links_csv", "Export links CSV…", "secondary"),
    )


def audit_run_toolbar_actions() -> tuple[ToolbarActionDef, ...]:
    return (
        ToolbarActionDef("audit_run_crawled_pages", "Run audit on crawled pages"),
    )


def audit_results_toolbar_actions() -> tuple[ToolbarActionDef, ...]:
    return (
        ToolbarActionDef("audit_refresh_results", "Refresh results"),
        ToolbarActionDef("audit_export_csv", "Export audits CSV…", "secondary"),
        ToolbarActionDef("audit_export_json", "Export audits JSON…", "secondary"),
    )


def reports_export_toolbar_actions() -> tuple[ToolbarActionDef, ...]:
    return (
        ToolbarActionDef("reports_export_markdown", "Export sample Markdown"),
    )
