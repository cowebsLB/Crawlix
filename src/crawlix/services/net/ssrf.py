"""Block private / link-local URLs when policy disallows intranet fetches."""

from __future__ import annotations

import ipaddress
from urllib.parse import urlparse


def host_is_blocked(host: str, *, allow_private: bool = False) -> bool:
    if allow_private:
        return False
    host = host.strip("[]")
    try:
        addr = ipaddress.ip_address(host)
        return bool(
            addr.is_private
            or addr.is_loopback
            or addr.is_link_local
            or addr.is_reserved
            or addr.is_multicast
        )
    except ValueError:
        return False


def assert_url_safe_for_fetch(url: str, *, allow_private: bool = False) -> None:
    p = urlparse(url)
    if p.scheme not in ("http", "https"):
        raise ValueError("Only http(s) URLs are allowed")
    host = p.hostname
    if not host:
        raise ValueError("Missing hostname")
    if host_is_blocked(host, allow_private=allow_private):
        raise ValueError("Private or local addresses are blocked by SSRF policy")
