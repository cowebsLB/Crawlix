"""Tests for keyword template suggestions."""

from crawlix.services.keywords.templates import TemplateContext, suggest_phrases


def test_suggest_dedupes_and_respects_existing() -> None:
    ctx = TemplateContext(
        site_type="saas",
        country_code="US",
        brand="Acme",
        topic="invoicing",
        city="",
        region="",
        domain="acme.com",
        year="2026",
    )
    phrases = suggest_phrases(ctx, existing_lower={"invoicing software".casefold()}, max_suggestions=20)
    assert all(isinstance(p, str) for p in phrases)
    assert len(phrases) == len({p.casefold() for p in phrases})
    assert "invoicing software" not in phrases


def test_local_pack_includes_city() -> None:
    ctx = TemplateContext(
        site_type="local_service",
        country_code="LB",
        brand="Cafe X",
        topic="coffee",
        city="Beirut",
        region="",
        domain="",
        year="2026",
    )
    phrases = suggest_phrases(ctx, max_suggestions=50)
    joined = " ".join(phrases).lower()
    assert "beirut" in joined
    assert "cafe x" in joined
