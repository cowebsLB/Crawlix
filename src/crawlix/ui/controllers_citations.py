"""Citations page controller helpers."""

from __future__ import annotations


def clipped_url(url: str, *, max_len: int = 80) -> str:
    if len(url) <= max_len:
        return url
    return url[: max_len - 3] + "..."


def clipped_error(err: str, *, max_len: int = 120) -> str:
    if len(err) <= max_len:
        return err
    return err[:max_len]


def build_citation_check_row_meta(
    *,
    check_id: int,
    fetched: str,
    location: str,
    source: str,
    status: str,
    http_status: int | None,
    final_url: str,
    error: str,
) -> dict[str, object]:
    return {
        "id": int(check_id),
        "fetched": str(fetched),
        "location": str(location),
        "source": str(source),
        "status": str(status),
        "http_status": http_status,
        "final_url": str(final_url),
        "error": str(error),
    }
