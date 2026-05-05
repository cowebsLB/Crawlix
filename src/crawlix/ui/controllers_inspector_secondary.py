"""SERP and citation inspector text builders."""

from __future__ import annotations

from crawlix.services.analyzer.insights import build_insights
from crawlix.ui.inspector_logic import citation_pseudo_issues, serp_pseudo_issues
from crawlix.ui.inspector_presenter import insights_to_plain_text


def build_serp_inspector_text(meta: dict[str, object]) -> str:
    status = str(meta.get("status") or "")
    organic = int(meta.get("organic_rows") or 0)
    pseudo = serp_pseudo_issues(status=status, organic_rows=organic)
    insights = build_insights(pseudo, inbound_internal=1)
    txt = (
        f"Snapshot ID: {meta.get('id')}\n"
        f"Keyword: {meta.get('phrase')}\n"
        f"Fetched: {meta.get('fetched')}\n"
        f"Status: {status}\n"
        f"Organic rows: {organic}\n"
    )
    return txt + "\n" + insights_to_plain_text(insights)


def build_citation_inspector_text(meta: dict[str, object]) -> str:
    status = str(meta.get("status") or "")
    raw_sc = meta.get("http_status")
    sc = raw_sc if isinstance(raw_sc, int) else None
    pseudo = citation_pseudo_issues(status=status, http_status=sc)
    insights = build_insights(pseudo, inbound_internal=1)
    txt = (
        f"Check ID: {meta.get('id')}\n"
        f"When: {meta.get('fetched')}\n"
        f"Location: {meta.get('location')}\n"
        f"Source: {meta.get('source')}\n"
        f"Status: {status or '—'}\n"
        f"HTTP: {'' if sc is None else sc}\n"
        f"URL: {meta.get('final_url') or ''}\n"
    )
    return txt + "\n" + insights_to_plain_text(insights)
