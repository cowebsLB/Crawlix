"""GitHub Releases metadata + SHA256 verification helpers."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import httpx

from crawlix.config import GITHUB_REPO_SLUG


def fetch_latest_release(*, token: str | None = None) -> dict[str, Any]:
    url = f"https://api.github.com/repos/{GITHUB_REPO_SLUG}/releases/latest"
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "Crawlix-Updater"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with httpx.Client(timeout=30.0) as client:
        r = client.get(url, headers=headers)
        r.raise_for_status()
        return r.json()


def verify_sha256(file_path: Path, expected_hex: str) -> bool:
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().lower() == expected_hex.strip().lower()
