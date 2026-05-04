"""Unit tests for citation URL templates (no network)."""

from crawlix.services.citations.placeholders import LocationFields, expand_template


def test_expand_template_yelp_style() -> None:
    loc = LocationFields(
        business_name="Joe's Pizza",
        city="Austin",
        region="TX",
        postal_code="78701",
        country_code="US",
        primary_phone_e164="+15551234567",
    )
    tpl = (
        "https://example.com/search?q={business_query}&loc={city}%2C%20{region}"
        "&zip={postal_code}&p={phone_digits}"
    )
    out = expand_template(tpl, loc)
    assert "78701" in out
    assert "15551234567" in out
    assert "example.com" in out
    assert "Austin" in out or "austin" in out.lower()


def test_expand_unknown_placeholder_raises() -> None:
    loc = LocationFields(
        business_name="X",
        city=None,
        region=None,
        postal_code=None,
        country_code=None,
        primary_phone_e164=None,
    )
    try:
        expand_template("https://x.com/{typo}", loc)
    except ValueError as e:
        assert "typo" in str(e).lower() or "unknown" in str(e).lower()
    else:
        raise AssertionError("expected ValueError")
