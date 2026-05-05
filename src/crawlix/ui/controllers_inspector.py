"""Inspector presentation controller helpers."""

from __future__ import annotations

from crawlix.services.analyzer.insights import build_insights
from crawlix.ui.inspector_presenter import insights_to_plain_text


def build_audit_inspector_text(meta: dict[str, object]) -> str:
    issues = meta.get("issues")
    if not isinstance(issues, list):
        issues = []
    inbound = int(meta.get("inbound") or 0)
    insights = build_insights(issues, inbound_internal=inbound)
    header = f"Page ID: {meta.get('page_id')}\\nURL: {meta.get('url_norm')}\\n"
    return header + "\\n" + insights_to_plain_text(insights)
