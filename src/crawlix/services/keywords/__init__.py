"""Keyword helpers: templates and project SEO context."""

from crawlix.services.keywords.templates import (
    COUNTRY_CHOICES,
    SITE_TYPE_CHOICES,
    TemplateContext,
    merge_context_from_project,
    suggest_phrases,
)

__all__ = [
    "COUNTRY_CHOICES",
    "SITE_TYPE_CHOICES",
    "TemplateContext",
    "merge_context_from_project",
    "suggest_phrases",
]
