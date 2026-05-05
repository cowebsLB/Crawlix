"""Sticky proxy per logical job; rotate between jobs only."""

from __future__ import annotations

import itertools
import threading
from dataclasses import dataclass
from typing import Any

import httpx

from crawlix.services.net.ssrf import httpx_event_hooks_ssrf


@dataclass
class ProxyEntry:
    id: int
    proxy_url: str
    username: str | None = None
    password: str | None = None


class ProxyManager:
    """Round-robin assignment for new jobs; each job_id keeps one client until cleared."""

    def __init__(self, proxies: list[ProxyEntry] | None = None) -> None:
        self._lock = threading.Lock()
        self._proxies = proxies or []
        self._cycle = itertools.cycle(range(len(self._proxies))) if self._proxies else None
        self._job_clients: dict[str, httpx.Client] = {}

    def set_proxies(self, proxies: list[ProxyEntry]) -> None:
        with self._lock:
            self._proxies = proxies
            self._cycle = itertools.cycle(range(len(self._proxies))) if self._proxies else None
            for c in self._job_clients.values():
                c.close()
            self._job_clients.clear()

    def next_for_new_job(self) -> ProxyEntry | None:
        with self._lock:
            if not self._proxies or self._cycle is None:
                return None
            idx = next(self._cycle)
            return self._proxies[idx]

    def client_for_job(self, job_key: str, proxy: ProxyEntry | None) -> httpx.Client:
        """Return sticky client for job_key; create if missing."""
        with self._lock:
            if job_key in self._job_clients:
                return self._job_clients[job_key]
            mounts: dict[str, Any] = {}
            if proxy:
                mounts["all://"] = httpx.HTTPTransport(proxy=proxy.proxy_url)
            client = httpx.Client(
                mounts=mounts,
                timeout=httpx.Timeout(30.0, connect=10.0),
                follow_redirects=True,
                event_hooks=httpx_event_hooks_ssrf(allow_private=False),
            )
            if proxy and proxy.username:
                # Basic proxy auth often in URL; httpx accepts proxy_url with creds
                pass
            self._job_clients[job_key] = client
            return client

    def release_job(self, job_key: str) -> None:
        with self._lock:
            c = self._job_clients.pop(job_key, None)
            if c is not None:
                c.close()
