from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QListWidgetItem

from crawlix.ui.dashboard_action_runner import decode_dashboard_list_item, resolve_route_from_decoded


def test_decode_suggested_filter_json_roundtrip() -> None:
    it = QListWidgetItem("x")
    it.setData(Qt.ItemDataRole.UserRole, "crawl:start")
    it.setData(Qt.ItemDataRole.UserRole + 3, '{"apply_saved_crawl_view": true}')
    d = decode_dashboard_list_item(it)
    assert d is not None
    assert d.target == "crawl:start"
    assert d.suggested_filter == {"apply_saved_crawl_view": True}
    r = resolve_route_from_decoded(d)
    assert r.focus_crawl_seeds is True
