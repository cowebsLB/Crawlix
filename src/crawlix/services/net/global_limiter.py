"""Global outbound TCP cap across modules (plan: default 4)."""

from __future__ import annotations

import threading

from crawlix.config import PolitenessDefaults


class GlobalOutboundLimiter:
    def __init__(self, cap: int | None = None) -> None:
        self._sem = threading.BoundedSemaphore(cap or PolitenessDefaults.global_outbound_tcp_cap)

    def acquire(self) -> None:
        self._sem.acquire()

    def release(self) -> None:
        self._sem.release()

    def __enter__(self) -> None:
        self.acquire()

    def __exit__(self, *args) -> None:  # noqa: ANN001
        self.release()
