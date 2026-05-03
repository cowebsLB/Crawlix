"""SERP fetch + best-effort parse — conservative defaults; user responsibility disclaimer in UI."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

import httpx
from sqlalchemy.orm import Session

from crawlix.db.models import Keyword, SerpResult
from crawlix.services.net.ssrf import assert_url_safe_for_fetch
from crawlix.utils.gzip_util import gzip_bytes


def fetch_serp_placeholder(
    session: Session,
    keyword_id: int,
    *,
    client: httpx.Client,
    search_engine: str = "duckduckgo_html",
) -> int:
    """Demo path: fetches DuckDuckGo HTML (respect their ToS in production — swap for API-backed)."""
    kw = session.get(Keyword, keyword_id)
    if not kw:
        raise ValueError("keyword not found")
    q = kw.phrase.replace(" ", "+")
    url = f"https://duckduckgo.com/html/?q={q}"
    assert_url_safe_for_fetch(url)
    resp = client.get(url, timeout=45.0, headers={"User-Agent": "Crawlix/0.1 (research; contact local install)"})
    html = resp.text
    organic: list[dict[str, Any]] = []
    for m in re.finditer(r'class="result__a"[^>]*href="([^"]+)"[^>]*>([^<]+)', html):
        organic.append({"url": m.group(1), "title": m.group(2).strip()})

    sr = SerpResult(
        keyword_id=keyword_id,
        search_engine=search_engine,
        geo=kw.locale,
        device=kw.device,
        results_json={"organic": organic[:20], "raw_note": "best_effort_parser_v1"},
        html_gzip=gzip_bytes(html.encode("utf-8")),
        parser_version="crawlix_serp_v1",
        fetched_at=datetime.now(UTC),
        status="degraded" if resp.status_code != 200 else "ok",
    )
    session.add(sr)
    session.commit()
    session.refresh(sr)
    return sr.id
