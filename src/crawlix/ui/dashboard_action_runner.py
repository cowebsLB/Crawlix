"""Decode dashboard action list metadata and accompany routing (MainWindow stays thin)."""

from __future__ import annotations

import json
from dataclasses import dataclass

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QListWidgetItem

from crawlix.ui.controllers_actions import DashboardActionRoute, resolve_dashboard_action


@dataclass(frozen=True)
class DecodedDashboardListItem:
    target: str
    entity_id: int | None
    entity_type: str | None
    suggested_filter: dict[str, object] | None


def decode_dashboard_list_item(item: QListWidgetItem | None) -> DecodedDashboardListItem | None:
    if item is None:
        return None
    target = str(item.data(Qt.ItemDataRole.UserRole) or "")
    raw_eid = item.data(Qt.ItemDataRole.UserRole + 1)
    entity_type = item.data(Qt.ItemDataRole.UserRole + 2)
    raw_filter = item.data(Qt.ItemDataRole.UserRole + 3)

    entity_id: int | None = None
    if raw_eid is not None:
        try:
            entity_id = int(raw_eid)
        except (TypeError, ValueError):
            entity_id = None

    entity_type_s = str(entity_type) if entity_type is not None else None

    suggested: dict[str, object] | None = None
    if isinstance(raw_filter, dict):
        suggested = raw_filter
    elif isinstance(raw_filter, str) and raw_filter.strip():
        try:
            parsed = json.loads(raw_filter)
            if isinstance(parsed, dict):
                suggested = parsed
        except json.JSONDecodeError:
            suggested = None

    return DecodedDashboardListItem(
        target=target,
        entity_id=entity_id,
        entity_type=entity_type_s,
        suggested_filter=suggested,
    )


def resolve_route_from_decoded(decoded: DecodedDashboardListItem) -> DashboardActionRoute:
    return resolve_dashboard_action(
        decoded.target,
        entity_id=decoded.entity_id,
        entity_type=decoded.entity_type,
    )
