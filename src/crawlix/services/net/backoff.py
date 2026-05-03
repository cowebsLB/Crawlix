"""429 / 5xx exponential backoff (max 5 retries, cap 60s)."""

from __future__ import annotations

import time


def sleep_for_retry(retry_count: int, cap_s: int = 60) -> None:
    delay = min(cap_s, 2**retry_count)
    time.sleep(delay)
