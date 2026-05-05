from crawlix.ui.controllers_serp import build_serp_row_meta, serp_organic_count


def test_serp_organic_count_handles_invalid_shapes() -> None:
    assert serp_organic_count(None) == 0
    assert serp_organic_count({}) == 0
    assert serp_organic_count({"organic": {"x": 1}}) == 0


def test_serp_organic_count_counts_list() -> None:
    assert serp_organic_count({"organic": [1, 2, 3]}) == 3


def test_build_serp_row_meta() -> None:
    m = build_serp_row_meta(
        snapshot_id=9,
        phrase="seo",
        status="ok",
        fetched="2026-05-05",
        organic_rows=11,
        has_html=True,
    )
    assert m["id"] == 9
    assert m["phrase"] == "seo"
    assert m["organic_rows"] == 11
    assert m["has_html"] is True
