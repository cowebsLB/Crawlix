"""Block private / link-local URLs when policy disallows intranet fetches."""

from __future__ import annotations

import ipaddress
import socket
import threading
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeout
from typing import Any
from urllib.parse import urlparse

import httpx

# DNS lookups must not block the UI thread; short timeout per lookup.
_DNS_POOL = ThreadPoolExecutor(max_workers=4, thread_name_prefix="ssrf_dns")
_DNS_CACHE_TTL_SEC = 60.0
_DNS_RESOLVE_TIMEOUT_SEC = 2.0
_DNS_CACHE_MAX = 512

_dns_cache_lock = threading.Lock()
# hostname lower -> (monotonic_expiry, tuple of canonical IP strings)
_dns_positive_cache: dict[str, tuple[float, tuple[str, ...]]] = {}


def _cache_put(host_key: str, ips: tuple[str, ...]) -> None:
    now = time.monotonic()
    with _dns_cache_lock:
        if len(_dns_positive_cache) >= _DNS_CACHE_MAX:
            # Drop arbitrary oldest bucket by clearing half (simple cap).
            for k in list(_dns_positive_cache.keys())[: _DNS_CACHE_MAX // 2]:
                _dns_positive_cache.pop(k, None)
        _dns_positive_cache[host_key] = (now + _DNS_CACHE_TTL_SEC, ips)


def _cache_get(host_key: str) -> tuple[str, ...] | None:
    now = time.monotonic()
    with _dns_cache_lock:
        ent = _dns_positive_cache.get(host_key)
        if not ent:
            return None
        exp, ips = ent
        if exp < now:
            del _dns_positive_cache[host_key]
            return None
        return ips


def _addr_blocked(addr: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    return bool(
        addr.is_private
        or addr.is_loopback
        or addr.is_link_local
        or addr.is_reserved
        or addr.is_multicast
    )


def host_is_blocked(host: str, *, allow_private: bool = False) -> bool:
    if allow_private:
        return False
    host = host.strip("[]")
    try:
        addr = ipaddress.ip_address(host)
        return _addr_blocked(addr)
    except ValueError:
        return False


def _getaddrinfo_ips(hostname: str) -> tuple[str, ...]:
    infos = socket.getaddrinfo(hostname, None, type=socket.SOCK_STREAM)
    out: list[str] = []
    seen: set[str] = set()
    for fam, _, _, _, sockaddr in infos:
        if fam not in (socket.AF_INET, socket.AF_INET6):
            continue
        ip = sockaddr[0]
        a = ipaddress.ip_address(ip)
        k = str(a)
        if k not in seen:
            seen.add(k)
            out.append(k)
    if not out:
        raise OSError(f"No addresses for host {hostname!r}")
    return tuple(out)


def _resolve_hostname_ips(hostname: str, *, timeout: float = _DNS_RESOLVE_TIMEOUT_SEC) -> tuple[str, ...]:
    """Return unique resolved IPs for hostname (A + AAAA). Raises on failure."""
    fut = _DNS_POOL.submit(_getaddrinfo_ips, hostname)
    try:
        return fut.result(timeout=timeout)
    except FuturesTimeout as e:
        raise ValueError("DNS resolution timed out (SSRF check)") from e


def assert_url_safe_for_fetch(url: str, *, allow_private: bool = False) -> None:
    """
    Enforce outbound fetch policy.

    - Literal IPs: blocked when private/local unless ``allow_private``.
    - Hostnames: resolve via DNS; **block if any A/AAAA maps to a blocked range**.
      Cached briefly to reduce resolver chatter.

    For **``httpx.Client``** with **``follow_redirects=True``**, also install
    :func:`httpx_event_hooks_ssrf` so each redirect request URL is checked.
    """
    p = urlparse(url)
    if p.scheme not in ("http", "https"):
        raise ValueError("Only http(s) URLs are allowed")
    host = p.hostname
    if not host:
        raise ValueError("Missing hostname")

    if allow_private:
        return

    host_key = host.lower()
    try:
        ipaddress.ip_address(host.strip("[]"))
        if host_is_blocked(host, allow_private=False):
            raise ValueError("Private or local addresses are blocked by SSRF policy")
        return
    except ValueError:
        pass

    cached = _cache_get(host_key)
    if cached is None:
        cached = _resolve_hostname_ips(host)
        _cache_put(host_key, cached)

    for ip_s in cached:
        addr = ipaddress.ip_address(ip_s)
        if _addr_blocked(addr):
            raise ValueError("Resolved address is private or local (SSRF policy)")


def clear_ssrf_dns_cache() -> None:
    """Clear cached DNS results (tests, or after changing resolver policy)."""
    with _dns_cache_lock:
        _dns_positive_cache.clear()


def httpx_event_hooks_ssrf(*, allow_private: bool = False) -> dict[str, list[Callable[..., Any]]]:
    """
    Event hooks for ``httpx.Client`` so **every** outbound URL is checked — including
    each redirect hop when ``follow_redirects=True``.
    """

    def on_request(request: httpx.Request) -> None:
        assert_url_safe_for_fetch(str(request.url), allow_private=allow_private)

    return {"request": [on_request]}
