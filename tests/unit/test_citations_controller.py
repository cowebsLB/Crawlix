from crawlix.ui.controllers_citations import build_citation_check_row_meta, clipped_error, clipped_url


def test_clipped_url_behavior() -> None:
    assert clipped_url("short") == "short"
    assert clipped_url("x" * 100, max_len=10) == "xxxxxxx..."


def test_clipped_error_behavior() -> None:
    assert clipped_error("abc", max_len=5) == "abc"
    assert clipped_error("abcdefgh", max_len=5) == "abcde"


def test_build_citation_check_row_meta() -> None:
    m = build_citation_check_row_meta(
        check_id=1,
        fetched="2026-05-05",
        location="HQ",
        source="Yelp",
        status="ok",
        http_status=200,
        final_url="https://x",
        error="",
    )
    assert m["id"] == 1
    assert m["location"] == "HQ"
    assert m["http_status"] == 200
