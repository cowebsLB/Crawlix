"""Unit tests for crawl_overview helpers."""

from types import SimpleNamespace

from crawlix.services.crawler.crawl_overview import (
    crawl_summary_metrics,
    duplicate_cluster_count,
    duplicate_final_counts,
    effective_final_url,
    format_internal_link_insights,
    http_error_count,
    normalization_hints,
    path_segment_counts,
    path_segment_lines_from_norms,
)


def _p(url_norm: str, url_final: str | None = None, depth: int = 0, status: int | None = 200):
    return SimpleNamespace(url_norm=url_norm, url_final=url_final, crawl_depth=depth, status_code=status)


def test_effective_final_url():
    p = _p("https://a.com/x", "https://a.com/y")
    assert effective_final_url(p) == "https://a.com/y"
    p2 = _p("https://a.com/z", None)
    assert effective_final_url(p2) == "https://a.com/z"


def test_duplicate_clusters():
    pages = [
        _p("https://a.com/1", "https://a.com/f"),
        _p("https://a.com/2", "https://a.com/f"),
        _p("https://a.com/3", "https://a.com/g"),
    ]
    assert duplicate_final_counts(pages)["https://a.com/f"] == 2
    assert duplicate_cluster_count(pages) == 1


def test_crawl_summary_metrics():
    pages = [
        _p("https://a.com/a", "https://a.com/x", 1, 200),
        _p("https://a.com/b", "https://a.com/x", 2, 404),
        _p("https://a.com/c", "https://a.com/y", 2, 200),
    ]
    m = crawl_summary_metrics(pages)
    assert m["pages"] == 3
    assert m["unique_final_urls"] == 2
    assert m["duplicate_clusters"] == 1
    assert m["max_depth"] == 2
    assert m["avg_depth"] == round((1 + 2 + 2) / 3, 2)
    assert m["http_errors"] == 1


def test_http_error_count():
    assert http_error_count([_p("u", "f", 0, 200), _p("u2", "f2", 0, 500)]) == 1


def test_path_segment_counts():
    pages = [
        _p("https://ex.com/html/about"),
        _p("https://ex.com/pages/web/x"),
        _p("https://ex.com/html/contact"),
    ]
    segs = path_segment_counts(pages)
    assert dict(segs) == {"/html/": 2, "/pages/": 1}


def test_path_segment_lines_from_norms():
    norms = ["https://ex.com/html/about", "https://ex.com/pages/web/x"]
    assert dict(path_segment_lines_from_norms(norms)) == {"/html/": 1, "/pages/": 1}


def test_normalization_hints_dup():
    text = normalization_hints("https://x/a.html", "https://x/a", dup_group_size=3)
    assert "html" in text.lower() or "cleaner" in text.lower()
    assert "3" in text


def test_format_internal_link_insights():
    pages = [(1, "https://ex.com/", 0), (2, "https://ex.com/p", 2)]
    in_map = {"https://ex.com/": 0, "https://ex.com/p": 5}
    out_map = {1: 20, 2: 0}
    txt = format_internal_link_insights(pages, in_map, out_map, top_n=3)
    assert "0 internal inbound" in txt
    assert "https://ex.com/" in txt
