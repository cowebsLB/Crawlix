from crawlix.services.analyzer.site_audit import cross_page_issues_for_batch


def test_duplicate_title_across_pages() -> None:
    rows = [
        {"page_id": 1, "url_norm": "https://ex.test/a", "url_final": None, "title": "Same", "content_fp": "a"},
        {"page_id": 2, "url_norm": "https://ex.test/b", "url_final": None, "title": "Same", "content_fp": "b"},
    ]
    extras = cross_page_issues_for_batch(rows)
    assert any(i["id"] == "duplicate_title_site" for i in extras[1])
    assert any(i["id"] == "duplicate_title_site" for i in extras[2])


def test_multiple_paths_same_final() -> None:
    rows = [
        {
            "page_id": 1,
            "url_norm": "https://ex.test/old",
            "url_final": "https://ex.test/new",
            "title": "T",
            "content_fp": "x",
        },
        {
            "page_id": 2,
            "url_norm": "https://ex.test/new",
            "url_final": "https://ex.test/new",
            "title": "T2",
            "content_fp": "y",
        },
    ]
    extras = cross_page_issues_for_batch(rows)
    assert any(i["id"] == "multiple_paths_same_destination" for i in extras[1])
    assert any(i["id"] == "multiple_paths_same_destination" for i in extras[2])


def test_mixed_prefixes_when_many_roots() -> None:
    rows = [
        {"page_id": i, "url_norm": f"https://ex.test/{seg}/p", "url_final": None, "title": "", "content_fp": ""}
        for i, seg in enumerate(["a", "b", "c", "d"], start=1)
    ]
    extras = cross_page_issues_for_batch(rows, diverse_prefix_threshold=4)
    assert any(i["id"] == "mixed_top_level_path_prefixes" for i in extras[1])
