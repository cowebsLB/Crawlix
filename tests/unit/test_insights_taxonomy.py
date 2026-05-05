from crawlix.services.analyzer.insights import (
    IssueCategory,
    build_insights,
    derive_priority,
    normalize_issue_category,
)


def test_category_normalization_maps_known_ids() -> None:
    issue = {"id": "missing_meta_description", "severity": "medium"}
    assert normalize_issue_category(issue) == IssueCategory.METADATA


def test_priority_not_equal_to_severity_low_priority_high_severity_case() -> None:
    # High severity can still be lower priority in weak-context pages.
    pri = derive_priority(
        severity="high",
        confidence="low",
        inbound_internal=0,
        blast_radius=1,
        recurrence_count=1,
    )
    assert pri in ("later", "soon")


def test_priority_not_equal_to_severity_high_priority_medium_case() -> None:
    # Medium severity can become immediate priority with high blast radius/importance.
    pri = derive_priority(
        severity="medium",
        confidence="high",
        inbound_internal=8,
        blast_radius=30,
        recurrence_count=5,
    )
    assert pri == "now"


def test_build_insights_orders_by_priority_then_severity() -> None:
    issues = [
        {"id": "deep_url_path", "severity": "low", "message": "Deep path", "evidence": {}},
        {"id": "non_200_status", "severity": "high", "message": "Bad status", "evidence": {"status": 500}},
    ]
    out = build_insights(issues, inbound_internal=5, blast_radius_by_issue_id={"non_200_status": 20})
    assert out
    assert out[0].summary == "Bad status"
