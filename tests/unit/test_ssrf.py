import pytest

from crawlix.services.net.ssrf import assert_url_safe_for_fetch, host_is_blocked


def test_blocks_loopback() -> None:
    assert host_is_blocked("127.0.0.1") is True


def test_allows_public() -> None:
    assert host_is_blocked("example.com") is False


def test_assert_url_blocks_private() -> None:
    with pytest.raises(ValueError):
        assert_url_safe_for_fetch("http://192.168.1.1/", allow_private=False)


def test_assert_url_allows_when_flag() -> None:
    assert_url_safe_for_fetch("http://192.168.1.1/", allow_private=True)
