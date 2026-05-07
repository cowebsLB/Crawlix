"""Status-to-variant mapping helpers for UI pills."""

from __future__ import annotations


def serp_status_variant(status: str) -> str:
    s = status.lower()
    if s in {"ok", "success", "completed"}:
        return "success"
    if s in {"degraded", "partial", "captcha", "empty"}:
        return "warning"
    if s in {"failed", "error", "timeout", "blocked"}:
        return "danger"
    return "neutral"


def citation_status_variant(status: str) -> str:
    s = status.lower()
    if s in {"ok", "success", "completed"}:
        return "success"
    if s in {"blocked", "failed", "error", "timeout"}:
        return "danger"
    if s in {"degraded", "queued", "running"}:
        return "warning"
    return "neutral"
