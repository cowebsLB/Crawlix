from PyQt6.QtCore import QSettings

from crawlix.ui.saved_views import SavedView, SavedViewStore


def test_saved_view_roundtrip() -> None:
    qs = QSettings("COWEBS_TEST", "Crawlix_Test")
    store = SavedViewStore(qs)
    page = "crawl_test"
    original = SavedView(
        search="abc",
        http_filter="4xx",
        depth_filter=2,
        max_inbound=7,
        min_outbound=3,
        dup_only=True,
    )
    store.save(page, original)
    loaded = store.load(page)
    assert loaded.search == "abc"
    assert loaded.http_filter == "4xx"
    assert loaded.depth_filter == 2
    assert loaded.max_inbound == 7
    assert loaded.min_outbound == 3
    assert loaded.dup_only is True
