from crawlix.services.analyzer.audit import audit_html, content_fingerprint


def test_audit_finds_missing_title() -> None:
    score, issues, _cats = audit_html("<html><body><h1>x</h1></body></html>", "https://a.test/")
    assert any(i["id"] == "missing_title" for i in issues)
    assert score < 100


def test_long_title_issue() -> None:
    long = "W" * 61
    html = f"<html><head><title>{long}</title></head><body><h1>x</h1></body></html>"
    _s, issues, _ = audit_html(html, "https://a.test/page")
    assert any(i["id"] == "long_title" for i in issues)


def test_missing_canonical() -> None:
    html = "<html><head><title>ok</title></head><body><h1>x</h1></body></html>"
    _s, issues, _ = audit_html(html, "https://a.test/")
    assert any(i["id"] == "missing_canonical" for i in issues)


def test_meta_noindex() -> None:
    html = (
        '<html><head><title>t</title>'
        '<meta name="robots" content="noindex,follow"/>'
        "</head><body><h1>x</h1></body></html>"
    )
    _s, issues, _ = audit_html(html, "https://a.test/")
    assert any(i["id"] == "meta_noindex" for i in issues)


def test_non_200_status() -> None:
    html = "<html><head><title>t</title></head><body><h1>x</h1></body></html>"
    _s, issues, _ = audit_html(html, "https://a.test/", status_code=404)
    assert any(i["id"] == "non_200_status" for i in issues)


def test_content_fingerprint_stable() -> None:
    h = "<html><body><script>z</script><p>Hello  world</p></body></html>"
    a = content_fingerprint(h)
    b = content_fingerprint(h)
    assert a == b and len(a) == 32


def test_canonical_mismatch() -> None:
    html = (
        "<html><head><title>t</title>"
        '<link rel="canonical" href="https://other.example/page"/>'
        "</head><body><h1>x</h1></body></html>"
    )
    _s, issues, _ = audit_html(html, "https://a.test/here", url_final="https://a.test/here")
    assert any(i["id"] == "canonical_mismatch" for i in issues)
