"""Design token interpolation for QSS."""

from __future__ import annotations

from pathlib import Path

from crawlix.ui.design_tokens import substitute_qss_tokens
from crawlix.ui.styles import load_stylesheet


def test_substitute_removes_placeholder_markers_dark() -> None:
    raw = Path("src/crawlix/ui/styles/app_dark.qss").read_text(encoding="utf-8")
    out = substitute_qss_tokens(raw, "dark")
    assert "%%" not in out
    assert "#141a22" in out


def test_substitute_removes_placeholder_markers_light() -> None:
    raw = Path("src/crawlix/ui/styles/app_light.qss").read_text(encoding="utf-8")
    out = substitute_qss_tokens(raw, "light")
    assert "%%" not in out
    assert "#f6f4ef" in out


def test_load_stylesheet_includes_shell_selectors() -> None:
    qss = load_stylesheet("dark")
    assert "TopCommandStrip" in qss
    assert "PageHost" in qss
