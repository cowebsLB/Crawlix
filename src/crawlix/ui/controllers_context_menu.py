"""Context menu definitions for common UI surfaces."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ContextMenuActionDef:
    action_id: str
    label: str


def crawl_context_menu_actions() -> tuple[ContextMenuActionDef, ...]:
    return (
        ContextMenuActionDef("crawl_audit_selected", "Audit selected page(s)…"),
    )


def keywords_context_menu_actions() -> tuple[ContextMenuActionDef, ...]:
    return (
        ContextMenuActionDef("keywords_refresh", "Refresh keywords"),
        ContextMenuActionDef("keywords_export_csv", "Export keywords CSV"),
    )


def serp_context_menu_actions() -> tuple[ContextMenuActionDef, ...]:
    return (
        ContextMenuActionDef("serp_refresh", "Refresh SERP snapshots"),
        ContextMenuActionDef("serp_run", "Run SERP snapshot"),
        ContextMenuActionDef("serp_export_csv", "Export snapshots CSV"),
    )


def rank_context_menu_actions() -> tuple[ContextMenuActionDef, ...]:
    return (
        ContextMenuActionDef("rank_refresh", "Refresh rank chart"),
        ContextMenuActionDef("rank_export_csv", "Export rank CSV"),
    )
