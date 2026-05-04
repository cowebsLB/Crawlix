"""Tests for SERP-derived rank vs project domain (no network)."""

from crawlix.services.scraper.ranking_from_serp import (
    compute_rank_for_project_domain,
    effective_url_for_ranking,
    host_matches_project_domain,
)


def test_host_matches_subdomain() -> None:
    assert host_matches_project_domain("www.example.com", "example.com") is True
    assert host_matches_project_domain("example.com", "example.com") is True
    assert host_matches_project_domain("other.com", "example.com") is False


def test_effective_url_ddg_redirect() -> None:
    u = "https://duckduckgo.com/l/?uddg=https%3A%2F%2Fwww.example.com%2Fpath"
    out = effective_url_for_ranking(u)
    assert "example.com" in out


def test_compute_rank_first_match() -> None:
    organic = [
        {"url": "https://other.test/"},
        {"url": "https://www.example.com/page"},
    ]
    pos, murl = compute_rank_for_project_domain(organic, "example.com")
    assert pos == 2
    assert "example.com" in (murl or "")


def test_compute_rank_none_without_domain() -> None:
    organic = [{"url": "https://a.com/"}]
    pos, _ = compute_rank_for_project_domain(organic, None)
    assert pos is None


def test_compute_rank_via_ddg_wrapped_url() -> None:
    organic = [
        {
            "url": (
                "https://duckduckgo.com/l/?uddg="
                "https%3A%2F%2Fshop.example.com%2F"
            )
        },
    ]
    pos, _ = compute_rank_for_project_domain(organic, "example.com")
    assert pos == 1
