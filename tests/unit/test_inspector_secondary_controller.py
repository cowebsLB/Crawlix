from crawlix.ui.controllers_inspector_secondary import build_citation_inspector_text, build_serp_inspector_text


def test_build_serp_inspector_text_contains_snapshot_context() -> None:
    meta = {"id": 1, "phrase": "seo tool", "fetched": "2026-05-05T00:00:00", "status": "error", "organic_rows": 0}
    txt = build_serp_inspector_text(meta)
    assert "Snapshot ID: 1" in txt
    assert "seo tool" in txt
    assert "SERP snapshot status is not OK" in txt


def test_build_citation_inspector_text_contains_check_context() -> None:
    meta = {
        "id": 9,
        "fetched": "2026-05-05T00:00:00",
        "location": "HQ",
        "source": "Yelp",
        "status": "error",
        "http_status": 404,
        "final_url": "https://example.test",
    }
    txt = build_citation_inspector_text(meta)
    assert "Check ID: 9" in txt
    assert "HQ" in txt
    assert "HTTP 404 from citation source" in txt
