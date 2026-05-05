from crawlix.ui.inspector_logic import citation_pseudo_issues, crawl_pseudo_issues, serp_pseudo_issues


def test_crawl_pseudo_issues_flags_critical_http_and_link_signals() -> None:
    issues = crawl_pseudo_issues(status_code=500, depth=2, inbound=0, outbound=0)
    ids = {i["id"] for i in issues}
    assert "non_200_status" in ids
    assert "orphan_internal" in ids
    assert "no_internal_outlinks" in ids


def test_serp_pseudo_issues_flags_non_ok_and_empty() -> None:
    issues = serp_pseudo_issues(status="error", organic_rows=0)
    ids = {i["id"] for i in issues}
    assert "crawl_efficiency_sparse_serp" in ids
    assert "technical_health_serp_status" in ids


def test_citation_pseudo_issues_uses_status_and_http() -> None:
    issues = citation_pseudo_issues(status="error", http_status=404)
    ids = {i["id"] for i in issues}
    assert "technical_health_citation_status" in ids
    assert "technical_health_citation_http" in ids
