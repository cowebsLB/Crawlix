"""Optional GSC / GA4 / Bing — OAuth flows TBD; UI shows connect cards."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class IntegrationStatus:
    provider: str
    connected: bool
    last_sync: str | None


def list_integration_placeholders() -> list[IntegrationStatus]:
    return [
        IntegrationStatus("gsc", False, None),
        IntegrationStatus("ga4", False, None),
        IntegrationStatus("bing_wm", False, None),
    ]
