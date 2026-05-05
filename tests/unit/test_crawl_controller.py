from crawlix.ui.controllers_crawl import build_crawl_hints_text


def test_build_crawl_hints_text_appends_insights() -> None:
    txt = build_crawl_hints_text(
        hints="Canonical mismatch candidate",
        status_code=404,
        depth=2,
        inbound=0,
        outbound=0,
        fallback_no_hints="No hints",
    )
    assert "Canonical mismatch candidate" in txt
    assert "HTTP status is 404" in txt


def test_build_crawl_hints_text_uses_fallback_when_hints_empty() -> None:
    txt = build_crawl_hints_text(
        hints="",
        status_code=None,
        depth=0,
        inbound=1,
        outbound=1,
        fallback_no_hints="No canonical hints",
    )
    assert "No canonical hints" in txt
