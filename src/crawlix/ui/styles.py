"""Load QSS theme (semantic status colors)."""

from __future__ import annotations

from pathlib import Path


def load_stylesheet(mode: str) -> str:
    path = Path(__file__).parent / "styles" / ("app_dark.qss" if mode != "light" else "app_light.qss")
    if path.exists():
        return path.read_text(encoding="utf-8")
    return _FALLBACK_DARK


_FALLBACK_DARK = """
QWidget { font-size: 12pt; color: #e8e8e8; }
QMainWindow, QDialog, QWizard, QWizardPage { background-color: #252526; color: #e8e8e8; }
QLabel { color: #e8e8e8; background: transparent; }
QLineEdit, QTextEdit, QSpinBox, QComboBox {
  background-color: #1e1e1e; color: #ffffff; border: 1px solid #6a6a6a; padding: 6px;
  selection-background-color: #264f78; selection-color: #ffffff;
}
QPushButton { background-color: #0e639c; color: #ffffff; padding: 8px 16px; }
"""
