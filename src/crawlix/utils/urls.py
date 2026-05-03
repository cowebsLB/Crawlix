"""URL normalization for crawl and dedupe."""

from __future__ import annotations

from urllib.parse import urlparse, urlunparse


def normalize_url(url: str) -> str:
    """Lowercase scheme/host, strip fragment, collapse default ports."""
    p = urlparse(url.strip())
    if not p.scheme or not p.netloc:
        return url.strip()
    netloc = p.netloc.lower()
    scheme = p.scheme.lower()
    if scheme == "http" and netloc.endswith(":80"):
        netloc = netloc[:-3]
    if scheme == "https" and netloc.endswith(":443"):
        netloc = netloc[:-4]
    path = p.path or "/"
    return urlunparse((scheme, netloc, path, p.params, p.query, ""))
