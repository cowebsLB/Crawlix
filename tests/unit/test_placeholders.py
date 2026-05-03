from crawlix.services.citations.placeholders import LocationFields, expand_template


def test_expand_known() -> None:
    loc = LocationFields(
        business_name="Joe's Pizza",
        city="Los Angeles",
        region="CA",
        postal_code="90001",
        country_code="us",
        primary_phone_e164="+13105551212",
    )
    out = expand_template("https://x.test/?q={business_query}&p={phone_digits}", loc)
    assert "13105551212" in out
    assert "Joe" in out or "%27" in out or "Pizza" in out
