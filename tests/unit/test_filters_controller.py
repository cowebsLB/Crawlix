from crawlix.ui.controllers_filters import (
    audit_filter_field_labels,
    crawl_depth_filter_options,
    crawl_http_filter_options,
)


def test_crawl_http_filter_options_order_and_values() -> None:
    options = crawl_http_filter_options()
    assert [opt.label for opt in options] == ["Any", "2xx", "3xx", "4xx", "5xx", "Errors (≥400)", "No status"]
    assert [opt.value for opt in options] == [None, "2xx", "3xx", "4xx", "5xx", "err", "none"]


def test_crawl_depth_filter_options_includes_any_and_range() -> None:
    options = crawl_depth_filter_options(max_depth=3)
    assert [opt.label for opt in options] == ["Any", "0", "1", "2", "3"]
    assert [opt.value for opt in options] == [None, 0, 1, 2, 3]


def test_audit_filter_field_labels_stable() -> None:
    assert audit_filter_field_labels() == ("Search URL:", "Max score (≤):", "Min issues (≥):")
