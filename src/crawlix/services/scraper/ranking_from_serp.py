"""Derive rank position from parsed SERP organic rows vs project default domain."""

from __future__ import annotations

from typing import Any
from urllib.parse import parse_qs, unquote, urlparse


def effective_url_for_ranking(url: str) -> str:
    """Resolve DuckDuckGo redirect URLs to the target URL when possible."""
    if not url:
        return url
    if "uddg=" in url:
        try:
            q = parse_qs(urlparse(url).query)
            inner = (q.get("uddg") or [None])[0]
            if inner:
                return unquote(inner)
        except Exception:
            pass
    return url


def hostname_from_url(url: str) -> str | None:
    try:
        u = url.strip()
        if not u:
            return None
        if "://" not in u:
            u = "https://" + u
        host = urlparse(u).hostname
        return host.lower() if host else None
    except Exception:
        return None


def host_matches_project_domain(host: str | None, project_domain: str | None) -> bool:
    if not host or not project_domain:
        return False
    pd = project_domain.strip().lower()
    if "://" in pd:
        pd = urlparse(pd).hostname or pd
    if "/" in pd and "://" not in project_domain:
        pd = pd.split("/")[0]
    pd = pd.split(":")[0]
    if not pd:
        return False
    host = host.lower()
    if host == pd:
        return True
    return host.endswith("." + pd)


def compute_rank_for_project_domain(
    organic: list[dict[str, Any]],
    default_domain: str | None,
) -> tuple[int | None, str | None]:
    """
    Return (1-based position, matched organic URL) for the first organic row
    whose effective URL hostname matches ``default_domain`` (including subdomains).
    """
    if not default_domain or not isinstance(organic, list):
        return None, None
    dom = default_domain.strip()
    if not dom:
        return None, None
    for i, row in enumerate(organic):
        raw = row.get("url") or ""
        if not isinstance(raw, str):
            continue
        eff = effective_url_for_ranking(raw)
        host = hostname_from_url(eff)
        if host_matches_project_domain(host, dom):
            return i + 1, raw if isinstance(raw, str) else None
    return None, None
