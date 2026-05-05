from __future__ import annotations

import json
from dataclasses import dataclass

from PyQt6.QtCore import QSettings


@dataclass
class SavedView:
    search: str = ""
    http_filter: str | None = None
    depth_filter: int | None = None
    max_inbound: int = -1
    min_outbound: int = -1
    dup_only: bool = False


class SavedViewStore:
    def __init__(self, qsettings: QSettings) -> None:
        self._qs = qsettings

    def load(self, page_key: str, view_key: str = "default") -> SavedView:
        raw = self._qs.value(f"ui/saved_view/{page_key}/{view_key}", "", str)
        if not raw:
            return SavedView()
        try:
            data = json.loads(str(raw))
        except Exception:
            return SavedView()
        return SavedView(
            search=str(data.get("search") or ""),
            http_filter=data.get("http_filter"),
            depth_filter=data.get("depth_filter"),
            max_inbound=int(data.get("max_inbound", -1)),
            min_outbound=int(data.get("min_outbound", -1)),
            dup_only=bool(data.get("dup_only", False)),
        )

    def save(self, page_key: str, value: SavedView, view_key: str = "default") -> None:
        payload = {
            "search": value.search,
            "http_filter": value.http_filter,
            "depth_filter": value.depth_filter,
            "max_inbound": int(value.max_inbound),
            "min_outbound": int(value.min_outbound),
            "dup_only": bool(value.dup_only),
        }
        self._qs.setValue(f"ui/saved_view/{page_key}/{view_key}", json.dumps(payload, ensure_ascii=True))
