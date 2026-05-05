"""Crawl detail/inspector presentation helpers."""

from __future__ import annotations

from crawlix.services.analyzer.insights import build_insights
from crawlix.ui.inspector_logic import crawl_pseudo_issues
from crawlix.ui.inspector_presenter import insights_to_plain_text


def build_crawl_hints_text(
    *,
    hints: str,
    status_code: int | None,
    depth: int | None,
    inbound: int,
    outbound: int,
    fallback_no_hints: str,
) -> str:
    pseudo = crawl_pseudo_issues(status_code=status_code, depth=depth, inbound=inbound, outbound=outbound)
    insights = build_insights(pseudo, inbound_internal=inbound)
    body = hints or fallback_no_hints
    if insights:
        body += "\n\n" + insights_to_plain_text(insights)
    return body
