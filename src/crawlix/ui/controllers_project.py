"""Project selection/reload helpers for MainWindow."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from crawlix.db.models import Project


def project_choices(session: Session) -> list[tuple[int, str]]:
    """Return project choices as ``(id, name)`` ordered by name."""
    return [(int(p.id), p.name) for p in session.execute(select(Project).order_by(Project.name)).scalars()]
