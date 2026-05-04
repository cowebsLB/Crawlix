"""On-page audit — titles, meta, headings, canonical, indexability, scoring."""

from __future__ import annotations

import hashlib
import re
from urllib.parse import urljoin, urlparse

from selectolax.parser import HTMLParser

from crawlix.utils.urls import normalize_url

_TITLE_SHORT = 15
_TITLE_LONG = 60
_PATH_SEGMENTS_DEEP = 6


def content_fingerprint(html: str, *, max_chars: int = 4000) -> str:
    """Lightweight body text fingerprint for duplicate-content heuristics."""
    tree = HTMLParser(html)
    for bad in tree.css("script, style, noscript"):
        bad.remove()
    body = tree.body
    text = body.text() if body else (tree.root.text() if tree.root else "")
    if not text:
        return ""
    collapsed = re.sub(r"\s+", " ", text).strip()[:max_chars]
    return hashlib.sha256(collapsed.encode("utf-8", errors="ignore")).hexdigest()[:32]


def _severity_penalty(severity: str) -> float:
    return {"high": 15.0, "medium": 8.0, "low": 3.0}.get(severity, 3.0)


def score_from_issues(issues: list[dict]) -> tuple[float, dict[str, float]]:
    cats: dict[str, float] = {}
    penalties: dict[str, float] = {}
    for issue in issues:
        cat = str(issue.get("category") or "general")
        penalties[cat] = penalties.get(cat, 0.0) + _severity_penalty(str(issue.get("severity", "low")))
    if not penalties:
        return 100.0, {"metadata": 100.0, "content": 100.0, "indexability": 100.0, "canonical": 100.0, "links": 100.0, "url_structure": 100.0, "duplicates": 100.0}
    for cat, pen in penalties.items():
        cats[cat] = max(0.0, 100.0 - pen)
    overall = sum(cats.values()) / len(cats)
    for default in ("metadata", "content", "indexability", "canonical", "links", "url_structure", "duplicates"):
        cats.setdefault(default, 100.0)
    return overall, cats


def _header_value(headers: dict[str, str] | None, name: str) -> str:
    if not headers:
        return ""
    for k, v in headers.items():
        if k.lower() == name.lower():
            return v or ""
    return ""


def _meta_robots_noindex(tree: HTMLParser) -> bool:
    for meta in tree.css("meta"):
        name = (meta.attributes.get("name") or meta.attributes.get("http-equiv") or "").lower()
        if name not in ("robots", "googlebot"):
            continue
        content = (meta.attributes.get("content") or "").lower()
        if "noindex" in content:
            return True
    return False


def _x_robots_noindex(header_val: str) -> bool:
    parts = header_val.lower().replace(",", " ").split()
    return "noindex" in parts


def _collect_canonical_hrefs(tree: HTMLParser, base_url: str) -> list[str]:
    hrefs: list[str] = []
    for node in tree.css('link[rel][href]'):
        rel = (node.attributes.get("rel") or "").lower()
        if "canonical" not in rel.split():
            continue
        href = (node.attributes.get("href") or "").strip()
        if not href:
            continue
        joined = urljoin(base_url, href)
        hrefs.append(normalize_url(joined))
    return hrefs


def _path_segment_count(url: str) -> int:
    path = urlparse(url).path or "/"
    segs = [s for s in path.strip("/").split("/") if s]
    return len(segs)


