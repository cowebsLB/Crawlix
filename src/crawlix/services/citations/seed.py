"""Seed built-in citation_sources from bundled YAML."""

from __future__ import annotations

from pathlib import Path

import yaml
from sqlalchemy import select
from sqlalchemy.orm import Session

from crawlix.db.models import CitationSource
from crawlix.paths import find_repo_root


def seed_builtin_sources(session: Session, yaml_path: Path | None = None) -> int:
    path = yaml_path or (find_repo_root() / "resources" / "citation_sources_default.yaml")
    if not path.exists():
        return 0
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        return 0
    count = 0
    order = 0
    for row in data:
        name = row.get("name")
        if not name:
            continue
        exists = session.scalar(
            select(CitationSource.id)
            .where(
                CitationSource.is_builtin.is_(True),
                CitationSource.name == name,
                CitationSource.project_id.is_(None),
            )
            .limit(1)
        )
        if exists:
            continue
        session.add(
            CitationSource(
                project_id=None,
                is_builtin=True,
                name=name,
                template_url=row["template_url"],
                region_tags=row.get("region_tags"),
                requires_playwright=bool(row.get("requires_playwright", False)),
                enabled=True,
                pack_version=int(row.get("pack_version", 1)),
                sort_order=order,
            )
        )
        order += 1
        count += 1
    session.commit()
    return count
