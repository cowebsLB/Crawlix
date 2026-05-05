"""SERP page controller helpers."""

from __future__ import annotations


def serp_organic_count(results_json: object) -> int:
    if not isinstance(results_json, dict):
        return 0
    organic = results_json.get("organic")
    if isinstance(organic, list):
        return len(organic)
    return 0


def build_serp_row_meta(
    *,
    snapshot_id: int,
    phrase: str,
    status: str,
    fetched: str,
    organic_rows: int,
    has_html: bool,
) -> dict[str, object]:
    return {
        "id": int(snapshot_id),
        "phrase": str(phrase),
        "status": str(status),
        "fetched": str(fetched),
        "organic_rows": int(organic_rows),
        "has_html": bool(has_html),
    }
