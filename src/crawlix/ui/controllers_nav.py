"""Navigation rail configuration and localization helpers."""

from __future__ import annotations

from collections.abc import Callable

NAV_SLUGS: tuple[str, ...] = (
    "dashboard",
    "crawl",
    "audit",
    "keywords",
    "citations",
    "local",
    "integrations",
    "reports",
    "settings",
)

NAV_GROUPS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Overview", ("dashboard",)),
    ("Technical SEO", ("crawl", "audit")),
    ("Discovery", ("keywords", "citations", "local")),
    ("Output", ("reports",)),
    ("System", ("integrations", "settings")),
)


def localized_nav_labels(tr: Callable[[str], str]) -> dict[str, str]:
    return {
        "dashboard": tr("Dashboard"),
        "crawl": tr("Crawl"),
        "audit": tr("Audit"),
        "keywords": tr("Keywords / SERP"),
        "citations": tr("Citations"),
        "local": tr("Local"),
        "integrations": tr("Integrations"),
        "reports": tr("Reports"),
        "settings": tr("Settings"),
    }
