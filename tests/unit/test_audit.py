from crawlix.services.analyzer.audit import audit_html


def test_audit_finds_missing_title() -> None:
    score, issues, _cats = audit_html("<html><body><h1>x</h1></body></html>", "https://a.test/")
    assert any(i["id"] == "missing_title" for i in issues)
    assert score < 100
