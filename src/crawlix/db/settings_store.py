"""Key-value settings in SQLite."""

from __future__ import annotations

from sqlalchemy.orm import Session

from crawlix.db.models import Setting


def get_value(session: Session, key: str, default: str | None = None) -> str | None:
    row = session.get(Setting, key)
    return row.value_text if row else default


def set_value(session: Session, key: str, value: str, value_type: str = "str") -> None:
    row = session.get(Setting, key)
    if row:
        row.value_text = value
        row.value_type = value_type
    else:
        session.add(Setting(key=key, value_text=value, value_type=value_type))
