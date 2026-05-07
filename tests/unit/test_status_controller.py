from crawlix.ui.controllers_status import citation_status_variant, serp_status_variant


def test_serp_status_variant_mapping() -> None:
    assert serp_status_variant("completed") == "success"
    assert serp_status_variant("captcha") == "warning"
    assert serp_status_variant("timeout") == "danger"
    assert serp_status_variant("unknown") == "neutral"


def test_citation_status_variant_mapping() -> None:
    assert citation_status_variant("ok") == "success"
    assert citation_status_variant("running") == "warning"
    assert citation_status_variant("blocked") == "danger"
    assert citation_status_variant("other") == "neutral"
