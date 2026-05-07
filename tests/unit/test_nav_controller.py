from crawlix.ui.controllers_nav import NAV_GROUPS, NAV_SLUGS, localized_nav_labels


def test_nav_groups_cover_each_slug_exactly_once() -> None:
    flattened = [slug for _, group_slugs in NAV_GROUPS for slug in group_slugs]
    assert sorted(flattened) == sorted(NAV_SLUGS)
    assert len(flattened) == len(set(flattened))


def test_localized_nav_labels_match_nav_slugs() -> None:
    labels = localized_nav_labels(lambda text: text)
    assert set(labels.keys()) == set(NAV_SLUGS)
    assert labels["keywords"] == "Keywords / SERP"
