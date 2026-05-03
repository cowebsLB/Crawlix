"""Ollama HTTP client with timeout and optional ai_cache."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
from sqlalchemy.orm import Session

from crawlix.config import OLLAMA_DEFAULT_URL
from crawlix.db.models import AiCache


def _hash_prompt(model: str, prompt: str) -> str:
    h = hashlib.sha256()
    h.update(model.encode())
    h.update(b"\0")
    h.update(prompt.encode())
    return h.hexdigest()


def generate(
    session: Session | None,
    prompt: str,
    *,
    model: str = "qwen2.5:3b",
    base_url: str = OLLAMA_DEFAULT_URL,
    timeout_s: float = 120.0,
    use_cache: bool = True,
) -> str:
    ph = _hash_prompt(model, prompt)
    if session and use_cache:
        row = (
            session.query(AiCache)
            .filter(AiCache.prompt_hash == ph, AiCache.model == model)
            .first()
        )
        if row and (row.expires_at is None or row.expires_at > datetime.now(UTC)):
            return row.response_text

    url = base_url.rstrip("/") + "/api/generate"
    payload = {"model": model, "prompt": prompt, "stream": False}
    with httpx.Client(timeout=timeout_s) as client:
        r = client.post(url, json=payload)
        r.raise_for_status()
        data: dict[str, Any] = r.json()
    text = data.get("response") or json.dumps(data)

    if session and use_cache:
        session.add(
            AiCache(
                prompt_hash=ph,
                model=model,
                response_text=text,
                expires_at=datetime.now(UTC) + timedelta(days=7),
            )
        )
        session.commit()
    return text
