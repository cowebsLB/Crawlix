"""URL-safe project slug generation."""

from __future__ import annotations

import re
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from crawlix.db.models import Project


def slugify(name: str, *, max_len: int = 200) -> str:
    raw = "".join(c if c.isalnum() or c in " -_" else "" for c in name.strip().lower())
    raw = re.sub(r"[\s_]+", "-", raw)
    while "--" in raw:
        raw = raw.replace("--", "-")
    raw = raw.strip("-")[:max_len]
    return raw or "project"


def unique_project_slug(session: Session, name: str) -> str:
    base = slugify(name)
    for i in range(500):
        candidate = base if i == 0 else f"{base}-{i}"
        exists = session.scalar(select(Project.id).where(Project.slug == candidate))
        if exists is None:
            return candidate
    return f"{base}-{uuid.uuid4().hex[:10]}"
