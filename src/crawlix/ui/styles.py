"""Load QSS theme; semantic tokens are interpolated via design_tokens."""

from __future__ import annotations

from pathlib import Path

from crawlix.ui.design_tokens import substitute_qss_tokens


def load_stylesheet(mode: str) -> str:
    normalized = mode if mode == "light" else "dark"
    path = Path(__file__).parent / "styles" / ("app_light.qss" if normalized == "light" else "app_dark.qss")
    if path.exists():
        raw = path.read_text(encoding="utf-8")
        return substitute_qss_tokens(raw, normalized)  # type: ignore[arg-type]
    return substitute_qss_tokens(_FALLBACK_DARK_TEMPLATE, normalized)  # type: ignore[arg-type]


_FALLBACK_DARK_TEMPLATE = """
QWidget { font-size: 12pt; color: %%text_primary%%; }
QMainWindow, QDialog, QWizard, QWizardPage { background-color: %%surface_base%%; color: %%text_primary%%; }
QLabel { color: %%text_primary%%; background: transparent; }
QLineEdit, QTextEdit, QSpinBox, QComboBox {
  background-color: %%surface_sunken%%; color: %%text_inverse%%;
  border: 1px solid %%border_strong%%; padding: %%space_8%%;
  selection-background-color: %%accent_selection%%; selection-color: %%text_inverse%%;
}
QPushButton {
  background-color: %%accent_action%%; color: %%text_inverse%%;
  padding: %%space_8%% 16px;
}
"""
