from crawlix.ui.controllers_audit import build_audit_row_meta, issue_count


def test_issue_count_handles_non_list() -> None:
    assert issue_count(None) == 0
    assert issue_count({"a": 1}) == 0
    assert issue_count([1, 2, 3]) == 3


def test_build_audit_row_meta_normalizes_payload() -> None:
    meta = build_audit_row_meta(
        page_id=5,
        url_norm="https://example.com/p",
        issues={"bad": True},
        inbound=2,
        outbound=3,
    )
    assert meta["page_id"] == 5
    assert meta["url_norm"] == "https://example.com/p"
    assert meta["issues"] == []
    assert meta["inbound"] == 2
    assert meta["outbound"] == 3
