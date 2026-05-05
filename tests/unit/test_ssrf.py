import socket

import httpx
import pytest

from crawlix.services.net.ssrf import (
    assert_url_safe_for_fetch,
    clear_ssrf_dns_cache,
    host_is_blocked,
    httpx_event_hooks_ssrf,
)


@pytest.fixture(autouse=True)
def _clear_ssrf_dns_cache() -> None:
    clear_ssrf_dns_cache()


def test_blocks_loopback() -> None:
    assert host_is_blocked("127.0.0.1") is True


def test_allows_public() -> None:
    assert host_is_blocked("example.com") is False


def test_assert_url_blocks_private() -> None:
    with pytest.raises(ValueError):
        assert_url_safe_for_fetch("http://192.168.1.1/", allow_private=False)


def test_assert_url_allows_when_flag() -> None:
    assert_url_safe_for_fetch("http://192.168.1.1/", allow_private=True)


def test_blocks_hostname_resolving_to_loopback(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_getaddrinfo(hostname: str, port: object, *args: object, **kwargs: object):
        _ = hostname, port
        return [(socket.AF_INET, socket.SOCK_STREAM, 0, "", ("127.0.0.1", 0))]

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)
    with pytest.raises(ValueError, match="Resolved address"):
        assert_url_safe_for_fetch("http://evil.example/")


def test_httpx_request_hook_blocks_url() -> None:
    hook = httpx_event_hooks_ssrf(allow_private=False)["request"][0]
    req = httpx.Request("GET", "http://127.0.0.1/x")
    with pytest.raises(ValueError):
        hook(req)


def test_allows_hostname_resolving_to_public(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_getaddrinfo(hostname: str, port: object, *args: object, **kwargs: object):
        _ = hostname, port
        return [(socket.AF_INET, socket.SOCK_STREAM, 0, "", ("8.8.8.8", 0))]

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)
    assert_url_safe_for_fetch("http://dns-test.example/")
