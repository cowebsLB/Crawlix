from crawlix.ui.controllers_inspector import build_audit_inspector_text


def test_build_audit_inspector_text_contains_header_and_insights() -> None:
    meta = {
        "page_id": 10,
        "url_norm": "https://example.com/x",
        "inbound": 0,
        "issues": [
            {"id": "missing_title", "severity": "high", "message": "No title", "evidence": {"url": "x"}}
        ],
    }
    txt = build_audit_inspector_text(meta)
    assert "Page ID: 10" in txt
    assert "https://example.com/x" in txt
    assert "No title" in txt
