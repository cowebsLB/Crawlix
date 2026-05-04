"""Live robots.txt check for audit jobs (may differ from crawl-time rules)."""

from __future__ import annotations

from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx


def url_allowed_by_robots(client: httpx.Client, url: str, *, cache: dict[str, RobotFileParser]) -> bool:
    base = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
    if base not in cache:
        rp = RobotFileParser()
        try:
            r = client.get(f"{base}/robots.txt", timeout=10.0)
            if r.status_code == 200:
                rp.parse(r.text.splitlines())
            else:
                rp.parse([])
        except Exception:
            rp.parse([])
        cache[base] = rp
    rp = cache[base]
    try:
        return rp.can_fetch("*", url)
    except Exception:
        return True
