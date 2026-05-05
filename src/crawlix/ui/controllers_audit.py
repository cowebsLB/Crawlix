"""Audit page controller helpers."""

from __future__ import annotations


def build_audit_row_meta(
    *,
    page_id: int,
    url_norm: str,
    issues: object,
    inbound: int,
    outbound: int,
) -> dict[str, object]:
    safe_issues = issues if isinstance(issues, list) else []
    return {
        "page_id": int(page_id),
        "url_norm": str(url_norm),
        "issues": safe_issues,
        "inbound": int(inbound),
        "outbound": int(outbound),
    }


def issue_count(issues: object) -> int:
    if isinstance(issues, list):
        return len(issues)
    return 0