def audit_html(
    html: str,
    url: str,
    *,
    url_final: str | None = None,
    status_code: int | None = None,
    response_headers: dict[str, str] | None = None,
    robots_txt_blocked: bool = False,
    outbound_internal: int | None = None,
    inbound_internal: int | None = None,
    crawl_depth: int | None = None,
) -> tuple[float, list[dict], dict[str, float]]:
    tree = HTMLParser(html)
    issues: list[dict] = []

    title_el = tree.css_first("title")
    title = title_el.text().strip() if title_el and title_el.text() else ""
    if not title:
        issues.append(
            {
                "id": "missing_title",
                "severity": "high",
                "category": "metadata",
                "message": "Document has no <title>",
                "evidence": {"url": url},
            }
        )
    else:
        tlen = len(title)
        if tlen < _TITLE_SHORT:
            issues.append(
                {
                    "id": "short_title",
                    "severity": "low",
                    "category": "metadata",
                    "message": "Title is very short for search snippets",
                    "evidence": {"length": tlen, "threshold_max": _TITLE_SHORT},
                }
            )
        if tlen > _TITLE_LONG:
            issues.append(
                {
                    "id": "long_title",
                    "severity": "low",
                    "category": "metadata",
                    "message": "Title may be truncated in search results",
                    "evidence": {"length": tlen, "threshold_max": _TITLE_LONG},
                }
            )

    desc = tree.css_first('meta[name="description"]')
    if not desc or not desc.attributes.get("content"):
        issues.append(
            {
                "id": "missing_meta_description",
                "severity": "medium",
                "category": "metadata",
                "message": "Missing meta description",
                "evidence": {},
            }
        )

    h1s = tree.css("h1")
    if len(h1s) == 0:
        issues.append(
            {
                "id": "missing_h1",
                "severity": "medium",
                "category": "content",
                "message": "No H1 heading",
                "evidence": {},
            }
        )
    elif len(h1s) > 1:
        issues.append(
            {
                "id": "multiple_h1",
                "severity": "low",
                "category": "content",
                "message": "Multiple H1 elements",
                "evidence": {"count": len(h1s)},
            }
        )

    base = url_final or url
    canon_hrefs = _collect_canonical_hrefs(tree, base)
    if not canon_hrefs:
        issues.append(
            {
                "id": "missing_canonical",
                "severity": "medium",
                "category": "canonical",
                "message": "No canonical link (rel=canonical) found",
                "evidence": {},
            }
        )
    elif len(canon_hrefs) > 1:
        uniq = sorted(set(canon_hrefs))
        if len(uniq) > 1:
            issues.append(
                {
                    "id": "multiple_canonical_tags",
                    "severity": "high",
                    "category": "canonical",
                    "message": "Multiple canonical link tags with different targets",
                    "evidence": {"hrefs": uniq[:10]},
                }
            )
        else:
            issues.append(
                {
                    "id": "duplicate_canonical_tags",
                    "severity": "low",
                    "category": "canonical",
                    "message": "More than one canonical link tag (same href)",
                    "evidence": {"href": uniq[0] if uniq else "", "tag_count": len(canon_hrefs)},
                }
            )
    elif len(canon_hrefs) == 1:
        cnorm = canon_hrefs[0]
        norm_req = normalize_url(url)
        norm_final = normalize_url(url_final) if url_final else norm_req
        if cnorm != norm_final and cnorm != norm_req:
            issues.append(
                {
                    "id": "canonical_mismatch",
                    "severity": "medium",
                    "category": "canonical",
                    "message": "Canonical URL does not match this page's URL (after redirects)",
                    "evidence": {"canonical": cnorm, "url_norm": norm_req, "url_final": norm_final},
                }
            )

    if _meta_robots_noindex(tree):
        issues.append(
            {
                "id": "meta_noindex",
                "severity": "high",
                "category": "indexability",
                "message": "Meta robots includes noindex",
                "evidence": {},
            }
        )
    xr = _header_value(response_headers, "x-robots-tag")
    if xr and _x_robots_noindex(xr):
        issues.append(
            {
                "id": "header_noindex",
                "severity": "high",
                "category": "indexability",
                "message": "X-Robots-Tag includes noindex",
                "evidence": {"value": xr[:200]},
            }
        )

    if robots_txt_blocked:
        issues.append(
            {
                "id": "robots_txt_blocked",
                "severity": "high",
                "category": "indexability",
                "message": "URL is disallowed by robots.txt (at audit time)",
                "evidence": {},
            }
        )

    if status_code is not None and status_code != 200:
        issues.append(
            {
                "id": "non_200_status",
                "severity": "high" if status_code >= 400 else "medium",
                "category": "indexability",
                "message": f"HTTP status is {status_code}, not 200 OK",
                "evidence": {"status_code": status_code},
            }
        )

    if inbound_internal is not None and crawl_depth is not None and crawl_depth > 0 and inbound_internal == 0:
        issues.append(
            {
                "id": "orphan_internal",
                "severity": "medium",
                "category": "links",
                "message": "No internal inbound links from other crawled pages (orphan beyond seed depth)",
                "evidence": {"inbound_internal": 0, "crawl_depth": crawl_depth},
            }
        )

    if outbound_internal is not None and outbound_internal == 0 and crawl_depth is not None and crawl_depth < 10:
        issues.append(
            {
                "id": "no_internal_outlinks",
                "severity": "low",
                "category": "links",
                "message": "Page has no internal outlinks in the crawl graph",
                "evidence": {"outbound_internal": 0},
            }
        )

    segs = _path_segment_count(url)
    if segs > _PATH_SEGMENTS_DEEP:
        issues.append(
            {
                "id": "deep_url_path",
                "severity": "low",
                "category": "url_structure",
                "message": "URL path is very deep (many segments)",
                "evidence": {"segments": segs, "threshold": _PATH_SEGMENTS_DEEP},
            }
        )

    overall, cats = score_from_issues(issues)
    return overall, issues, cats
